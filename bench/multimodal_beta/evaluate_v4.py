"""Evaluate beta API responses with Pipeline V4's medical matching stack."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


HERE = Path(__file__).resolve().parent
EVAL_ROOT = HERE.parents[1]
PIPELINE_DIR = EVAL_ROOT / "bench" / "pipelines" / "pipeline_v4 - fork" / "main"
sys.path.insert(0, str(EVAL_ROOT))
sys.path.insert(0, str(PIPELINE_DIR))

from evaluator import (  # noqa: E402
    DiagnosticEvaluator,
    EvaluationResult,
    calculate_global_statistics,
    generate_evaluation_details,
    generate_summary_json,
    setup_logging,
)
from medlabeler import MedicalLabeler  # noqa: E402


class AdapterError(RuntimeError):
    """Raised when beta responses cannot be converted safely."""


class StrictMultimodalEvaluator(DiagnosticEvaluator):
    """Pipeline V4 evaluator with a diagnosis-equivalence judge."""

    def _get_llm_judgment(
        self, gdx_text: str, ddx_texts: list[str]
    ) -> dict[str, Any]:
        ddx_options = "\n".join(
            f"{index}. {text}" for index, text in enumerate(ddx_texts, start=1)
        )
        prompt = f"""You are a medical expert validating diagnostic equivalence.

Reference diagnosis: {gdx_text}

Differential diagnosis options:
{ddx_options}

Select an option only if it denotes the same disease entity as the reference
diagnosis. Accept synonyms, abbreviations, spelling variants, and a more
specific form that still preserves the reference diagnosis.

Do NOT accept an option merely because it:
- has a similar presentation, anatomical site, mechanism, or treatment;
- belongs to the differential diagnosis;
- is a different subtype, cause, complication, precursor, or related disease;
- shares a broad parent category while changing the actual diagnosis.

Respond with ONLY the number (1-{len(ddx_texts)}) of the equivalent option.
If none are diagnostically equivalent, respond with "0".

