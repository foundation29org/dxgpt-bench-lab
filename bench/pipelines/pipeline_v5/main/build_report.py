#!/usr/bin/env python3
"""
Build docs/benchmark-report-v5.html from the Pipeline V5 run outputs
====================================================================

Reads the latest V5 run of each reference model on narrative_v2, the medium
reasoning-effort runs, the agentic PoC arms (bench/agentic_poc), the HPO v2
runs, the V4 strict HPO runs they are compared with, the model cutoffs and the
PubMed dates of the live block, and writes a self-contained HTML report with
the same stylesheet as the strict reports (docs/benchmark-report-strict.css).

Every number in the report comes from the run files, so after re-scoring
(narrative_v2 v0.2, a new model) it is enough to run this script again.

Usage:
    py build_report.py [--output ../../../../docs/benchmark-report-v5.html]
"""

import argparse
import collections
import glob
import html
import json
import math
import os
import re
import statistics
from datetime import date
from math import comb

import yaml

import compare_judges
from score_blocks import load_details, strict_position

HERE = os.path.dirname(os.path.abspath(__file__))
EVAL_ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
OUTPUT_ROOT = os.path.join(HERE, 'output')
NARRATIVE_DIR = os.path.join(OUTPUT_ROOT, 'narrative_v2', 'juanjo_classic_v2')
NARRATIVE_V2 = os.path.join(EVAL_ROOT, 'bench', 'datasets', 'narrative_v2.json')
NARRATIVE_TOOLS = os.path.join(EVAL_ROOT, 'data29', 'data-repos', 'narrative-v2')
JUDGE_AUDIT = os.path.join(EVAL_ROOT, 'bench', 'multimodal_beta', 'outputs', 'judge_audit')
BASELINE = 'terra56'
# Cheaper judges re-scored on the same narrative_v2 lists (OUTPUT_TAG judge_<model>)
# claude-opus-5-5: judge from another family (Anthropic), to check the dependence on Gemini
JUDGE_CANDIDATES = ['gemini-3.8-flash', 'gemini-2.5-flash', 'claude-opus-5-5']

# id, run folder, model as in model_cutoffs.yaml, label, colour (fixed per model)
MODELS = [
    ('sol61', 'gpt_6_1_sol_low_translated_en', 'gpt-6.1-sol', 'gpt-6.1-sol low', '#2a78d6'),
    ('opus5', 'claude_opus_5_low_translated_en', 'claude-opus-5', 'Claude Opus 5 low', '#eb6834'),
    ('terra56', 'gpt_5_6_terra_low_translated_en', 'gpt-5.6-terra', 'gpt-5.6-terra low', '#1baf7a'),
    ('terra61', 'gpt_6_1_terra_low_translated_en', 'gpt-6.1-terra', 'gpt-6.1-terra low', '#eda100'),
    ('gem31', 'gemini_3_1_pro_preview_low_translated_en', 'gemini-3.1-pro-preview', 'gemini-3.1-pro-preview low', '#e87ba4'),
    ('mini54', 'gpt_5_4_mini_low_translated_en', 'gpt-5.4-mini', 'gpt-5.4-mini low', '#008300'),
]

GROUPS = [
    ('total', 'Total', lambda c: True),
    ('realRare', 'Raras, casos reales', lambda c: c['metadata']['block'] in ('live', 'urg') and c['metadata'].get('rare_disease') is True),
    ('realCommon', 'No raras, casos reales', lambda c: c['metadata']['block'] in ('live', 'urg') and c['metadata'].get('rare_disease') is False),
    ('realcases', '<code>live</code>+<code>urg</code>', lambda c: c['metadata']['block'] in ('live', 'urg')),
    ('live', '<code>live</code>', lambda c: c['metadata']['block'] == 'live'),
    ('urg', '<code>urg</code>', lambda c: c['metadata']['block'] == 'urg'),
    ('exam', '<code>exam</code>', lambda c: c['metadata']['block'] == 'exam'),
    ('synth', '<code>synth</code>', lambda c: c['metadata']['block'] == 'synth'),
    ('rare', 'Raras', lambda c: c['metadata'].get('rare_disease') is True),
    ('common', 'No raras', lambda c: c['metadata'].get('rare_disease') is False),
]

# Groups for the effort and agentic sections: real cases split by rare / not rare
REAL_SPLIT = [
    ('realcases', 'Casos reales (<code>live</code>+<code>urg</code>)', lambda c: c['metadata']['block'] in ('live', 'urg')),
    ('realRare', 'Raras, casos reales', lambda c: c['metadata']['block'] in ('live', 'urg') and c['metadata'].get('rare_disease') is True),
    ('realCommon', 'No raras, casos reales', lambda c: c['metadata']['block'] in ('live', 'urg') and c['metadata'].get('rare_disease') is False),
    ('exam', '<code>exam</code>', lambda c: c['metadata']['block'] == 'exam'),
    ('total', 'Total', lambda c: True),
]

# Generation prices, USD per million tokens in / out (Server/services/costUtils.js)
PRICES = {'gpt-5.6-terra': (2.0, 12.0), 'gpt-6.1-sol': (2.0, 10.0)}

# Same model and prompt with reasoning_effort medium: model id, run folder
EFFORT = [
    ('terra56', 'gpt_5_6_terra_medium_translated_en'),
    ('sol61', 'gpt_6_1_sol_medium_translated_en'),
]

# Second run of the same model, config and cases (run-to-run variability): model id, run folder
# Same model with the prompt that asks for exactly 5 diagnoses (production left «N» to the model until 30-oct-2026)
N5_PROMPT = 'juanjo_classic_v2_n5'
N5 = [('terra56', 'gpt_5_6_terra_low_translated_en'), ('sol61', 'gpt_6_1_sol_low_translated_en')]
RERUNS = [('terra56', 'gpt_5_6_terra_low_translated_en__rerun2'), ('sol61', 'gpt_6_1_sol_low_translated_en__rerun2')]

# gpt-6.1-sol on HPO v2, same prompt and parameters as Terra's July lists; Flash re-scoring tag
HPO_FOLDERS = {'terra': 'gpt_5_6_terra_low', 'sol': 'gpt_6_1_sol_low'}
FLASH_TAG = '__judge_gemini_3_8_flash'

# MyGene2 gold where the two judges disagree the most: OMIM 108145 is distal arthrogryposis
# type 5 (PIEZO2, same disease); type 5D is another disease (ECEL1, OMIM 615065)
JUDGE_EXAMPLE = ('mygene2_hpo', 'Arthrogryposis with oculomotor limitation and electroretinal anomalies')
# HPO v2 gold plus the MONDO exact synonyms of each OMIM code in accepted_names
# (data29/data-repos/hpo-v2/gold_synonyms.py): same lists and judges, only the gold changes
SYN_VERSION = 'v2_syn'
# sermas (rare-disease DxGPT on App Service): DxGPT's prompt plus «specialized in rare diseases»,
# on four HPO v2 datasets; both prompts graded by Gemini 3.8 Flash
SERMAS_PROMPT = 'sermas_rare'
# Same narrative_v2 lists graded with graded_v3 (Julián's point 6) and one grade per repeated option
GRADED_V3_TAG = '__graded_v3'
GRADED_V3_EXAMPLE = ('L-PMC13354413', 'terra56')
# Claude Opus 5 on the four smaller HPO v2 datasets, same prompt and judge (Gemini 2.5 Pro) as Sol and Terra
OPUS_HPO_FOLDER = 'claude_opus_5_low'
OPUS_HPO = ['lirical_hpo', 'mygene2_hpo', 'hms_hpo', 'mme_hpo']
OPUS_PRICE = (5.0, 25.0)
SERMAS_HPO = ['mme_hpo', 'hms_hpo', 'mygene2_hpo', 'lirical_hpo']
HPO_MODEL_IDS = {'terra': 'gpt-5.6-terra', 'sol': 'gpt-6.1-sol'}

# HPO v2 cases (DDD comes from the public G2P panel) that show what "with gene" and
# "without gene" mean: dataset, case id, why it counts or not
GENE_EXAMPLES = [
    ('ddd_hpo', 'DDD_G2P01077', 'Más de diez genes dan el mismo síndrome de Noonan: sin estudio genético se llega al síndrome, no al gen.'),
    ('ddd_hpo', 'DDD_G2P00906', 'Más de veinte genes dan la misma anemia de Fanconi.'),
    ('ddd_hpo', 'DDD_G2P00034', 'El síndrome de Rett se debe casi siempre a MECP2: el modelo nombra el gen y cuenta en las dos.'),
    ('ddd_hpo', 'DDD_G2P01363', 'Sin el gen queda «autism», un rasgo y no un diagnóstico: no se añade nombre sin gen.'),
    ('ddd_hpo', 'DDD_G2P00001', 'Respuesta de otra enfermedad: no cuenta en ninguna.'),
]

# Agentic PoC arms: base model id, arm, label, models whose lists must exist
# before the second stage (the panel waits for the slowest)
POC_WORK = os.path.join(EVAL_ROOT, 'bench', 'agentic_poc', 'work')
POC_ARMS = [
    ('terra56', 'arm_a_self_critique', 'A · autocrítica', ['terra56']),
    ('terra56', 'arm_c_sources', 'C · fuentes HPO + PubMed', ['terra56']),
    ('terra56', 'arm_b_panel_terra_sol', 'B2 · panel Terra + Sol', ['terra56', 'sol61']),
    ('terra56', 'arm_b_panel', 'B · panel Terra + Sol + Opus', ['terra56', 'sol61', 'opus5']),
    ('sol61', 'arm_a_self_critique_on_sol', 'A · autocrítica', ['sol61']),
    ('sol61', 'arm_c_sources_on_sol', 'C · fuentes HPO + PubMed', ['sol61']),
    ('sol61', 'arm_b_panel_terra_sol_on_sol', 'B2 · panel Terra + Sol, modera Sol', ['sol61', 'terra56']),
]

# HPO datasets: key, label, V4 strict folder under judge_audit
HPO = [
    ('ddd_hpo', 'DDD', os.path.join('rare_hpo_terra_strict_gemini25pro', 'ddd')),
    ('ramedis_hpo', 'RAMEDIS', os.path.join('rare_hpo_terra_strict_gemini25pro', 'ramedis')),
    ('lirical_hpo', 'LIRICAL', os.path.join('rare_hpo_terra_strict_gemini25pro', 'lirical')),
    ('mygene2_hpo', 'MyGene2', os.path.join('rare_hpo_terra_strict_gemini25pro', 'mygene2')),
    ('hms_hpo', 'HMS', 'hms88_gpt56terra_low_strict'),
    ('mme_hpo', 'MME', os.path.join('rare_hpo_terra_strict_gemini25pro', 'mme')),
]

# all_256_clean, Terra low: V4 strict and the first V5 re-evaluation (pipeline_v5/main/README.md)
ALL256 = [
    ('gpt-5.6-terra low', 'V4 strict', 63.3, 80.1, 83.2),
    ('gpt-5.6-terra low', 'V5 <code>graded_v1</code>, gold del dataset (sin normalizar)', 69.1, 79.3, 81.2),
    ('gpt-6.1-terra low', 'V4 strict', 62.5, 75.0, 77.3),
    ('gpt-6.1-sol low', 'V4 strict', 64.1, 76.6, 82.0),
]


def position(resolution):
    return int(resolution['position'][1:]) if resolution else None


def latest_run(folder):
    runs = sorted(glob.glob(os.path.join(folder, '2*')))
    return runs[-1] if runs else None


def metrics(strict, lax=None):
    n = len(strict)
    lax = strict if lax is None else lax

    def pct(values, k):
        return round(100 * sum(1 for p in values if p is not None and p <= k) / n, 1) if n else None

    matched = [p for p in strict if p is not None]
    return {
        'n': n, 'r1': pct(strict, 1), 'r3': pct(strict, 3), 'r5': pct(strict, 5),
        'cov': round(100 * len(matched) / n, 1) if n else None,
        'avgPos': round(statistics.mean(matched), 3) if matched else None,
        'p1': sum(1 for p in strict if p == 1), 'p23': sum(1 for p in strict if p in (2, 3)),
        'p45': sum(1 for p in strict if p in (4, 5)), 'p6p': sum(1 for p in strict if p is not None and p >= 6),
        'laxR1': pct(lax, 1), 'laxR5': pct(lax, 5),
    }


def mcnemar_p(wins, losses):
    n = wins + losses
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(comb(n, i) for i in range(min(wins, losses) + 1)) / 2 ** n)


def paired(a, b, ids, k):
    """Cases where a hits and b misses (wins) and the reverse, with exact McNemar.
    k is a cutoff, or a dict with a cutoff per case."""
    def hit(positions, i):
        cutoff = k[i] if isinstance(k, dict) else k
        return positions[i] is not None and positions[i] <= cutoff
    wins = sum(1 for i in ids if hit(a, i) and not hit(b, i))
    losses = sum(1 for i in ids if hit(b, i) and not hit(a, i))
    return {'wins': wins, 'losses': losses, 'net': round(100 * (wins - losses) / len(ids), 1),
            'p': round(mcnemar_p(wins, losses), 3)}


def pooled_sign_test(a_runs, b_runs, ids, k=1):
    """Both runs of each model at once: per case, hits of A minus hits of B (each from 0 to the number of runs),
    and an exact two-sided sign test on the cases where they differ."""
    def hits(runs, i):
        return sum(1 for p in runs if p[i] is not None and p[i] <= k)
    diffs = [hits(a_runs, i) - hits(b_runs, i) for i in ids]
    wins, losses = sum(1 for d in diffs if d > 0), sum(1 for d in diffs if d < 0)
    n = wins + losses
    p = min(1.0, 2 * sum(math.comb(n, j) for j in range(min(wins, losses) + 1)) / 2 ** n) if n else 1.0
    return {'a': round(100 * sum(hits(a_runs, i) for i in ids) / (len(a_runs) * len(ids)), 1),
            'b': round(100 * sum(hits(b_runs, i) for i in ids) / (len(b_runs) * len(ids)), 1),
            'wins': wins, 'losses': losses, 'p': p}


def finished_run(folder):
    """Latest run in folder whose evaluation has finished (summary.json written), or None."""
    runs = [r for r in sorted(glob.glob(os.path.join(folder, '2*'))) if os.path.exists(os.path.join(r, 'summary.json'))]
    return runs[-1] if runs else None


def load_labeled(folder):
    with open(glob.glob(os.path.join(folder, '*___ddxs_from_labeler.json'))[0], 'r', encoding='utf-8') as f:
        return json.load(f)


def narrative_run(folder):
    """Strict positions of the latest V5 run in a narrative_v2 folder, the run name and the labeler lists."""
    run = latest_run(os.path.join(NARRATIVE_DIR, folder))
    details = load_details(os.path.join(run, 'evaluation_details.txt'))
    strict = {k: position(v['eval_details']['final_resolution']) for k, v in details.items()}
    return strict, os.path.basename(run), load_labeled(os.path.join(NARRATIVE_DIR, folder))


def hpo_example(case):
    """Gold with gene, gene-free name, and the model's answer graded against each: the first
    option that hits either gold, or the first option if none does."""
    roles = {g['name']: (g.get('details') or {}).get('role') for g in case['gdx_details']}
    gold = next(name for name, role in roles.items() if role != 'clinical')
    clinical = next((name for name, role in roles.items() if role == 'clinical'), None)
    grades = {t['gdx']: [o['grade'] for o in t['options']] for t in case['eval_details'].get('graded_trace', [])}
    names = [d['name'] for d in case['ddx_details']]
    hits = [p for p in range(len(names)) if grades[gold][p] == 2 or (clinical and grades[clinical][p] == 2)]
    p = hits[0] if hits else 0
    return {'gold': gold, 'clinical': clinical, 'answer': names[p], 'position': p + 1,
            'gradeGold': grades[gold][p], 'gradeClinical': grades[clinical][p] if clinical else None}


def generation_cost(folder, model):
    """Mean generation cost per case in USD, from the token counts in emulator.log."""
    log = os.path.join(NARRATIVE_DIR, folder, 'emulator.log')
    if model not in PRICES or not os.path.exists(log):
        return None
    with open(log, 'r', encoding='utf-8', errors='ignore') as f:
        tokens = [(int(a), int(b)) for a, b in re.findall(r'prompt=(\d+), completion=(\d+)', f.read())]
    price_in, price_out = PRICES[model]
    return sum(a * price_in + b * price_out for a, b in tokens) / 1e6 / len(tokens) if tokens else None


def hpo_sol():
    """gpt-6.1-sol against Terra on the HPO v2 datasets Sol has finished, with Gemini 2.5 Pro,
    and how Gemini 3.8 Flash grades the same lists. Case ids are prefixed with the dataset."""
    result = {'rows': [], 'pending': [], 'judges': []}
    every = {name: {} for name in ('terra', 'sol', 'terraGene', 'solGene')}
    limit, cost, judge_cost, times = {}, 0.0, 0.0, []
    flash_parts = {'terra': [], 'sol': []}
    flash_pos = {(m, j): {} for m in HPO_FOLDERS for j in ('pro', 'flash')}
    example = {(j, kind): [0, 0] for j in ('pro', 'flash') for kind in ('da5', 'da5d')}
    example['cases'] = set()
    for key, label, _ in HPO:
        folder = os.path.join(OUTPUT_ROOT, f'{key}_v2', 'juanjo_classic_v2')
        runs = {m: finished_run(os.path.join(folder, f)) for m, f in HPO_FOLDERS.items()}
        for m, f in HPO_FOLDERS.items():
            flash = finished_run(os.path.join(folder, f + FLASH_TAG))
            if runs[m] and flash:
                pro_details = load_details(os.path.join(runs[m], 'evaluation_details.txt'))
                flash_details = load_details(os.path.join(flash, 'evaluation_details.txt'))
                common = [i for i in pro_details if i in flash_details]
                flash_parts[m].append(compare_judges.agreement(pro_details, flash_details, common))
                for judge, details in (('pro', pro_details), ('flash', flash_details)):
                    flash_pos[(m, judge)].update({f'{key}:{i}': strict_position(details[i], False) for i in common})
                    if key == JUDGE_EXAMPLE[0]:
                        count_example(details, judge, example)
        if not runs['sol']:
            result['pending'].append(label)
            continue
        details = {m: load_details(os.path.join(runs[m], 'evaluation_details.txt')) for m in HPO_FOLDERS}
        lengths = {m: {c['id']: len(c.get('ddx_details', {})) for c in load_labeled(os.path.join(folder, f))}
                   for m, f in HPO_FOLDERS.items()}
        ids = [i for i in details['terra'] if i in details['sol']]
        keys = [f'{key}:{i}' for i in ids]
        for m in HPO_FOLDERS:
            every[m].update({f'{key}:{i}': strict_position(details[m][i], False) for i in ids})
            every[m + 'Gene'].update({f'{key}:{i}': strict_position(details[m][i], True) for i in ids})
        limit.update({f'{key}:{i}': min(5, lengths['terra'][i]) for i in ids})
        sol_folder = os.path.join(folder, HPO_FOLDERS['sol'])
        cost += (generation_cost(sol_folder, 'gpt-6.1-sol') or 0) * len(lengths['sol'])
        times += [c['emulator_time_seconds'] for c in load_labeled(sol_folder) if c.get('emulator_time_seconds')]
        with open(os.path.join(runs['sol'], 'summary.json'), 'r', encoding='utf-8') as f:
            judge_cost += json.load(f)['judge']['estimated_cost_usd']
        result['rows'].append(sol_row(label, keys, every, limit, lengths, ids))
    if result['rows']:
        keys = list(every['terra'])
        result['total'] = sol_row('Total', keys, every, limit, None, None)
        result['cost'] = cost / len(keys)
        result['latency'] = round(statistics.median(times), 1)
        result['judgeCost'] = round(judge_cost, 2)
    for m, parts in flash_parts.items():
        if parts:
            keys = list(flash_pos[(m, 'pro')])
            result['judges'].append({'model': m, **compare_judges.summarize(parts),
                                     'proR1': metrics([flash_pos[(m, 'pro')][k] for k in keys])['r1'],
                                     'flashR1': metrics([flash_pos[(m, 'flash')][k] for k in keys])['r1']})
    keys = [k for k in flash_pos[('sol', 'flash')] if k in flash_pos[('terra', 'flash')]]
    if keys:
        result['flash'] = {'n': len(keys), 'r1': paired(flash_pos[('sol', 'flash')], flash_pos[('terra', 'flash')], keys, 1),
                           **{m: metrics([flash_pos[(m, 'flash')][k] for k in keys]) for m in HPO_FOLDERS}}
        mygene = [k for k in keys if k.startswith(JUDGE_EXAMPLE[0] + ':')]
        cases = example.pop('cases')
        result['example'] = {'grades': {f'{j}_{kind}': v for (j, kind), v in example.items()}, 'cases': len(cases),
                             'solR1': {j: metrics([flash_pos[('sol', j)][k] for k in mygene])['r1'] for j in ('pro', 'flash')}}
    return result


