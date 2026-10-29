#!/usr/bin/env python3
"""
Compare judges on the same DDX lists (ROADMAP step 6)
=====================================================

Each model's official narrative_v2 run is judged by gemini-2.5-pro. Re-scoring
the same lists with another judge (OUTPUT_TAG: judge_<model>) writes them to
output/narrative_v2/juanjo_classic_v2/<model folder>__judge_<model>/. This
script puts the judges side by side:

1. strict R@1 and R@5 of every model with every judge, total and live + urg;
2. whether the order of the models changes (Kendall tau against the reference
   judge);
3. agreement with the reference judge, case by case (strict hit at P1 and in
   the top 5) and option by option: same 2/1/0 grade (with Cohen's kappa),
   same "2 or not" (the only boundary the strict score uses), and in which
   direction the other judge differs;
4. calls, cost and latency of each judge.

A rerun of the reference judge (tag judge_<reference>_rerun) gives the noise
floor: how much the reference judge disagrees with itself.

build_report.py uses compare() to add the comparison to the V5 report.

Usage:
    py compare_judges.py --judges gemini-3.8-flash gemini-2.5-flash [--output judge_comparison.md]
"""

import argparse
import glob
import json
import os
from itertools import combinations
from typing import Dict, List, Optional

import yaml

from score_blocks import load_details

HERE = os.path.dirname(os.path.abspath(__file__))
EVAL_ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
NARRATIVE_DIR = os.path.join(HERE, 'output', 'narrative_v2', 'juanjo_classic_v2')
REFERENCE = 'gemini-2.5-pro'
MODELS = [
    ('gpt_6_1_sol_low_translated_en', 'gpt-6.1-sol'),
    ('claude_opus_5_low_translated_en', 'claude-opus-5'),
    ('gpt_5_6_terra_low_translated_en', 'gpt-5.6-terra'),
    ('gpt_6_1_terra_low_translated_en', 'gpt-6.1-terra'),
    ('gemini_3_1_pro_preview_low_translated_en', 'gemini-3.1-pro'),
    ('gpt_5_4_mini_low_translated_en', 'gpt-5.4-mini'),
]
SUBSETS = [('realcases', 'Casos reales (`live`+`urg`, 210)'), ('total', 'Total (300)')]


def tag_folder(judge: str) -> str:
    return 'judge_' + judge.replace('-', '_').replace('.', '_')


def latest_run(folder: str) -> Optional[str]:
    runs = sorted(glob.glob(os.path.join(folder, '2*')))
    runs = [r for r in runs if os.path.exists(os.path.join(r, 'evaluation_details.txt'))]
    return runs[-1] if runs else None


def run_judge(run: str) -> str:
    with open(glob.glob(os.path.join(run, '*___config.yaml'))[0], 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)['EVALUATOR']['JUDGE_MODEL']


def strict_position(case: Dict) -> Optional[int]:
    resolution = case['eval_details'].get('final_resolution')
    return int(resolution['position'][1:]) if resolution else None


def option_grades(case: Dict) -> Dict[tuple, int]:
    grades = {}
    for trace in case['eval_details'].get('graded_trace', []):
        for option in trace['options']:
            if option.get('grade') is not None:
                grades[(trace['gdx'], option['position'])] = option['grade']
    return grades


def kappa(pairs: List[tuple]) -> float:
    labels = sorted({a for a, _ in pairs} | {b for _, b in pairs})
    n = len(pairs)
    observed = sum(1 for a, b in pairs if a == b) / n
    expected = sum((sum(1 for a, _ in pairs if a == label) / n) * (sum(1 for _, b in pairs if b == label) / n)
                   for label in labels)
    return (observed - expected) / (1 - expected) if expected < 1 else 1.0


def kendall_tau(order_a: List[str], order_b: List[str]) -> float:
    rank_b = {m: i for i, m in enumerate(order_b)}
    concordant = discordant = 0
    for x, y in combinations(order_a, 2):
        if rank_b[x] < rank_b[y]:
            concordant += 1
        else:
            discordant += 1
    return (concordant - discordant) / (concordant + discordant)


