"""Re-score a traditional Pipeline V4 run with the strict judge.

Reads an existing evaluation_details.txt (gold, DDX, and medical codes already
resolved). Does not call the emulator, MedLabeler, or write back into
pipeline_v4 output. The historical evaluator.py stays untouched.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

from evaluate_v4 import evaluate_dataset_multimodal


HERE = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Re-evaluate a traditional Pipeline V4 run with "
            "strict_equivalence, without modifying Pipeline V4."
        )
    )
    parser.add_argument("--evaluation-details", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--source-label", required=True)
    parser.add_argument("--judge-model", default="gemini-2.5-pro")
    parser.add_argument(
        "--judge-thinking-level",
        choices=("off", "low", "medium", "high"),
        default="low",
        help=(
            "Judge reasoning setting. 'off' maps to thinking_budget=0 for "
            "Gemini 2.5 Flash."
        ),
    )
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument(
        "--case-id",
        action="append",
        dest="case_ids",
        help="Evaluate only this case ID. Repeat to select multiple cases.",
    )
    return parser.parse_args()


def load_evaluation_details(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        raise FileNotFoundError(f"evaluation_details not found: {path}")
    blocks = path.read_text(encoding="utf-8").split("\n---\n")
    rows = [json.loads(block) for block in blocks if block.strip()]
    if not rows:
        raise ValueError(f"No cases in {path}")
    return rows


def details_to_labeled(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    labeled = []
    for row in rows:
        case_id = str(row.get("case_id") or "")
        if not case_id:
            raise ValueError("evaluation_details row has no case_id")
        source_bert_by_gdx = {}
        source_traces = (
            row.get("eval_details", {}).get("evaluation_trace") or []
        )
        for trace in source_traces:
            semantic = trace.get("semantic_check") or {}
            if semantic.get("status") not in {"SUCCESS", "FAILED"}:
                continue
            if str(semantic.get("details") or "").startswith(
                "Semantic evaluation error:"
            ):
                continue
            for trace_gdx_name in (trace.get("gdx_evaluated") or {}):
                source_bert_by_gdx[trace_gdx_name] = {
                    "bert_scores": semantic.get("bert_scores") or [],
                    "bert_best": semantic.get("bert_best"),
                }

        gdx = {}
        for item in row.get("gdx_details") or []:
            name = str(item.get("name") or "").strip()
            if name:
                details = dict(item.get("details") or {})
                if name in source_bert_by_gdx:
                    details["_source_bert_evaluation"] = source_bert_by_gdx[name]
                gdx[name] = details
        ddx = {}
        for item in row.get("ddx_details") or []:
            name = str(item.get("name") or "").strip()
            if name:
                ddx[name] = item.get("details") or {}
        if not gdx:
            raise ValueError(f"Case {case_id} has no gold diagnoses")
        labeled.append(
            {
                "id": case_id,
                "case_id": case_id,
                "gdx_details": gdx,
                "ddx_details": ddx,
            }
        )
    return labeled


def infer_dataset_path(source_details: Path) -> str:
    """Recover the dataset path from the source run's config snapshot."""
    config_paths = sorted(source_details.parent.glob("*___config.yaml"))
    if not config_paths:
        return "unknown"
    with config_paths[0].open(encoding="utf-8") as stream:
        source_config = yaml.safe_load(stream) or {}
    return str(source_config.get("DATASET_PATH") or "unknown")


def build_config(
    args: argparse.Namespace,
    case_count: int,
    source_details: Path,
) -> dict[str, Any]:
    return {
        "EXPERIMENT_NAME": f"judge-audit-strict-{args.source_label}",
        "EXPERIMENT_DESCRIPTION": (
            f"Strict re-score of {args.source_label} from existing "
            "evaluation_details. No new inference or MedLabeler."
        ),
        "DXGPT_EMULATOR": {
            "MODEL": args.source_label,
            "CANDIDATE_PROMPT_PATH": "bench/candidate-prompts/juanjo_classic_v2.txt",
            "PARAMS": {"reasoning_effort": "low"},
        },
        "EVALUATOR": {
            "BERT_ACCEPTANCE_THRESHOLD": 0.80,
            "BERT_AUTOCONFIRM_THRESHOLD": 0.90,
            "ENABLE_ICD10_PARENT_SEARCH": True,
            "ENABLE_ICD10_SIBLING_SEARCH": True,
            "JUDGE_MODEL": args.judge_model,
            "JUDGE_PARAMS": {
                "thinking_level": args.judge_thinking_level,
                "max_tokens": 10000,
                "temperature": 0.1,
            },
            "JUDGE_MAX_ATTEMPTS": 3,
            "JUDGE_RETRY_DELAY_SECONDS": 2,
            "PARALLEL_WORKERS": max(1, args.workers),
        },
        "MULTIMODAL_BETA": {
            "GOLD_SCOPE": "primary",
            "GOLD_ONTOLOGY": "source_run",
            "NORMALIZATION": "reused_from_evaluation_details",
            "BERT_SCORES": "reused_from_source_evaluation_trace",
            "LLM_MATCH_MODE": "strict_equivalence",
            "SOURCE_EVALUATION_DETAILS": str(source_details.resolve()),
            "SOURCE_CASE_COUNT": case_count,
        },
        "DATASET_PATH": infer_dataset_path(source_details),
    }


def main() -> int:
    args = parse_args()
    source = args.evaluation_details.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = load_evaluation_details(source)
    if args.case_ids:
        requested_ids = set(args.case_ids)
        rows = [
            row for row in rows if str(row.get("case_id") or "") in requested_ids
        ]
        found_ids = {str(row.get("case_id") or "") for row in rows}
        missing_ids = requested_ids - found_ids
        if missing_ids:
            raise ValueError(
                "Requested case IDs not found: " + ", ".join(sorted(missing_ids))
            )
    labeled = details_to_labeled(rows)
    labeled_path = output_dir / "labeled_from_details.json"
    labeled_path.write_text(
        json.dumps(labeled, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    config = build_config(args, len(labeled), source)
    with (output_dir / "config.yaml").open("w", encoding="utf-8") as stream:
        yaml.safe_dump(config, stream, sort_keys=False, allow_unicode=True)

    evaluate_dataset_multimodal(labeled, output_dir, config)
    print(f"Strict re-score written to {output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