def hpo_syn():
    """Same HPO lists and judges, gold v2 against gold v2 plus MONDO exact synonyms (HPO v2_syn)."""
    result = {'rows': [], 'agreement': [], 'example': {}}
    positions = {}
    for judge, tag in (('pro', ''), ('flash', FLASH_TAG)):
        for m, f in HPO_FOLDERS.items():
            before, after, labels = {}, {}, []
            for key, label, _ in HPO:
                runs = [finished_run(os.path.join(OUTPUT_ROOT, f'{key}_{version}', 'juanjo_classic_v2', f + tag))
                        for version in ('v2', SYN_VERSION)]
                if not all(runs):
                    continue
                details = [load_details(os.path.join(run, 'evaluation_details.txt')) for run in runs]
                for i in details[0]:
                    if i in details[1]:
                        before[f'{key}:{i}'] = strict_position(details[0][i], False)
                        after[f'{key}:{i}'] = strict_position(details[1][i], False)
                labels.append(label)
                if key == JUDGE_EXAMPLE[0] and judge == 'pro':
                    for name, d in zip(('v2', 'syn'), details):
                        counts = result['example'].setdefault(name, {(name, kind): [0, 0] for kind in ('da5', 'da5d')} | {'cases': set()})
                        count_example(d, name, counts)
            positions[(judge, m)] = (before, after)
            if before:
                keys = list(before)
                result['rows'].append({'judge': judge, 'model': m, 'datasets': labels, 'n': len(keys),
                                       'before': metrics([before[k] for k in keys]), 'after': metrics([after[k] for k in keys]),
                                       'test': paired(after, before, keys, 1)})
    for m in HPO_FOLDERS:
        if (('pro', m) not in positions) or (('flash', m) not in positions):
            continue
        keys = [k for k in positions[('pro', m)][0] if k in positions[('flash', m)][0]]
        if not keys:
            continue
        row = {'model': m, 'n': len(keys)}
        for index, version in enumerate(('v2', 'syn')):
            pro, flash = positions[('pro', m)][index], positions[('flash', m)][index]
            row[version] = {'sameP1': round(100 * sum(1 for k in keys if (pro[k] == 1) == (flash[k] == 1)) / len(keys), 1),
                            'pro': metrics([pro[k] for k in keys])['r1'], 'flash': metrics([flash[k] for k in keys])['r1']}
        result['agreement'].append(row)
    result['example'] = {version: {kind: counts[(version, kind)] for kind in ('da5', 'da5d')}
                         for version, counts in result['example'].items()}
    return result


def lax_position(case):
    """Best position with grade 1 or 2 for any gold: a near miss counts."""
    best = strict_position(case, False)
    for trace in case['eval_details'].get('graded_trace', []):
        for option in trace['options']:
            if option['grade'] in (1, 2):
                best = option['position'] if best is None else min(best, option['position'])
    return best


def hpo_opus():
    """Claude Opus 5 against Sol and Terra on the HPO v2 datasets Opus has finished, Gemini 2.5 Pro judge."""
    folders = {**HPO_FOLDERS, 'opus': OPUS_HPO_FOLDER}
    strict, lax = {m: {} for m in folders}, {m: {} for m in folders}
    rows, lengths, tokens, judge_cost = [], [], [0, 0], 0.0
    for key, label, _ in HPO:
        if key not in OPUS_HPO:
            continue
        root = os.path.join(OUTPUT_ROOT, f'{key}_v2', 'juanjo_classic_v2')
        runs = {m: finished_run(os.path.join(root, f)) for m, f in folders.items()}
        if not all(runs.values()):
            continue
        details = {m: load_details(os.path.join(r, 'evaluation_details.txt')) for m, r in runs.items()}
        ids = sorted(set.intersection(*(set(d) for d in details.values())))
        keys = [f'{key}:{i}' for i in ids]
        for m in folders:
            strict[m].update({f'{key}:{i}': strict_position(details[m][i], False) for i in ids})
            lax[m].update({f'{key}:{i}': lax_position(details[m][i]) for i in ids})
        rows.append({'label': label, 'n': len(keys), **{m: metrics([strict[m][k] for k in keys]) for m in folders},
                     'r1': paired(strict['sol'], strict['opus'], keys, 1)})
        folder = os.path.join(root, OPUS_HPO_FOLDER)
        lengths += [len(c.get('ddx_details', {})) for c in load_labeled(folder)]
        with open(os.path.join(folder, 'emulator.log'), 'r', encoding='utf-8', errors='ignore') as f:
            for a, b in re.findall(r'input=(\d+), output=(\d+)', f.read()):
                tokens[0] += int(a)
                tokens[1] += int(b)
        with open(os.path.join(runs['opus'], 'summary.json'), 'r', encoding='utf-8') as f:
            judge_cost += json.load(f)['judge']['estimated_cost_usd']
    keys = list(strict['opus'])
    if not keys:
        return None
    total = {'label': 'Total', 'n': len(keys), **{m: metrics([strict[m][k] for k in keys]) for m in folders},
             'r1': paired(strict['sol'], strict['opus'], keys, 1), 'r5': paired(strict['sol'], strict['opus'], keys, 5),
             'terraR1': paired(strict['terra'], strict['opus'], keys, 1)}
    return {'rows': rows, 'total': total, 'options': statistics.median(lengths),
            'lax': {m: metrics([lax[m][k] for k in keys])['r1'] for m in folders},
            'laxTest': paired(lax['sol'], lax['opus'], keys, 1),
            'cost': (tokens[0] * OPUS_PRICE[0] + tokens[1] * OPUS_PRICE[1]) / 1e6 / len(lengths), 'judgeCost': round(judge_cost, 2)}


def option_key(case_id, gold, name):
    return case_id, gold, re.sub(r'[\W_]+', ' ', name.lower()).strip()


def graded_v3(dataset, tag=GRADED_V3_TAG):
    """graded_v2 against graded_v3 on the same narrative_v2 lists, Gemini 2.5 Pro on both."""
    runs = {}
    for mid, folder, _, name, color in MODELS:
        v3 = finished_run(os.path.join(NARRATIVE_DIR, folder + tag))
        if v3:
            runs[mid] = {'name': name, 'color': color,
                         'v2': load_details(os.path.join(latest_run(os.path.join(NARRATIVE_DIR, folder)), 'evaluation_details.txt')),
                         'v3': load_details(os.path.join(v3, 'evaluation_details.txt')), 'v3Run': v3}
    if not runs:
        return None
    groups = {key: [i for i, c in dataset.items() if belongs(c)] for key, _, belongs in REAL_SPLIT}
    result = {'models': [], 'n': len(runs)}
    positions = {}
    for mid, r in runs.items():
        pos = {v: {i: position(c['eval_details']['final_resolution']) for i, c in r[v].items()} for v in ('v2', 'v3')}
        positions[mid] = pos
        result['models'].append({'id': mid, 'name': r['name'], 'color': r['color'],
                                 'groups': {key: {'n': len(ids), 'v2': metrics([pos['v2'][i] for i in ids]), 'v3': metrics([pos['v3'][i] for i in ids]),
                                                  'r1': paired(pos['v3'], pos['v2'], ids, 1)} for key, ids in groups.items()}})
    result['order'] = {v: [m['name'] for m in sorted(result['models'], key=lambda m: -m['groups']['realcases'][v]['r1'])] for v in ('v2', 'v3')}
    if {'sol61', 'terra56'} <= set(positions):
        result['solTerra'] = {v: {key: paired(positions['sol61'][v], positions['terra56'][v], groups[key], 1) for key in ('realcases', 'realRare')}
                              for v in ('v2', 'v3')}

    # Identical options (same case, gold and text) across the models, and how each option's grade moved
    seen = {v: {} for v in ('v2', 'v3')}
    moves = {}
    for r in runs.values():
        for v in ('v2', 'v3'):
            for case_id, case in r[v].items():
                for trace in case['eval_details'].get('graded_trace', []):
                    for option in trace['options']:
                        if option['grade'] is not None and not option.get('code_match'):
                            seen[v].setdefault(option_key(case_id, trace['gdx'], option['name']), set()).add(option['grade'])
        for case_id, case in r['v2'].items():
            after = {(t['gdx'], o['position']): o['grade'] for t in r['v3'].get(case_id, {}).get('eval_details', {}).get('graded_trace', [])
                     for o in t['options']}
            for trace in case['eval_details'].get('graded_trace', []):
                for option in trace['options']:
                    new = after.get((trace['gdx'], option['position']))
                    if option['grade'] is not None and new is not None:
                        moves[(option['grade'], new)] = moves.get((option['grade'], new), 0) + 1
    # Cases that change their P1 hit, whether the P1 grade came from the cache and whether the option is a disjunction
    p1 = {'gains': 0, 'losses': 0, 'reused': 0, 'disjunction': 0}
    for r in runs.values():
        for case_id, case in r['v2'].items():
            before = position(case['eval_details']['final_resolution']) == 1
            resolution = r['v3'][case_id]['eval_details']['final_resolution']
            after = position(resolution) == 1
            if after and not before:
                p1['gains'] += 1
                option = list(resolution['matched_ddx'])[0]
                p1['disjunction'] += bool(re.search(r'/|\bor\b', option, re.I))
                p1['reused'] += any(o['position'] == 1 and o['grade'] == 2 and o.get('grade_reused')
                                    for t in r['v3'][case_id]['eval_details']['graded_trace'] for o in t['options'])
            p1['losses'] += before and not after
    result['p1'] = p1
    result['consistency'] = {v: {'repeated': sum(1 for s in seen[v].values()), 'differ': sum(1 for s in seen[v].values() if len(s) > 1)}
                             for v in ('v2', 'v3')}
    result['moves'] = {f'{a}{b}': n for (a, b), n in moves.items()}
    case_id, mid = GRADED_V3_EXAMPLE
    if mid in runs and case_id in runs[mid]['v2']:
        result['example'] = {v: [(o['name'], o['grade']) for t in runs[mid][v][case_id]['eval_details']['graded_trace'] for o in t['options']
                                 if o['position'] == 1][0] for v in ('v2', 'v3')}
    cost = {'v3': 0.0, 'calls': 0, 'reused': 0}
    for r in runs.values():
        with open(os.path.join(r['v3Run'], 'summary.json'), 'r', encoding='utf-8') as f:
            judge = json.load(f)['judge']
        cost['v3'] += judge['estimated_cost_usd'] or 0
        cost['calls'] += judge['calls']
        cost['reused'] += judge.get('reused_grades', 0)
    result['cost'] = cost
    return result


def hpo_sermas():
    """Sol and Terra with the sermas prompt against juanjo_classic_v2 on the same HPO v2 cases, Flash judge on both."""
    prompts = ('juanjo_classic_v2', SERMAS_PROMPT)
    pos = {(m, p): {} for m in HPO_FOLDERS for p in prompts}
    labels, lists = [], {m: {'lengths': [], 'times': [], 'cost': 0.0} for m in HPO_FOLDERS}
    for key, label, _ in HPO:
        if key not in SERMAS_HPO:
            continue
        root = os.path.join(OUTPUT_ROOT, f'{key}_v2')
        runs = {(m, p): finished_run(os.path.join(root, p, f + FLASH_TAG)) for m, f in HPO_FOLDERS.items() for p in prompts}
        if not all(runs.values()):
            continue
        details = {k: load_details(os.path.join(r, 'evaluation_details.txt')) for k, r in runs.items()}
        ids = sorted(set.intersection(*(set(d) for d in details.values())))
        for k in runs:
            pos[k].update({f'{key}:{i}': strict_position(details[k][i], False) for i in ids})
        labels.append(label)
        for m, f in HPO_FOLDERS.items():
            path = os.path.join(root, SERMAS_PROMPT, f + FLASH_TAG)
            labeled = load_labeled(path)
            lists[m]['lengths'] += [len(c.get('ddx_details', {})) for c in labeled]
            lists[m]['times'] += [c['emulator_time_seconds'] for c in labeled if c.get('emulator_time_seconds')]
            lists[m]['cost'] += (generation_cost(path, HPO_MODEL_IDS[m]) or 0) * len(labeled)
    keys = list(pos[('sol', SERMAS_PROMPT)])
    if not keys:
        return None
    return {
        'datasets': labels, 'n': len(keys),
        'prompt': {m: {'classic': metrics([pos[(m, prompts[0])][k] for k in keys]), 'sermas': metrics([pos[(m, prompts[1])][k] for k in keys]),
                       'r1': paired(pos[(m, prompts[1])], pos[(m, prompts[0])], keys, 1),
                       'r5': paired(pos[(m, prompts[1])], pos[(m, prompts[0])], keys, 5)} for m in HPO_FOLDERS},
        'solTerra': {p: {'r1': paired(pos[('sol', p)], pos[('terra', p)], keys, 1), 'r5': paired(pos[('sol', p)], pos[('terra', p)], keys, 5)}
                     for p in prompts},
        'lists': {m: {'options': statistics.median(v['lengths']), 'under5': round(100 * sum(1 for n in v['lengths'] if n < 5) / len(v['lengths'])),
                      'latency': round(statistics.median(v['times']), 1), 'cost': v['cost'] / len(v['lengths'])} for m, v in lists.items()},
    }


def count_example(details, judge, counts):
    """Grade 2 out of all grades the judge gave to «type 5» and «type 5D» options for the example gold."""
    for case_id, case in details.items():
        for trace in case['eval_details'].get('graded_trace', []):
            if trace['gdx'] != JUDGE_EXAMPLE[1]:
                continue
            counts['cases'].add(case_id)
            for option in trace['options']:
                name = option['name'].lower()
                kind = 'da5d' if re.search(r'type 5d|\b5d\b', name) else 'da5' if re.search(r'type 5\b|\bda5\b', name) else None
                if kind and option['grade'] is not None:
                    counts[(judge, kind)][0] += option['grade'] == 2
                    counts[(judge, kind)][1] += 1


def sol_row(label, keys, every, limit, lengths, ids):
    row = {'label': label, 'n': len(keys),
           **{m: metrics([every[m][k] for k in keys]) for m in every},
           'r1': paired(every['sol'], every['terra'], keys, 1), 'r5': paired(every['sol'], every['terra'], keys, 5),
           'length': paired(every['sol'], every['terra'], keys, limit),
           'lengthHit': {m: round(100 * sum(1 for k in keys if every[m][k] is not None and every[m][k] <= limit[k]) / len(keys), 1)
                         for m in HPO_FOLDERS}}
    if lengths:
        row['options'] = {m: statistics.median(lengths[m][i] for i in ids) for m in HPO_FOLDERS}
    return row