def agreement(reference: Dict[str, Dict], other: Dict[str, Dict], case_ids) -> Dict:
    """Case-level and option-level agreement between two runs of the same lists."""
    same1 = same5 = 0
    pairs = []
    for case_id in case_ids:
        p_ref, p_other = strict_position(reference[case_id]), strict_position(other[case_id])
        same1 += (p_ref == 1) == (p_other == 1)
        same5 += (p_ref is not None and p_ref <= 5) == (p_other is not None and p_other <= 5)
        g_ref, g_other = option_grades(reference[case_id]), option_grades(other[case_id])
        pairs += [(g_ref[key], g_other[key]) for key in g_ref if key in g_other]
    return {'cases': len(case_ids), 'sameP1': same1, 'sameTop5': same5, 'pairs': pairs}


def summarize(parts: List[Dict]) -> Dict:
    cases = sum(p['cases'] for p in parts)
    pairs = [pair for p in parts for pair in p['pairs']]
    n = len(pairs)
    return {
        'cases': cases, 'options': n,
        'sameP1': 100 * sum(p['sameP1'] for p in parts) / cases,
        'sameTop5': 100 * sum(p['sameTop5'] for p in parts) / cases,
        'sameGrade': 100 * sum(1 for a, b in pairs if a == b) / n,
        'kappa': kappa(pairs),
        'same2': 100 * sum(1 for a, b in pairs if (a == 2) == (b == 2)) / n,
        'kappa2': kappa([(a == 2, b == 2) for a, b in pairs]),
        'higher': 100 * sum(1 for a, b in pairs if b > a) / n,
        'lower': 100 * sum(1 for a, b in pairs if b < a) / n,
    }


