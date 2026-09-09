"""Score a reused T+I eval against David's ronda 2 labels.

Does not call models. Skips 24910386 (invalid form label) until David recodes it.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


HERE = Path(__file__).resolve().parent
DELIVERABLE = HERE / "reviews" / "david_deliverable_ronda2.md"
SKIP = {"24910386"}


def parse_david(path: Path) -> dict[str, dict[str, str]]:
    text = path.read_text(encoding="utf-8")
    rows: dict[str, dict[str, str]] = {}
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 5:
            continue
        case_id = cells[0]
        if not re.match(r"^(N-)?\d+$", case_id):
            continue
        pos_raw = cells[1]
        try:
            pos = int(pos_raw) if pos_raw else None
        except ValueError:
            pos = None
        rows[case_id] = {
            "pos": pos,
            "verdict": cells[2],
            "gold": cells[3],
        }
    return rows


def load_details(path: Path) -> dict[str, dict]:
    out = {}
    for block in path.read_text(encoding="utf-8").split("\n---\n"):
        if not block.strip():
            continue
        row = json.loads(block)
        case_id = str(row.get("case_id") or row.get("id") or "")
        ev = row.get("eval_details") or {}
        fr = ev.get("final_resolution") or {}
        pos = None
        raw = fr.get("position")
        if raw:
            try:
                pos = int(str(raw).lstrip("Pp"))
            except ValueError:
                pos = None
        method = str(fr.get("method") or "").upper()
        out[case_id] = {
            "match": bool(ev.get("best_match_found")),
            "pos": pos,
            "method": method,
        }
    return out


def expected_match(david: dict) -> bool | None:
    verdict = david["verdict"]
    if verdict == "falso_positivo":
        return False
    if verdict == "falso_negativo":
        return True
    if verdict == "correcto":
        pos = david["pos"]
        return bool(pos and pos > 0)
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--details", type=Path, required=True)
    parser.add_argument("--label", required=True)
    args = parser.parse_args()
    david = parse_david(DELIVERABLE)
    run = load_details(args.details)
    scored = 0
    agree = 0
    disagree = []
    skipped = []
    for case_id, drow in david.items():
        if case_id in SKIP:
            skipped.append(case_id)
            continue
        want = expected_match(drow)
        if want is None:
            skipped.append(case_id)
            continue
        got = run.get(case_id)
        if got is None:
            skipped.append(case_id)
            continue
        scored += 1
        if got["match"] == want:
            agree += 1
        else:
            disagree.append(
                f"{case_id} david={drow['verdict']} want_match={want} "
                f"got_match={got['match']} method={got['method']} P={got['pos']}"
            )
    n = scored
    print(f"{args.label}: agree {agree}/{n} ({100 * agree / n:.1f}%)  skip {skipped}")
    for line in disagree:
        print("  DISAGREE", line)
    matched = sum(1 for v in run.values() if v["match"])
    print(f"  coverage {matched}/{len(run)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