def collect():
    with open(NARRATIVE_V2, 'r', encoding='utf-8') as f:
        dataset = {c['id']: c for c in json.load(f)}
    with open(os.path.join(NARRATIVE_TOOLS, 'work', 'live_dates.json'), 'r', encoding='utf-8') as f:
        live_dates = json.load(f)
    with open(os.path.join(NARRATIVE_TOOLS, 'model_cutoffs.yaml'), 'r', encoding='utf-8') as f:
        cutoffs = yaml.safe_load(f)['models']

    data = {'models': [], 'mcnemar': {}, 'cutoffs': [], 'liveMonths': {}, 'hpo': [], 'geneExamples': []}
    positions = {}
    for mid, folder, model, label, color in MODELS:
        run = latest_run(os.path.join(NARRATIVE_DIR, folder))
        details = load_details(os.path.join(run, 'evaluation_details.txt'))
        with open(os.path.join(run, 'summary.json'), 'r', encoding='utf-8') as f:
            summary = json.load(f)
        with open(glob.glob(os.path.join(NARRATIVE_DIR, folder, '*___ddxs_from_labeler.json'))[0], 'r', encoding='utf-8') as f:
            labeled = json.load(f)
        strict = {k: position(v['eval_details']['final_resolution']) for k, v in details.items()}
        lax = {k: position(v['eval_details']['lax_resolution']) for k, v in details.items()}
        positions[mid] = strict
        groups = {}
        for key, _, belongs in GROUPS:
            ids = [i for i, c in dataset.items() if belongs(c)]
            groups[key] = metrics([strict[i] for i in ids], [lax[i] for i in ids])
        unseen = [i for i, row in live_dates.items() if model not in row['maybe_seen_by']]
        groups['liveUnseen'] = metrics([strict[i] for i in unseen], [lax[i] for i in unseen])
        times = [c['emulator_time_seconds'] for c in labeled if c.get('emulator_time_seconds')]
        data['models'].append({
            'id': mid, 'name': label, 'model': model, 'color': color, 'run': os.path.basename(run),
            'latency': round(statistics.median(times), 1), 'genCost': generation_cost(folder, model),
            'options': statistics.median(len(c.get('ddx_details', {})) for c in labeled),
            'judgeCalls': summary['judge']['calls'], 'judgeCost': summary['judge']['estimated_cost_usd'],
            'judgeErrors': len(summary['global']['cases_with_judge_errors']),
            'cutoff': str(cutoffs.get(model, {}).get('cutoff', '')), 'groups': groups,
        })

    for subset in ('realRare', 'realCommon', 'realcases', 'total'):
        belongs = dict((k, f) for k, _, f in GROUPS)[subset]
        ids = [i for i, c in dataset.items() if belongs(c)]
        for k in (1, 5):
            rows = [{'id': mid, **paired(positions[mid], positions[BASELINE], ids, k)} for mid, *_ in MODELS if mid != BASELINE]
            data['mcnemar'][f'{subset}_r{k}'] = {'n': len(ids), 'rows': rows}

    split_ids = {key: [i for i, c in dataset.items() if belongs(c)] for key, _, belongs in REAL_SPLIT}
    by_id = {m['id']: m for m in data['models']}
    data['effort'] = []
    for mid, folder in EFFORT:
        if not latest_run(os.path.join(NARRATIVE_DIR, folder)):
            continue
        low = by_id[mid]
        medium, run, labeled = narrative_run(folder)
        times = [c['emulator_time_seconds'] for c in labeled if c.get('emulator_time_seconds')]
        data['effort'].append({
            'id': mid, 'name': low['model'], 'color': low['color'], 'run': run,
            'low': {'latency': low['latency'], 'genCost': low['genCost'], 'options': low['options']},
            'medium': {'latency': round(statistics.median(times), 1), 'genCost': generation_cost(folder, low['model']),
                       'options': statistics.median(len(c.get('ddx_details', {})) for c in labeled)},
            'groups': {key: {'n': len(ids), 'low': metrics([positions[mid][i] for i in ids]),
                             'medium': metrics([medium[i] for i in ids]),
                             'r1': paired(medium, positions[mid], ids, 1), 'r5': paired(medium, positions[mid], ids, 5)}
                       for key, ids in split_ids.items()},
        })

    # Exactly 5 diagnoses against «N»: same model, cases and judge, only the prompt changes
    data['n5'] = []
    for mid, folder in N5:
        path = os.path.join(OUTPUT_ROOT, 'narrative_v2', N5_PROMPT, folder)
        run = finished_run(path)
        if not run:
            continue
        details = load_details(os.path.join(run, 'evaluation_details.txt'))
        five = {i: strict_position(c, False) for i, c in details.items()}
        labeled = load_labeled(path)
        lengths = [len(c.get('ddx_details', {})) for c in labeled]
        base = by_id[mid]
        data['n5'].append({
            'name': base['model'], 'color': base['color'],
            'n': {'options': base['options'], 'latency': base['latency'], 'cost': base['genCost'],
                  'under5': round(100 * sum(1 for c in narrative_run(folder)[2] if len(c.get('ddx_details', {})) < 5) / 300)},
            'five': {'options': statistics.median(lengths), 'cost': generation_cost(path, base['model']),
                     'latency': round(statistics.median(c['emulator_time_seconds'] for c in labeled if c.get('emulator_time_seconds')), 1),
                     'under5': round(100 * sum(1 for n in lengths if n < 5) / len(lengths))},
            'groups': {key: {'n': len(ids), 'base': metrics([positions[mid][i] for i in ids]), 'five': metrics([five[i] for i in ids]),
                             'r1': paired(five, positions[mid], ids, 1), 'r5': paired(five, positions[mid], ids, 5)}
                       for key, ids in split_ids.items()},
        })

    # Same model run twice: how many cases flip by chance, and whether the Sol gap holds in every pairing of runs
    data['rerun'] = None
    runs = {}
    for mid, folder in RERUNS:
        if finished_run(os.path.join(NARRATIVE_DIR, folder)):
            runs[mid] = [positions[mid], narrative_run(folder)[0]]
    if runs:
        data['rerun'] = {'models': [{'id': mid, 'name': by_id[mid]['model'], 'groups': {key: {
            'n': len(ids), 'first': metrics([first[i] for i in ids]), 'second': metrics([second[i] for i in ids]),
            'change': paired(second, first, ids, 1), 'change5': paired(second, first, ids, 5),
        } for key, ids in split_ids.items()}} for mid, (first, second) in runs.items()], 'cross': []}
        sol_runs = runs.get('sol61', [positions['sol61']])
        terra_runs = runs.get(BASELINE, [positions[BASELINE]])
        if len(sol_runs) == len(terra_runs) == 2:
            data['rerun']['pooled'] = {key: pooled_sign_test(sol_runs, terra_runs, ids) for key, ids in split_ids.items()}
        for si, sol in enumerate(sol_runs, 1):
            for ti, terra in enumerate(terra_runs, 1):
                data['rerun']['cross'].append({'sol': si, 'terra': ti, 'groups': {
                    key: {'sol': metrics([sol[i] for i in ids])['r1'], 'terra': metrics([terra[i] for i in ids])['r1'],
                          'test': paired(sol, terra, ids, 1)} for key, ids in split_ids.items()}})

    # Agentic PoC: each arm against the model whose list it revised. R@5 can rise
    # only because an arm returns more options, so the length control counts a
    # hit only within the number of options the base gave in that case.
    real = split_ids['realcases']
    folders = {mid: folder for mid, folder, *_ in MODELS}
    base_length = {mid: {c['id']: min(5, len(c.get('ddx_details', {}))) for c in narrative_run(folders[mid])[2]}
                   for mid in dict.fromkeys(a[0] for a in POC_ARMS)}
    data['poc'] = {'bases': {}, 'arms': []}
    for mid in base_length:
        m = by_id[mid]
        data['poc']['bases'][mid] = {
            'name': m['model'], 'color': m['color'], 'cost': m['genCost'], 'latency': m['latency'], 'options': m['options'],
            'groups': {key: metrics([positions[mid][i] for i in ids]) for key, ids in split_ids.items()},
            'lengthHit': round(100 * sum(1 for i in real if positions[mid][i] is not None and positions[mid][i] <= base_length[mid][i]) / len(real), 1),
        }
    for base, arm, label, members in POC_ARMS:
        folder = f'{folders[base]}__{arm}'
        traces_path = os.path.join(POC_WORK, f'{arm}_traces.json')
        if not latest_run(os.path.join(NARRATIVE_DIR, folder)):
            continue
        arm_positions, run, labeled = narrative_run(folder)
        row = {
            'base': base, 'arm': arm, 'label': label, 'run': run,
            'options': statistics.median(len(c.get('ddx_details', {})) for c in labeled),
            'groups': {key: metrics([arm_positions[i] for i in ids]) for key, ids in split_ids.items()},
            'vsBase': {f'r{k}': paired(arm_positions, positions[base], real, k) for k in (1, 5)},
            'vsBaseRare': paired(arm_positions, positions[base], split_ids['realRare'], 1),
            'vsBaseCommon': paired(arm_positions, positions[base], split_ids['realCommon'], 1),
            'vsSol': paired(arm_positions, positions['sol61'], real, 1),
            'length': paired(arm_positions, positions[base], real, base_length[base]),
            'lengthHit': round(100 * sum(1 for i in real if arm_positions[i] is not None and arm_positions[i] <= base_length[base][i]) / len(real), 1),
            'stageCost': None, 'cost': None, 'latency': None,
        }
        if os.path.exists(traces_path):
            with open(traces_path, 'r', encoding='utf-8') as f:
                traces = json.load(f)
            totals, n = traces['totals'], len(traces['cases'])
            row['stageCost'] = totals['cost_usd'] / n
            row['stageCalls'] = totals['calls'] / n
            row['stageP50'] = totals['p50_seconds']
            member_costs = [by_id[m]['genCost'] for m in members]
            if all(c is not None for c in member_costs):
                row['cost'] = sum(member_costs) + row['stageCost']
            # Members answer in parallel; the second-stage calls go one after another
            row['latency'] = round(max(by_id[m]['latency'] for m in members) + row['stageCalls'] * totals['p50_seconds'], 1)
        data['poc']['arms'].append(row)

    for model, info in cutoffs.items():
        maybe_seen = sum(1 for row in live_dates.values() if model in row['maybe_seen_by'])
        data['cutoffs'].append({'model': model, 'cutoff': str(info['cutoff']), 'released': str(info.get('released', '')),
                                'source': info['source'], 'url': info['url'], 'live': len(live_dates),
                                'unseenEntrez': len(live_dates), 'unseenPublic': len(live_dates) - maybe_seen})
    data['liveMonths'] = {
        'firstPublic': collections.Counter(r['first_public_date'][:7] for r in live_dates.values()),
        'entrez': collections.Counter(r['entrez_date'][:7] for r in live_dates.values()),
    }

    totals = collections.defaultdict(list)
    for key, label, v4_folder in HPO:
        v4 = load_details(os.path.join(JUDGE_AUDIT, v4_folder, 'evaluation_details.txt'))
        run = latest_run(os.path.join(OUTPUT_ROOT, f'{key}_v2', 'juanjo_classic_v2', 'gpt_5_6_terra_low'))
        v5 = load_details(os.path.join(run, 'evaluation_details.txt'))
        with open(os.path.join(run, 'summary.json'), 'r', encoding='utf-8') as f:
            summary = json.load(f)
        with open(os.path.join(EVAL_ROOT, 'bench', 'datasets', f'{key}_v2.json'), 'r', encoding='utf-8') as f:
            cases = json.load(f)
        ids = [c['id'] for c in cases]
        clinical = {c['id'] for c in cases if any(d.get('role') == 'clinical' for d in c['diagnoses'])}
        columns = {
            'v4': [position(v4[i]['eval_details']['final_resolution']) for i in ids],
            'v5orig': [strict_position(v5[i], True) for i in ids],
            'v5v2': [strict_position(v5[i], False) for i in ids],
        }
        row = {'key': key, 'label': label, 'nOriginal': len(v4), 'n': len(ids), 'nClinical': len(clinical),
               'judgeCalls': summary['judge']['calls'], 'judgeCost': summary['judge']['estimated_cost_usd'],
               'judgeErrors': len(summary['global']['cases_with_judge_errors'])}
        for name, values in columns.items():
            row[name] = metrics(values)
            totals[name].extend(values)
        if key == 'ddd_hpo':
            inside = [i for i in ids if i in clinical]
            outside = [i for i in ids if i not in clinical]
            row['split'] = {
                'withClinical': {'n': len(inside), 'orig': metrics([strict_position(v5[i], True) for i in inside]),
                                 'v2': metrics([strict_position(v5[i], False) for i in inside])},
                'withoutClinical': {'n': len(outside), 'v2': metrics([strict_position(v5[i], False) for i in outside])},
            }
        data['hpo'].append(row)
        data['geneExamples'] += [{**hpo_example(v5[case_id]), 'note': note}
                                 for ex_key, case_id, note in GENE_EXAMPLES if ex_key == key and case_id in v5]
    data['hpoSol'] = hpo_sol()
    data['hpoSyn'] = hpo_syn()
    data['hpoOpus'] = hpo_opus()
    data['hpoSermas'] = hpo_sermas()
    judges = compare_judges.compare(JUDGE_CANDIDATES)
    if judges:
        judges['colors'] = {name: color for (_, name), (*_, color) in zip(compare_judges.MODELS, MODELS)}
    data['judges'] = judges
    data['gradedV3'] = graded_v3(dataset)

    data['hpoTotal'] = {'label': 'Total', 'nOriginal': sum(r['nOriginal'] for r in data['hpo']),
                        'n': len(totals['v4']), 'nClinical': sum(r['nClinical'] for r in data['hpo']),
                        'judgeCalls': sum(r['judgeCalls'] for r in data['hpo']),
                        'judgeCost': round(sum(r['judgeCost'] for r in data['hpo']), 2),
                        **{name: metrics(values) for name, values in totals.items()}}
    return data


def pct(value, digits=1):
    return '—' if value is None else f'{value:.{digits}f}'.replace('.', ',') + ' %'


def num(value, digits=1):
    return '—' if value is None else f'{value:.{digits}f}'.replace('.', ',')


def thousands(value):
    return f'{value:,}'.replace(',', '.')


def p_value(p):
    return '&lt; 0,001' if p < 0.001 else num(p, 3 if p < 0.01 else 2)


def p_text(p):
    return 'p &lt; 0,001' if p < 0.001 else f'p = {p_value(p)}'


def models_table(data):
    best = {key: max(m['groups']['total'][key] for m in data['models']) for key in ('r1', 'r3', 'r5')}
    rows = []
    for m in data['models']:
        g = m['groups']['total']
        cells = ''.join(f'<td>{"<strong>" if g[k] == best[k] else ""}{pct(g[k])}{"</strong>" if g[k] == best[k] else ""}</td>'
                        for k in ('r1', 'r3', 'r5'))
        rows.append(
            f'<tr{" class=\"winner\"" if m["id"] == data["models"][0]["id"] else ""}>'
            f'<td><span class="dot" style="background:{m["color"]}"></span> <strong>{m["name"]}</strong>'
            f'{" <span class=\"badge badge-muted\">línea base</span>" if m["id"] == BASELINE else ""}</td>'
            f'{cells}<td>{pct(g["cov"])}</td><td>{num(g["avgPos"], 3)}</td>'
            f'<td>{pct(m["groups"]["realcases"]["r1"])}</td><td>{pct(g["laxR5"])}</td>'
            f'<td>{num(m["options"], 0)}</td><td>{num(m["latency"])}</td><td>{num(m["judgeCost"], 2)} $</td></tr>')
    return '\n'.join(rows)


def mcnemar_table(data):
    names = {m['id']: m['name'] for m in data['models']}
    r1, r5 = data['mcnemar']['realcases_r1']['rows'], data['mcnemar']['realcases_r5']['rows']
    rows = []
    for a, b in zip(r1, r5):
        rows.append(f'<tr><td>{names[a["id"]]}</td>'
                    f'<td>{a["wins"]} / {a["losses"]}</td><td>{num(a["net"])} pp</td><td>{p_value(a["p"])}</td>'
                    f'<td>{b["wins"]} / {b["losses"]}</td><td>{num(b["net"])} pp</td><td>{p_value(b["p"])}</td></tr>')
    return '\n'.join(rows)


def cutoffs_table(data):
    rows = []
    for c in sorted(data['cutoffs'], key=lambda c: c['cutoff']):
        rows.append(f'<tr><td>{c["model"]}</td><td>{c["cutoff"]}</td><td>{c["released"]}</td>'
                    f'<td>{c["unseenEntrez"]} de {c["live"]}</td><td>{c["unseenPublic"]} de {c["live"]}</td>'
                    f'<td><a href="{html.escape(c["url"])}">{html.escape(c["source"])}</a></td></tr>')
    return '\n'.join(rows)


def hpo_table(data):
    rows = []
    for r in data['hpo'] + [data['hpoTotal']]:
        total = r is data['hpoTotal']
        open_, close = ('<strong>', '</strong>') if total else ('', '')
        rows.append(
            f'<tr{" class=\"winner\"" if total else ""}><td>{open_}{r["label"]}{close}</td>'
            f'<td>{thousands(r["n"])}</td><td>{thousands(r["nClinical"])}</td>'
            f'<td>{pct(r["v4"]["r1"])}</td><td>{pct(r["v5orig"]["r1"])}</td><td>{open_}{pct(r["v5v2"]["r1"])}{close}</td>'
            f'<td>{pct(r["v4"]["r5"])}</td><td>{pct(r["v5orig"]["r5"])}</td><td>{open_}{pct(r["v5v2"]["r5"])}{close}</td></tr>')
    return '\n'.join(rows)


def judges_section(data):
    j = data.get('judges')
    if not j:
        return ''
    names = {'gemini-2.5-pro': 'Gemini 2.5 Pro (actual)', 'gemini-3.8-flash': 'Gemini 3.8 Flash', 'gemini-2.5-flash': 'Gemini 2.5 Flash',
             'claude-opus-5-5': 'Claude Opus 5.5'}
    taus = j['tau']['realcases_r1']
    same_order = all(v == 1 for v in taus.values())
    agreement_rows = '\n'.join(
        f'<tr><td>{html.escape(a["judge"])}</td><td>{html.escape(a["scope"])}</td><td>{pct(a["sameP1"])}</td><td>{pct(a["same2"])}</td>'
        f'<td>{num(a["kappa2"], 2)}</td><td>{pct(a["sameGrade"])}</td><td>{num(a["kappa"], 2)}</td></tr>' for a in j['agreement'])
    cost_rows = '\n'.join(
        f'<tr><td>{names.get(c["judge"], c["judge"])}</td><td>{c["calls"]}</td><td>{num(c["cost"], 2)} $</td><td>{num(c["p50"])} s</td><td>{c["errors"]}</td></tr>'
        for c in j['cost'])
    flash = next(a for a in j['agreement'] if a['judge'] == 'gemini-3.8-flash')
    rerun = next((a for a in j['agreement'] if 'repetido' in a['judge']), None)
    cost = {c['judge']: c for c in j['cost']}
    claude = next((a for a in j['agreement'] if a['judge'] == 'claude-opus-5-5'), None)
    claude_text = (f' <strong>Un juez de otra familia, Claude Opus 5.5, tampoco cambia el orden</strong> y coincide con Pro en «¿es un 2?» en el '
                   f'{pct(claude["same2"])} de las opciones, igual que Flash: la conclusión no depende de usar un juez de Google. '
                   f'No favorece a Claude Opus 5, que con él saca un punto menos que con Pro.' if claude else '')
    return f'''
  <div class="section">
    <div class="section-title">Prueba de jueces · mismas listas, {len(j['judges'])} jueces</div>
    <div class="callout callout-info">
      Paso 6 del ROADMAP: si el orden de los modelos no cambia con un juez más barato, se puede usar el barato. Se han vuelto a
      puntuar las listas de los seis modelos con Gemini 3.8 Flash y Gemini 2.5 Flash, sin generar listas nuevas. Para saber cuánto
      varía el propio juez actual, Gemini 2.5 Pro se ha repetido sobre las listas de Terra 5.6.
      <strong>{"El orden de los modelos en casos reales no cambia con ningún juez." if same_order else "El orden de los modelos cambia con algún juez."}</strong>
      Gemini 3.8 Flash coincide con Pro en «¿es un 2 o no?» en el {pct(flash['same2'])} de las opciones{f", casi lo mismo que Pro consigo mismo ({pct(rerun['same2'])})" if rerun else ""},
      y cuesta {num(cost['gemini-2.5-pro']['cost'] / max(cost['gemini-3.8-flash']['cost'], 0.01), 0)} veces menos. Falta lo decisivo: cuál de los dos se
      parece más al criterio de David (<a href="tareas-david/02-escala-del-juez.md">tarea 2</a>).{claude_text}
    </div>
    <div class="viz-panel">
      <div class="viz-panel-title"><span>Acierto en casos reales según el juez</span>
        <div class="viz-tabs" id="judge-tabs">
          <button type="button" class="viz-tab active" data-k="r1">R@1</button>
          <button type="button" class="viz-tab" data-k="r5">R@5</button>
        </div>
      </div>
      <div class="viz-panel-sub">Cada fila es un modelo; cada marca, la nota estricta que le da un juez sobre las mismas listas
        (<code>live</code>+<code>urg</code>, 210 casos). Si las marcas de una fila están juntas, el juez no cambia la conclusión.</div>
      <div class="svg-wrap"><svg id="judge-svg" class="svg-chart" viewBox="0 0 680 320" role="img" aria-label="Acierto de cada modelo según el juez"></svg></div>
      <div class="viz-legend">
        <span class="viz-legend-item"><svg width="12" height="12"><circle cx="6" cy="6" r="5" fill="#1e293b"/></svg>Gemini 2.5 Pro (actual)</span>
        <span class="viz-legend-item"><svg width="12" height="12"><rect x="1.5" y="1.5" width="9" height="9" transform="rotate(45 6 6)" fill="#fff" stroke="#1e293b" stroke-width="2"/></svg>Gemini 3.8 Flash</span>
        <span class="viz-legend-item"><svg width="12" height="12"><rect x="2" y="2" width="8" height="8" fill="#94a3b8"/></svg>Gemini 2.5 Flash</span>
        <span class="viz-legend-item"><svg width="12" height="12"><path d="M6 1 L11 10 L1 10 Z" fill="#eb6834"/></svg>Claude Opus 5.5</span>
      </div>
    </div>
    <h3>Coincidencia con Gemini 2.5 Pro</h3>
    <div class="table-scroll">
    <table class="num">
      <thead><tr><th>Juez</th><th>Sobre</th><th>Mismo acierto en P1 (por caso)</th><th>Mismo «2 o no» (por opción)</th><th>Kappa «2 o no»</th>
        <th>Misma nota 2/1/0</th><th>Kappa 2/1/0</th></tr></thead>
      <tbody>
{agreement_rows}
      </tbody>
    </table>
    </div>
    <p class="note">La nota estricta solo usa la frontera «2 o no». Las diferencias de Flash están sobre todo entre 1 y 0, que solo afecta a la
      nota laxa. Gemini 3.8 Flash da algo más de aciertos estrictos que Pro (1–4 puntos según el modelo): no se pueden mezclar cifras de
      jueces distintos; si se cambia de juez, se re-puntúa todo.</p>
    <h3>Coste y latencia del juez (seis modelos, 300 casos cada uno)</h3>
    <div class="table-scroll">
    <table class="num">
      <thead><tr><th>Juez</th><th>Llamadas</th><th>Coste estimado</th><th>Mediana por llamada</th><th>Casos con error</th></tr></thead>
      <tbody>
{cost_rows}
      </tbody>
    </table>
    </div>
    <p class="note">Precios de Google: Gemini 3.8 Flash 0,75 $ / 3,75 $ por millón de tokens hasta el 31-dic-2026 (el doble después).
      Gemini 2.5 Flash razona sin límite por defecto y gasta más tokens que 3.8 Flash. Claude Opus 5.5 con esfuerzo <code>low</code>,
      4 $ / 20 $ por millón de tokens.</p>
  </div>
'''


def cents(usd):
    return '—' if usd is None else num(usd * 100, 2) + ' c$'


