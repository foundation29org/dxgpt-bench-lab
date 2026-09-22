"""Evaluate routing safety and end-to-end fact preservation."""

from __future__ import annotations

import argparse
import json
import math
import re
import statistics
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


class EvaluationError(RuntimeError):
    """Raised when benchmark outputs are missing or malformed."""


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--classification-results",
        type=Path,
        default=root / "outputs" / "classification.jsonl",
    )
    parser.add_argument("--product-responses", type=Path)
    parser.add_argument(
        "--product-only",
        action="store_true",
        help="Evaluate product responses without requiring classifier results.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=root / "outputs" / "evaluation.md",
    )
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise EvaluationError(f"JSONL file does not exist: {path}")
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as error:
                raise EvaluationError(f"Invalid JSON at {path}:{line_number}") from error
            if not isinstance(record, dict):
                raise EvaluationError(f"Expected an object at {path}:{line_number}")
            records.append(record)
    if not records:
        raise EvaluationError(f"No records found in {path}")
    return records


def ratio(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def percentile(values: list[float], percentile_value: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil(percentile_value * len(ordered)) - 1))
    return ordered[index]


def classification_metrics(records: list[dict[str, Any]]) -> dict[str, Any]:
    successful = [record for record in records if record.get("status") == "success"]
    policy = (
        "v1"
        if any(record.get("policy") == "v1" for record in records)
        else "legacy"
    )
    if policy == "v1":
        mixed_source_ids = {
            str((record.get("metadata") or {}).get("source_case_id") or "")
            for record in successful
            if (record.get("metadata") or {}).get("artifact_type") == "mixed"
        }
        mixed_source_ids.discard("")
        successful = [
            {
                **record,
                "expected_class": "contains_medical_visual",
                "expected_route": "ocr_plus_image",
            }
            if str((record.get("metadata") or {}).get("source_case_id") or "")
            in mixed_source_ids
            else record
            for record in successful
        ]
    confusion: dict[str, Counter[str]] = defaultdict(Counter)
    route_correct = 0
    class_correct = 0
    expected_counts: Counter[str] = Counter()
    for record in successful:
        expected_class = str(record.get("expected_class") or "unknown")
        predicted_class = str(record.get("predicted_class") or "unknown")
        expected_counts[expected_class] += 1
        confusion[expected_class][predicted_class] += 1
        class_correct += expected_class == predicted_class
        route_correct += record.get("expected_route") == record.get("predicted_route")

    medical_class = (
        "contains_medical_visual" if policy == "v1" else "medical_image"
    )
    document_class = "document_only" if policy == "v1" else "document_image"
    medical = [
        record for record in successful
        if record.get("expected_class") == medical_class and (
            policy != "v1" or record.get("expected_route") == "direct_vision"
        )
    ]
    documents = [
        record for record in successful
        if record.get("expected_class") == document_class
    ]
    mixed = (
        [
            record for record in successful
            if record.get("expected_class") == medical_class
            and record.get("expected_route") == "ocr_plus_image"
        ]
        if policy == "v1"
        else [
            record for record in successful
            if record.get("expected_class") == "mixed"
        ]
    )
    document_ocr_routes = (
        {"ocr_text"} if policy == "v1" else {"ocr_plus_image"}
    )
    unsafe_ocr_routes = (
        {"ocr_text", "ocr_plus_image"}
        if policy == "v1"
        else {"ocr_plus_image"}
    )
    unsafe_medical = [
        record for record in medical
        if record.get("predicted_route") in unsafe_ocr_routes
    ]
    routed_documents = [
        record for record in documents
        if record.get("predicted_route") in document_ocr_routes
    ]
    routed_mixed = [
        record for record in mixed
        if record.get("predicted_route") == "ocr_plus_image"
    ]
    latencies = [
        float(record.get("latency_seconds") or 0)
        for record in successful
    ]
    per_class = {
        expected: {
            "support": support,
            "recall": ratio(confusion[expected][expected], support),
        }
        for expected, support in sorted(expected_counts.items())
    }
    metrics = {
        "records": len(records),
        "policy": policy,
        "successful": len(successful),
        "coverage": ratio(len(successful), len(records)),
        "class_accuracy": ratio(class_correct, len(successful)),
        "route_accuracy": ratio(route_correct, len(successful)),
        "document_ocr_recall": ratio(len(routed_documents), len(documents)),
        "mixed_ocr_recall": (
            ratio(len(routed_mixed), len(mixed)) if mixed else 1.0
        ),
        "unsafe_medical_ocr_rate": ratio(len(unsafe_medical), len(medical)),
        "latency_mean_seconds": statistics.mean(latencies) if latencies else 0.0,
        "latency_p95_seconds": percentile(latencies, 0.95),
        "per_class": per_class,
        "confusion": {
            expected: dict(sorted(predictions.items()))
            for expected, predictions in sorted(confusion.items())
        },
        "unsafe_medical_ids": [str(record.get("id")) for record in unsafe_medical],
    }
    metrics["acceptance"] = {
        "coverage_at_least_95pct": metrics["coverage"] >= 0.95,
        "document_ocr_recall_at_least_90pct": metrics["document_ocr_recall"] >= 0.90,
        "unsafe_medical_ocr_is_zero": metrics["unsafe_medical_ocr_rate"] == 0,
        "mixed_ocr_recall_at_least_90pct": (
            metrics["mixed_ocr_recall"] >= 0.90
        ),
    }
    metrics["passed"] = all(metrics["acceptance"].values())
    return metrics


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).casefold()
    normalized = "".join(character for character in normalized if not unicodedata.combining(character))
    return " ".join(re.findall(r"\d+(?:\.\d+)?|[a-z]+", normalized))


