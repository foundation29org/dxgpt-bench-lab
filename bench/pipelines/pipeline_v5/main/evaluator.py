#!/usr/bin/env python3
"""
Evaluator V5 - Graded DDX Evaluation
====================================

Evaluates differential diagnoses (DDX) against reference diagnoses (GDX).

Changes from Pipeline V4:
- Only SNOMED exact decides without the judge. ICD-10 relations (exact, child,
  parent, sibling) are recorded per option and the judge decides (rubric C1).
- SapBERT does not decide anything: no auto-confirmation, no position override.
- The judge sees every case and grades every option:
    2 = same entity, 1 = related, 0 = different disease.
- Strict metrics count grade 2 only; lax metrics count grade >= 1.
- The strict position is the best position across codes and judge, not the
  position found by the first layer that matches.
- The judge reads the gold as written in the dataset, not the labeler's
  normalized text, plus its accepted_names when the dataset provides them.
- "X with Y" and "finding due to X" references are matched by "X" (rubric C2).
"""

import json
import os
import sys
import logging
import time
import threading
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Tuple

# Add project root to path (so we can import utils)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.llm import get_llm
from utils.icd10.taxonomy import ICD10Taxonomy

# Constants
LOG_FILE_NAME = 'evaluation'
JUDGE_PROMPT_VERSION = 'graded_v2'
GRADE_SAME = 2
GRADE_RELATED = 1
GRADE_DIFFERENT = 0
VALID_GRADES = (GRADE_DIFFERENT, GRADE_RELATED, GRADE_SAME)

# USD per million tokens (input, output including reasoning), as used in the
# judge reports under bench/multimodal_beta/results.
JUDGE_PRICES_PER_MILLION = {
    'gemini-2.5-pro': (1.25, 10.0),
}


@dataclass
class EvaluationResult:
    """Result of a complete case evaluation"""
    case_id: str
    gdx_details: List[Tuple[str, Dict]]
    ddx_details: List[Tuple[str, Dict]]
    eval_details: Dict