def rerun_section(data):
    r = data.get('rerun')
    if not r:
        return ''
    models = r['models']
    head = ''.join(f'<th>{m["name"]} 1.ª</th><th>2.ª</th><th>Cambian (gana / pierde)</th><th>p</th>' for m in models)
    rows = []
    for key, label, _ in REAL_SPLIT:
        cells = ''.join(f'<td>{pct(g["first"]["r1"])}</td><td>{pct(g["second"]["r1"])}</td>'
                        f'<td>{g["change"]["wins"]} / {g["change"]["losses"]}</td><td>{p_value(g["change"]["p"])}</td>'
                        for g in (m['groups'][key] for m in models))
        rows.append(f'<tr><td>{label}</td><td>{models[0]["groups"][key]["n"]}</td>{cells}</tr>')
    cross_rows = '\n'.join(
        f'<tr><td>Sol {c["sol"]}.ª frente a Terra {c["terra"]}.ª</td>' + ''.join(
            f'<td>{pct(c["groups"][key]["sol"])} / {pct(c["groups"][key]["terra"])}</td>'
            f'<td>{c["groups"][key]["test"]["wins"]} / {c["groups"][key]["test"]["losses"]}</td><td>{p_value(c["groups"][key]["test"]["p"])}</td>'
            for key in ('realcases', 'realRare', 'realCommon')) + '</tr>' for c in r['cross'])
    flips = {m['name']: m['groups']['realcases']['change']['wins'] + m['groups']['realcases']['change']['losses'] for m in models}
    n = models[0]['groups']['realcases']['n']
    moves = [abs(m['groups']['realcases']['second']['r1'] - m['groups']['realcases']['first']['r1']) for m in models]
    rare_move = max(models, key=lambda m: abs(m['groups']['realRare']['second']['r1'] - m['groups']['realRare']['first']['r1']))
    real_p = [c['groups']['realcases']['test']['p'] for c in r['cross']]
    rare_p = [c['groups']['realRare']['test']['p'] for c in r['cross']]
    holds = all(p < 0.05 for p in real_p)
    names = ' y '.join(m['name'] for m in models)
    pooled = r.get('pooled')
    pooled_text = ''
    if pooled:
        cross_rows += '\n<tr class="winner"><td><strong>Las dos ejecuciones de cada modelo</strong></td>' + ''.join(
            f'<td>{pct(pooled[key]["a"])} / {pct(pooled[key]["b"])}</td><td>{pooled[key]["wins"]} / {pooled[key]["losses"]}</td>'
            f'<td>{p_value(pooled[key]["p"])}</td>' for key in ('realcases', 'realRare', 'realCommon')) + '</tr>'
        rare, real, common = pooled['realRare'], pooled['realcases'], pooled['realCommon']
        pooled_text = (f' <strong>Juntando las dos ejecuciones de cada modelo</strong>, Sol supera a Terra en raras reales '
                       f'({pct(rare["a"])} frente a {pct(rare["b"])}, {p_text(rare["p"])}) y en el conjunto de casos reales '
                       f'({pct(real["a"])} frente a {pct(real["b"])}, {p_text(real["p"])}); en no raras empatan '
                       f'({pct(common["a"])} frente a {pct(common["b"])}). La ventaja en raras es de unos '
                       f'{num(rare["a"] - rare["b"])} puntos, no los {num(models[-1]["groups"]["realRare"]["first"]["r1"] - models[0]["groups"]["realRare"]["first"]["r1"])} '
                       f'de la 1.ª ejecución: con 210 casos, una sola ejecución no basta para decidir entre dos modelos cercanos.')
    return f'''
  <div class="section">
    <div class="section-title">Variabilidad entre ejecuciones · {names}, dos veces cada uno</div>
    <div class="callout callout-info">
      Si se repite exactamente la misma ejecución (mismo modelo, prompt, casos y juez), las respuestas no salen idénticas. Para saber
      cuánto pesa eso, {names} low se han ejecutado una segunda vez sobre los 300 casos: generan, traducen, etiquetan y el juez puntúa de nuevo.
      En casos reales cambian {" y ".join(f"{v} ({k})" for k, v in flips.items())} de {n} casos (acierto en una ejecución y fallo en la
      otra), en las dos direcciones, así que la cifra de casos reales se mueve como mucho {num(max(moves))} puntos. En grupos más pequeños
      se mueve más: {rare_move["name"]} pasa de {pct(rare_move["groups"]["realRare"]["first"]["r1"])} a
      {pct(rare_move["groups"]["realRare"]["second"]["r1"])} en raras reales (116 casos).
      <strong>{"La ventaja de Sol sobre Terra se mantiene en todas las combinaciones de ejecuciones" if holds else "La ventaja de Sol sobre Terra no se mantiene en todas las combinaciones de ejecuciones"}</strong>
      (casos reales, p entre {p_value(min(real_p))} y {p_value(max(real_p))}; raras reales, entre {p_value(min(rare_p))} y {p_value(max(rare_p))}).{pooled_text}
    </div>
    <div class="table-scroll">
    <table class="num">
      <thead><tr><th>Grupo</th><th>Casos</th>{head}</tr></thead>
      <tbody>
{chr(10).join(rows)}
      </tbody>
    </table>
    </div>
    <h3>Sol frente a Terra con cada pareja de ejecuciones (R@1)</h3>
    <div class="table-scroll">
    <table class="num">
      <thead><tr><th>Ejecuciones</th><th>Casos reales: Sol / Terra</th><th>Gana / pierde</th><th>p</th>
        <th>Raras reales</th><th>Gana / pierde</th><th>p</th><th>No raras reales</th><th>Gana / pierde</th><th>p</th></tr></thead>
      <tbody>
{cross_rows}
      </tbody>
    </table>
    </div>
    <p class="note">Cambian: casos que acierta la 2.ª ejecución y no la 1.ª, y al revés. Una diferencia entre dos modelos solo dice algo si
      supera lo que varía un modelo consigo mismo. «Las dos ejecuciones»: en cada caso, aciertos de Sol (0, 1 o 2) menos aciertos de Terra;
      gana y pierde cuentan los casos en que esa resta es positiva o negativa, con una prueba de signos exacta. Las cifras del resto del
      informe son las de la 1.ª ejecución. El juez también varía: con las mismas listas de Terra, una segunda llamada a Gemini 2.5 Pro
      cambia el 5,7 % de las notas y el acierto en P1 en 8 de 300 casos (R@1 61,3 % frente a 60,0 %).</p>
  </div>
'''


def grade_text(grade, position):
    if grade == 2:
        return f'<strong>acierto</strong> (nota 2, P{position})'
    if grade == 1:
        return 'no cuenta (nota 1, relacionada)'
    if grade == 0:
        return 'no cuenta (nota 0, otra enfermedad)'
    return '—'


def gene_explainer(data):
    examples = data.get('geneExamples')
    if not examples:
        return ''
    rows = '\n'.join(
        f'<tr><td>{html.escape(e["gold"])}</td><td>{html.escape(e["clinical"]) if e["clinical"] else "<em>ninguno</em>"}</td>'
        f'<td>«{html.escape(e["answer"])}» (P{e["position"]})</td><td>{grade_text(e["gradeGold"], e["position"])}</td>'
        f'<td>{grade_text(e["gradeClinical"], e["position"]) if e["clinical"] else grade_text(e["gradeGold"], e["position"])}</td>'
        f'<td>{html.escape(e["note"])}</td></tr>' for e in examples)
    return f'''
    <h3>Qué quiere decir «con gen» y «sin gen»</h3>
    <div class="explain">
      <div class="card"><div class="card-label">El mismo cuadro, varios genes</div>
        <p>Muchas enfermedades raras se deben a uno de varios genes posibles. El síndrome de Noonan lo causan más de diez genes distintos y
           la anemia de Fanconi más de veinte. Los síntomas son prácticamente los mismos; cuál es el gen solo lo dice un estudio genético.</p></div>
      <div class="card"><div class="card-label">El dataset pone el gen</div>
        <p>En DDD y LIRICAL el diagnóstico de referencia (el gold) es la enfermedad con su gen: «SOS1-related Noonan syndrome», síndrome
           de Noonan por SOS1. Es el diagnóstico final, el que se tiene después del estudio genético.</p></div>
      <div class="card"><div class="card-label">El modelo solo ve síntomas</div>
        <p>DxGPT recibe la lista de síntomas del paciente (términos HPO), sin ningún resultado genético. Con eso, lo que diría un buen
           clínico es «síndrome de Noonan», y después pediría el panel de genes para saber cuál.</p></div>
    </div>
    <p style="margin-top:14px">Si solo vale el gold <strong>con gen</strong>, responder «Noonan syndrome» es una enfermedad relacionada (nota 1)
      y no cuenta como acierto, aunque es justo lo que se puede saber sin estudio genético. Por eso a cada gold con gen se le ha añadido,
      cuando tiene sentido, su nombre <strong>sin gen</strong> («Noonan syndrome»), y la cifra «con gen o sin gen» acepta cualquiera de los
      dos. Si el modelo nombra el gen y acierta, cuenta en las dos. Ejemplos reales del dataset DDD, con la respuesta de Terra 5.6:</p>
    <div class="table-scroll">
    <table>
      <thead><tr><th>Gold del dataset</th><th>Nombre sin gen añadido</th><th>Respuesta de Terra</th><th>Solo gold con gen</th>
        <th>Gold con gen o sin gen</th><th>Por qué</th></tr></thead>
      <tbody>
{rows}
      </tbody>
    </table>
    </div>
    <p class="note">Si al quitar el gen solo queda un rasgo («CHD8-related autism» → «autism»), no se añade nombre sin gen: describe al
      paciente pero no dice qué enfermedad tiene, y esos casos no se pueden resolver sin estudio genético. Los nombres sin gen los propuso
      Gemini 2.5 Pro y están pendientes de revisión clínica (<a href="tareas-david/README.md">tarea 3 de David</a>). La posición (P1, P2…)
      es el lugar de la respuesta en la lista del modelo.</p>
'''


def hpo_sol_section(data):
    s = data.get('hpoSol')
    if not s or not s['rows']:
        return ''
    labels = {'terra': 'Terra 5.6', 'sol': 'gpt-6.1-sol'}

    def row(r, total=False):
        o, c = ('<strong>', '</strong>') if total else ('', '')
        return (f'<tr{" class=\"winner\"" if total else ""}><td>{o}{r["label"]}{c}</td><td>{thousands(r["n"])}</td>'
                f'<td>{pct(r["terra"]["r1"])}</td><td>{o}{pct(r["sol"]["r1"])}{c}</td><td>{r["r1"]["wins"]} / {r["r1"]["losses"]}</td><td>{p_value(r["r1"]["p"])}</td>'
                f'<td>{pct(r["terraGene"]["r1"])}</td><td>{pct(r["solGene"]["r1"])}</td>'
                f'<td>{pct(r["terra"]["r5"])}</td><td>{o}{pct(r["sol"]["r5"])}{c}</td><td>{p_value(r["r5"]["p"])}</td>'
                f'<td>{pct(r["lengthHit"]["terra"])}</td><td>{pct(r["lengthHit"]["sol"])}</td><td>{p_value(r["length"]["p"])}</td></tr>')

    t = s['total']
    done = len(s['rows'])
    pending = (f' Faltan {", ".join(s["pending"])}: la tabla se completa al volver a generar el informe.' if s['pending'] else '')
    progress = f'{done} de {len(HPO)} datasets terminados' if s['pending'] else f'Los {done} datasets'
    even = [r for r in s['rows'] if r['r1']['p'] >= 0.05]
    flash, example = s.get('flash'), s.get('example')
    flash_text = (f'<p><strong>Con Gemini 3.8 Flash de juez la ventaja de Sol se mantiene:</strong> R@1 {pct(flash["terra"]["r1"])} con Terra y '
                  f'{pct(flash["sol"]["r1"])} con Sol ({flash["r1"]["wins"]} / {flash["r1"]["losses"]}, {p_text(flash["r1"]["p"])}) '
                  f'sobre {thousands(flash["n"])} casos.</p>' if flash else '')
    if example:
        g = example['grades']
        share = lambda k: f'{g[k][0]} de {g[k][1]}'
        flash_text += f'''
    <div class="callout callout-warn">
      <strong>Dónde se separan los jueces: un sinónimo que Pro no reconoce.</strong> En MyGene2, {example["cases"]} casos tienen como gold
      «{html.escape(JUDGE_EXAMPLE[1])}» (OMIM 108145), que es la misma enfermedad que «distal arthrogryposis type 5» (DA5, gen PIEZO2;
      sinónimo en MONDO). «Distal arthrogryposis type 5D» es otra enfermedad (gen ECEL1, OMIM 615065). Pro lo hace al revés: da un 2
      a «type 5» en {share("pro_da5")} veces y a «type 5D» en {share("pro_da5d")}. Flash da un 2 a «type 5» en {share("flash_da5")} y a
      «type 5D» en {share("flash_da5d")}. Sobre todo por este gold, R@1 de Sol en MyGene2 es {pct(example["solR1"]["pro"])} con Pro y
      {pct(example["solR1"]["flash"])} con Flash. Ninguno de los dos jueces ve los códigos OMIM: pasarle al juez los sinónimos del gold
      (MONDO u Orphanet) evitaría el problema con cualquiera de los dos.
    </div>
'''
    judge_rows = '\n'.join(
        f'<tr><td>{labels[j["model"]]}</td><td>{thousands(j["cases"])}</td><td>{pct(j["sameP1"])}</td><td>{pct(j["same2"])}</td>'
        f'<td>{num(j["kappa2"], 2)}</td><td>{pct(j["sameGrade"])}</td><td>{pct(j["proR1"])}</td><td>{pct(j["flashR1"])}</td></tr>'
        for j in s['judges'])
    judges = f'''
    <h3>Juez más barato en raras: Gemini 3.8 Flash frente a Gemini 2.5 Pro</h3>
    <div class="table-scroll">
    <table class="num">
      <thead><tr><th>Listas de</th><th>Casos</th><th>Mismo acierto en P1 (por caso)</th><th>Mismo «2 o no» (por opción)</th><th>Kappa «2 o no»</th>
        <th>Misma nota 2/1/0</th><th>R@1 con Pro</th><th>R@1 con Flash</th></tr></thead>
      <tbody>
{judge_rows}
      </tbody>
    </table>
    </div>
    <p class="note">Mismas listas puntuadas por los dos jueces, gold con gen o sin gen. En <code>narrative_v2</code> Flash coincidía con Pro en
      «¿es un 2?» en el 98,0 % de las opciones; en raras, donde la frontera entre el nombre con gen y sin gen es más fina, es la cifra de arriba.</p>
{flash_text}''' if s['judges'] else ''
    return f'''
  <div class="section">
    <div class="section-title">Raras HPO v2 · Terra 5.6 frente a gpt-6.1-sol</div>
    <div class="callout callout-info">
      En <code>narrative_v2</code>, gpt-6.1-sol acierta unos 11 puntos más que Terra en raras, pero sobre solo 116 casos. Aquí se comprueba
      con las listas HPO: Sol genera las suyas con el mismo prompt y parámetros que las de Terra de julio, y las puntúa el mismo juez
      (Gemini 2.5 Pro). {progress}, {thousands(t["n"])} casos.{pending}
      {"Hasta ahora, R" if s["pending"] else "R"}@1 {pct(t["terra"]["r1"])} con Terra y <strong>{pct(t["sol"]["r1"])} con Sol</strong> ({t["r1"]["wins"]} casos ganados y
      {t["r1"]["losses"]} perdidos, {p_text(t["r1"]["p"])}); R@5 {pct(t["terra"]["r5"])} y {pct(t["sol"]["r5"])}.
      {"" if s["pending"] or not even else f"En {' y '.join(r['label'] for r in even)} ({' y '.join(str(r['n']) for r in even)} casos) la diferencia de R@1 está dentro del azar."}
    </div>
    <div class="table-scroll">
    <table class="num">
      <thead><tr><th>Dataset</th><th>Casos</th><th>R@1 Terra</th><th>R@1 Sol</th><th>Sol gana / pierde</th><th>p</th>
        <th>R@1 Terra, solo con gen</th><th>R@1 Sol, solo con gen</th><th>R@5 Terra</th><th>R@5 Sol</th><th>p R@5</th>
        <th>R@5* Terra</th><th>R@5* Sol</th><th>p R@5*</th></tr></thead>
      <tbody>
{chr(10).join(row(r) for r in s["rows"])}
{row(t, True) if done > 1 else ""}
      </tbody>
    </table>
    </div>
    <p class="note">Gold con gen o sin gen salvo en las columnas «solo con gen». R@5*: acierto contado solo dentro del número de opciones
      que dio Terra en ese caso, para que Sol no gane por dar listas más largas. Sol: {cents(s["cost"])} de generación por caso y
      {num(s["latency"])} s de latencia mediana; juez {num(s["judgeCost"], 2)} $ en estos datasets.</p>
{judges}
  </div>
'''


def hpo_syn_section(data):
    s = data.get('hpoSyn')
    if not s or not s['rows']:
        return ''
    labels = {'terra': 'Terra 5.6', 'sol': 'gpt-6.1-sol'}
    judges = {'pro': 'Gemini 2.5 Pro', 'flash': 'Gemini 3.8 Flash'}
    rows = '\n'.join(
        f'<tr><td>{judges[r["judge"]]}</td><td>{labels[r["model"]]}</td><td>{", ".join(r["datasets"])}</td><td>{thousands(r["n"])}</td>'
        f'<td>{pct(r["before"]["r1"])}</td><td>{pct(r["after"]["r1"])}</td><td>{r["test"]["wins"]} / {r["test"]["losses"]}</td>'
        f'<td>{p_value(r["test"]["p"])}</td><td>{pct(r["before"]["r5"])}</td><td>{pct(r["after"]["r5"])}</td></tr>' for r in s['rows'])
    agreement = '\n'.join(
        f'<tr><td>{labels[a["model"]]}</td><td>{thousands(a["n"])}</td><td>{pct(a["v2"]["sameP1"])}</td><td>{pct(a["syn"]["sameP1"])}</td>'
        f'<td>{pct(a["v2"]["pro"])} / {pct(a["v2"]["flash"])}</td><td>{pct(a["syn"]["pro"])} / {pct(a["syn"]["flash"])}</td></tr>'
        for a in s['agreement'])
    example = ''
    if {'v2', 'syn'} <= set(s['example']):
        e = s['example']
        share = lambda v, k: f'{e[v][k][0]} de {e[v][k][1]}'
        example = (f'En el ejemplo de MyGene2, Pro da ahora un 2 a «type 5» en {share("syn", "da5")} opciones (antes {share("v2", "da5")}) y '
                   f'a «type 5D», que es otra enfermedad, en {share("syn", "da5d")} (antes {share("v2", "da5d")}).')
    return f'''
  <div class="section">
    <div class="section-title">Raras HPO v2 · prueba: sinónimos del gold para el juez</div>
    <div class="callout callout-info">
      El juez solo ve el nombre del gold. Si el dataset usa un nombre poco habitual, el juez puede no reconocer un sinónimo, como
      pasaba con la artrogriposis distal tipo 5. Prueba: añadir al gold los sinónimos exactos que da MONDO (la ontología de
      enfermedades de Monarch) para su código OMIM, y volver a puntuar las mismas listas con los mismos jueces. Solo cambia lo que se
      da por bueno, y viene de una fuente curada, no de un LLM. {example}
    </div>
    <div class="table-scroll">
    <table class="num">
      <thead><tr><th>Juez</th><th>Listas de</th><th>Datasets</th><th>Casos</th><th>R@1 gold v2</th><th>R@1 con sinónimos</th>
        <th>Gana / pierde</th><th>p</th><th>R@5 gold v2</th><th>R@5 con sinónimos</th></tr></thead>
      <tbody>
{rows}
      </tbody>
    </table>
    </div>
    <h3>¿Se acercan los dos jueces?</h3>
    <div class="table-scroll">
    <table class="num">
      <thead><tr><th>Listas de</th><th>Casos</th><th>Mismo acierto en P1, gold v2</th><th>Con sinónimos</th>
        <th>R@1 Pro / Flash, gold v2</th><th>Con sinónimos</th></tr></thead>
      <tbody>
{agreement}
      </tbody>
    </table>
    </div>
    <p class="note">Solo datasets puntuados por los dos jueces con los dos gold. Los sinónimos salen de
      <code>data29/data-repos/hpo-v2/gold_synonyms.py</code> (API de Monarch; solo sinónimos exactos, sin códigos Orphanet porque suelen
      ser grupos). Es una prueba: el dataset oficial sigue siendo HPO v2.</p>
  </div>
'''