def contains_fact(description: str, fact: str) -> bool:
    """Match normalized fact tokens in order while allowing minor paraphrasing."""
    description_tokens = normalize_text(description).split()
    fact_tokens = normalize_text(fact).split()
    if not fact_tokens:
        return False
    position = 0
    for token in fact_tokens:
        try:
            position = description_tokens.index(token, position) + 1
        except ValueError:
            return False
    return True


def text_values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        values: list[str] = []
        for item in value:
            values.extend(text_values(item))
        return values
    if isinstance(value, dict):
        values = []
        for item in value.values():
            values.extend(text_values(item))
        return values
    return []


def product_metrics(
    records: list[dict[str, Any]],
    mixed_source_ids: set[str] | None = None,
) -> dict[str, Any]:
    by_artifact: dict[str, list[float]] = defaultdict(list)
    diagnostic_coverage_by_artifact: dict[str, list[float]] = defaultdict(list)
    literal_top1_by_artifact: dict[str, list[float]] = defaultdict(list)
    latency_by_artifact: dict[str, list[float]] = defaultdict(list)
    case_scores: list[dict[str, Any]] = []
    mixed_source_ids = mixed_source_ids or set()
    successful = 0
    for record in records:
        metadata = record.get("metadata") or {}
        expected_facts = [str(value) for value in metadata.get("expected_facts") or []]
        final_response = record.get("final_response") or {}
        description = "\n".join(
            [
                str((record.get("http_response") or {}).get("description") or ""),
                *text_values(final_response),
            ]
        )
        found = [
            fact
            for fact in expected_facts
            if contains_fact(description, fact)
        ]
        score = ratio(len(found), len(expected_facts))
        artifact_type = str(metadata.get("artifact_type") or "unknown")
        diagnoses = final_response.get("data") or []
        has_diagnosis = bool(diagnoses)
        predicted_top1 = (
            str(diagnoses[0].get("diagnosis") or "")
            if diagnoses and isinstance(diagnoses[0], dict)
            else ""
        )
        gold_names = [
            str(item.get("name") or "")
            for item in (record.get("gold") or {}).get("diagnoses") or []
            if isinstance(item, dict)
        ]
        literal_top1_match = bool(predicted_top1) and any(
            normalize_text(predicted_top1) == normalize_text(gold)
            for gold in gold_names
        )
        by_artifact[artifact_type].append(score)
        diagnostic_coverage_by_artifact[artifact_type].append(float(has_diagnosis))
        literal_top1_by_artifact[artifact_type].append(float(literal_top1_match))
        duration_seconds = float(record.get("duration_seconds") or 0)
        latency_by_artifact[artifact_type].append(duration_seconds)
        input_data = record.get("inputs") or {}
        is_image = bool(input_data.get("images"))
        source_case_id = str(metadata.get("source_case_id") or "")
        expected_image_route = (
            str(metadata.get("expected_image_route") or "") or (
                "vision"
                if source_case_id in mixed_source_ids
                else "ocr_text"
            )
        ) if is_image else None
        image_routing = (record.get("http_response") or {}).get("imageRouting") or []
        actual_image_route = (
            str(image_routing[0].get("route") or "")
            if image_routing and isinstance(image_routing[0], dict)
            else None
        )
        ocr_status = (
            str((image_routing[0].get("ocr") or {}).get("status") or "")
            if image_routing and isinstance(image_routing[0], dict)
            else None
        )
        ocr_text_used = (
            image_routing[0].get("ocrTextUsed") is True
            if image_routing and isinstance(image_routing[0], dict)
            else False
        )
        successful += record.get("status") == "success"
        case_scores.append(
            {
                "id": str(record.get("case_id") or ""),
                "artifact_type": artifact_type,
                "fact_recall": score,
                "has_diagnosis": has_diagnosis,
                "literal_top1_match": literal_top1_match,
                "duration_seconds": duration_seconds,
                "expected_image_route": expected_image_route,
                "actual_image_route": actual_image_route,
                "ocr_status": ocr_status,
                "ocr_text_used": ocr_text_used,
                "missing_facts": [fact for fact in expected_facts if fact not in found],
                "status": record.get("status"),
            }
        )

    latencies = [case["duration_seconds"] for case in case_scores]
    image_cases = [
        case for case in case_scores
        if case["expected_image_route"] is not None
    ]
    document_images = [
        case for case in image_cases
        if case["expected_image_route"] == "ocr_text"
    ]
    mixed_images = [
        case for case in image_cases
        if case["expected_image_route"] == "vision"
    ]
    return {
        "records": len(records),
        "technical_success_rate": ratio(successful, len(records)),
        "fact_recall_mean": statistics.mean(
            [case["fact_recall"] for case in case_scores]
        ),
        "fact_recall_by_artifact": {
            artifact: statistics.mean(scores)
            for artifact, scores in sorted(by_artifact.items())
        },
        "diagnostic_coverage": statistics.mean(
            [float(case["has_diagnosis"]) for case in case_scores]
        ),
        "diagnostic_coverage_by_artifact": {
            artifact: statistics.mean(scores)
            for artifact, scores in sorted(diagnostic_coverage_by_artifact.items())
        },
        "literal_top1_match_rate": statistics.mean(
            [float(case["literal_top1_match"]) for case in case_scores]
        ),
        "literal_top1_by_artifact": {
            artifact: statistics.mean(scores)
            for artifact, scores in sorted(literal_top1_by_artifact.items())
        },
        "latency_mean_seconds": statistics.mean(latencies) if latencies else 0.0,
        "latency_p95_seconds": percentile(latencies, 0.95),
        "latency_by_artifact": {
            artifact: {
                "mean_seconds": statistics.mean(values),
                "p95_seconds": percentile(values, 0.95),
            }
            for artifact, values in sorted(latency_by_artifact.items())
        },
        "image_route_accuracy": ratio(
            sum(
                case["actual_image_route"] == case["expected_image_route"]
                for case in image_cases
            ),
            len(image_cases),
        ),
        "document_image_ocr_recall": ratio(
            sum(case["actual_image_route"] == "ocr_text" for case in document_images),
            len(document_images),
        ),
        "mixed_image_vision_recall": ratio(
            sum(case["actual_image_route"] == "vision" for case in mixed_images),
            len(mixed_images),
        ),
        "mixed_image_hybrid_success": ratio(
            sum(
                case["actual_image_route"] == "vision"
                and case["ocr_text_used"]
                and case["ocr_status"] == "succeeded"
                for case in mixed_images
            ),
            len(mixed_images),
        ),
        "fact_recall_document_images": (
            statistics.mean(case["fact_recall"] for case in document_images)
            if document_images else 0.0
        ),
        "fact_recall_mixed_images": (
            statistics.mean(case["fact_recall"] for case in mixed_images)
            if mixed_images else 0.0
        ),
        "diagnostic_coverage_document_images": (
            statistics.mean(
                float(case["has_diagnosis"]) for case in document_images
            )
            if document_images else 0.0
        ),
        "diagnostic_coverage_mixed_images": (
            statistics.mean(
                float(case["has_diagnosis"]) for case in mixed_images
            )
            if mixed_images else 0.0
        ),
        "document_image_ocr_success": ratio(
            sum(case["ocr_status"] == "succeeded" for case in document_images),
            len(document_images),
        ),
        "unsafe_mixed_image_ids": [
            case["id"]
            for case in mixed_images
            if case["actual_image_route"] != "vision"
        ],
        "cases": case_scores,
    }


