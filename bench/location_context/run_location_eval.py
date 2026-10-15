"""Paired evaluation of the patient-location line in DxGPT's diagnosis prompt.

Calls the real ``/api/diagnose`` endpoint (the one the web client uses) once per
case and arm. An arm is the country sent with the request; ``none`` sends no
country, which is today's behaviour. Everything else is identical between arms.

Suites
------
endemic     Hand-written vignettes where a geographically restricted disease is a
            plausible diagnosis, plus common-disease controls. Reports where the
            expected diagnosis ranks per arm. A probe, not a validated benchmark.
regression  MedReaMM pilot100 (text only) sent with each country. Writes
            ``responses.jsonl`` in the schema ``multimodal_beta/evaluate_v4.py``
            reads, so the strict-equivalence judge scores each arm unchanged.

Server and model come from the environment (same variables as multimodal_beta):
DXGPT_API_BASE_URL, DXGPT_TENANT_ID, DXGPT_EVAL_MODEL.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
import uuid
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from typing import Any, Callable

import requests
import yaml

HERE = Path(__file__).resolve().parent
OUTPUT_ROOT = HERE / "outputs"
VIGNETTES = HERE / "endemic_vignettes.yaml"
VIGNETTE_GROUPS = ("classic", "vague", "controls")
REGRESSION_MANIFEST = (
    HERE.parent / "multimodal_beta" / "datasets" / "processed"
    / "medreamm_pilot100" / "manifest.yaml"
)

NO_COUNTRY = "none"
BASELINE_ARMS = (NO_COUNTRY, "ES")
REQUEST_TIMEOUT_SECONDS = 400
MAX_ATTEMPTS = 3


@dataclass(frozen=True)
class Job:
    suite: str
    case_id: str
    arm: str
    rep: int
    text: str
    meta: dict[str, Any] = field(default_factory=dict, compare=False, hash=False)

    @property
    def key(self) -> str:
        return f"{self.case_id}|{self.arm}|{self.rep}"


def api_settings() -> tuple[str, dict[str, str], str]:
    base_url = os.environ.get("DXGPT_API_BASE_URL", "http://localhost:8443/api").rstrip("/")
    headers = {"X-Tenant-Id": os.environ.get("DXGPT_TENANT_ID", "dxgpt-local")}
    return base_url, headers, os.environ.get("DXGPT_EVAL_MODEL", "gpt56terra")


def diagnose(job: Job) -> dict[str, Any]:
    """One /api/diagnose call, returned as a result record (never raises)."""
    base_url, headers, model = api_settings()
    payload: dict[str, Any] = {
        "description": job.text,
        "myuuid": str(uuid.uuid4()),
        "lang": "en",
        "timezone": "UTC",
        "model": model,
        "response_mode": "direct",
    }
    if job.arm != NO_COUNTRY:
        payload["countryCode"] = job.arm

    started = time.monotonic()
    error = ""
    body: dict[str, Any] = {}
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = requests.post(
                f"{base_url}/diagnose", json=payload, headers=headers,
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
            response.raise_for_status()
            body = response.json()
            if body.get("result") == "success" and isinstance(body.get("data"), list):
                error = ""
                break
            error = f"unexpected result: {str(body)[:200]}"
        except Exception as exc:  # network, HTTP and JSON errors alike
            error = f"{type(exc).__name__}: {exc}"
        time.sleep(5 * attempt)

    return {
        "case_id": job.case_id,
        "arm": job.arm,
        "rep": job.rep,
        "status": "error" if error else "success",
        "error": error or None,
        "duration_seconds": round(time.monotonic() - started, 2),
        "request_id": payload["myuuid"],
        "model": model,
        "final_response": {"result": body.get("result"), "data": body.get("data") or [], "model": model},
        "http_response": {"description": job.text},
        "gold": job.meta.get("gold") or {},
        "metadata": {key: value for key, value in job.meta.items() if key != "gold"},
        "pipeline": {},
        "inputs": {"condition": "T", "country": job.arm, "text_chars": len(job.text)},
    }


def read_done(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    done = set()
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                row = json.loads(line)
                if row.get("status") == "success":
                    done.add(f"{row['case_id']}|{row['arm']}|{row['rep']}")
    return done


def run_jobs(jobs: list[Job], output_for: Callable[[Job], Path], workers: int) -> None:
    """Run jobs concurrently, appending each finished record to its own JSONL."""
    done = {path: read_done(path) for path in {output_for(job) for job in jobs}}
    pending = [job for job in jobs if job.key not in done[output_for(job)]]
    print(f"{len(jobs)} jobs, {len(jobs) - len(pending)} already done, {len(pending)} to run")
    lock = Lock()
    failures = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(diagnose, job): job for job in pending}
        for index, future in enumerate(as_completed(futures), start=1):
            job, record = futures[future], future.result()
            path = output_for(job)
            with lock:
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open("a", encoding="utf-8") as stream:
                    stream.write(json.dumps(record, ensure_ascii=False) + "\n")
            failures += record["status"] != "success"
            print(f"[{index}/{len(pending)}] {job.case_id} arm={job.arm} rep={job.rep} "
                  f"{record['status']} {record['duration_seconds']}s")
    if failures:
        print(f"WARNING: {failures} job(s) failed; rerun the same command to retry them")


# --------------------------------------------------------------------------- endemic

def endemic_jobs(reps: int) -> list[Job]:
    spec = yaml.safe_load(VIGNETTES.read_text(encoding="utf-8"))
    jobs = []
    for group in VIGNETTE_GROUPS:
        for case in spec[group]:
            arms = list(dict.fromkeys([*BASELINE_ARMS, *case["countries"]]))
            meta = {"group": group, "countries": case["countries"]}
            for arm in arms:
                for rep in range(1, reps + 1):
                    jobs.append(Job("endemic", case["id"], arm, rep, case["text"].strip(), meta))
    return jobs


def expected_rank(names: list[str], pattern: str) -> int | None:
    regex = re.compile(pattern, re.IGNORECASE)
    for position, name in enumerate(names, start=1):
        if regex.search(name):
            return position
    return None


def vignette_index() -> dict[str, dict[str, Any]]:
    """Case id -> group and expected pattern, read from the current YAML."""
    spec = yaml.safe_load(VIGNETTES.read_text(encoding="utf-8"))
    return {
        case["id"]: {"group": group, "expected": case["expected"]}
        for group in VIGNETTE_GROUPS
        for case in spec[group]
    }


def summarize_endemic(path: Path) -> str:
    index = vignette_index()
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    rows = [row for row in rows if row["status"] == "success" and row["case_id"] in index]
    by_case: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        by_case[row["case_id"]][row["arm"]].append(row)

    def names(row: dict[str, Any]) -> list[str]:
        return [str(item.get("diagnosis", "")) for item in row["final_response"]["data"]]

    def arm_order(arm: str) -> tuple[bool, bool, str]:
        return (arm != NO_COUNTRY, arm != "ES", arm)

    lines = ["| Case | Group | Arm | Rank of expected dx (per rep) | Top-1 per rep |", "|---|---|---|---|---|"]
    totals: dict[tuple[str, str], list[int]] = defaultdict(lambda: [0, 0, 0])  # runs, at #1, in top 5
    for case_id, arms in by_case.items():
        group, pattern = index[case_id]["group"], index[case_id]["expected"]
        for arm in sorted(arms, key=arm_order):
            ranks, tops = [], []
            for row in sorted(arms[arm], key=lambda r: r["rep"]):
                found = expected_rank(names(row), pattern)
                ranks.append("-" if found is None else str(found))
                tops.append(names(row)[0] if names(row) else "-")
                bucket = totals[(group, "baseline " + arm if arm in BASELINE_ARMS else "endemic country")]
                bucket[0] += 1
                bucket[1] += found == 1
                bucket[2] += found is not None
            lines.append(f"| {case_id} | {group} | {arm} | {', '.join(ranks)} | {' / '.join(tops)} |")

    lines += ["", "| Group | Arm | Runs | Expected at #1 | Expected in top 5 |", "|---|---|---|---|---|"]
    for (group, arm), (runs, top1, top5) in sorted(totals.items(), key=lambda item: (VIGNETTE_GROUPS.index(item[0][0]), item[0][1])):
        lines.append(f"| {group} | {arm} | {runs} | {top1} ({top1 / runs:.0%}) | {top5} ({top5 / runs:.0%}) |")
    return "\n".join(lines)


def run_endemic(args: argparse.Namespace) -> None:
    output = OUTPUT_ROOT / "endemic" / "responses.jsonl"
    run_jobs(endemic_jobs(args.reps), lambda _job: output, args.workers)
    report = summarize_endemic(output)
    (output.parent / "summary.md").write_text(report + "\n", encoding="utf-8")
    print("\n" + report)


def summarize_only(_args: argparse.Namespace) -> None:
    output = OUTPUT_ROOT / "endemic" / "responses.jsonl"
    report = summarize_endemic(output)
    (output.parent / "summary.md").write_text(report + "\n", encoding="utf-8")
    print(report)


# ------------------------------------------------------------------------- regression

def regression_jobs(arms: list[str], limit: int | None) -> list[Job]:
    manifest = yaml.safe_load(REGRESSION_MANIFEST.read_text(encoding="utf-8"))
    cases = manifest["cases"][:limit] if limit else manifest["cases"]
    jobs = []
    for case in cases:
        text = (REGRESSION_MANIFEST.parent / case["text_file"]).read_text(encoding="utf-8").strip()
        for arm in arms:
            jobs.append(Job("regression", str(case["id"]), arm, 1, text, {"gold": case["gold"]}))
    return jobs


def run_regression(args: argparse.Namespace) -> None:
    def output_for(job: Job) -> Path:
        return OUTPUT_ROOT / "regression" / job.arm / "responses.jsonl"

    run_jobs(regression_jobs(args.arms, args.limit), output_for, args.workers)
    for arm in args.arms:
        print(f"evaluate with: py bench\\multimodal_beta\\evaluate_v4.py "
              f"--responses bench\\location_context\\outputs\\regression\\{arm}\\responses.jsonl "
              f"--output-dir bench\\location_context\\outputs\\regression\\{arm}\\evaluation_v4_primary_strict")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--workers", type=int, default=6)
    suites = parser.add_subparsers(dest="suite", required=True)

    endemic = suites.add_parser("endemic")
    endemic.add_argument("--reps", type=int, default=2, help="Repetitions per case and arm (model noise).")
    endemic.set_defaults(run=run_endemic)

    suites.add_parser("summarize-endemic", help="Rebuild the endemic summary from saved responses.").set_defaults(run=summarize_only)

    regression = suites.add_parser("regression")
    regression.add_argument("--arms", nargs="+", default=[NO_COUNTRY, "IN", "NG"])
    regression.add_argument("--limit", type=int)
    regression.set_defaults(run=run_regression)
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    arguments.run(arguments)