def graded_table(s, version):
    keys = (('realcases', 'Casos reales'), ('realRare', 'Raras reales'), ('total', 'Total'))
    head = ''.join(f'<th>{label}: v2</th><th>{version}</th><th>Gana / pierde</th>' for _, label in keys)
    rows = '\n'.join(
        f'<tr><td><span class="dot" style="background:{m["color"]}"></span> {m["name"]}</td>'
        + ''.join(f'<td>{pct(m["groups"][k]["v2"]["r1"])}</td><td>{pct(m["groups"][k]["v3"]["r1"])}</td>'
                  f'<td>{m["groups"][k]["r1"]["wins"]} / {m["groups"][k]["r1"]["losses"]}</td>' for k, _ in keys) + '</tr>'
        for m in s['models'])
    return f'''
    <div class="table-scroll">
    <table class="num">
      <thead><tr><th>R@1</th>{head}</tr></thead>
      <tbody>
{rows}
      </tbody>
    </table>
    </div>'''


def graded_v3_section(data):
    s = data.get('gradedV3')
    if not s:
        return ''
    c, p1 = s['consistency'], s['p1']
    share = lambda v: f'{c[v]["differ"]} de {thousands(c[v]["repeated"])} ({pct(100 * c[v]["differ"] / c[v]["repeated"])})'
    moves = s['moves']
    same_order = s['order']['v2'] == s['order']['v3']
    order = ('El orden de los modelos en casos reales no cambia.' if same_order else
             f'El orden en casos reales pasa de {", ".join(s["order"]["v2"])} a {", ".join(s["order"]["v3"])}.')
    example = ''
    if 'example' in s:
        e = s['example']
        example = (f' En su ejemplo, la P1 de Terra 5.6 («{e["v3"][0]}») pasa de {e["v2"][1]} a {e["v3"][1]}.')
    sol_terra = ''
    if 'solTerra' in s:
        st = s['solTerra']
        sol_terra = (f' Sol frente a Terra 5.6 en raras reales: {st["v2"]["realRare"]["wins"]} / {st["v2"]["realRare"]["losses"]} con v2 '
                     f'y {st["v3"]["realRare"]["wins"]} / {st["v3"]["realRare"]["losses"]} con v3 ({p_text(st["v3"]["realRare"]["p"])}).')
    return f'''
  <div class="section">
    <div class="section-title">Punto 6 de Julián · juez con <code>graded_v3</code> (adoptado)</div>
    <div class="callout callout-info">
      La rúbrica decía qué nota lleva «X con Y» frente a «X», pero no una respuesta que nombra el gold y añade una causa o una complicación,
      y el juez la puntuaba distinto según el orden de las palabras. <code>graded_v3</code> da un 2 cuando la opción afirma el diagnóstico de
      referencia aunque añada causa o complicación, salvo las disyuntivas («A o B») y otra enfermedad cuyo nombre lo contiene. Además, cada
      opción repetida (mismo caso, gold y texto) se puntúa una sola vez y la nota se reutiliza en todos los modelos. Se vuelven a puntuar las
      mismas listas de {s["n"]} modelos con el mismo juez, Gemini 2.5 Pro.{example}
      {order} Las respuestas iguales con notas distintas pasan de {share("v2")} a {share("v3")}.{sol_terra}
    </div>
    <div class="callout callout-warn">
      <strong>Decidido el 30-oct-2026 (Julián): se adopta <code>graded_v3</code> y la rúbrica deja de ajustarse con contraejemplos</strong>,
      porque con cualquier dataset saldrá alguno. Criterio: la enfermedad que propone el modelo es la misma entidad si está relacionada con
      el gold y se trata de la misma forma. Con v3, {p1["gains"]} casos pasan a acertar en P1 y {p1["losses"]} dejan de hacerlo; entre los que
      suben hay respuestas que la regla escrita no buscaba pero que encajan en ese criterio, como «Stevens-Johnson / NET» para NET o
      «herpangina» para faringoamigdalitis aguda. {p1["reused"]} de esas ganancias vienen de una nota reutilizada. Se probó una versión más
      estricta (v3b: disyuntivas nunca 2 y cada opción puntuada dos veces) sobre las 178 opciones que cambiaban (3,57 $) y se descartó con
      esta decisión. <code>graded_v3</code> es el juez por defecto desde ahora; las cifras de este informe siguen con v2 hasta volver a
      puntuar con <code>narrative_v2</code> v0.2.
    </div>
{graded_table(s, 'v3')}
    <p class="note">Gana / pierde: casos que acierta en P1 con v3 y no con v2, y al revés. Notas que cambian entre v2 y v3:
      de 1 a 2, {thousands(moves.get("12", 0))}; de 2 a 1, {thousands(moves.get("21", 0))}; de 0 a 1, {thousands(moves.get("01", 0))};
      de 1 a 0, {thousands(moves.get("10", 0))}. Parte es el ruido del juez y no la regla nueva. Juez v3: {s["cost"]["calls"]} llamadas,
      {thousands(s["cost"]["reused"])} notas reutilizadas, ≈ {num(s["cost"]["v3"], 2)} $.</p>
  </div>
'''


def hpo_opus_section(data):
    s = data.get('hpoOpus')
    if not s:
        return ''
    sol_cost = data.get('hpoSol', {}).get('cost')

    def row(r, total=False):
        o, c = ('<strong>', '</strong>') if total else ('', '')
        return (f'<tr{" class=\"winner\"" if total else ""}><td>{o}{r["label"]}{c}</td><td>{thousands(r["n"])}</td>'
                f'<td>{pct(r["terra"]["r1"])}</td><td>{o}{pct(r["sol"]["r1"])}{c}</td><td>{pct(r["opus"]["r1"])}</td>'
                f'<td>{r["r1"]["wins"]} / {r["r1"]["losses"]}</td><td>{p_value(r["r1"]["p"])}</td>'
                f'<td>{pct(r["terra"]["r5"])}</td><td>{o}{pct(r["sol"]["r5"])}{c}</td><td>{pct(r["opus"]["r5"])}</td></tr>')
    t = s['total']
    rows = '\n'.join([row(r) for r in s['rows']] + [row(t, True)])
    cost_text = (f'Opus cuesta {cents(s["cost"])} por caso en generación, frente a {cents(sol_cost)} de Sol.' if sol_cost
                 else f'Opus cuesta {cents(s["cost"])} por caso en generación.')
    return f'''
  <div class="section">
    <div class="section-title">Raras HPO v2 · Claude Opus 5 frente a Sol y Terra</div>
    <div class="callout callout-info">
      En <code>narrative_v2</code> Claude Opus 5 es el mejor en casos reales no raros, pero en raras reales queda por detrás de Sol.
      Para comprobarlo con más casos se pasa Opus 5 (esfuerzo <code>low</code>, mismo prompt y juez Gemini 2.5 Pro) por los cuatro datasets
      pequeños de HPO v2. <strong>Opus queda por detrás de los dos</strong>: R@1 {pct(t["opus"]["r1"])} frente a {pct(t["sol"]["r1"])} de Sol
      ({t["r1"]["wins"]} / {t["r1"]["losses"]}, {p_text(t["r1"]["p"])}) y {pct(t["terra"]["r1"])} de Terra
      ({t["terraR1"]["losses"]} / {t["terraR1"]["wins"]} a favor de Terra, {p_text(t["terraR1"]["p"])}). En R@5 tampoco lo compensa,
      aunque da {num(s["options"], 0)} opciones (mediana): {pct(t["opus"]["r5"])} frente a {pct(t["sol"]["r5"])}.
      No es que nombre la enfermedad de forma menos precisa: contando también las notas 1 en P1, Opus llega al {pct(s["lax"]["opus"])}
      y Sol al {pct(s["lax"]["sol"])} ({s["laxTest"]["wins"]} / {s["laxTest"]["losses"]}, {p_text(s["laxTest"]["p"])}).
      {cost_text}
    </div>
    <div class="table-scroll">
    <table class="num">
      <thead><tr><th>Dataset</th><th>Casos</th><th>R@1 Terra</th><th>R@1 Sol</th><th>R@1 Opus</th><th>Sol frente a Opus</th><th>p</th>
        <th>R@5 Terra</th><th>R@5 Sol</th><th>R@5 Opus</th></tr></thead>
      <tbody>
{rows}
      </tbody>
    </table>
    </div>
    <p class="note">McNemar exacto sobre los mismos casos, gold v2 (con gen o sin gen). DDD y RAMEDIS no se han pasado por Opus por coste
      (unos 6,7 c$ por caso). Juez de las listas de Opus: {num(s["judgeCost"], 2)} $.</p>
  </div>
'''


def hpo_sermas_section(data):
    s = data.get('hpoSermas')
    if not s:
        return ''
    labels = {'terra': 'Terra 5.6', 'sol': 'gpt-6.1-sol'}
    prompt_rows = '\n'.join(
        f'<tr><td>{labels[m]}</td><td>{pct(r["classic"]["r1"])}</td><td>{pct(r["sermas"]["r1"])}</td><td>{r["r1"]["wins"]} / {r["r1"]["losses"]}</td>'
        f'<td>{p_value(r["r1"]["p"])}</td><td>{pct(r["classic"]["r5"])}</td><td>{pct(r["sermas"]["r5"])}</td><td>{r["r5"]["wins"]} / {r["r5"]["losses"]}</td>'
        f'<td>{p_value(r["r5"]["p"])}</td></tr>' for m, r in s['prompt'].items())
    names = {'classic': 'DxGPT (<code>juanjo_classic_v2</code>)', 'sermas': f'sermas (<code>{SERMAS_PROMPT}</code>)'}
    versus = '\n'.join(
        f'<tr><td>{names[kind]}</td><td>{pct(s["prompt"]["sol"][kind]["r1"])}</td><td>{pct(s["prompt"]["terra"][kind]["r1"])}</td>'
        f'<td>{t["r1"]["wins"]} / {t["r1"]["losses"]}</td><td>{p_value(t["r1"]["p"])}</td>'
        f'<td>{pct(s["prompt"]["sol"][kind]["r5"])}</td><td>{pct(s["prompt"]["terra"][kind]["r5"])}</td>'
        f'<td>{t["r5"]["wins"]} / {t["r5"]["losses"]}</td><td>{p_value(t["r5"]["p"])}</td></tr>'
        for kind, t in (('classic', s['solTerra']['juanjo_classic_v2']), ('sermas', s['solTerra'][SERMAS_PROMPT])))
    list_rows = '\n'.join(
        f'<tr><td>{labels[m]}</td><td>{num(v["options"])}</td><td>{v["under5"]} %</td><td>{num(v["latency"])} s</td><td>{cents(v["cost"])}</td></tr>'
        for m, v in s['lists'].items())
    sermas = s['solTerra'][SERMAS_PROMPT]['r1']
    sol, terra = s['prompt']['sol']['sermas'], s['prompt']['terra']['sermas']
    verdict = (f'Con el prompt de sermas, Sol acierta en primer lugar el {pct(sol["r1"])} de los casos y Terra el {pct(terra["r1"])} '
               f'({sermas["wins"]} casos que solo acierta Sol frente a {sermas["losses"]} que solo acierta Terra, {p_text(sermas["p"])}).')
    if sermas['p'] < 0.05 and sermas['wins'] > sermas['losses']:
        lists = s['lists']
        verdict += (f' <strong>Para sermas, Sol:</strong> gana con los dos prompts, cuesta menos por caso ({cents(lists["sol"]["cost"])} frente a '
                    f'{cents(lists["terra"]["cost"])}) y sus {num(lists["sol"]["latency"])} s de mediana caben de sobra en App Service, que corta a los 230 s.')
    datasets = s['datasets'][0] if len(s['datasets']) == 1 else ', '.join(s['datasets'][:-1]) + ' y ' + s['datasets'][-1]
    return f'''
  <div class="section">
    <div class="section-title">Prompt de sermas (raras) · Sol frente a Terra</div>
    <div class="callout callout-info">
      sermas es la versión de DxGPT solo para enfermedades raras, desplegada en App Service. Su prompt es el de DxGPT con tres cambios:
      «specialized in rare diseases», «rare disease diagnoses» y «description of the rare disease». Para elegir modelo se generan listas
      nuevas de Sol y Terra con ese prompt en {datasets} ({thousands(s["n"])} casos de HPO v2), y se comparan con las
      listas del prompt de DxGPT en los mismos casos. Los dos prompts los puntúa el mismo juez, Gemini 3.8 Flash. {verdict}
    </div>
    <h3>Sol frente a Terra con cada prompt</h3>
    <div class="table-scroll">
    <table class="num">
      <thead><tr><th>Prompt</th><th>R@1 Sol</th><th>R@1 Terra</th><th>Gana / pierde</th><th>p</th>
        <th>R@5 Sol</th><th>R@5 Terra</th><th>Gana / pierde</th><th>p</th></tr></thead>
      <tbody>
{versus}
      </tbody>
    </table>
    </div>
    <h3>¿Cambia algo el prompt de raras?</h3>
    <div class="table-scroll">
    <table class="num">
      <thead><tr><th>Modelo</th><th>R@1 DxGPT</th><th>R@1 sermas</th><th>Gana / pierde</th><th>p</th>
        <th>R@5 DxGPT</th><th>R@5 sermas</th><th>Gana / pierde</th><th>p</th></tr></thead>
      <tbody>
{prompt_rows}
      </tbody>
    </table>
    </div>
    <div class="table-scroll">
    <table class="num">
      <thead><tr><th>Listas con el prompt de sermas</th><th>Opciones (mediana)</th><th>Casos con menos de 5</th><th>Latencia (mediana)</th><th>Coste por caso</th></tr></thead>
      <tbody>
{list_rows}
      </tbody>
    </table>
    </div>
    <p class="note">McNemar exacto sobre los mismos casos, gold v2 (con gen o sin gen). Las listas de Terra con el prompt de DxGPT son las de julio
      y las de Sol las de octubre; las de sermas son de hoy. Parte de la diferencia entre prompts puede ser la variación normal entre ejecuciones
      (ver «Variabilidad entre ejecuciones»).</p>
  </div>
'''


def n5_section(data):
    runs = data.get('n5')
    if not runs:
        return ''
    head = ''.join(f'<th>{r["name"]}: «N»</th><th>«5»</th><th>Gana / pierde</th><th>p</th>' for r in runs)
    rows = []
    for k in ('r1', 'r5'):
        for key, label, _ in REAL_SPLIT:
            cells = ''.join(f'<td>{pct(g["base"][k])}</td><td>{pct(g["five"][k])}</td>'
                            f'<td>{g[k]["wins"]} / {g[k]["losses"]}</td><td>{p_value(g[k]["p"])}</td>'
                            for g in (r['groups'][key] for r in runs))
            rows.append(f'<tr><td>R@{k[1]} · {label}</td><td>{runs[0]["groups"][key]["n"]}</td>{cells}</tr>')
    cost_rows = '\n'.join(
        f'<tr><td><span class="dot" style="background:{r["color"]}"></span> {r["name"]}</td><td>{label}</td><td>{num(v["options"])}</td>'
        f'<td>{v["under5"]} %</td><td>{cents(v["cost"])}</td><td>{num(v["latency"])} s</td></tr>'
        for r in runs for label, v in (('«N»', r['n']), ('«5»', r['five'])))
    significant = [r['name'] for r in runs for key in ('realcases', 'realRare', 'realCommon', 'total') for k in ('r1', 'r5')
                   if r['groups'][key][k]['p'] < 0.05]
    real = {r['name']: r['groups']['realcases'] for r in runs}
    return f'''
  <div class="section">
    <div class="section-title">Pedir exactamente 5 diagnósticos · {" y ".join(r["name"] for r in runs)}</div>
    <div class="callout callout-info">
      El prompt usado hasta ahora, igual que el de producción, dice «generate N possible diagnoses» y deja que el modelo decida cuántos da: Terra 5.6
      da menos de 5 en la mitad de los casos, Gemini 3.1 Pro casi siempre 3 y Claude Opus 5 siempre 10, y eso afecta a R@5. Con el pipeline
      anterior, pedir 5 restaba precisión. Aquí se repite con el mismo modelo, casos y juez, cambiando solo «N» por «5»
      (<code>{N5_PROMPT}.txt</code>). En casos reales, R@1 pasa de {"; ".join(f"{pct(g['base']['r1'])} a {pct(g['five']['r1'])} ({k})" for k, g in real.items())}.
      <strong>{"Ninguna diferencia es significativa: pedir 5 no resta precisión." if not significant else "Hay diferencias significativas en " + ", ".join(dict.fromkeys(significant)) + "."}</strong>
      <br><strong>Decidido el 30-oct-2026: producción pide 5.</strong> Cambiado en los dos prompts de diagnóstico de
      <code>Server/assets/prompts.js</code> (<code>withoutDiseases</code>, «generate 5 possible diagnoses», y <code>withDiseases</code>,
      «generate 5 more»), en la rama <code>develop</code>, pendiente de desplegar. Para medir lo mismo que producción, las próximas
      ejecuciones oficiales del benchmark usarán <code>{N5_PROMPT}</code>.
    </div>
    <div class="table-scroll">
    <table class="num">
      <thead><tr><th>Grupo</th><th>Casos</th>{head}</tr></thead>
      <tbody>
{chr(10).join(rows)}
      </tbody>
    </table>
    </div>
    <div class="table-scroll">
    <table class="num">
      <thead><tr><th>Modelo</th><th>Prompt</th><th>Opciones (mediana)</th><th>Casos con menos de 5</th><th>Coste por caso</th><th>Latencia (mediana)</th></tr></thead>
      <tbody>
{cost_rows}
      </tbody>
    </table>
    </div>
    <p class="note">McNemar exacto de «5» frente a «N» sobre los mismos casos. Una variación de este tamaño entra en lo que cambia un modelo
      al repetir la misma ejecución (ver «Variabilidad entre ejecuciones»).</p>
  </div>
'''


def effort_section(data):
    effort = data.get('effort')
    if not effort:
        return ''
    head = ''.join(f'<th>{e["name"]} low</th><th>medium</th><th>Gana / pierde</th><th>p</th>' for e in effort)
    rows = []
    for key, label, _ in REAL_SPLIT:
        cells = ''.join(f'<td>{pct(g["low"]["r1"])}</td><td>{pct(g["medium"]["r1"])}</td>'
                        f'<td>{g["r1"]["wins"]} / {g["r1"]["losses"]}</td><td>{p_value(g["r1"]["p"])}</td>'
                        for g in (e['groups'][key] for e in effort))
        rows.append(f'<tr><td>{label}</td><td>{effort[0]["groups"][key]["n"]}</td>{cells}</tr>')
    cost_rows = []
    for e in effort:
        for level in ('low', 'medium'):
            g = e['groups']['realcases'][level]
            cost_rows.append(
                f'<tr><td><span class="dot" style="background:{e["color"]}"></span> {e["name"]}</td><td><code>{level}</code></td>'
                f'<td>{pct(g["r1"])}</td><td>{pct(g["r5"])}</td><td>{cents(e[level]["genCost"])}</td>'
                f'<td>{num(e[level]["latency"])} s</td><td>{num(e[level]["options"], 0)}</td></tr>')
    tests = [e['groups'][key][k] for e in effort for key, *_ in REAL_SPLIT for k in ('r1', 'r5')]
    min_p = min(t['p'] for t in tests)
    extra = ', '.join(f'{e["name"]} +{num(100 * (e["medium"]["genCost"] / e["low"]["genCost"] - 1), 0)} %'
                      for e in effort if e['low']['genCost'] and e['medium']['genCost'])
    return f'''
  <div class="section">
    <div class="section-title">Esfuerzo de razonamiento <code>medium</code> · Terra 5.6 y gpt-6.1-sol</div>
    <div class="callout callout-info">
      Mismo prompt y mismos 300 casos; solo cambia <code>reasoning_effort</code> de <code>low</code> a <code>medium</code>.
      <strong>{"En ningún grupo la diferencia es significativa" if min_p >= 0.05 else "Algún grupo cambia de forma significativa"}</strong>
      (el p más bajo, en R@1 o R@5, es {p_value(min_p)}), igual que en <code>all_256_clean</code> con V4. Medium cuesta más por caso
      ({extra}) y tarda algo más. Se mantiene <code>low</code>.
    </div>
    <h3>R@1 estricta, <code>low</code> frente a <code>medium</code></h3>
    <div class="table-scroll">
    <table class="num">
      <thead><tr><th>Grupo</th><th>Casos</th>{head}</tr></thead>
      <tbody>
{chr(10).join(rows)}
      </tbody>
    </table>
    </div>
    <p class="note">Gana / pierde: casos que acierta <code>medium</code> y no <code>low</code>, y al revés; p de McNemar exacto sobre esos casos.</p>
    <h3>Casos reales, coste y latencia</h3>
    <div class="table-scroll">
    <table class="num">
      <thead><tr><th>Modelo</th><th>Esfuerzo</th><th>R@1</th><th>R@5</th><th>Coste por caso</th><th>Latencia mediana</th><th>Opciones (mediana)</th></tr></thead>
      <tbody>
{chr(10).join(cost_rows)}
      </tbody>
    </table>
    </div>
    <p class="note">Coste de generación con los tokens de cada run (los de razonamiento cuentan como salida) y los precios de
      <code>Server/services/costUtils.js</code>; no incluye el juez.</p>
  </div>
'''