class GradedEvaluator:
    """Pipeline V5 evaluation engine: identical codes plus a graded judge"""

    def __init__(self, config: Dict[str, Any], logger: logging.Logger):
        self.config = config
        self.evaluator_config = config.get('EVALUATOR', {})
        self.logger = logger

        self.judge_model_name = self.evaluator_config.get('JUDGE_MODEL', 'gemini-2.5-pro')
        judge_params = self.evaluator_config.get('JUDGE_PARAMS', {})
        self.judge_reasoning_effort = judge_params.get('reasoning_effort', 'low')
        self.judge_thinking_level = judge_params.get('thinking_level', 'low')
        self.judge_max_tokens = judge_params.get('max_tokens', 10000)
        self.judge_temperature = judge_params.get('temperature', 0.1)
        self.judge_max_attempts = max(1, int(self.evaluator_config.get('JUDGE_MAX_ATTEMPTS', 3)))
        self.judge_retry_delay_seconds = max(
            0.0, float(self.evaluator_config.get('JUDGE_RETRY_DELAY_SECONDS', 2.0))
        )

        judge_model_lower = self.judge_model_name.lower()
        self.is_judge_gemini = 'gemini' in judge_model_lower
        self.is_judge_reasoning = any(
            token in judge_model_lower for token in ('o3', 'gpt-5', 'gpt5', 'grok')
        )

        self.llm = get_llm(self.judge_model_name, logger=logger)
        self.icd10_taxonomy = ICD10Taxonomy()
        self.judge_call_metrics: List[Dict[str, Any]] = []
        self._judge_metrics_lock = threading.Lock()

        if self.logger:
            self.logger.info(f"Judge model: {self.judge_model_name} (prompt {JUDGE_PROMPT_VERSION})")

    def warmup_dependencies(self) -> None:
        """Load the ICD-10 taxonomy once before worker threads start."""
        try:
            self.icd10_taxonomy.get("A00")
        except Exception as e:
            if self.logger:
                self.logger.warning(f"ICD10 taxonomy preload failed: {e}")

    def evaluate_case(self, case_data: Dict, case_num: int = 0, total_cases: int = 0) -> EvaluationResult:
        """Evaluate a single case: code matches, judge grades and resolutions."""
        case_id = case_data.get("case_id", case_data.get("id", "unknown"))

        if "gdx_details" in case_data:
            gdx_details = list(case_data["gdx_details"].items())
        elif "diagnoses" in case_data:
            gdx_details = [(diag["name"], diag) for diag in case_data["diagnoses"]]
        else:
            gdx_details = []

        ddx_details = list(case_data.get("ddx_details", {}).items())

        graded_trace = []
        judge_errors = []
        for gdx_name, gdx_info in gdx_details:
            gdx_trace = self._grade_gdx(gdx_name, gdx_info, ddx_details)
            graded_trace.append(gdx_trace)
            if gdx_trace["judge"].get("error"):
                judge_errors.append(f"{gdx_name}: {gdx_trace['judge']['error']}")

        strict = self._best_resolution(graded_trace, gdx_details, ddx_details, minimum_grade=GRADE_SAME)
        lax = self._best_resolution(graded_trace, gdx_details, ddx_details, minimum_grade=GRADE_RELATED)

        eval_details = {
            "best_match_found": strict is not None,
            "final_resolution": strict,
            "lax_resolution": lax,
            "judge_prompt_version": JUDGE_PROMPT_VERSION,
            "judge_error": "; ".join(judge_errors) if judge_errors else None,
            "graded_trace": graded_trace,
        }

        if self.logger:
            if strict:
                self.logger.info(f"[{case_num}/{total_cases}] {case_id} {strict['method']} → **{strict['position']}**")
            elif lax:
                self.logger.info(f"[{case_num}/{total_cases}] {case_id} NO_MATCH (related at {lax['position']})")
            else:
                self.logger.info(f"[{case_num}/{total_cases}] {case_id} NO_MATCH")

        return EvaluationResult(
            case_id=case_id,
            gdx_details=gdx_details,
            ddx_details=ddx_details,
            eval_details=eval_details
        )

    def _grade_gdx(self, gdx_name: str, gdx_info: Dict, ddx_list: List) -> Dict:
        """Grade every DDX option against one GDX."""
        # The judge reads the gold as written in the dataset. V4 passed the
        # labeler's normalized_text, which sometimes names another entity
        # ("Cystic fibrosis with bronchiectasis" -> "Bronchiectasis").
        gdx_text = gdx_name
        accepted_names = [n for n in gdx_info.get("accepted_names") or [] if n and n != gdx_name]
        if accepted_names:
            gdx_text = f"{gdx_name} (also known as: {', '.join(accepted_names)})"
        ddx_texts = [ddx_name for ddx_name, _ in ddx_list]

        options = []
        for position, (ddx_name, ddx_info) in enumerate(ddx_list, 1):
            code_match = self._code_match(gdx_info, ddx_info)
            options.append({
                "position": position,
                "name": ddx_name,
                "code_match": code_match,
                "icd10_relation": None if code_match else self._icd10_relation(gdx_info, ddx_info),
            })

        if ddx_texts:
            judge = self._grade_options(gdx_text, ddx_texts)
        else:
            judge = {"grades": [], "reference_is_disease": None, "attempts": 0}

        judge_grades = judge.get("grades")
        for index, option in enumerate(options):
            judge_grade = judge_grades[index] if judge_grades is not None else None
            option["judge_grade"] = judge_grade
            option["grade"] = GRADE_SAME if option["code_match"] else judge_grade

        return {
            "gdx": gdx_name,
            "gdx_text": gdx_text,
            "gdx_normalized_text": gdx_info.get("normalized_text"),
            "options": options,
            "judge": judge,
        }

    def _best_resolution(self, graded_trace: List[Dict], gdx_details: List, ddx_details: List,
                         minimum_grade: int) -> Optional[Dict]:
        """Earliest option, across all GDX, whose grade reaches minimum_grade."""
        best = None
        for gdx_index, gdx_trace in enumerate(graded_trace):
            for option in gdx_trace["options"]:
                grade = option["grade"]
                if grade is None or grade < minimum_grade:
                    continue
                if best is None or option["position"] < best[1]["position"]:
                    best = (gdx_index, option)
                break

        if best is None:
            return None

        gdx_index, option = best
        gdx_name, gdx_info = gdx_details[gdx_index]
        ddx_name, ddx_info = ddx_details[option["position"] - 1]
        if option["code_match"] and minimum_grade == GRADE_SAME:
            method = option["code_match"]
        else:
            method = "JUDGE"
        return {
            "position": f"P{option['position']}",
            "method": method,
            "grade": option["grade"],
            "matched_gdx": {gdx_name: gdx_info},
            "matched_ddx": {ddx_name: ddx_info},
        }

    def _code_match(self, gdx_info: Dict, ddx_info: Dict) -> Optional[str]:
        """Return the identical-code layer that matches, if any.

        Only SNOMED decides without the judge (rubric rule C1): ICD-10 codes
        group distinct diseases, such as pyruvate dehydrogenase and pyruvate
        carboxylase deficiency.
        """
        gdx_codes = gdx_info.get("medical_codes", {})
        ddx_codes = ddx_info.get("medical_codes", {})
        if set(gdx_codes.get("snomed", [])) & set(ddx_codes.get("snomed", [])):
            return "SNOMED_EXACT"
        return None

    def _icd10_relation(self, gdx_info: Dict, ddx_info: Dict) -> Optional[str]:
        """Record the ICD-10 relation (exact, child, parent, sibling) without scoring it."""
        gdx_codes = gdx_info.get("medical_codes", {}).get("icd10", [])
        ddx_codes = ddx_info.get("medical_codes", {}).get("icd10", [])
        if set(gdx_codes) & set(ddx_codes):
            return "EXACT"
        for relation, related_codes in (
            ("CHILD", self._safe_taxonomy(self.icd10_taxonomy.children, gdx_codes)),
            ("PARENT", self._safe_taxonomy(self.icd10_taxonomy.parents, gdx_codes)),
            ("SIBLING", self._safe_taxonomy(self.icd10_taxonomy.siblings, gdx_codes)),
        ):
            if related_codes & set(ddx_codes):
                return relation
        return None

    def _safe_taxonomy(self, lookup, codes: List[str]) -> set:
        related = set()
        for code in codes:
            try:
                related.update(lookup(code))
            except Exception:
                continue
        return related

    def _build_judge_prompt(self, gdx_text: str, ddx_texts: List[str]) -> str:
        ddx_options = "\n".join(f"{index}. {text}" for index, text in enumerate(ddx_texts, start=1))
        option_count = len(ddx_texts)
        return f"""You are a medical expert grading a differential diagnosis against a reference diagnosis.

Reference diagnosis: {gdx_text}

Differential diagnosis options:
{ddx_options}

Grade every option with one of these values:

2 = Same disease entity. Accept synonyms, abbreviations and spelling variants. Accept a more specific form only when every patient with the option necessarily has the reference diagnosis: a named subtype of the reference, or the reference with added laterality or extent. Also accept the underlying disease when the reference adds a complication or manifestation to it ("X with Y" is matched by "X") or names a finding caused by it ("finding due to X" is matched by "X").
1 = Related but not the same entity: a broader category; an option that omits a qualifier that defines the reference (for example "GIST" for "malignant GIST"); a different subtype, variant, gene or phenotype within the same family; a cause, complication, precursor or consequence of the reference; or a disjunction such as "A or B" that includes the reference.
0 = A different disease.

Grade each option on its own; several options can share a grade. Do not give credit for a similar presentation, anatomical site, mechanism or treatment.

Also state whether the reference names a disease or clinical diagnosis. A mechanism, a stage, a laboratory value or an isolated finding is not one.

Respond with JSON only, without prose or code fences. The "grades" list must contain exactly {option_count} integers, one per option, in option order. Example shape:
{{"grades": [0, 2, 1], "reference_is_disease": true}}"""

    def _call_judge(self, prompt: str) -> Any:
        if self.is_judge_gemini:
            return self.llm.generate(
                prompt,
                thinking_level=self.judge_thinking_level,
                max_tokens=self.judge_max_tokens,
                temperature=self.judge_temperature,
            )
        if self.is_judge_reasoning:
            return self.llm.generate(
                prompt,
                reasoning_effort=self.judge_reasoning_effort,
                max_tokens=self.judge_max_tokens,
            )
        return self.llm.generate(
            prompt,
            max_tokens=self.judge_max_tokens,
            temperature=self.judge_temperature,
        )

    def _parse_judge_response(self, response_text: str, option_count: int) -> Tuple[List[int], bool]:
        text = response_text.strip()
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end < start:
            raise ValueError("no JSON object in response")
        data = json.loads(text[start:end + 1])

        grades = data.get("grades")
        if not isinstance(grades, list) or len(grades) != option_count:
            raise ValueError(f"expected {option_count} grades, got {grades!r}")
        parsed = []
        for grade in grades:
            if isinstance(grade, bool) or not isinstance(grade, (int, float)) or int(grade) != grade:
                raise ValueError(f"grade {grade!r} is not an integer")
            if int(grade) not in VALID_GRADES:
                raise ValueError(f"grade {grade!r} is not 0, 1 or 2")
            parsed.append(int(grade))

        reference_is_disease = data.get("reference_is_disease", True)
        if not isinstance(reference_is_disease, bool):
            reference_is_disease = str(reference_is_disease).strip().lower() != "false"
        return parsed, reference_is_disease

    def _grade_options(self, gdx_text: str, ddx_texts: List[str]) -> Dict:
        """Ask the judge for one grade per option, retrying invalid answers."""
        prompt = self._build_judge_prompt(gdx_text, ddx_texts)
        response_text = ""
        error_text = None
        for attempt in range(1, self.judge_max_attempts + 1):
            started = time.perf_counter()
            response_text = ""
            call_succeeded = False
            grades = None
            reference_is_disease = None
            try:
                response_text = str(self._call_judge(prompt)).strip()
                call_succeeded = True
                grades, reference_is_disease = self._parse_judge_response(response_text, len(ddx_texts))
                error_text = None
            except Exception as error:
                error_text = f"{type(error).__name__}: {error}"
            finally:
                usage = self.llm.get_last_usage() if call_succeeded else None
                metric = {
                    "model": self.judge_model_name,
                    "attempt": attempt,
                    "duration_seconds": round(time.perf_counter() - started, 6),
                    "option_count": len(ddx_texts),
                    "response": response_text,
                    "call_succeeded": call_succeeded,
                    "response_valid": grades is not None,
                    "error": error_text,
                    **(usage or {}),
                }
                with self._judge_metrics_lock:
                    self.judge_call_metrics.append(metric)

            if grades is not None:
                return {
                    "grades": grades,
                    "reference_is_disease": reference_is_disease,
                    "attempts": attempt,
                    "raw_response": response_text,
                }
            if self.logger:
                self.logger.warning(
                    f"Judge attempt {attempt}/{self.judge_max_attempts} failed: {error_text}"
                )
            if attempt < self.judge_max_attempts:
                time.sleep(self.judge_retry_delay_seconds * attempt)

        return {
            "grades": None,
            "reference_is_disease": None,
            "attempts": self.judge_max_attempts,
            "raw_response": response_text,
            "error": error_text,
        }