Answer:"""
        try:
            if self.is_judge_gemini:
                response = self.llm.generate(
                    prompt,
                    thinking_level=self.judge_thinking_level,
                    max_tokens=self.judge_max_tokens,
                    temperature=self.judge_temperature,
                )
            elif self.is_judge_reasoning:
                response = self.llm.generate(
                    prompt,
                    reasoning_effort=self.judge_reasoning_effort,
                    max_tokens=self.judge_max_tokens,
                )
            else:
                response = self.llm.generate(
                    prompt,
                    max_tokens=self.judge_max_tokens,
                    temperature=self.judge_temperature,
                )
            position = int(str(response).strip())
            if 1 <= position <= len(ddx_texts):
                return {"position": position}
        except (TypeError, ValueError):
            pass
        except Exception as error:
            if self.logger:
                self.logger.error("Strict LLM judgment failed: %s", error)
        return {"position": None}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Normalize beta diagnoses with MedLabeler and evaluate through "
            "SNOMED, ICD-10, SapBERT, and an LLM judge."
        )
    )
    parser.add_argument("--responses", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument(
        "--reuse-labeled",
        type=Path,
        help="Reuse a prior MedLabeler JSON and run only the evaluator.",
    )
    parser.add_argument(
        "--gold-scope",
        choices=("primary", "all"),
        default="primary",
        help="Use the primary diagnosis only (canonical) or all MedReaMM diagnoses.",
    )
    parser.add_argument("--judge-model", default="gemini-2.5-pro")
    parser.add_argument(
        "--judge-mode",
        choices=("strict_equivalence", "legacy_similarity"),
        default="strict_equivalence",
        help="Diagnostic equivalence is canonical; legacy is a comparison bridge.",
    )
    parser.add_argument("--workers", type=int, default=8)
    return parser.parse_args()


def load_responses(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise AdapterError(f"Responses file does not exist: {path}")
    records_by_id: dict[str, dict[str, Any]] = {}
    ordered_ids: list[str] = []
    with path.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as error:
                raise AdapterError(
                    f"Invalid JSON on line {line_number} of {path}"
                ) from error
            case_id = str(row.get("case_id") or "").strip()
            if not case_id:
                raise AdapterError(
                    f"Response on line {line_number} has no case ID"
                )
            if case_id not in records_by_id:
                ordered_ids.append(case_id)
                records_by_id[case_id] = row
            elif row.get("status") == "success":
                # Resumed runs append the successful retry after the failed
                # attempt. Keep one canonical record per case.
                records_by_id[case_id] = row

    if not ordered_ids:
        raise AdapterError(f"No response records found in {path}")
    rows = [records_by_id[case_id] for case_id in ordered_ids]
    failed = [row for row in rows if row.get("status") != "success"]
    if failed:
        preview = ", ".join(str(row.get("case_id")) for row in failed[:10])
        raise AdapterError(
            f"{len(failed)} case(s) have no successful response: {preview}"
        )
    return rows


def select_gold(
    diagnoses: list[dict[str, Any]], scope: str
) -> list[dict[str, Any]]:
    if scope == "all":
        return diagnoses
    primary = [
        diagnosis
        for diagnosis in diagnoses
        if str(diagnosis.get("role") or "").lower() == "primary"
    ]
    return primary or diagnoses[:1]


def adapt_responses(
    rows: list[dict[str, Any]], gold_scope: str
) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for row in rows:
        final_response = row.get("final_response") or {}
        predictions = final_response.get("data") or []
        if not isinstance(predictions, list):
            raise AdapterError(
                f"Case {row.get('case_id')} has a non-list diagnosis payload"
            )

        ddx_details: dict[str, dict[str, Any]] = {}
        for position, prediction in enumerate(predictions, start=1):
            name = str(prediction.get("diagnosis") or "").strip()
            if not name or name in ddx_details:
                continue
            ddx_details[name] = {
                "normalized_text": name,
                "position": position,
                "description": prediction.get("description") or "",
            }

        raw_gold = (row.get("gold") or {}).get("diagnoses") or []
        gold = []
        for diagnosis in select_gold(raw_gold, gold_scope):
            name = str(diagnosis.get("name") or "").strip()
            if not name:
                continue
            gold.append(
                {
                    "name": name,
                    "normalized_text": name,
                    "role": diagnosis.get("role") or "unspecified",
                    "icd11": diagnosis.get("icd11") or "",
                    "icd11_title": diagnosis.get("title") or "",
                    "medical_codes": {
                        "icd10": [],
                        "snomed": [],
                        "omim": [],
                        "orpha": [],
                    },
                }
            )
        if not gold:
            raise AdapterError(f"Case {row.get('case_id')} has no usable gold diagnosis")

        cases.append(
            {
                "id": str(row["case_id"]),
                "case": (row.get("http_response") or {}).get("description") or "",
                "diagnoses": gold,
                "ddx_details": ddx_details,
                "beta_pipeline": row.get("pipeline") or {},
                "beta_metadata": row.get("metadata") or {},
            }
        )
    return cases


def evaluator_config(
    args: argparse.Namespace,
    case_count: int,
    evaluated_model: str,
) -> dict[str, Any]:
    return {
        "EXPERIMENT_NAME": (
            f"medreamm-pilot{case_count}-dxgpt-beta-product"
        ),
        "EXPERIMENT_DESCRIPTION": (
            f"DxGPT beta end-to-end MedReaMM {case_count}-case cohort "
            "evaluated with Pipeline V4."
        ),
        "DXGPT_EMULATOR": {
            "MODEL": evaluated_model,
            "CANDIDATE_PROMPT_PATH": "Server/assets/prompts.js",
            "PARAMS": {"reasoning_effort": "low"},
        },
        "EVALUATOR": {
            "BERT_ACCEPTANCE_THRESHOLD": 0.80,
            "BERT_AUTOCONFIRM_THRESHOLD": 0.90,
            "ENABLE_ICD10_PARENT_SEARCH": True,
            "ENABLE_ICD10_SIBLING_SEARCH": True,
            "JUDGE_MODEL": args.judge_model,
            "JUDGE_PARAMS": {
                "thinking_level": "low",
                "max_tokens": 10000,
                "temperature": 0.1,
            },
            "PARALLEL_WORKERS": max(1, args.workers),
        },
        "MULTIMODAL_BETA": {
            "GOLD_SCOPE": args.gold_scope,
            "GOLD_ONTOLOGY": "ICD-11",
            "NORMALIZATION": "Azure Health Text Analytics",
            "LLM_MATCH_MODE": args.judge_mode,
            "SOURCE_RESPONSES": str(args.responses.resolve()),
        },
    }


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)


def add_gold_medical_codes(
    labeler: MedicalLabeler,
    labeled_cases: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Normalize GDX through an isolated second MedLabeler pass."""
    gold_as_ddx = []
    for case in labeled_cases:
        gold_as_ddx.append(
            {
                "id": case["id"],
                "ddx_details": {
                    diagnosis["name"]: {
                        "normalized_text": diagnosis["name"],
                        "position": position,
                    }
                    for position, diagnosis in enumerate(
                        case.get("diagnoses", []), start=1
                    )
                },
            }
        )

    normalized_gold = labeler.process_dataset(gold_as_ddx)
    codes_by_case = {
        case["id"]: {
            name: details.get("medical_codes") or {}
            for name, details in case.get("ddx_details", {}).items()
        }
        for case in normalized_gold
    }
    for case in labeled_cases:
        case_codes = codes_by_case.get(case["id"], {})
        for diagnosis in case.get("diagnoses", []):
            diagnosis["medical_codes"] = case_codes.get(
                diagnosis["name"],
                {"icd10": [], "snomed": [], "omim": [], "orpha": []},
            )
    return labeled_cases