def poc_section(data):
    poc = data.get('poc')
    if not poc or not poc['arms']:
        return ''

    def bar(value, color):
        return (f'<div class="bar-container"><div class="bar-track"><div class="bar-fill" style="width:{value}%;background:{color}"></div></div>'
                f'<span class="bar-label">{pct(value)}</span></div>')

    def test(t):
        return f'<td>{t["wins"]} / {t["losses"]}</td><td>{p_value(t["p"])}</td>' if t else '<td>—</td><td>—</td>'

    rows, length_rows = [], []
    for base, b in poc['bases'].items():
        arms = [a for a in poc['arms'] if a['base'] == base]
        if not arms:
            continue
        rows.append(f'<tr class="group-row"><td colspan="10">Sobre la lista de {b["name"]} low</td></tr>')
        length_rows.append(f'<tr class="group-row"><td colspan="8">Sobre la lista de {b["name"]} low</td></tr>')
        entries = [(f'<strong>{b["name"]} solo</strong>', b, None, '#94a3b8')] + [(a['label'], a, a, b['color']) for a in arms]
        for label, entry, arm, color in entries:
            g = entry['groups']
            rows.append(
                f'<tr><td>{label}</td><td>{bar(g["realcases"]["r1"], color)}</td>{test(arm and arm["vsBase"]["r1"])}'
                f'<td>{pct(g["realRare"]["r1"])}</td><td>{pct(g["realCommon"]["r1"])}</td><td>{pct(g["exam"]["r1"])}</td>'
                f'<td>{pct(g["realcases"]["r5"])}</td><td>{cents(entry["cost"])}</td><td>{num(entry["latency"], 0)} s</td></tr>')
            stage = (f'<td>{num(arm["stageCalls"], 0)}</td><td>{num(arm["stageCost"] * 1000, 1)} m$</td><td>{num(arm["stageP50"])} s</td>'
                     if arm and arm['stageCost'] is not None else '<td>—</td><td>—</td><td>—</td>')
            length_rows.append(f'<tr><td>{label}</td><td>{num(entry["options"], 0)}</td><td>{pct(entry["lengthHit"])}</td>'
                               f'{test(arm and arm["length"])}{stage}</tr>')

    arms = {a['arm']: a for a in poc['arms']}
    terra, sol = poc['bases'].get('terra56'), poc['bases'].get('sol61')
    on_terra = [a for a in poc['arms'] if a['base'] == 'terra56']
    on_sol = [a for a in poc['arms'] if a['base'] == 'sol61']
    panel = arms.get('arm_b_panel_terra_sol')
    lines = []
    if terra and on_terra:
        r1 = [a['groups']['realcases']['r1'] for a in on_terra]
        lines.append(f'Sobre Terra, la segunda etapa sube R@1 en casos reales de {pct(terra["groups"]["realcases"]["r1"])} a '
                     f'{pct(min(r1))}–{pct(max(r1))}.')
        if panel:
            lines.append(f'El panel Terra + Sol llega a {pct(panel["groups"]["realcases"]["r1"])} ({p_text(panel["vsBase"]["r1"]["p"])} '
                         f'frente a Terra) y sube las raras de {pct(terra["groups"]["realRare"]["r1"])} a {pct(panel["groups"]["realRare"]["r1"])}.')
    if sol:
        lines.append(f'Pero Sol solo ya da {pct(sol["groups"]["realcases"]["r1"])} ({pct(sol["groups"]["realRare"]["r1"])} en raras)'
                     + (f', y frente a Sol el panel gana {panel["vsSol"]["wins"]} casos y pierde {panel["vsSol"]["losses"]} '
                        f'({p_text(panel["vsSol"]["p"])}).' if panel else '.'))
    if on_sol:
        better = [a for a in on_sol if a['vsBase']['r1']['p'] < 0.05 and a['vsBase']['r1']['net'] > 0]
        best = max(on_sol, key=lambda a: a['groups']['realcases']['r1'])
        lines.append(('<strong>Sobre Sol, ningún brazo mejora de forma significativa</strong>' if not better else
                      '<strong>Sobre Sol, algún brazo mejora de forma significativa</strong>')
                     + f' (el mejor, {html.escape(best["label"])}, {pct(best["groups"]["realcases"]["r1"])}, {p_text(best["vsBase"]["r1"]["p"])}):'
                       ' lo que la capa añadía a Terra era subirla al nivel de Sol. La palanca grande es el modelo.')
    return f'''
  <div class="section">
    <div class="section-title">Capa agéntica · PoC offline sobre las listas de Terra y de Sol</div>
    <div class="callout callout-info">
      Una segunda etapa sobre la lista que ya dio el modelo, sin volver a generarla: <strong>A</strong>, el modelo relee el caso y
      revisa su lista; <strong>B</strong> y <strong>B2</strong>, un moderador consolida las listas de varios modelos; <strong>C</strong>,
      el modelo revisa su lista con HPO y PubMed (hasta el 30-jun-2026). Detalle en
      <a href="../bench/agentic_poc/README.md">bench/agentic_poc</a>.
      {" ".join(lines)}
      Una ejecución por brazo y gold sin validar: <strong>la decisión entre Sol solo y el panel espera a <code>narrative_v2</code> v0.2</strong>.
    </div>
    <h3>R@1 estricta por brazo</h3>
    <div class="table-scroll">
    <table class="num">
      <thead><tr><th>Run</th><th>R@1 casos reales</th><th>Gana / pierde frente a su base</th><th>p</th><th>Raras, casos reales</th>
        <th>No raras, casos reales</th><th><code>exam</code></th><th>R@5 casos reales</th><th>Coste por caso</th><th>Latencia aprox.</th></tr></thead>
      <tbody>
{chr(10).join(rows)}
      </tbody>
    </table>
    </div>
    <p class="note">Coste por caso: generación de todos los modelos que intervienen más la segunda etapa, con los precios de
      <code>costUtils.js</code>. B usa también Claude Opus 5, que no está en <code>costUtils.js</code>: sin coste. Latencia aproximada:
      el modelo más lento del panel (mediana) más las llamadas de la segunda etapa, una tras otra (mediana por llamada); en C, sin contar
      las búsquedas en PubMed. Tendría que ser una segunda fase asíncrona.</p>
    <h3>Control de longitud y coste de la segunda etapa</h3>
    <div class="table-scroll">
    <table class="num">
      <thead><tr><th>Run</th><th>Opciones (mediana)</th><th>Acierto dentro de la longitud de la base</th><th>Gana / pierde frente a su base</th><th>p</th>
        <th>Llamadas extra por caso</th><th>Coste 2.ª etapa por caso</th><th>Mediana por llamada</th></tr></thead>
      <tbody>
{chr(10).join(length_rows)}
      </tbody>
    </table>
    </div>
    <p class="note">Los brazos devuelven 5 opciones; si la base dio menos, R@5 podría subir solo por la longitud. Aquí un acierto cuenta
      solo dentro del número de opciones que dio la base en ese caso (casos reales, 210).</p>
  </div>
'''


def all256_table():
    return '\n'.join(f'<tr><td>{m}</td><td>{e}</td><td>{pct(a)}</td><td>{pct(b)}</td><td>{pct(c)}</td></tr>'
                     for m, e, a, b, c in ALL256)


def build_html(data):
    models = {m['id']: m for m in data['models']}
    best = data['models'][0]
    base = models[BASELINE]
    ddd = data['hpo'][0]
    hpo_total = data['hpoTotal']
    unseen_min = min(data['cutoffs'], key=lambda c: c['unseenPublic'])
    sol_total = (data.get('hpoSol') or {}).get('total')
    sol_rare = (f'. gpt-6.1-sol: {pct(sol_total["sol"]["r1"])} sobre {thousands(sol_total["n"])} casos, {p_text(sol_total["r1"]["p"])}'
                if sol_total else '')
    summary_r1 = data['mcnemar']['realcases_r1']['rows']

    def stratum_card(key, label):
        top = max(data['models'], key=lambda m: m['groups'][key]['r1'])
        n = top['groups'][key]['n']
        if top['id'] == BASELINE:
            sub = f'{top["name"]}, R@1 ({n} casos)'
        else:
            test = next(r for r in data['mcnemar'][f'{key}_r1']['rows'] if r['id'] == top['id'])
            sub = (f'{top["name"]}, R@1 ({n} casos). Terra 5.6: {pct(base["groups"][key]["r1"])}; '
                   f'{test["wins"]} / {test["losses"]} casos, {p_text(test["p"])}')
            pooled = (data.get('rerun') or {}).get('pooled')
            if pooled and top['id'] == 'sol61':
                sub += (f'. Con dos ejecuciones de cada uno: {pct(pooled[key]["a"])} frente a {pct(pooled[key]["b"])}, '
                        f'{p_text(pooled[key]["p"])}')
        return '\n'.join([f'      <div class="card"><div class="card-label">Mejor en {label.lower()}</div>',
                          f'        <div class="card-value">{pct(top["groups"][key]["r1"])}</div>',
                          f'        <div class="card-sub">{sub}</div></div>'])
    best_test = next(r for r in summary_r1 if r['id'] == best['id'])
    judge_cost = sum(m['judgeCost'] for m in data['models'])
    js_data = json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    today = date.today()
    months = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']
    stamp = f'{today.day} {months[today.month - 1]} {today.year}'

    return f'''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DxGPT — Pipeline V5</title>
<link rel="stylesheet" href="benchmark-report-strict.css">
<style>
  .dot {{ width: 10px; height: 10px; border-radius: 50%; display: inline-block; vertical-align: middle; }}
  .heat td {{ text-align: center; font-variant-numeric: tabular-nums; }}
  .heat td:first-child {{ text-align: left; white-space: nowrap; }}
  .heat th {{ text-align: center; }}
  .heat th:first-child {{ text-align: left; }}
  .num td {{ font-variant-numeric: tabular-nums; }}
  .stack-track {{ gap: 2px; background: #f1f5f9; }}
  .stack-row {{ grid-template-columns: 200px 1fr 120px; }}
  .stack-val {{ font-weight: 600; font-size: 0.78rem; }}
  .viz-toolbar .viz-tabs + .viz-tabs {{ margin-left: auto; }}
  .explain {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 16px; }}
  .explain .card p {{ font-size: 0.86rem; margin-top: 6px; }}
  .svg-chart text {{ font-variant-numeric: tabular-nums; }}
  .group-row td {{ background: #f8fafc; font-weight: 600; font-size: 0.82rem; }}
  @media (max-width: 640px) {{ .stack-row {{ grid-template-columns: 120px 1fr 92px; }} .section {{ padding: 20px 16px; }} }}
</style>
</head>
<body>
<div class="hero">
  <div class="hero-badge">Borrador · Pipeline V5 <code>graded_v2</code> · {stamp}</div>
  <h1>Pipeline V5: narrativo y raras</h1>
  <p><code>narrative_v2</code> v0.1 (300 casos, sin validación clínica) y raras HPO v2 (3.006 casos), con el evaluador V5
     y juez Gemini 2.5 Pro. La serie histórica (Pipeline V4, <code>all_256_clean</code>) sigue en el informe strict de texto.</p>
  <p class="hero-nav">
    <a href="benchmark-report-v5.html">V5 (este)</a> ·
    <a href="benchmark-report-strict-texto.html">Texto V4 strict</a> ·
    <a href="benchmark-report-strict-multimodal.html">Multimodal</a> ·
    <a href="benchmark-report-jueces.html">Jueces</a> ·
    <a href="pipeline/pipeline-v5.md">Cómo funciona V5</a>
  </p>
</div>
<div class="container">

  <div class="section">
    <div class="section-title">Resumen</div>
    <div class="cards">
{stratum_card('realRare', 'Raras, casos reales')}
{stratum_card('realCommon', 'No raras, casos reales')}
      <div class="card"><div class="card-label">Raras HPO v2, Terra 5.6</div>
        <div class="card-value">{pct(hpo_total['v5v2']['r1'])}</div>
        <div class="card-sub">R@1 aceptando también el nombre sin gen; {pct(hpo_total['v4']['r1'])} con V4 strict sobre las mismas listas{sol_rare}</div></div>
      <div class="card"><div class="card-label"><code>live</code> no visto</div>
        <div class="card-value">{unseen_min['unseenPublic']}–150</div>
        <div class="card-sub">casos publicados después del corte de cada modelo (el mínimo es {unseen_min['model']})</div></div>
    </div>
    <div class="callout callout-info">
      Cifra principal: <strong>R@1 estricta en casos reales (<code>live</code>+<code>urg</code>), por separado en raras y en no
      raras</strong>: son poblaciones distintas y mezclarlas diluye las diferencias. La cifra conjunta de casos reales
      ({pct(best['groups']['realcases']['r1'])} con {best['name']}, {pct(base['groups']['realcases']['r1'])} con Terra 5.6,
      {p_text(best_test['p'])}) queda como secundaria. <code>exam</code> apenas separa a los modelos y <code>synth</code> es demasiado fácil. La nota estricta solo cuenta la misma enfermedad (nota 2 del
      juez); la laxa (2 o 1) es de uso interno. Todo es provisional hasta que David valide <code>narrative_v2</code>: las listas
      no cambiarán, solo se re-puntúan. Más abajo, otras pruebas: Terra repetido para medir cuánto varía una ejecución,
      esfuerzo de razonamiento <code>medium</code>, una capa agéntica offline sobre las listas de Terra y de Sol, y Sol frente a
      Terra en raras.
    </div>
  </div>

  <div class="section">
    <div class="section-title">Qué cambia respecto a V4</div>
    <div class="explain">
      <div class="card"><div class="card-label">El juez ve todos los casos</div>
        <p>En V4 el juez solo entraba si las capas automáticas (códigos ICD-10 y SapBERT) no encontraban nada. En V5 solo el
           código SNOMED idéntico decide sin juez; todo lo demás lo juzga Gemini 2.5 Pro.</p></div>
      <div class="card"><div class="card-label">Una nota por opción</div>
        <p>El juez puntúa cada diagnóstico de la lista: 2 = misma enfermedad, 1 = relacionada, 0 = otra. La posición del
           acierto es la del primer 2, no la de la primera capa que acertaba.</p></div>
      <div class="card"><div class="card-label">Gold tal como está escrito</div>
        <p>El juez lee el diagnóstico de referencia del dataset y sus nombres aceptados, no el texto normalizado por Azure,
           que a veces nombraba otra enfermedad.</p></div>
    </div>
    <p class="note">Detalle, reglas del juez y cómo ejecutarlo: <a href="pipeline/pipeline-v5.md">docs/pipeline/pipeline-v5.md</a>.</p>
  </div>

  <div class="section">
    <div class="section-title">narrative_v2 · 300 casos · seis modelos</div>
    <div class="callout callout-warn">
      Mismo prompt (<code>juanjo_classic_v2</code>) y esfuerzo <code>low</code> en todos. Gemini 3 Pro ya no existe en la API
      de Google: se usa gemini-3.1-pro-preview. Los bloques: <code>live</code> = 150 case reports de PubMed de jul–oct 2026;
      <code>urg</code> = 60 urgencias en español; <code>exam</code> = 60 viñetas MedQA/MedBullets; <code>synth</code> = 30 raras sintéticas.
    </div>

    <div class="viz-panel">
      <div class="viz-panel-title"><span>Casos reales frente a preguntas de examen</span>
        <div class="viz-tabs" id="dumbbell-tabs">
          <button type="button" class="viz-tab active" data-k="r1">R@1</button>
          <button type="button" class="viz-tab" data-k="r5">R@5</button>
        </div>
      </div>
      <div class="viz-panel-sub">En examen todos los modelos están en una franja estrecha; en casos reales se separan.
        La distancia entre los dos puntos es lo que pierde cada modelo al pasar de viñetas de examen a casos reales.</div>
      <div class="svg-wrap"><svg id="dumbbell-svg" class="svg-chart" viewBox="0 0 680 330" role="img" aria-label="R@1 en casos reales y en examen por modelo"></svg></div>
      <div class="viz-legend">
        <span class="viz-legend-item"><svg width="12" height="12"><circle cx="6" cy="6" r="5" fill="#475569"/></svg>Casos reales (<code>live</code>+<code>urg</code>, 210)</span>
        <span class="viz-legend-item"><svg width="12" height="12"><circle cx="6" cy="6" r="4.5" fill="#fff" stroke="#475569" stroke-width="2"/></svg>Preguntas de examen (<code>exam</code>, 60)</span>
      </div>
    </div>

    <div class="viz-panel" style="margin-top:20px">
      <div class="viz-panel-title"><span>Acierto por bloque</span>
        <div class="viz-tabs" id="heat-tabs">
          <button type="button" class="viz-tab active" data-k="r1">R@1</button>
          <button type="button" class="viz-tab" data-k="r5">R@5</button>
          <button type="button" class="viz-tab" data-k="laxR5">R@5 laxa</button>
        </div>
      </div>
      <div class="viz-panel-sub">Más oscuro = más acierto, en la misma escala para toda la tabla. «<code>live</code> sin ver» quita los casos publicados antes del corte de cada modelo.</div>
      <div class="table-scroll"><table class="heat" id="heat-table"></table></div>
    </div>

    <div style="margin-top:20px">
      <div class="viz-panel">
        <div class="viz-panel-title"><span>Diferencia con Terra 5.6, caso a caso</span></div>
        <div class="viz-toolbar">
          <div class="viz-tabs" id="mc-subset-tabs">
            <button type="button" class="viz-tab active" data-s="realRare">Raras reales</button>
            <button type="button" class="viz-tab" data-s="realCommon">No raras reales</button>
            <button type="button" class="viz-tab" data-s="realcases">Reales, conjunto</button>
            <button type="button" class="viz-tab" data-s="total">Total</button>
          </div>
          <div class="viz-tabs" id="mc-k-tabs">
            <button type="button" class="viz-tab active" data-k="1">R@1</button>
            <button type="button" class="viz-tab" data-k="5">R@5</button>
          </div>
        </div>
        <div class="viz-panel-sub">Casos que el modelo acierta y Terra 5.6 no (derecha) y al revés (izquierda). p de McNemar exacto:
          por debajo de 0,05 la diferencia difícilmente es casualidad.</div>
        <div class="svg-wrap"><svg id="mc-svg" class="svg-chart" viewBox="0 0 680 300" role="img" aria-label="Casos ganados y perdidos frente a Terra 5.6"></svg></div>
        <div class="viz-legend">
          <span class="viz-legend-item"><span class="viz-swatch" style="background:#2a78d6"></span>Acierta el modelo, falla Terra 5.6</span>
          <span class="viz-legend-item"><span class="viz-swatch" style="background:#e34948"></span>Acierta Terra 5.6, falla el modelo</span>
        </div>
      </div>
      <div class="viz-panel" style="margin-top:20px">
        <div class="viz-panel-title"><span>Acierto frente a latencia</span>
          <div class="viz-tabs" id="scatter-tabs">
            <button type="button" class="viz-tab active" data-k="r1">R@1</button>
            <button type="button" class="viz-tab" data-k="r5">R@5</button>
          </div>
        </div>
        <div class="viz-panel-sub">Casos reales. Latencia: mediana por caso con 8 llamadas en paralelo (4 en Opus), incluida la traducción de <code>urg</code>. Escala logarítmica.</div>
        <div class="svg-wrap"><svg id="scatter-svg" class="svg-chart" viewBox="0 0 680 320" role="img" aria-label="Acierto en casos reales frente a latencia"></svg></div>
      </div>
    </div>

    <div class="viz-panel" style="margin-top:20px">
      <div class="viz-panel-title"><span>En qué posición acierta cada modelo</span>
        <div class="viz-tabs" id="stack-tabs">
          <button type="button" class="viz-tab active" data-g="realcases">Casos reales</button>
          <button type="button" class="viz-tab" data-g="realRare">Raras reales</button>
          <button type="button" class="viz-tab" data-g="realCommon">No raras reales</button>
          <button type="button" class="viz-tab" data-g="total">Total</button>
          <button type="button" class="viz-tab" data-g="live">live</button>
          <button type="button" class="viz-tab" data-g="urg">urg</button>
          <button type="button" class="viz-tab" data-g="exam">exam</button>
        </div>
      </div>
      <div class="viz-panel-sub">Cada barra es el 100 % de los casos del bloque; el hueco gris del final son los casos sin acierto estricto.
        Claude Opus 5 da listas de unas 10 opciones, por eso es el único con aciertos en P6 o más.</div>
      <div class="viz-legend" style="margin:0 0 10px">
        <span class="viz-legend-item"><span class="viz-swatch" style="background:#1c5cab"></span>P1</span>
        <span class="viz-legend-item"><span class="viz-swatch" style="background:#3987e5"></span>P2–P3</span>
        <span class="viz-legend-item"><span class="viz-swatch" style="background:#86b6ef"></span>P4–P5</span>
        <span class="viz-legend-item"><span class="viz-swatch" style="background:#b7d3f6"></span>P6 o más</span>
        <span class="viz-legend-item"><span class="viz-swatch" style="background:#f1f5f9;border:1px solid #e2e8f0"></span>Sin acierto</span>
      </div>
      <div id="stack-container"></div>
    </div>

    <h3>Tabla completa (300 casos)</h3>
    <div class="table-scroll">
    <table class="num">
      <thead><tr><th>Modelo</th><th>R@1</th><th>R@3</th><th>R@5</th><th>Cobertura</th><th>Pos. media</th>
        <th>R@1 casos reales</th><th>R@5 laxa</th><th>Opciones (mediana)</th><th>s/caso</th><th>Coste juez</th></tr></thead>
      <tbody>
{models_table(data)}
      </tbody>
    </table>
    </div>
    <p class="note">Cobertura = acierto en cualquier posición; con listas de distinta longitud solo R@1 y R@5 son comparables.
      Juez: {sum(m['judgeCalls'] for m in data['models'])} llamadas, ≈ {num(judge_cost, 0)} $ los seis runs,
      {sum(m['judgeErrors'] for m in data['models'])} casos con error del juez. Runs:
      {', '.join(f"{m['model']} <code>{m['run']}</code>" for m in data['models'])}.</p>

    <h3>Diferencia con Terra 5.6 en casos reales (210 casos)</h3>
    <div class="table-scroll">
    <table class="num">
      <thead><tr><th>Modelo</th><th>R@1 gana / pierde</th><th>Neto</th><th>p</th><th>R@5 gana / pierde</th><th>Neto</th><th>p</th></tr></thead>
      <tbody>
{mcnemar_table(data)}
      </tbody>
    </table>
    </div>
  </div>

{rerun_section(data)}
  <div class="section">
    <div class="section-title">Contaminación · ¿pudo ver el modelo los casos <code>live</code>?</div>
    <div class="callout callout-info">
      El bloque <code>live</code> se eligió por fecha de entrada en PubMed (desde el 1-jul-2026), pero muchas revistas publican
      online antes. Abajo, cada caso por su <strong>primera fecha pública</strong> y las fechas de corte que declaran los
      proveedores. gemini-3.1-pro-preview (ene-2025) y gpt-5.4-mini (ago-2025) quedan fuera del gráfico, a la izquierda.
    </div>
    <div class="viz-panel">
      <div class="viz-panel-title"><span>Casos <code>live</code> por mes y cortes de los modelos</span></div>
      <div class="viz-panel-sub">Barras: casos por mes de primera publicación (online, PubMed o PMC). Líneas verticales: fin del mes de corte de cada modelo.
        Lo que queda a la izquierda de la línea de un modelo pudo estar en su entrenamiento.</div>
      <div class="svg-wrap"><svg id="timeline-svg" class="svg-chart" viewBox="0 0 680 300" role="img" aria-label="Casos live por mes de publicación y cortes de los modelos"></svg></div>
    </div>
    <h3>Fechas de corte</h3>
    <div class="table-scroll">
    <table>
      <thead><tr><th>Modelo</th><th>Corte</th><th>Lanzado</th><th><code>live</code> sin ver (entrada en PubMed)</th><th><code>live</code> sin ver (primera publicación)</th><th>Fuente</th></tr></thead>
      <tbody>
{cutoffs_table(data)}
      </tbody>
    </table>
    </div>
    <p class="note">Ningún modelo declara un corte posterior a junio de 2026. Sin los casos que pudo ver, el R@1 de cada modelo en
      <code>live</code> cambia 1–2 puntos y no a su favor: gpt-6.1-terra acierta {pct(models['terra61']['groups']['liveUnseen']['r1'])}
      en los {models['terra61']['groups']['liveUnseen']['n']} casos que no pudo ver y {pct(models['terra61']['groups']['live']['r1'])} en todo
      <code>live</code>. Una fecha de corte es lo que declara el proveedor; no descarta preprints.</p>
  </div>

{effort_section(data)}
{n5_section(data)}
{poc_section(data)}
{judges_section(data)}
{graded_v3_section(data)}
  <div class="section">
    <div class="section-title">Raras HPO v2 · Terra 5.6 low · 3.006 casos</div>
    <div class="callout callout-info">
      Mismas listas de Terra que el benchmark HPO strict de septiembre; solo cambian el evaluador y lo que se acepta como correcto.
      En raras el modelo solo ve una lista de síntomas, nunca un estudio genético, pero muchos gold llevan el gen en el nombre.
      <ul style="margin:8px 0 0 20px">
        <li><strong>V4 strict</strong>: el informe de septiembre.</li>
        <li><strong>V5, gold con gen (original)</strong>: solo vale el diagnóstico tal como venía en el dataset, con su gen.</li>
        <li><strong>V5, gold con gen o sin gen (v2)</strong>: el mismo run, pero vale también el nombre de la enfermedad sin gen.</li>
      </ul>
      Las tres columnas, sobre los 3.006 casos que quedan tras quitar los 11 de gold dudoso de T3. Solo se aplica a raras:
      en <code>narrative_v2</code> el gold ya está al nivel de enfermedad.
    </div>
{gene_explainer(data)}
    <div class="viz-panel">
      <div class="viz-panel-title"><span>Acierto por dataset con cada evaluación</span>
        <div class="viz-tabs" id="hpo-tabs">
          <button type="button" class="viz-tab active" data-k="r1">R@1</button>
          <button type="button" class="viz-tab" data-k="r5">R@5</button>
        </div>
      </div>
      <div class="viz-panel-sub">DDD y LIRICAL son los datasets con gen o subtipo genético en el gold: ahí es donde aceptar el nombre sin gen cambia la nota.</div>
      <div class="svg-wrap"><svg id="hpo-svg" class="svg-chart" viewBox="0 0 680 320" role="img" aria-label="Acierto HPO por dataset con V4 strict, V5 con gold con gen y V5 con gold con gen o sin gen"></svg></div>
      <div class="viz-legend">
        <span class="viz-legend-item"><span class="viz-swatch" style="background:#94a3b8"></span>V4 strict (sept)</span>
        <span class="viz-legend-item"><span class="viz-swatch" style="background:#86b6ef"></span>V5, gold con gen (original)</span>
        <span class="viz-legend-item"><span class="viz-swatch" style="background:#1c5cab"></span>V5, gold con gen o sin gen (v2)</span>
      </div>
    </div>
    <div class="table-scroll">
    <table class="num">
      <thead><tr><th>Dataset</th><th>Casos</th><th>Con nombre sin gen</th><th>R@1 V4</th><th>R@1 V5 con gen</th><th>R@1 V5 con o sin gen</th>
        <th>R@5 V4</th><th>R@5 V5 con gen</th><th>R@5 V5 con o sin gen</th></tr></thead>
      <tbody>
{hpo_table(data)}
      </tbody>
    </table>
    </div>
    <div class="callout callout-warn">
      <strong>DDD se lee en dos partes.</strong> En los {thousands(ddd['split']['withClinical']['n'])} casos con nombre sin gen, R@1 pasa de
      {pct(ddd['split']['withClinical']['orig']['r1'])} a {pct(ddd['split']['withClinical']['v2']['r1'])}. A los
      {ddd['split']['withoutClinical']['n']} restantes no se les añadió nombre sin gen, porque quedaría un rasgo genérico (de «SETD5-related
      intellectual disability» quedaría «intellectual disability») o el nombre ya está en la lista HPO. Se quedan en
      {pct(ddd['split']['withoutClinical']['v2']['r1'])}: sin estudio genético no tienen un diagnóstico propio.
      Los nombres sin gen los propuso Gemini 2.5 Pro y están pendientes de revisión clínica.
      Juez: {thousands(hpo_total['judgeCalls'])} llamadas, ≈ {num(hpo_total['judgeCost'], 0)} $.
    </div>
  </div>

{hpo_sol_section(data)}
{hpo_opus_section(data)}
{hpo_syn_section(data)}
{hpo_sermas_section(data)}
  <div class="section">
    <div class="section-title">Serie histórica · all_256_clean</div>
    <div class="table-scroll">
    <table class="num">
      <thead><tr><th>Modelo</th><th>Evaluación</th><th>R@1</th><th>R@3</th><th>R@5</th></tr></thead>
      <tbody>
{all256_table()}
      </tbody>
    </table>
    </div>
    <p class="note"><code>all_256_clean</code> queda como serie histórica con V4 strict: el 63 % son preguntas de examen y 24 gold no son una enfermedad.
      El resto de modelos está en <a href="benchmark-report-strict-texto.html">el informe strict de texto</a>.</p>
  </div>
</div>
<footer>Borrador interno · Pipeline V5 · generado con <code>bench/pipelines/pipeline_v5/main/build_report.py</code> el {today.isoformat()}</footer>
<div id="viz-tooltip" class="viz-tooltip"></div>
<script>
var DATA = {js_data};
{CHART_JS}
</script>
</body>
</html>
'''