def setup_logging(output_dir: str) -> logging.Logger:
    """Setup logging to both console and file"""
    logger = logging.getLogger('pipeline_v5')
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter('[%(asctime)s] - %(levelname)s - %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    log_file = os.path.join(output_dir, LOG_FILE_NAME + ".log")
    file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def generate_evaluation_details(results: List[EvaluationResult], output_path: str):
    """Write one JSON block per case, separated by '---' as in Pipeline V4"""
    with open(output_path, 'w', encoding='utf-8') as f:
        for i, result in enumerate(results):
            if i > 0:
                f.write('\n---\n')
            case_data = {
                "case_id": result.case_id,
                "gdx_details": [{"name": name, "details": details} for name, details in result.gdx_details],
                "ddx_details": [{"name": name, "details": details} for name, details in result.ddx_details],
                "eval_details": result.eval_details
            }
            json.dump(case_data, f, ensure_ascii=False, indent=2)


def _resolution_positions(results: List[EvaluationResult], key: str) -> List[Optional[int]]:
    positions = []
    for result in results:
        resolution = result.eval_details.get(key)
        positions.append(int(resolution["position"][1:]) if resolution else None)
    return positions


def _recall_block(positions: List[Optional[int]], total: int) -> Dict[str, Any]:
    matched = [p for p in positions if p is not None]

    def pct(count: int) -> float:
        return round(count / total * 100, 2) if total else 0.0

    return {
        "r_at_1": pct(sum(1 for p in matched if p <= 1)),
        "r_at_3": pct(sum(1 for p in matched if p <= 3)),
        "r_at_5": pct(sum(1 for p in matched if p <= 5)),
        "coverage": pct(len(matched)),
        "matched_cases": len(matched),
        "average_position": round(statistics.mean(matched), 3) if matched else 0,
        "mrr": round(sum(1 / p for p in matched) / total, 3) if total else 0,
    }


def calculate_global_statistics(results: List[EvaluationResult]) -> Dict:
    """Strict and lax metrics, plus the audit lists the judge produces"""
    total = len(results)
    strict_positions = _resolution_positions(results, "final_resolution")
    lax_positions = _resolution_positions(results, "lax_resolution")

    position_counts: Dict[str, int] = {}
    method_counts: Dict[str, int] = {}
    for result in results:
        resolution = result.eval_details.get("final_resolution")
        if resolution:
            position_counts[resolution["position"]] = position_counts.get(resolution["position"], 0) + 1
            method_counts[resolution["method"]] = method_counts.get(resolution["method"], 0) + 1

    relation_grades: Dict[str, Dict[str, int]] = {}
    code_judge_disagreements = []
    reference_not_disease = []
    judge_errors = []
    for result in results:
        if result.eval_details.get("judge_error") or result.eval_details.get("worker_error"):
            judge_errors.append(result.case_id)
        for gdx_trace in result.eval_details.get("graded_trace", []):
            if gdx_trace["judge"].get("reference_is_disease") is False:
                reference_not_disease.append({"case_id": result.case_id, "gdx": gdx_trace["gdx"]})
            for option in gdx_trace["options"]:
                relation = option.get("icd10_relation")
                if relation:
                    bucket = relation_grades.setdefault(relation, {})
                    key = str(option["judge_grade"])
                    bucket[key] = bucket.get(key, 0) + 1
                if option["code_match"] and option["judge_grade"] is not None and option["judge_grade"] < GRADE_SAME:
                    code_judge_disagreements.append({
                        "case_id": result.case_id,
                        "gdx": gdx_trace["gdx"],
                        "position": option["position"],
                        "ddx": option["name"],
                        "code_match": option["code_match"],
                        "judge_grade": option["judge_grade"],
                    })

    return {
        "total_cases": total,
        "strict": _recall_block(strict_positions, total),
        "lax": _recall_block(lax_positions, total),
        "top_counts": dict(sorted(position_counts.items(), key=lambda item: int(item[0][1:]))),
        "resolution_method_counts": method_counts,
        "icd10_relation_judge_grades": relation_grades,
        "code_judge_disagreements": code_judge_disagreements,
        "reference_not_disease": reference_not_disease,
        "cases_with_judge_errors": judge_errors,
    }


def calculate_judge_totals(metrics: List[Dict[str, Any]], judge_model: str) -> Dict[str, Any]:
    """Token, latency and cost totals for the judge calls"""
    durations = [m["duration_seconds"] for m in metrics if m.get("call_succeeded")]
    input_tokens = sum(m.get("input_tokens", 0) for m in metrics)
    output_tokens = sum(m.get("output_tokens", 0) for m in metrics)
    reasoning_tokens = sum(m.get("reasoning_tokens", 0) for m in metrics)
    totals = {
        "calls": len(metrics),
        "invalid_responses": sum(1 for m in metrics if m.get("call_succeeded") and not m.get("response_valid")),
        "failed_calls": sum(1 for m in metrics if not m.get("call_succeeded")),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "reasoning_tokens": reasoning_tokens,
        "p50_seconds": round(statistics.median(durations), 2) if durations else None,
        "p95_seconds": round(sorted(durations)[int(0.95 * (len(durations) - 1))], 2) if durations else None,
        "estimated_cost_usd": None,
    }
    prices = JUDGE_PRICES_PER_MILLION.get(judge_model.lower())
    if prices:
        totals["estimated_cost_usd"] = round(
            (input_tokens * prices[0] + (output_tokens + reasoning_tokens) * prices[1]) / 1_000_000, 4
        )
    return totals


def generate_summary_json(results: List[EvaluationResult], output_path: str, config: Dict[str, Any],
                          judge_totals: Dict[str, Any]):
    """Write summary statistics in JSON format"""
    evaluator_config = config.get('EVALUATOR', {})
    summary = {
        "configuration": {
            "pipeline": "v5",
            "experiment_name": config.get('EXPERIMENT_NAME', 'unknown'),
            "experiment_description": config.get('EXPERIMENT_DESCRIPTION', 'unknown'),
            "judge_model": evaluator_config.get('JUDGE_MODEL', 'gemini-2.5-pro'),
            "judge_params": evaluator_config.get('JUDGE_PARAMS', {}),
            "judge_prompt_version": JUDGE_PROMPT_VERSION,
            "automatic_layers": ["SNOMED_EXACT"],
            "dataset_path": config.get('DATASET_PATH', 'unknown'),
            "reused_labeled_ddx": config.get('REUSE_LABELED_DDX'),
            "timestamp": config.get('TIMESTAMP', 'unknown')
        },
        "global": calculate_global_statistics(results),
        "judge": judge_totals,
    }
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)


