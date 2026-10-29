#!/usr/bin/env python3
"""
Strict metrics of Pipeline V5 runs by block
===========================================

Reads the evaluation_details.txt of one or more V5 runs and prints a Markdown
table per metric: total, each metadata.block of the dataset (narrative_v2:
live, urg, exam, synth), live + urg, and rare / not rare.

With --live-dates (data29/data-repos/narrative-v2/work/live_dates.json) it
adds "live unseen": the live cases published after the model's cutoff.

Gold entries with role "clinical" (HPO v2: the disease name without the gene)
are graded like any other gold. --without-clinical ignores them, which gives
the result with the gold with the gene (the original one) on the same judge
calls.

Usage:
    py score_blocks.py --dataset bench/datasets/narrative_v2.json \
                       --runs <run dir> [<run dir> ...] \
                       [--live-dates <live_dates.json>] [--without-clinical]
"""

import argparse
import glob
import json
import os
from typing import Dict, List, Optional

import yaml

EVAL_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))


def load_details(path: str) -> Dict[str, Dict]:
    with open(path, 'r', encoding='utf-8') as f:
        blocks = f.read().split('\n---\n')
    cases = {}
    for block in blocks:
        if block.strip():
            case = json.loads(block)
            cases[str(case["case_id"])] = case
    return cases


def strict_position(case: Dict, without_clinical: bool) -> Optional[int]:
    details = case["eval_details"]
    if not without_clinical:
        resolution = details.get("final_resolution")
        return int(resolution["position"][1:]) if resolution else None
    roles = {g["name"]: (g.get("details") or {}).get("role") for g in case.get("gdx_details", [])}
    best = None
    for gdx_trace in details.get("graded_trace", []):
        if roles.get(gdx_trace["gdx"]) == "clinical":
            continue
        for option in gdx_trace["options"]:
            if option["grade"] == 2:
                best = option["position"] if best is None else min(best, option["position"])
                break
    return best


def run_model(run_dir: str) -> str:
    for path in glob.glob(os.path.join(run_dir, '*___config.yaml')):
        with open(path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config['DXGPT_EMULATOR']['MODEL']
    return os.path.basename(os.path.dirname(run_dir))


def pct(positions: List[Optional[int]], k: int) -> str:
    if not positions:
        return "—"
    return f"{100.0 * sum(1 for p in positions if p is not None and p <= k) / len(positions):.1f} %".replace('.', ',')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', required=True, help='Dataset JSON, relative to the eval repo root')
    parser.add_argument('--runs', nargs='+', required=True, help='V5 evaluation folders (with evaluation_details.txt)')
    parser.add_argument('--live-dates', help='live_dates.json from data29/data-repos/narrative-v2/live_dates.py')
    parser.add_argument('--without-clinical', action='store_true', help='Ignore gold entries with role "clinical" (the name without the gene)')
    args = parser.parse_args()

    with open(os.path.join(EVAL_ROOT, args.dataset), 'r', encoding='utf-8') as f:
        dataset = {str(c['id']): c for c in json.load(f)}
    live_dates = None
    if args.live_dates:
        with open(args.live_dates, 'r', encoding='utf-8') as f:
            live_dates = json.load(f)

    order = ['live', 'urg', 'exam', 'synth']
    blocks = sorted({c.get('metadata', {}).get('block') for c in dataset.values()} - {None},
                    key=lambda b: (order.index(b) if b in order else len(order), b))
    groups = [('Total', lambda c: True)]
    groups += [(f'`{b}`', lambda c, b=b: c.get('metadata', {}).get('block') == b) for b in blocks]
    if {'live', 'urg'} <= set(blocks):
        groups.append(('`live`+`urg`', lambda c: c.get('metadata', {}).get('block') in ('live', 'urg')))
    if any('rare_disease' in c.get('metadata', {}) for c in dataset.values()):
        groups.append(('Raras', lambda c: c.get('metadata', {}).get('rare_disease') is True))
        groups.append(('No raras', lambda c: c.get('metadata', {}).get('rare_disease') is False))

    rows = []
    for run_dir in args.runs:
        details = load_details(os.path.join(run_dir, 'evaluation_details.txt'))
        model = run_model(run_dir)
        positions = {cid: strict_position(case, args.without_clinical) for cid, case in details.items()}
        cells = []
        for _, belongs in groups:
            selected = [positions[cid] for cid, c in dataset.items() if cid in positions and belongs(c)]
            cells.append((selected, len(selected)))
        if live_dates is not None:
            unseen = [positions[cid] for cid, row in live_dates.items()
                      if cid in positions and model not in row['maybe_seen_by']]
            cells.append((unseen, len(unseen)))
        missing = len(dataset) - len(positions)
        rows.append((model, cells, missing))

    headers = [name for name, _ in groups] + (['`live` sin ver'] if live_dates is not None else [])
    for k in (1, 5):
        print(f"\nR@{k} estricta{' (solo gold con gen, sin el nombre sin gen)' if args.without_clinical else ''}\n")
        print('| Modelo | ' + ' | '.join(headers) + ' |')
        print('|---|' + '---:|' * len(headers))
        for model, cells, _ in rows:
            print(f'| {model} | ' + ' | '.join(pct(sel, k) for sel, _ in cells) + ' |')
    print('\nCasos por columna: ' + ', '.join(f'{h} {n}' for h, (_, n) in zip(headers, rows[0][1])))
    for model, cells, missing in rows:
        if missing:
            print(f'Aviso: {model} no tiene evaluación para {missing} casos del dataset')
        if live_dates is not None:
            print(f'{model}: `live` sin ver = {cells[-1][1]} casos')


if __name__ == '__main__':
    main()