def evaluate_dataset_multimodal(
    labeled_cases: list[dict[str, Any]],
    output_dir: Path,
    config: dict[str, Any],
) -> None:
    """Run Pipeline V4 layers without changing the historical evaluator."""
    logger = setup_logging(str(output_dir))
    judge_mode = config["MULTIMODAL_BETA"]["LLM_MATCH_MODE"]
    evaluator_class = (
        StrictMultimodalEvaluator
        if judge_mode == "strict_equivalence"
        else DiagnosticEvaluator
    )
    evaluator = evaluator_class(config, logger)
    workers = max(1, int(config["EVALUATOR"].get("PARALLEL_WORKERS", 1)))
    total = len(labeled_cases)
    results: list[EvaluationResult | None] = [None] * total

    if workers > 1:
        evaluator.warmup_dependencies()
        with ThreadPoolExecutor(
            max_workers=workers, thread_name_prefix="multimodal-eval"
        ) as executor:
            futures = {
                executor.submit(
                    evaluator.evaluate_case, case, index + 1, total
                ): index
                for index, case in enumerate(labeled_cases)
            }
            for future in as_completed(futures):
                index = futures[future]
                try:
                    results[index] = future.result()
                except Exception as error:
                    case = labeled_cases[index]
                    case_id = case.get("case_id", case.get("id", f"case_{index + 1}"))
                    logger.error(
                        "Worker failed for case %s: %s: %s",
                        case_id,
                        type(error).__name__,
                        error,
                    )
                    results[index] = EvaluationResult(
                        case_id=case_id,
                        gdx_details=[],
                        ddx_details=[],
                        eval_details={
                            "best_match_found": False,
                            "final_resolution": None,
                            "evaluation_trace": [],
                            "worker_error": f"{type(error).__name__}: {error}",
                        },
                    )
    else:
        for index, case in enumerate(labeled_cases):
            results[index] = evaluator.evaluate_case(case, index + 1, total)

    completed = [result for result in results if result is not None]
    generate_evaluation_details(
        completed, str(output_dir / "evaluation_details.txt")
    )
    generate_summary_json(completed, str(output_dir / "summary.json"), config)
    stats = calculate_global_statistics(completed)
    logger.info(
        "%s multimodal result: %s/%s matches; avg position %.3f",
        judge_mode,
        stats["matched_cases"],
        stats["total_cases"],
        stats["average_position"],
    )


def main() -> int:
    args = parse_args()
    responses_path = args.responses.resolve()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    output_dir = (
        args.output_dir.resolve()
        if args.output_dir
        else responses_path.parent / "evaluation_v4" / timestamp
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = load_responses(responses_path)
    adapted = adapt_responses(rows, args.gold_scope)
    adapter_path = output_dir / "adapted_input.json"
    labeled_path = output_dir / "labeled_input.json"
    write_json(adapter_path, adapted)

    if args.reuse_labeled:
        reuse_path = args.reuse_labeled.resolve()
        if not reuse_path.is_file():
            raise AdapterError(f"Labeled input does not exist: {reuse_path}")
        with reuse_path.open("r", encoding="utf-8") as stream:
            labeled = json.load(stream)
        if len(labeled) != len(adapted):
            raise AdapterError(
                "Reused labeled input has a different number of cases"
            )
    else:
        logger = logging.getLogger("multimodal_beta_medlabeler")
        logger.setLevel(logging.INFO)
        labeler = MedicalLabeler(logger=logger)
        labeled = labeler.process_dataset(adapted)
        labeled = add_gold_medical_codes(labeler, labeled)
    write_json(labeled_path, labeled)

    models = sorted(
        {
            str((row.get("final_response") or {}).get("model") or "unknown")
            for row in rows
        }
    )
    evaluated_model = models[0] if len(models) == 1 else "mixed:" + ",".join(models)
    config = evaluator_config(args, len(adapted), evaluated_model)
    with (output_dir / "config.yaml").open("w", encoding="utf-8") as stream:
        yaml.safe_dump(config, stream, sort_keys=False, allow_unicode=True)

    evaluate_dataset_multimodal(labeled, output_dir, config)
    print(f"Pipeline V4 evaluation written to {output_dir}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AdapterError as error:
        print(f"Adapter error: {error}")
        raise SystemExit(2) from error
