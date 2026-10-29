#!/usr/bin/env python3
"""
Build docs/benchmark-report-v5.html from the Pipeline V5 run outputs
====================================================================

Reads the latest V5 run of each reference model on narrative_v2, the HPO v2
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
import os
import statistics
from datetime import date
from math import comb

import yaml

from score_blocks import load_details, strict_position

HERE = os.path.dirname(os.path.abspath(__file__))
EVAL_ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
OUTPUT_ROOT = os.path.join(HERE, 'output')
NARRATIVE_DIR = os.path.join(OUTPUT_ROOT, 'narrative_v2', 'juanjo_classic_v2')
NARRATIVE_V2 = os.path.join(EVAL_ROOT, 'bench', 'datasets', 'narrative_v2.json')
NARRATIVE_TOOLS = os.path.join(EVAL_ROOT, 'data29', 'data-repos', 'narrative-v2')
JUDGE_AUDIT = os.path.join(EVAL_ROOT, 'bench', 'multimodal_beta', 'outputs', 'judge_audit')
BASELINE = 'terra56'

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
    ('realcases', '<code>live</code>+<code>urg</code>', lambda c: c['metadata']['block'] in ('live', 'urg')),
    ('live', '<code>live</code>', lambda c: c['metadata']['block'] == 'live'),
    ('urg', '<code>urg</code>', lambda c: c['metadata']['block'] == 'urg'),
    ('exam', '<code>exam</code>', lambda c: c['metadata']['block'] == 'exam'),
    ('synth', '<code>synth</code>', lambda c: c['metadata']['block'] == 'synth'),
    ('rare', 'Raras', lambda c: c['metadata'].get('rare_disease') is True),
    ('common', 'No raras', lambda c: c['metadata'].get('rare_disease') is False),
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


def collect():
    with open(NARRATIVE_V2, 'r', encoding='utf-8') as f:
        dataset = {c['id']: c for c in json.load(f)}
    with open(os.path.join(NARRATIVE_TOOLS, 'work', 'live_dates.json'), 'r', encoding='utf-8') as f:
        live_dates = json.load(f)
    with open(os.path.join(NARRATIVE_TOOLS, 'model_cutoffs.yaml'), 'r', encoding='utf-8') as f:
        cutoffs = yaml.safe_load(f)['models']

    data = {'models': [], 'mcnemar': {}, 'cutoffs': [], 'liveMonths': {}, 'hpo': []}
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
            'latency': round(statistics.median(times), 1),
            'options': statistics.median(len(c.get('ddx_details', {})) for c in labeled),
            'judgeCalls': summary['judge']['calls'], 'judgeCost': summary['judge']['estimated_cost_usd'],
            'judgeErrors': len(summary['global']['cases_with_judge_errors']),
            'cutoff': str(cutoffs.get(model, {}).get('cutoff', '')), 'groups': groups,
        })

    for subset in ('realcases', 'total'):
        belongs = dict((k, f) for k, _, f in GROUPS)[subset]
        ids = [i for i, c in dataset.items() if belongs(c)]
        for k in (1, 5):
            rows = []
            for mid, *_ in MODELS:
                if mid == BASELINE:
                    continue
                hit = lambda p: p is not None and p <= k  # noqa: E731
                wins = sum(1 for i in ids if hit(positions[mid][i]) and not hit(positions[BASELINE][i]))
                losses = sum(1 for i in ids if not hit(positions[mid][i]) and hit(positions[BASELINE][i]))
                rows.append({'id': mid, 'wins': wins, 'losses': losses,
                             'net': round(100 * (wins - losses) / len(ids), 1), 'p': round(mcnemar_p(wins, losses), 3)})
            data['mcnemar'][f'{subset}_r{k}'] = {'n': len(ids), 'rows': rows}

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
    summary_r1 = data['mcnemar']['realcases_r1']['rows']
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
      <div class="card"><div class="card-label">Mejor en casos reales</div>
        <div class="card-value">{pct(best['groups']['realcases']['r1'])}</div>
        <div class="card-sub">{best['name']}, R@1 en <code>live</code>+<code>urg</code> (210 casos). {'+' if best_test['net'] > 0 else ''}{num(best_test['net'])} pp sobre Terra 5.6, p = {p_value(best_test['p'])}</div></div>
      <div class="card"><div class="card-label">Línea base (Terra 5.6)</div>
        <div class="card-value">{pct(base['groups']['realcases']['r1'])}</div>
        <div class="card-sub">R@1 en casos reales; {pct(base['groups']['exam']['r1'])} en preguntas de examen</div></div>
      <div class="card"><div class="card-label">Raras HPO v2, Terra 5.6</div>
        <div class="card-value">{pct(hpo_total['v5v2']['r1'])}</div>
        <div class="card-sub">R@1 aceptando también el nombre sin gen; {pct(hpo_total['v4']['r1'])} con V4 strict sobre las mismas listas</div></div>
      <div class="card"><div class="card-label"><code>live</code> no visto</div>
        <div class="card-value">{unseen_min['unseenPublic']}–150</div>
        <div class="card-sub">casos publicados después del corte de cada modelo (el mínimo es {unseen_min['model']})</div></div>
    </div>
    <div class="callout callout-info">
      Cifra principal: <strong>R@1 estricta en casos reales (<code>live</code>+<code>urg</code>)</strong>. <code>exam</code> apenas
      separa a los modelos y <code>synth</code> es demasiado fácil. La nota estricta solo cuenta la misma enfermedad (nota 2 del
      juez); la laxa (2 o 1) es de uso interno. Todo es provisional hasta que David valide <code>narrative_v2</code>: las listas
      no cambiarán, solo se re-puntúan.
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
            <button type="button" class="viz-tab active" data-s="realcases">Casos reales</button>
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

  <div class="section">
    <div class="section-title">Raras HPO v2 · Terra 5.6 low · 3.006 casos</div>
    <div class="callout callout-info">
      Mismas listas de Terra que el benchmark HPO strict de septiembre; solo cambian el evaluador y lo que se acepta como correcto.
      En raras el modelo solo ve una lista de síntomas, nunca un estudio genético, pero muchos gold llevan el gen en el nombre.
      <ul style="margin:8px 0 0 20px">
        <li><strong>V4 strict</strong>: el informe de septiembre.</li>
        <li><strong>V5, gold con gen (original)</strong>: solo vale el diagnóstico tal como venía en el dataset,
            «RPGRIP1-related Leber congenital amaurosis». Si el modelo dice «Leber congenital amaurosis», el juez da un 1 y no es acierto.</li>
        <li><strong>V5, gold con gen o sin gen (v2)</strong>: el mismo run, pero vale también el nombre sin gen,
            «Leber congenital amaurosis». La misma respuesta es un 2 y sí es acierto.</li>
      </ul>
      Las tres columnas, sobre los 3.006 casos que quedan tras quitar los 11 de gold dudoso de T3. Solo se aplica a raras:
      en <code>narrative_v2</code> el gold ya está al nivel de enfermedad.
    </div>
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
  var HEAT_COLS = [['total', 'Total'], ['realcases', 'live+urg'], ['live', 'live'], ['urg', 'urg'], ['exam', 'exam'],
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
  var mcSubset = 'realcases', mcK = '1';
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