def percentage(value: float) -> str:
    return f"{value * 100:.1f}%"


def classification_markdown(metrics: dict[str, Any]) -> list[str]:
    lines = [
        "# Document-image routing benchmark",
        "",
        f"Overall status: **{'PASS' if metrics['passed'] else 'FAIL'}**",
        "",
        f"- Coverage: {percentage(metrics['coverage'])}",
        f"- Class accuracy: {percentage(metrics['class_accuracy'])}",
        f"- Route accuracy: {percentage(metrics['route_accuracy'])}",
        f"- Document OCR recall: {percentage(metrics['document_ocr_recall'])}",
        f"- Mixed-image OCR recall: "
        f"{percentage(metrics['mixed_ocr_recall'])}",
        f"- Unsafe OCR on medical images: "
        f"{percentage(metrics['unsafe_medical_ocr_rate'])}",
        f"- Mean / p95 latency: {metrics['latency_mean_seconds']:.2f}s / "
        f"{metrics['latency_p95_seconds']:.2f}s",
        "",
        "## Acceptance gates",
        "",
    ]
    for name, passed in metrics["acceptance"].items():
        lines.append(f"- [{'x' if passed else ' '}] {name}")
    lines.extend(["", "## Recall by class", ""])
    for name, values in metrics["per_class"].items():
        lines.append(
            f"- {name}: {percentage(values['recall'])} (n={values['support']})"
        )
    if metrics["unsafe_medical_ids"]:
        lines.extend(
            [
                "",
                "## Unsafe medical-image routes",
                "",
                *[f"- {case_id}" for case_id in metrics["unsafe_medical_ids"]],
            ]
        )
    return lines