CHART_JS = r'''
(function () {
  var MODELS = DATA.models;
  var byId = {};
  MODELS.forEach(function (m) { byId[m.id] = m; });
  var INK = '#1e293b', MUTED = '#64748b', GRID = '#e2e8f0', AXIS = '#cbd5e1';

  function f1(v) { return v == null ? '—' : v.toFixed(1).replace('.', ','); }
  function pc(v) { return v == null ? '—' : f1(v) + ' %'; }
  function esc(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;'); }

  var tooltip = document.getElementById('viz-tooltip');
  function showTip(evt, html) {
    tooltip.innerHTML = html;
    tooltip.style.opacity = '1';
    var x = evt.clientX + 14, y = evt.clientY + 14;
    if (x + 290 > window.innerWidth) x = evt.clientX - 295;
    if (y + 150 > window.innerHeight) y = evt.clientY - 150;
    tooltip.style.left = x + 'px';
    tooltip.style.top = y + 'px';
  }
  function hideTip() { tooltip.style.opacity = '0'; }
  function bindTips(svg, selector, html) {
    Array.prototype.forEach.call(svg.querySelectorAll(selector), function (el) {
      el.addEventListener('mousemove', function (e) { showTip(e, html(el)); });
      el.addEventListener('mouseleave', hideTip);
    });
  }
  function tabs(id, onSelect) {
    var root = document.getElementById(id);
    root.addEventListener('click', function (e) {
      var btn = e.target.closest('.viz-tab');
      if (!btn) return;
      Array.prototype.forEach.call(root.querySelectorAll('.viz-tab'), function (b) { b.classList.remove('active'); });
      btn.classList.add('active');
      onSelect(btn);
    });
  }
  function text(x, y, s, opts) {
    opts = opts || {};
    return '<text x="' + x.toFixed(1) + '" y="' + y.toFixed(1) + '" text-anchor="' + (opts.anchor || 'start') +
      '" fill="' + (opts.fill || INK) + '" font-size="' + (opts.size || 11) + '"' +
      (opts.weight ? ' font-weight="' + opts.weight + '"' : '') + '>' + s + '</text>';
  }

  // 1) Dumbbell: real cases vs exam
  var dumbK = 'r1';
  function renderDumbbell() {
    var svg = document.getElementById('dumbbell-svg');
    var W = 680, padL = 190, padR = 40, padT = 30, row = 44, H = padT + row * MODELS.length + 36;
    svg.setAttribute('viewBox', '0 0 ' + W + ' ' + H);
    var x0 = 30, x1 = 100;
    function sx(v) { return padL + (v - x0) / (x1 - x0) * (W - padL - padR); }
    var rows = MODELS.slice().sort(function (a, b) { return b.groups.realcases[dumbK] - a.groups.realcases[dumbK]; });
    var out = [];
    for (var t = 30; t <= 100; t += 10) {
      out.push('<line x1="' + sx(t) + '" y1="' + (padT - 8) + '" x2="' + sx(t) + '" y2="' + (H - 30) + '" stroke="' + GRID + '"/>');
      out.push(text(sx(t), H - 12, t + ' %', { anchor: 'middle', fill: MUTED, size: 10.5 }));
    }
    rows.forEach(function (m, i) {
      var y = padT + i * row + row / 2;
      var real = m.groups.realcases[dumbK], exam = m.groups.exam[dumbK];
      out.push(text(padL - 14, y + 4, esc(m.name), { anchor: 'end', weight: m.id === 'terra56' ? 700 : 600 }));
      out.push('<line x1="' + sx(real) + '" y1="' + y + '" x2="' + sx(exam) + '" y2="' + y + '" stroke="' + m.color + '" stroke-width="2" opacity="0.6"/>');
      out.push('<circle cx="' + sx(exam) + '" cy="' + y + '" r="6" fill="#fff" stroke="' + m.color + '" stroke-width="2.5"/>');
      out.push('<circle cx="' + sx(real) + '" cy="' + y + '" r="6.5" fill="' + m.color + '" stroke="#fff" stroke-width="2"/>');
      out.push(text(sx(real) - 11, y + 4, pc(real), { anchor: 'end', size: 10.5, weight: 700 }));
      out.push(text(sx(exam) + 11, y + 4, pc(exam), { anchor: 'start', size: 10.5, fill: MUTED }));
      out.push('<rect class="hit" data-id="' + m.id + '" x="0" y="' + (y - row / 2) + '" width="' + W + '" height="' + row + '" fill="transparent"/>');
    });
    svg.innerHTML = out.join('');
    bindTips(svg, '.hit', function (el) {
      var m = byId[el.getAttribute('data-id')], k = dumbK === 'r1' ? 'R@1' : 'R@5';
      return '<strong>' + esc(m.name) + '</strong><br>' + k + ' casos reales: <b>' + pc(m.groups.realcases[dumbK]) + '</b> (n=210)<br>' +
        k + ' examen: <b>' + pc(m.groups.exam[dumbK]) + '</b> (n=60)<br>Diferencia: ' + f1(m.groups.exam[dumbK] - m.groups.realcases[dumbK]) + ' puntos';
    });
  }
  tabs('dumbbell-tabs', function (b) { dumbK = b.getAttribute('data-k'); renderDumbbell(); });

  // 2) Heat table by block
  var heatK = 'r1';
  var HEAT_COLS = [['realRare', 'Raras reales'], ['realCommon', 'No raras reales'], ['realcases', 'live+urg'], ['total', 'Total'],
                   ['live', 'live'], ['urg', 'urg'], ['exam', 'exam'],
                   ['synth', 'synth'], ['rare', 'Raras'], ['common', 'No raras'], ['liveUnseen', 'live sin ver']];
  var RAMP = ['#cde2fb', '#b7d3f6', '#9ec5f4', '#86b6ef', '#6da7ec', '#5598e7', '#3987e5', '#2a78d6', '#256abf', '#1c5cab', '#184f95'];
  function renderHeat() {
    var vals = [];
    MODELS.forEach(function (m) { HEAT_COLS.forEach(function (c) { vals.push(m.groups[c[0]][heatK]); }); });
    var lo = Math.min.apply(null, vals), hi = Math.max.apply(null, vals);
    var head = '<thead><tr><th>Modelo</th>' + HEAT_COLS.map(function (c) {
      return '<th>' + c[1] + '<br><span style="font-weight:400;text-transform:none">n=' + MODELS[0].groups[c[0]].n + (c[0] === 'liveUnseen' ? '*' : '') + '</span></th>';
    }).join('') + '</tr></thead>';
    var body = MODELS.map(function (m) {
      return '<tr><td><span class="dot" style="background:' + m.color + '"></span> ' + esc(m.name) + '</td>' + HEAT_COLS.map(function (c) {
        var g = m.groups[c[0]], v = g[heatK];
        var idx = Math.round((v - lo) / Math.max(1, hi - lo) * (RAMP.length - 1));
        var fg = idx >= 6 ? '#ffffff' : INK;
        var title = c[0] === 'liveUnseen' ? ' title="' + g.n + ' casos sin ver"' : '';
        return '<td style="background:' + RAMP[idx] + ';color:' + fg + '"' + title + '>' + f1(v) + '</td>';
      }).join('') + '</tr>';
    }).join('');
    document.getElementById('heat-table').innerHTML = head + '<tbody>' + body + '</tbody>' +
      '<caption style="caption-side:bottom;text-align:left;font-size:0.76rem;color:' + MUTED + ';padding-top:8px">Porcentajes. ' +
      '* «live sin ver» tiene n distinto por modelo: ' + MODELS.map(function (m) { return esc(m.model) + ' ' + m.groups.liveUnseen.n; }).join(', ') + '.</caption>';
  }
  tabs('heat-tabs', function (b) { heatK = b.getAttribute('data-k'); renderHeat(); });

  // 3) Wins / losses vs Terra 5.6
  var mcSubset = 'realRare', mcK = '1';
  function renderMc() {
    var svg = document.getElementById('mc-svg');
    var block = DATA.mcnemar[mcSubset + '_r' + mcK];
    var rows = block.rows.slice().sort(function (a, b) { return (b.wins - b.losses) - (a.wins - a.losses); });
    var W = 680, padL = 210, padR = 30, padT = 24, row = 46, H = padT + row * rows.length + 34;
    svg.setAttribute('viewBox', '0 0 ' + W + ' ' + H);
    var maxV = Math.max.apply(null, rows.map(function (r) { return Math.max(r.wins, r.losses); }));
    maxV = Math.ceil((maxV + 4) / 10) * 10;
    var mid = padL + (W - padL - padR) / 2, half = (W - padL - padR) / 2;
    function len(v) { return v / maxV * half; }
    var out = [];
    [-maxV, -maxV / 2, 0, maxV / 2, maxV].forEach(function (t) {
      var x = mid + len(t);
      out.push('<line x1="' + x + '" y1="' + (padT - 6) + '" x2="' + x + '" y2="' + (H - 28) + '" stroke="' + (t === 0 ? AXIS : GRID) + '"/>');
      out.push(text(x, H - 10, Math.abs(t), { anchor: 'middle', fill: MUTED, size: 10 }));
    });
    rows.forEach(function (r, i) {
      var m = byId[r.id], y = padT + i * row;
      var sig = r.p < 0.05;
      out.push(text(padL - 12, y + 16, esc(m.name), { anchor: 'end', weight: 600 }));
      out.push(text(padL - 12, y + 30, 'neto ' + (r.net > 0 ? '+' : '') + f1(r.net) + ' pp · p ' + (r.p < 0.001 ? '< 0,001' : '= ' + r.p.toFixed(r.p < 0.01 ? 3 : 2).replace('.', ',')),
        { anchor: 'end', fill: sig ? INK : MUTED, size: 10, weight: sig ? 700 : 400 }));
      var bw = 14, yb = y + 8;
      out.push('<rect x="' + (mid + 1) + '" y="' + yb + '" width="' + Math.max(0, len(r.wins) - 1) + '" height="' + bw + '" rx="4" fill="#2a78d6"/>');
      out.push('<rect x="' + (mid - len(r.losses)) + '" y="' + yb + '" width="' + Math.max(0, len(r.losses) - 1) + '" height="' + bw + '" rx="4" fill="#e34948"/>');
      out.push(text(mid + len(r.wins) + 5, yb + 11, r.wins, { size: 10, fill: MUTED }));
      out.push(text(mid - len(r.losses) - 5, yb + 11, r.losses, { anchor: 'end', size: 10, fill: MUTED }));
      out.push('<rect class="hit" data-id="' + r.id + '" x="0" y="' + y + '" width="' + W + '" height="' + row + '" fill="transparent"/>');
    });
    svg.innerHTML = out.join('');
    bindTips(svg, '.hit', function (el) {
      var r = block.rows.filter(function (x) { return x.id === el.getAttribute('data-id'); })[0], m = byId[r.id];
      return '<strong>' + esc(m.name) + '</strong> frente a Terra 5.6 (n=' + block.n + ', R@' + mcK + ')<br>' +
        'Acierta solo el modelo: <b>' + r.wins + '</b><br>Acierta solo Terra 5.6: <b>' + r.losses + '</b><br>' +
        'Neto: ' + (r.net > 0 ? '+' : '') + f1(r.net) + ' puntos · p = ' + r.p.toString().replace('.', ',');
    });
  }
  tabs('mc-subset-tabs', function (b) { mcSubset = b.getAttribute('data-s'); renderMc(); });
  tabs('mc-k-tabs', function (b) { mcK = b.getAttribute('data-k'); renderMc(); });

  // 4) Scatter: real-case accuracy vs latency
  var scK = 'r1';
  function renderScatter() {
    var svg = document.getElementById('scatter-svg');
    var W = 680, H = 320, padL = 52, padR = 30, padT = 18, padB = 44;
    var ys = MODELS.map(function (m) { return m.groups.realcases[scK]; });
    var y0 = Math.floor((Math.min.apply(null, ys) - 4) / 5) * 5, y1 = Math.ceil((Math.max.apply(null, ys) + 3) / 5) * 5;
    var lx0 = Math.log10(3), lx1 = Math.log10(40);
    function sx(v) { return padL + (Math.log10(v) - lx0) / (lx1 - lx0) * (W - padL - padR); }
    function sy(v) { return padT + (1 - (v - y0) / (y1 - y0)) * (H - padT - padB); }
    var out = [];
    for (var t = y0; t <= y1; t += 5) {
      out.push('<line x1="' + padL + '" y1="' + sy(t) + '" x2="' + (W - padR) + '" y2="' + sy(t) + '" stroke="' + GRID + '"/>');
      out.push(text(padL - 8, sy(t) + 4, t + ' %', { anchor: 'end', fill: MUTED, size: 10 }));
    }
    [3, 5, 10, 20, 30].forEach(function (t) {
      out.push('<line x1="' + sx(t) + '" y1="' + padT + '" x2="' + sx(t) + '" y2="' + (H - padB) + '" stroke="' + GRID + '"/>');
      out.push(text(sx(t), H - padB + 16, t + ' s', { anchor: 'middle', fill: MUTED, size: 10 }));
    });
    out.push(text(padL + (W - padL - padR) / 2, H - 6, 'Latencia mediana por caso (s, escala log)', { anchor: 'middle', fill: '#475569', size: 10.5, weight: 600 }));
    var placed = [];
    MODELS.slice().sort(function (a, b) { return a.latency - b.latency; }).forEach(function (m) {
      var cx = sx(m.latency), cy = sy(m.groups.realcases[scK]);
      out.push('<circle cx="' + cx.toFixed(1) + '" cy="' + cy.toFixed(1) + '" r="6.5" fill="' + m.color + '" stroke="#fff" stroke-width="2"/>');
      var label = esc(m.model), w = label.length * 5.6;
      var cands = [[10, 4, 'start'], [-10, 4, 'end'], [0, -12, 'middle'], [0, 19, 'middle'], [10, -9, 'start'], [-10, -9, 'end'], [10, 16, 'start'], [-10, 16, 'end']];
      var best = cands[0];
      for (var i = 0; i < cands.length; i++) {
        var c = cands[i], x1b = c[2] === 'start' ? cx + c[0] : (c[2] === 'end' ? cx + c[0] - w : cx - w / 2), y1b = cy + c[1] - 10;
        var clash = x1b < padL || x1b + w > W - padR || placed.some(function (p) { return x1b < p[2] && x1b + w > p[0] && y1b < p[3] && y1b + 12 > p[1]; });
        if (!clash) { best = c; break; }
      }
      var bx = best[2] === 'start' ? cx + best[0] : (best[2] === 'end' ? cx + best[0] - w : cx - w / 2);
      placed.push([bx, cy + best[1] - 10, bx + w, cy + best[1] + 2]);
      out.push('<text x="' + (cx + best[0]).toFixed(1) + '" y="' + (cy + best[1]).toFixed(1) + '" text-anchor="' + best[2] + '" fill="' + INK +
        '" font-size="10.5" font-weight="600" stroke="#fff" stroke-width="3" paint-order="stroke">' + label + '</text>');
      out.push('<circle class="hit" data-id="' + m.id + '" cx="' + cx.toFixed(1) + '" cy="' + cy.toFixed(1) + '" r="14" fill="transparent"/>');
    });
    svg.innerHTML = out.join('');
    bindTips(svg, '.hit', function (el) {
      var m = byId[el.getAttribute('data-id')];
      return '<strong>' + esc(m.name) + '</strong><br>R@1 casos reales: <b>' + pc(m.groups.realcases.r1) + '</b> · R@5: <b>' + pc(m.groups.realcases.r5) +
        '</b><br>Latencia mediana: ' + f1(m.latency) + ' s · opciones por caso: ' + m.options;
    });
  }
  tabs('scatter-tabs', function (b) { scK = b.getAttribute('data-k'); renderScatter(); });

  // 5) Position breakdown
  var stackG = 'realcases';
  function renderStack() {
    var rows = MODELS.slice().sort(function (a, b) { return b.groups[stackG].r1 - a.groups[stackG].r1; });
    var el = document.getElementById('stack-container');
    el.innerHTML = rows.map(function (m) {
      var g = m.groups[stackG], n = g.n;
      var segs = [[g.p1, '#1c5cab'], [g.p23, '#3987e5'], [g.p45, '#86b6ef'], [g.p6p, '#b7d3f6']];
      return '<div class="stack-row" data-id="' + m.id + '"><div class="stack-label"><span class="dot" style="background:' + m.color + '"></span> ' + esc(m.name) + '</div>' +
        '<div class="stack-track">' + segs.filter(function (s) { return s[0] > 0; }).map(function (s) {
          return '<div class="stack-seg" style="width:' + (s[0] / n * 100).toFixed(2) + '%;background:' + s[1] + '"></div>';
        }).join('') + '</div><div class="stack-val">R@1 ' + f1(g.r1) + ' · R@5 ' + f1(g.r5) + '</div></div>';
    }).join('');
    Array.prototype.forEach.call(el.querySelectorAll('.stack-row'), function (row) {
      row.addEventListener('mousemove', function (e) {
        var m = byId[row.getAttribute('data-id')], g = m.groups[stackG];
        showTip(e, '<strong>' + esc(m.name) + '</strong> (n=' + g.n + ')<br>P1: <b>' + g.p1 + '</b> → R@1 ' + pc(g.r1) +
          '<br>P2–P3: +' + g.p23 + ' → R@3 ' + pc(g.r3) + '<br>P4–P5: +' + g.p45 + ' → R@5 ' + pc(g.r5) +
          (g.p6p ? '<br>P6 o más: +' + g.p6p : '') + '<br>Sin acierto: ' + (g.n - g.p1 - g.p23 - g.p45 - g.p6p));
      });
      row.addEventListener('mouseleave', hideTip);
    });
  }
  tabs('stack-tabs', function (b) { stackG = b.getAttribute('data-g'); renderStack(); });

  // 6) Live cases by month and model cutoffs
  function renderTimeline() {
    var svg = document.getElementById('timeline-svg');
    var months = ['2026-01', '2026-02', '2026-03', '2026-04', '2026-05', '2026-06', '2026-07', '2026-08', '2026-09', '2026-10'];
    var names = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct'];
    var W = 680, H = 300, padL = 44, padR = 20, padT = 70, padB = 40;
    var counts = months.map(function (m) { return DATA.liveMonths.firstPublic[m] || 0; });
    var maxC = Math.ceil(Math.max.apply(null, counts) / 10) * 10;
    var slot = (W - padL - padR) / months.length;
    function sy(v) { return padT + (1 - v / maxC) * (H - padT - padB); }
    var out = [];
    for (var t = 0; t <= maxC; t += 10) {
      out.push('<line x1="' + padL + '" y1="' + sy(t) + '" x2="' + (W - padR) + '" y2="' + sy(t) + '" stroke="' + GRID + '"/>');
      out.push(text(padL - 8, sy(t) + 4, t, { anchor: 'end', fill: MUTED, size: 10 }));
    }
    months.forEach(function (m, i) {
      var c = counts[i], x = padL + i * slot + 6, w = slot - 12;
      if (c > 0) out.push('<rect class="hit-bar" data-m="' + m + '" x="' + x + '" y="' + sy(c) + '" width="' + w + '" height="' + (sy(0) - sy(c)) + '" rx="4" fill="#64748b"/>');
      if (c > 0) out.push(text(x + w / 2, sy(c) - 5, c, { anchor: 'middle', fill: MUTED, size: 10 }));
      out.push(text(x + w / 2, H - padB + 16, names[i], { anchor: 'middle', fill: MUTED, size: 10.5 }));
    });
    function monthEnd(cut) { var i = months.indexOf(cut); return i < 0 ? null : padL + (i + 1) * slot; }
    var xLive = monthEnd('2026-06');
    out.unshift('<rect x="' + xLive + '" y="' + (padT - 4) + '" width="' + (W - padR - xLive) + '" height="' + (sy(0) - padT + 4) + '" fill="#f1f5f9"/>');
    out.push(text(W - padR - 6, padT + 10, 'Entrada en PubMed del bloque live (desde 1-jul)', { anchor: 'end', size: 10, fill: '#475569', weight: 600 }));
    var cuts = MODELS.filter(function (m) { return monthEnd(m.cutoff) !== null; }).sort(function (a, b) { return a.cutoff < b.cutoff ? -1 : 1; });
    var labels = [];
    cuts.forEach(function (m, lvl) {
      var x = monthEnd(m.cutoff);
      var yLab = 14 + lvl * 14;
      out.push('<line x1="' + x + '" y1="' + (yLab + 4) + '" x2="' + x + '" y2="' + sy(0) + '" stroke="' + m.color + '" stroke-width="2.5"/>');
      out.push('<circle cx="' + x + '" cy="' + (yLab - 3) + '" r="4" fill="' + m.color + '"/>');
      labels.push('<text x="' + (x - 7) + '" y="' + (yLab + 1) + '" text-anchor="end" fill="' + INK + '" font-size="10" font-weight="600" ' +
        'stroke="#fff" stroke-width="3" paint-order="stroke">' + esc(m.model) + ' (corte ' + m.cutoff + ')</text>');
    });
    out = out.concat(labels);
    svg.innerHTML = out.join('');
    bindTips(svg, '.hit-bar', function (el) {
      var m = el.getAttribute('data-m');
      var seen = MODELS.filter(function (x) { return x.cutoff && x.cutoff >= m; }).map(function (x) { return esc(x.model); });
      return '<strong>' + m + '</strong><br>' + DATA.liveMonths.firstPublic[m] + ' casos publicados por primera vez ese mes<br>' +
        (seen.length ? 'Dentro del corte de: ' + seen.join(', ') : 'Después del corte de todos los modelos');
    });
  }

  // 7) HPO grouped bars
  var hpoK = 'r1';
  function renderHpo() {
    var svg = document.getElementById('hpo-svg');
    var rows = DATA.hpo.concat([DATA.hpoTotal]);
    var series = [['v4', '#94a3b8', 'V4 strict'], ['v5orig', '#86b6ef', 'V5, gold con gen'], ['v5v2', '#1c5cab', 'V5, gold con gen o sin gen']];
    var W = 680, H = 320, padL = 44, padR = 16, padT = 20, padB = 44;
    var maxV = 80;
    var slot = (W - padL - padR) / rows.length, bw = (slot - 22) / 3;
    function sy(v) { return padT + (1 - v / maxV) * (H - padT - padB); }
    var out = [];
    for (var t = 0; t <= maxV; t += 20) {
      out.push('<line x1="' + padL + '" y1="' + sy(t) + '" x2="' + (W - padR) + '" y2="' + sy(t) + '" stroke="' + (t === 0 ? AXIS : GRID) + '"/>');
      out.push(text(padL - 8, sy(t) + 4, t + ' %', { anchor: 'end', fill: MUTED, size: 10 }));
    }
    rows.forEach(function (r, i) {
      var x0 = padL + i * slot + 11;
      series.forEach(function (s, j) {
        var v = r[s[0]][hpoK], x = x0 + j * bw;
        out.push('<rect class="hit-bar" data-i="' + i + '" x="' + (x + 1).toFixed(1) + '" y="' + sy(v).toFixed(1) + '" width="' + (bw - 2).toFixed(1) +
          '" height="' + (sy(0) - sy(v)).toFixed(1) + '" rx="3" fill="' + s[1] + '"/>');
        if (r.label === 'Total' || r.key === 'ddd_hpo' || r.key === 'lirical_hpo') {
          out.push(text(x + bw / 2, sy(v) - 4, Math.round(v), { anchor: 'middle', size: 9.5, fill: j === 2 ? INK : MUTED, weight: j === 2 ? 700 : 400 }));
        }
      });
      out.push(text(x0 + bw * 1.5, H - padB + 16, r.label, { anchor: 'middle', fill: r.label === 'Total' ? INK : MUTED, size: 10.5, weight: r.label === 'Total' ? 700 : 400 }));
      out.push(text(x0 + bw * 1.5, H - padB + 29, 'n=' + r.n.toLocaleString('es-ES'), { anchor: 'middle', fill: MUTED, size: 9 }));
    });
    svg.innerHTML = out.join('');
    bindTips(svg, '.hit-bar', function (el) {
      var r = rows[+el.getAttribute('data-i')], k = hpoK === 'r1' ? 'R@1' : 'R@5';
      return '<strong>' + r.label + '</strong> (n=' + r.n.toLocaleString('es-ES') + ', ' + r.nClinical.toLocaleString('es-ES') + ' con nombre sin gen)<br>' +
        series.map(function (s) { return s[2] + ': <b>' + pc(r[s[0]][hpoK]) + '</b>'; }).join('<br>') + '<br>' + k + ' estricta';
    });
  }
  tabs('hpo-tabs', function (b) { hpoK = b.getAttribute('data-k'); renderHpo(); });

  // 8) Same lists, several judges
  var judgeK = 'r1';
  function renderJudges() {
    var J = DATA.judges;
    var svg = document.getElementById('judge-svg');
    if (!J || !svg) return;
    var block = J.recall['realcases_' + judgeK];
    var W = 680, padL = 170, padR = 30, padT = 20, row = 44, H = padT + row * J.models.length + 36;
    svg.setAttribute('viewBox', '0 0 ' + W + ' ' + H);
    var vals = [];
    J.judges.forEach(function (j) { J.models.forEach(function (m) { vals.push(block.values[j][m]); }); });
    var x0 = Math.floor((Math.min.apply(null, vals) - 3) / 5) * 5, x1 = Math.ceil((Math.max.apply(null, vals) + 3) / 5) * 5;
    function sx(v) { return padL + (v - x0) / (x1 - x0) * (W - padL - padR); }
    var MARK = {
      'gemini-2.5-pro': function (x, y) { return '<circle cx="' + x + '" cy="' + y + '" r="6.5" fill="#1e293b" stroke="#fff" stroke-width="2"/>'; },
      'gemini-3.8-flash': function (x, y) { return '<rect x="' + (x - 5) + '" y="' + (y - 5) + '" width="10" height="10" transform="rotate(45 ' + x + ' ' + y + ')" fill="#fff" stroke="#1e293b" stroke-width="2"/>'; },
      'gemini-2.5-flash': function (x, y) { return '<rect x="' + (x - 4.5) + '" y="' + (y - 4.5) + '" width="9" height="9" fill="#94a3b8" stroke="#fff" stroke-width="1.5"/>'; },
      'claude-opus-5-5': function (x, y) { return '<path d="M' + x + ' ' + (y - 6) + ' L' + (x + 6) + ' ' + (y + 5) + ' L' + (x - 6) + ' ' + (y + 5) + ' Z" fill="#eb6834" stroke="#fff" stroke-width="1.5"/>'; }
    };
    var out = [];
    for (var t = x0; t <= x1; t += 5) {
      out.push('<line x1="' + sx(t) + '" y1="' + (padT - 6) + '" x2="' + sx(t) + '" y2="' + (H - 30) + '" stroke="' + GRID + '"/>');
      out.push(text(sx(t), H - 12, t + ' %', { anchor: 'middle', fill: MUTED, size: 10.5 }));
    }
    block.orders['gemini-2.5-pro'].forEach(function (m, i) {
      var y = padT + i * row + row / 2;
      var xs = J.judges.map(function (j) { return sx(block.values[j][m]); });
      out.push('<line x1="' + Math.min.apply(null, xs) + '" y1="' + y + '" x2="' + Math.max.apply(null, xs) + '" y2="' + y + '" stroke="' + J.colors[m] + '" stroke-width="3" opacity="0.5"/>');
      out.push('<circle cx="' + (padL - 150) + '" cy="' + y + '" r="5" fill="' + J.colors[m] + '"/>');
      out.push(text(padL - 140, y + 4, esc(m), { weight: 600 }));
      J.judges.slice().reverse().forEach(function (j) { if (MARK[j]) out.push(MARK[j](sx(block.values[j][m]), y)); });
      out.push('<rect class="hit" data-m="' + esc(m) + '" x="0" y="' + (y - row / 2) + '" width="' + W + '" height="' + row + '" fill="transparent"/>');
    });
    svg.innerHTML = out.join('');
    bindTips(svg, '.hit', function (el) {
      var m = el.getAttribute('data-m');
      return '<strong>' + esc(m) + '</strong> · casos reales, R@' + judgeK.slice(1) + ' estricta<br>' +
        J.judges.map(function (j) { return esc(j) + ': <b>' + pc(block.values[j][m]) + '</b>'; }).join('<br>');
    });
  }
  if (document.getElementById('judge-tabs')) {
    tabs('judge-tabs', function (b) { judgeK = b.getAttribute('data-k'); renderJudges(); });
  }

  renderJudges();
  renderDumbbell();
  renderHeat();
  renderMc();
  renderScatter();
  renderStack();
  renderTimeline();
  renderHpo();
})();
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default=os.path.join(EVAL_ROOT, 'docs', 'benchmark-report-v5.html'))
    args = parser.parse_args()
    data = collect()
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(build_html(data))
    print(f'Wrote {args.output}')


if __name__ == '__main__':
    main()