def evaluate_dataset(input_path: str, output_dir: str, config: Dict[str, Any]) -> None:
    """
    Evaluate a dataset with DDX and GDX

    Args:
        input_path: Path to input JSON file with DDX and GDX
        output_dir: Directory to save evaluation results
        config: Configuration dictionary
    """
    logger = setup_logging(output_dir)
    evaluator_config = config.get('EVALUATOR', {})

    output_details_path = os.path.join(output_dir, "evaluation_details.txt")
    output_summary_path = os.path.join(output_dir, "summary.json")
    output_judge_metrics_path = os.path.join(output_dir, "judge_metrics.json")

    logger.info("--- Starting Evaluation Pipeline V5 ---")
    logger.info("  Automatic layers: SNOMED_EXACT")
    logger.info(f"  Judge: {evaluator_config.get('JUDGE_MODEL', 'gemini-2.5-pro')} ({JUDGE_PROMPT_VERSION}) on every case")
    logger.info(f"  Output directory: {output_dir}")

    logger.info("Loading input data...")
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        logger.error(f"Input file '{input_path}' not found")
        return
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in input file: {e}")
        return

    if isinstance(data, list):
        all_cases = data
    else:
        all_cases = []
        for category, cases in data.items():
            all_cases.extend(cases)

    case_limit = evaluator_config.get('CASE_LIMIT')
    if case_limit:
        all_cases = all_cases[:int(case_limit)]
    logger.info(f"Found {len(all_cases)} cases to evaluate")

    evaluator = GradedEvaluator(config, logger)
    evaluator.warmup_dependencies()

    parallel_workers = max(1, int(evaluator_config.get('PARALLEL_WORKERS', 1) or 1))
    total = len(all_cases)
    logger.info(f"Processing cases with {parallel_workers} worker(s)...")

    ordered: List[Optional[EvaluationResult]] = [None] * total
    completed = 0
    with ThreadPoolExecutor(max_workers=parallel_workers, thread_name_prefix="eval") as executor:
        future_to_idx = {
            executor.submit(evaluator.evaluate_case, case_data, i + 1, total): i
            for i, case_data in enumerate(all_cases)
        }
        for fut in as_completed(future_to_idx):
            idx0 = future_to_idx[fut]
            try:
                result = fut.result()
            except Exception as e:
                case_data = all_cases[idx0]
                case_id = case_data.get("case_id", case_data.get("id", f"case_{idx0+1}"))
                logger.error(f"[{idx0+1}/{total}] WORKER_ERROR for case {case_id}: {type(e).__name__}: {e}")
                result = EvaluationResult(
                    case_id=case_id,
                    gdx_details=[],
                    ddx_details=[],
                    eval_details={
                        "best_match_found": False,
                        "final_resolution": None,
                        "lax_resolution": None,
                        "graded_trace": [],
                        "worker_error": f"{type(e).__name__}: {e}",
                    },
                )
            ordered[idx0] = result
            completed += 1
            if completed % 10 == 0 or completed == total:
                logger.info(f"PROGRESS: {completed}/{total} cases evaluated ({100.0*completed/total:.1f}%)")
    all_results = [r for r in ordered if r is not None]

    logger.info("\nGenerating outputs...")
    judge_totals = calculate_judge_totals(evaluator.judge_call_metrics, evaluator.judge_model_name)
    generate_evaluation_details(all_results, output_details_path)
    generate_summary_json(all_results, output_summary_path, config, judge_totals)
    with open(output_judge_metrics_path, 'w', encoding='utf-8') as f:
        json.dump({"totals": judge_totals, "calls": evaluator.judge_call_metrics}, f, indent=2, ensure_ascii=False)

    stats = calculate_global_statistics(all_results)
    strict, lax = stats["strict"], stats["lax"]
    logger.info("\n--- FINAL RESULTS ---")
    logger.info(f"Total cases: {stats['total_cases']}")
    logger.info(f"Strict: R@1 {strict['r_at_1']}% | R@3 {strict['r_at_3']}% | R@5 {strict['r_at_5']}% | coverage {strict['coverage']}%")
    logger.info(f"Lax:    R@1 {lax['r_at_1']}% | R@3 {lax['r_at_3']}% | R@5 {lax['r_at_5']}% | coverage {lax['coverage']}%")
    logger.info(f"Resolution methods: {stats['resolution_method_counts']}")
    logger.info(f"Judge: {judge_totals['calls']} calls, {judge_totals['invalid_responses']} invalid, "
                f"cost ≈ ${judge_totals['estimated_cost_usd']}")
    if stats["cases_with_judge_errors"]:
        logger.warning(f"Cases with judge errors: {stats['cases_with_judge_errors']}")