def product_markdown(metrics: dict[str, Any]) -> list[str]:
    lines = [
        "",
        "# End-to-end document fidelity",
        "",
        f"- Technical success: {percentage(metrics['technical_success_rate'])}",
        f"- Mean exact fact recall: {percentage(metrics['fact_recall_mean'])}",
        f"- Diagnostic coverage: {percentage(metrics['diagnostic_coverage'])}",
        f"- Literal top-1 name match (not clinical equivalence): "
        f"{percentage(metrics['literal_top1_match_rate'])}",
        f"- Image route accuracy: {percentage(metrics['image_route_accuracy'])}",
        f"- Document-image OCR recall: "
        f"{percentage(metrics['document_image_ocr_recall'])}",
        f"- Document-image OCR success: "
        f"{percentage(metrics['document_image_ocr_success'])}",
        f"- Mixed-image vision recall: "
        f"{percentage(metrics['mixed_image_vision_recall'])}",
        f"- Mixed-image OCR + vision success: "
        f"{percentage(metrics['mixed_image_hybrid_success'])}",
        f"- Document-image facts / diagnostic coverage: "
        f"{percentage(metrics['fact_recall_document_images'])} / "
        f"{percentage(metrics['diagnostic_coverage_document_images'])}",
        f"- Mixed-image facts / diagnostic coverage: "
        f"{percentage(metrics['fact_recall_mixed_images'])} / "
        f"{percentage(metrics['diagnostic_coverage_mixed_images'])}",
        f"- Mean / p95 end-to-end latency: "
        f"{metrics['latency_mean_seconds']:.2f}s / "
        f"{metrics['latency_p95_seconds']:.2f}s",
        "",
        "## Metrics by artifact",
        "",
    ]
    for artifact, score in metrics["fact_recall_by_artifact"].items():
        lines.append(
            f"- {artifact}: facts {percentage(score)}, "
            f"diagnostic coverage "
            f"{percentage(metrics['diagnostic_coverage_by_artifact'][artifact])}, "
            f"literal top-1 "
            f"{percentage(metrics['literal_top1_by_artifact'][artifact])}, "
            f"mean/p95 latency "
            f"{metrics['latency_by_artifact'][artifact]['mean_seconds']:.2f}s/"
            f"{metrics['latency_by_artifact'][artifact]['p95_seconds']:.2f}s"
        )
    if metrics["unsafe_mixed_image_ids"]:
        lines.extend(
            [
                "",
                "## Unsafe mixed-image routes",
                "",
                *[
                    f"- {case_id}"
                    for case_id in metrics["unsafe_mixed_image_ids"]
                ],
            ]
        )
    missing = [case for case in metrics["cases"] if case["missing_facts"]]
    if missing:
        lines.extend(["", "## Missing expected facts", ""])
        for case in missing:
            lines.append(
                f"- {case['id']}: " + "; ".join(case["missing_facts"])
            )
    return lines


def main() -> int:
    args = parse_args()
    if args.product_only and not args.product_responses:
        raise EvaluationError("--product-only requires --product-responses")

    classification = None
    mixed_source_ids: set[str] = set()
    report: list[str] = []
    if not args.product_only:
        classification_records = read_jsonl(
            args.classification_results.resolve()
        )
        classification = classification_metrics(classification_records)
        mixed_source_ids = {
            str((record.get("metadata") or {}).get("source_case_id") or "")
            for record in classification_records
            if (record.get("metadata") or {}).get("artifact_type") == "mixed"
        }
        mixed_source_ids.discard("")
        report = classification_markdown(classification)

    product = None
    if args.product_responses:
        product = product_metrics(
            read_jsonl(args.product_responses.resolve()),
            mixed_source_ids,
        )
        report.extend(product_markdown(product))

    output_path = args.output.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    metrics_path = output_path.with_suffix(".json")
    metrics_path.write_text(
        json.dumps(
            {
                "classification": classification,
                "product": product,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Saved evaluation to {output_path}")
    return 0 if classification is None or classification["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
