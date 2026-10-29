#!/usr/bin/env python3
"""
Re-judge the cases of a V5 run that ended with a judge error
============================================================

When the judge fails three times on a case (for example, Gemini returns 503
"high demand"), the case is scored without that gold. This script re-evaluates
only those cases with the same configuration and labeled DDX, and rewrites
evaluation_details.txt, summary.json and judge_metrics.json of the run. The
new judge calls are added to the old ones, so the cost stays complete.

Usage:
    py repair_judge_errors.py <run dir>
"""

import argparse
import glob
import json
import logging
import os
import sys
from typing import Dict, List

import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from evaluator import (EvaluationResult, GradedEvaluator, calculate_judge_totals,  # noqa: E402
                       generate_evaluation_details, generate_summary_json)


def load_results(path: str) -> List[EvaluationResult]:
    with open(path, 'r', encoding='utf-8') as f:
        blocks = [b for b in f.read().split('\n---\n') if b.strip()]
    results = []
    for block in blocks:
        case = json.loads(block)
        results.append(EvaluationResult(
            case_id=case["case_id"],
            gdx_details=[(g["name"], g["details"]) for g in case["gdx_details"]],
            ddx_details=[(d["name"], d["details"]) for d in case["ddx_details"]],
            eval_details=case["eval_details"],
        ))
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('run_dir', help='V5 evaluation folder (with evaluation_details.txt)')
    args = parser.parse_args()
    run_dir = os.path.abspath(args.run_dir)

    with open(glob.glob(os.path.join(run_dir, '*___config.yaml'))[0], 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    labeled_path = glob.glob(os.path.join(os.path.dirname(run_dir), '*___ddxs_from_labeler.json'))[0]
    with open(labeled_path, 'r', encoding='utf-8') as f:
        labeled: Dict[str, Dict] = {str(c.get('case_id', c.get('id'))): c for c in json.load(f)}

    details_path = os.path.join(run_dir, 'evaluation_details.txt')
    metrics_path = os.path.join(run_dir, 'judge_metrics.json')
    results = load_results(details_path)
    failed = [i for i, r in enumerate(results)
              if r.eval_details.get('judge_error') or r.eval_details.get('worker_error')]
    if not failed:
        print('No judge errors in this run')
        return

    with open(metrics_path, 'r', encoding='utf-8') as f:
        old_calls = json.load(f)["calls"]

    # Console only: setup_logging() would truncate the run's evaluation.log
    logger = logging.getLogger('pipeline_v5_repair')
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler())
    evaluator = GradedEvaluator(config, logger)
    evaluator.warmup_dependencies()

    for index in failed:
        case_id = str(results[index].case_id)
        repaired = evaluator.evaluate_case(labeled[case_id], index + 1, len(results))
        error = repaired.eval_details.get('judge_error')
        print(f"{case_id}: {'still failing: ' + error if error else 'repaired'}")
        results[index] = repaired

    calls = old_calls + evaluator.judge_call_metrics
    totals = calculate_judge_totals(calls, evaluator.judge_model_name)
    generate_evaluation_details(results, details_path)
    generate_summary_json(results, os.path.join(run_dir, 'summary.json'), config, totals)
    with open(metrics_path, 'w', encoding='utf-8') as f:
        json.dump({"totals": totals, "calls": calls}, f, indent=2, ensure_ascii=False)
    print(f"Rewrote {details_path}, summary.json and judge_metrics.json ({len(evaluator.judge_call_metrics)} new calls)")


if __name__ == '__main__':
    main()
