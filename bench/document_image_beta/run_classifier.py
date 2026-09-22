"""Run a conservative vision classifier for document-image routing."""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from openai import AzureOpenAI


CLASSES = ("document_image", "medical_image", "mixed", "unknown")
CLASSIFICATION_SCHEMA = {
    "type": "object",
    "properties": {
        "classification": {"type": "string", "enum": list(CLASSES)},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "evidence": {
            "type": "array",
            "items": {"type": "string"},
            "maxItems": 4,
        },
    },
    "required": ["classification", "confidence", "evidence"],
    "additionalProperties": False,
}
SYSTEM_PROMPT = """You route medical uploads; you do not diagnose.
Classify the image by its PRIMARY visual content:
- document_image: a photographed or scanned page whose main content is readable prose, tables, or report text.
- medical_image: clinical visual evidence such as X-ray, CT, MRI, ultrasound, pathology, dermatology, fundoscopy, ECG, or endoscopy. Small labels and annotations do not make it a document.
- mixed: substantial report text and a substantial medical image share the same canvas.
- unknown: insufficient evidence, unrelated content, or ambiguous.

Be conservative. Never call an image document_image merely because it contains labels.
Return confidence as a calibrated probability for the selected class."""

V1_CLASSES = ("document_only", "contains_medical_visual", "unknown")
V1_CLASSIFICATION_SCHEMA = {
    "type": "object",
    "properties": {
        "classification": {"type": "string", "enum": list(V1_CLASSES)},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "has_document_text": {"type": "boolean"},
        "has_medical_visual": {"type": "boolean"},
        "evidence": {
            "type": "array",
            "items": {"type": "string"},
            "maxItems": 4,
        },
    },
    "required": [
        "classification",
        "confidence",
        "has_document_text",
        "has_medical_visual",
        "evidence",
    ],
    "additionalProperties": False,
}
V1_SYSTEM_PROMPT = """You route uploads for a medical diagnostic product. Do not diagnose.

Determine whether the image is exclusively a text document or contains any
meaningful medical visual evidence.

Return document_only only when:
- the useful content is exclusively prose, forms, tables, or laboratory values;
- there is no radiograph, CT, MRI, ultrasound, pathology, dermatology,
  fundoscopy, endoscopy, ECG, clinical photograph, medical chart, plot, or
  other visual evidence that Terra should inspect.

Return contains_medical_visual when any medically meaningful visual is present,
even if the same canvas also contains substantial report text. Small labels,
arrows, measurements, and image annotations belong to the medical visual and
must not cause it to be treated as a text-only document.

Set has_document_text=true only for substantial standalone clinical prose,
forms, tables, or laboratory values worth extracting with OCR. Keep it false
for labels, arrows, measurements, legends, and annotations alone.

Return unknown whenever the distinction is uncertain. Prefer unknown over
document_only."""


class ClassifierError(RuntimeError):
    """Raised when the classifier manifest or configuration is invalid."""


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=root / "generated" / "classification_manifest.yaml",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=root / "outputs" / "classification.jsonl",
    )
    parser.add_argument(
        "--deployment",
        default=os.getenv("DOCUMENT_IMAGE_CLASSIFIER_DEPLOYMENT", ""),
    )
    parser.add_argument("--threshold", type=float, default=0.9)
    parser.add_argument(
        "--policy",
        choices=("legacy", "v1"),
        default="legacy",
        help="Use the legacy benchmark policy or the exact production V1 policy.",
    )
    parser.add_argument("--limit", type=int)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def load_manifest(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ClassifierError(f"Manifest does not exist: {path}")
    with path.open("r", encoding="utf-8") as stream:
        manifest = yaml.safe_load(stream)
    if not isinstance(manifest, dict) or not isinstance(manifest.get("assets"), list):
        raise ClassifierError("Manifest requires an assets list")
    return manifest


def resolve_asset(manifest_path: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    if not path.is_absolute():
        path = manifest_path.parent / path
    path = path.resolve()
    if not path.is_file():
        raise ClassifierError(f"Image does not exist: {path}")
    return path


def route_for_prediction(
    classification: str,
    confidence: float,
    threshold: float,
    policy: str = "legacy",
    prediction: dict[str, Any] | None = None,
) -> str:
    """Enable additive OCR only for high-confidence document-bearing images."""
    if policy == "v1":
        prediction = prediction or {}
        is_consistent_document = (
            classification == "document_only"
            and prediction.get("has_document_text") is True
            and prediction.get("has_medical_visual") is False
        )
        is_mixed_document = (
            classification == "contains_medical_visual"
            and prediction.get("has_document_text") is True
            and prediction.get("has_medical_visual") is True
        )
        if confidence >= threshold:
            if is_consistent_document:
                return "ocr_text"
            if is_mixed_document:
                return "ocr_plus_image"
        return "direct_vision"
    if classification in {"document_image", "mixed"} and confidence >= threshold:
        return "ocr_plus_image"
    return "direct_vision"


def expected_for_policy(
    asset: dict[str, Any],
    policy: str,
    mixed_source_ids: set[str] | None = None,
) -> tuple[str, str]:
    expected_class = str(asset.get("expected_class") or "unknown")
    if policy != "v1":
        return expected_class, str(asset.get("expected_route") or "direct_vision")
    source_case_id = str((asset.get("metadata") or {}).get("source_case_id") or "")
    if source_case_id and source_case_id in (mixed_source_ids or set()):
        return "contains_medical_visual", "ocr_plus_image"
    if expected_class == "document_image":
        return "document_only", "ocr_text"
    if expected_class in {"medical_image", "mixed"}:
        return "contains_medical_visual", "direct_vision"
    return "unknown", "direct_vision"


def image_data_url(path: Path) -> str:
    mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    if not mime_type.startswith("image/"):
        raise ClassifierError(f"Classifier only accepts image files: {path}")
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def create_client(deployment: str) -> tuple[AzureOpenAI, str]:
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "").strip()
    api_key = os.getenv("AZURE_OPENAI_API_KEY", "").strip()
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")
    if not endpoint or not api_key or not deployment:
        raise ClassifierError(
            "Set AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY and "
            "DOCUMENT_IMAGE_CLASSIFIER_DEPLOYMENT (or --deployment)"
        )
    return (
        AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
        ),
        deployment,
    )


