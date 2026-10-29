"""Shared pieces of the agentic-layer PoC.

Every arm starts from the differential that a model already produced for
narrative_v2 (the frozen labeler output of Pipeline V5), adds a second stage,
and writes its new lists in the same labeler format. Pipeline V5 then grades
those lists with the same judge as the baseline (see evaluate_arm.py).
"""

import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Callable, Dict, List

HERE = Path(__file__).resolve().parent
EVAL_ROOT = HERE.parents[1]
sys.path.insert(0, str(EVAL_ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(EVAL_ROOT / ".env")

from utils.llm import get_llm  # noqa: E402

WORK_DIR = HERE / "work"
RUNS_DIR = EVAL_ROOT / "bench" / "pipelines" / "pipeline_v5" / "main" / "output" / "narrative_v2" / "juanjo_classic_v2"
# Run folder of each model on narrative_v2, its model name and its V5 config.
RUN_FOLDERS = {
    "terra": "gpt_5_6_terra_low_translated_en",
    "sol": "gpt_6_1_sol_low_translated_en",
    "opus": "claude_opus_5_low_translated_en",
}
BASE_LISTS = {
    name: RUNS_DIR / folder / f"juanjo_classic_v2___{folder}___ddxs_from_labeler.json"
    for name, folder in RUN_FOLDERS.items()
}
BASE_MODELS = {"terra": "gpt-5.6-terra", "sol": "gpt-6.1-sol"}
BASE_CONFIGS = {"terra": "config_terra_low_narrative_v2.yaml", "sol": "config_gpt61sol_low_narrative_v2.yaml"}
# USD per million tokens (input, output), from Server/services/costUtils.js.
PRICES = {"gpt-5.6-terra": (2.0, 12.0), "gpt-6.1-sol": (2.0, 10.0)}
MAX_DIAGNOSES = 5


def arm_id(arm: str, base: str) -> str:
    """Arms on the production model keep their plain name; others say their base."""
    return arm if base == "terra" else f"{arm}_on_{base}"


def base_of(arm_name: str) -> str:
    return arm_name.rsplit("_on_", 1)[1] if "_on_" in arm_name else "terra"


def load_lists(name: str) -> Dict[str, Dict]:
    """Labeler output of a model, by case id."""
    rows = json.loads(BASE_LISTS[name].read_text(encoding="utf-8"))
    return {row["id"]: row for row in rows}


def ranked_names(case: Dict, limit: int = None) -> List[str]:
    items = sorted(case.get("ddx_details", {}).items(), key=lambda item: item[1].get("position", 0))
    return [name for name, _ in items][:limit]


def parse_json(text: str) -> Dict:
    text = str(text).strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("no JSON object in response")
    return json.loads(text[start:end + 1])


def clean_diagnoses(values: List) -> List[str]:
    """Unique, non-empty names, at most MAX_DIAGNOSES."""
    seen, names = set(), []
    for value in values or []:
        name = str(value).strip()
        if name and name.lower() not in seen:
            seen.add(name.lower())
            names.append(name)
    return names[:MAX_DIAGNOSES]


class Model:
    """A reasoning model with retries and per-call usage, safe across threads."""

    def __init__(self, name: str = "gpt-5.6-terra", reasoning_effort: str = "low"):
        self.name = name
        self.reasoning_effort = reasoning_effort
        self.llm = get_llm(name)
        self.calls: List[Dict] = []
        self._lock = threading.Lock()

    def ask_json(self, prompt: str, attempts: int = 3, max_tokens: int = 12000) -> Dict:
        error = None
        for attempt in range(1, attempts + 1):
            started = time.perf_counter()
            try:
                response = self.llm.generate(prompt, reasoning_effort=self.reasoning_effort, max_tokens=max_tokens)
                usage = self.llm.get_last_usage() or {}
                with self._lock:
                    self.calls.append({"seconds": time.perf_counter() - started, **usage})
                return parse_json(response)
            except Exception as exc:  # retry invalid or failed calls
                error = f"{type(exc).__name__}: {exc}"
                time.sleep(2 * attempt)
        raise RuntimeError(error)

    def totals(self) -> Dict:
        input_tokens = sum(c.get("input_tokens", 0) for c in self.calls)
        # Reasoning tokens are billed as output.
        output_tokens = sum(c.get("output_tokens", 0) + c.get("reasoning_tokens", 0) for c in self.calls)
        price_in, price_out = PRICES.get(self.name, (0.0, 0.0))
        seconds = sorted(c["seconds"] for c in self.calls)
        return {
            "model": self.name,
            "calls": len(self.calls),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": round((input_tokens * price_in + output_tokens * price_out) / 1_000_000, 3),
            "p50_seconds": round(seconds[len(seconds) // 2], 1) if seconds else None,
        }


def run_arm(name: str, cases: List[Dict], worker: Callable[[Dict], Dict], workers: int = 8) -> List[Dict]:
    """Run worker(case) -> {"diagnoses": [...], ...trace} over the cases, in parallel."""
    results: Dict[str, Dict] = {}
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(worker, case): case for case in cases}
        for done, future in enumerate(as_completed(futures), start=1):
            case = futures[future]
            try:
                results[case["id"]] = future.result()
            except Exception as exc:  # keep the baseline list for this case
                results[case["id"]] = {"diagnoses": ranked_names(case, MAX_DIAGNOSES), "error": f"{type(exc).__name__}: {exc}"}
            if done % 25 == 0 or done == len(cases):
                print(f"   {name}: {done}/{len(cases)}")
    return [results[case["id"]] for case in cases]


def write_arm(name: str, base_cases: List[Dict], outputs: List[Dict], extra: Dict) -> Path:
    """Write the arm's lists in labeler format, plus traces and totals."""
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    labeled = []
    for case, output in zip(base_cases, outputs):
        ddx = {
            dx: {"normalized_text": dx, "position": position,
                 "medical_codes": {"icd10": [], "snomed": [], "omim": [], "orpha": []}}
            for position, dx in enumerate(output["diagnoses"], start=1)
        }
        labeled.append({**{k: v for k, v in case.items() if k != "ddx_details"}, "ddx_details": ddx})
    path = WORK_DIR / f"{name}.json"
    path.write_text(json.dumps(labeled, ensure_ascii=False, indent=1), encoding="utf-8")
    traces = [{"id": case["id"], **output} for case, output in zip(base_cases, outputs)]
    (WORK_DIR / f"{name}_traces.json").write_text(
        json.dumps({"totals": extra, "cases": traces}, ensure_ascii=False, indent=1), encoding="utf-8")
    errors = sum(1 for o in outputs if o.get("error"))
    print(f"   {name}: written to {path} ({errors} cases kept the baseline list after errors)")
    print(json.dumps(extra, indent=1))
    return path