def compare(judges: List[str]) -> Optional[Dict]:
    """Everything the report needs; None if some judge has no run."""
    with open(os.path.join(EVAL_ROOT, 'bench', 'datasets', 'narrative_v2.json'), 'r', encoding='utf-8') as f:
        dataset = {c['id']: c for c in json.load(f)}
    subsets = {'total': list(dataset), 'realcases': [i for i, c in dataset.items() if c['metadata']['block'] in ('live', 'urg')]}

    all_judges = [REFERENCE] + list(judges)
    runs: Dict[str, Dict[str, Dict]] = {j: {} for j in all_judges}
    summaries: Dict[str, Dict[str, Dict]] = {j: {} for j in all_judges}
    for folder, name in MODELS:
        for judge in all_judges:
            run = latest_run(os.path.join(NARRATIVE_DIR, folder if judge == REFERENCE else f'{folder}__{tag_folder(judge)}'))
            if run is None:
                continue
            assert run_judge(run) == judge, (run, run_judge(run), judge)
            runs[judge][name] = load_details(os.path.join(run, 'evaluation_details.txt'))
            with open(os.path.join(run, 'summary.json'), 'r', encoding='utf-8') as f:
                summaries[judge][name] = json.load(f)
    models = [name for _, name in MODELS if all(name in runs[j] for j in all_judges)]
    if not models or not judges:
        return None

    def recall(details, ids, k):
        positions = [strict_position(details[i]) for i in ids]
        return round(100 * sum(1 for p in positions if p is not None and p <= k) / len(positions), 1)

    result = {'reference': REFERENCE, 'judges': all_judges, 'models': models, 'recall': {}, 'tau': {}, 'agreement': [], 'cost': []}
    for subset, _ in SUBSETS:
        for k in (1, 5):
            values = {j: {m: recall(runs[j][m], subsets[subset], k) for m in models} for j in all_judges}
            orders = {j: sorted(models, key=lambda m: -values[j][m]) for j in all_judges}
            result['recall'][f'{subset}_r{k}'] = {'values': values, 'orders': orders}
            result['tau'][f'{subset}_r{k}'] = {j: round(kendall_tau(orders[REFERENCE], orders[j]), 2) for j in judges}

    for judge in judges:
        parts = [agreement(runs[REFERENCE][m], runs[judge][m], list(dataset)) for m in models]
        result['agreement'].append({'judge': judge, 'scope': f'{len(models)} modelos', **summarize(parts)})
    for rerun_dir in sorted(glob.glob(os.path.join(NARRATIVE_DIR, f'*__{tag_folder(REFERENCE)}_rerun'))):
        name = next(n for f, n in MODELS if os.path.basename(rerun_dir).startswith(f + '__'))
        rerun = load_details(os.path.join(latest_run(rerun_dir), 'evaluation_details.txt'))
        part = agreement(runs[REFERENCE][name], rerun, list(dataset))
        result['agreement'].append({'judge': f'{REFERENCE} (repetido)', 'scope': name, **summarize([part])})

    for judge in all_judges:
        s = [summaries[judge][m] for m in models]
        result['cost'].append({
            'judge': judge, 'calls': sum(x['judge']['calls'] for x in s),
            'cost': round(sum(x['judge']['estimated_cost_usd'] or 0 for x in s), 2),
            'p50': sorted(x['judge']['p50_seconds'] for x in s)[len(s) // 2],
            'errors': sum(len(x['global']['cases_with_judge_errors']) for x in s),
        })
    return result


def num(value: float, digits: int = 1) -> str:
    return f'{value:.{digits}f}'.replace('.', ',')


def to_markdown(result: Dict) -> str:
    judges, models = result['judges'], result['models']
    out = ['# Comparación de jueces sobre `narrative_v2`', '',
           f'Mismas listas de diagnósticos; solo cambia el juez. Referencia: `{result["reference"]}`. '
           f'Modelos: {len(models)}.', '']
    for subset, title in SUBSETS:
        for k in (1, 5):
            block = result['recall'][f'{subset}_r{k}']
            out += [f'## R@{k} estricta · {title}', '',
                    '| Modelo | ' + ' | '.join(f'`{j}`' for j in judges) + ' |', '|---|' + '---:|' * len(judges)]
            for m in models:
                out.append(f'| {m} | ' + ' | '.join(num(block['values'][j][m]) + ' %' for j in judges) + ' |')
            out.append('| **Orden** | ' + ' | '.join(' > '.join(block['orders'][j]) for j in judges) + ' |')
            out.append('| Kendall tau con la referencia | 1 | ' +
                       ' | '.join(num(result['tau'][f'{subset}_r{k}'][j], 2) for j in judges[1:]) + ' |')
            out.append('')
    out += ['## Coincidencia con la referencia', '',
            'Por caso: ¿coinciden en si hay acierto estricto en P1 (o en el top 5)? Por opción: ¿ponen la misma nota '
            '2/1/0, y coinciden en «es un 2 o no» (lo único que usa la nota estricta)? «Más nota» = el otro juez puntúa más alto.', '',
            '| Juez | Sobre | Mismo veredicto P1 | Mismo veredicto top 5 | Misma nota 2/1/0 | Kappa 2/1/0 | Mismo «2 o no» | Kappa «2 o no» | Más nota | Menos nota | Opciones |',
            '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for a in result['agreement']:
        out.append(f'| `{a["judge"]}` | {a["scope"]} | {num(a["sameP1"])} % | {num(a["sameTop5"])} % | {num(a["sameGrade"])} % | '
                   f'{num(a["kappa"], 2)} | {num(a["same2"])} % | {num(a["kappa2"], 2)} | {num(a["higher"])} % | {num(a["lower"])} % | {a["options"]} |')
    out += ['', '## Coste y latencia del juez', '',
            '| Juez | Llamadas | Coste estimado | Mediana por llamada | Casos con error del juez |', '|---|---:|---:|---:|---:|']
    for c in result['cost']:
        out.append(f'| `{c["judge"]}` | {c["calls"]} | {num(c["cost"], 2)} $ | {num(c["p50"])} s | {c["errors"]} |')
    return '\n'.join(out) + '\n'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--judges', nargs='+', required=True, help='Judges re-scored with OUTPUT_TAG judge_<model>')
    parser.add_argument('--output', default=os.path.join(NARRATIVE_DIR, 'judge_comparison.md'))
    args = parser.parse_args()
    result = compare(args.judges)
    if result is None:
        raise SystemExit('No runs for those judges')
    text = to_markdown(result)
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(text)
    print(text)
    print(f'Wrote {args.output}')


if __name__ == '__main__':
    main()