def classify(
    client: AzureOpenAI,
    deployment: str,
    image_path: Path,
    policy: str = "legacy",
) -> tuple[dict[str, Any], dict[str, int]]:
    system_prompt = V1_SYSTEM_PROMPT if policy == "v1" else SYSTEM_PROMPT
    schema = V1_CLASSIFICATION_SCHEMA if policy == "v1" else CLASSIFICATION_SCHEMA
    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Classify this upload for safe routing.",
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_data_url(image_path),
                            "detail": "low",
                        },
                    },
                ],
            },
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "document_image_routing",
                "strict": True,
                "schema": schema,
            },
        },
        **({"reasoning_effort": "low"} if policy == "v1" else {}),
    )
    content = response.choices[0].message.content
    if not content:
        raise ClassifierError("Classifier returned an empty response")
    result = json.loads(content)
    usage = response.usage
    return result, {
        "input_tokens": int(getattr(usage, "prompt_tokens", 0) or 0),
        "output_tokens": int(getattr(usage, "completion_tokens", 0) or 0),
        "total_tokens": int(getattr(usage, "total_tokens", 0) or 0),
    }


def main() -> int:
    load_dotenv()
    args = parse_args()
    if not 0 < args.threshold <= 1:
        raise ClassifierError("--threshold must be greater than 0 and at most 1")

    manifest_path = args.manifest.resolve()
    assets = load_manifest(manifest_path)["assets"]
    mixed_source_ids = {
        str((asset.get("metadata") or {}).get("source_case_id") or "")
        for asset in assets
        if asset.get("expected_class") == "mixed"
    }
    mixed_source_ids.discard("")
    if args.limit:
        assets = assets[: args.limit]
    validated = [
        (asset, resolve_asset(manifest_path, str(asset.get("path") or "")))
        for asset in assets
    ]
    print(f"Validated {len(validated)} classification asset(s)")
    if args.dry_run:
        counts: dict[str, int] = {}
        for asset, path in validated:
            expected = str(asset.get("expected_class") or "missing")
            counts[expected] = counts.get(expected, 0) + 1
            print(f"{asset['id']}: {expected} — {path.name}")
        print("Expected classes:", json.dumps(counts, sort_keys=True))
        return 0

    client, deployment = create_client(args.deployment)
    output_path = args.output.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    failures = 0
    with output_path.open("w", encoding="utf-8") as stream:
        for index, (asset, image_path) in enumerate(validated, start=1):
            started = time.monotonic()
            try:
                prediction, usage = classify(
                    client,
                    deployment,
                    image_path,
                    args.policy,
                )
                predicted_class = str(prediction["classification"])
                confidence = float(prediction["confidence"])
                expected_class, expected_route = expected_for_policy(
                    asset,
                    args.policy,
                    mixed_source_ids,
                )
                record = {
                    "id": str(asset["id"]),
                    "status": "success",
                    "expected_class": expected_class,
                    "expected_route": expected_route,
                    "predicted_class": predicted_class,
                    "confidence": confidence,
                    "predicted_route": route_for_prediction(
                        predicted_class,
                        confidence,
                        args.threshold,
                        args.policy,
                        prediction,
                    ),
                    "evidence": prediction["evidence"],
                    "latency_seconds": round(time.monotonic() - started, 3),
                    "usage": usage,
                    "model": deployment,
                    "policy": args.policy,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "metadata": asset.get("metadata") or {},
                }
            except Exception as error:
                failures += 1
                expected_class, expected_route = expected_for_policy(
                    asset,
                    args.policy,
                    mixed_source_ids,
                )
                record = {
                    "id": str(asset.get("id") or ""),
                    "status": "error",
                    "expected_class": expected_class,
                    "expected_route": expected_route,
                    "predicted_class": "unknown",
                    "confidence": 0.0,
                    "predicted_route": "direct_vision",
                    "latency_seconds": round(time.monotonic() - started, 3),
                    "error": f"{type(error).__name__}: {error}",
                    "model": deployment,
                    "policy": args.policy,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "metadata": asset.get("metadata") or {},
                }
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
            stream.flush()
            print(
                f"[{index}/{len(validated)}] {record['id']}: "
                f"{record['predicted_class']} -> {record['predicted_route']}"
            )

    print(f"Saved results to {output_path}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
