"""MedReaMM pilot250 T+I (Server v0.00196, prompt «5», 3-nov-2026) al formato del evaluador V5:
mismas listas de Sol y de Terra, solo cambia el evaluador (V5, juez Gemini 3.8 Flash, graded_v3).
Gold: solo el diagnóstico principal, como en la evaluación V4 (strict, primary only).

Uso (desde eval/): python bench/pipelines/pipeline_v5/main/medreamm_to_v5.py
y después main.py --config con config_gpt61sol_medreamm250_ti.yaml y config_gpt56terra_medreamm250_ti.yaml.
"""
import json, os, sys
from pathlib import Path

EVAL = Path(__file__).resolve().parents[4]
MM = EVAL / 'bench' / 'multimodal_beta'
DS = MM / 'datasets' / 'processed' / 'medreamm_pilot250'
OUT_ROOT = EVAL / 'bench' / 'pipelines' / 'pipeline_v5' / 'main' / 'output'
DATASET = EVAL / 'bench' / 'datasets' / 'medreamm_pilot250_ti.json'
PROMPT = 'juanjo_classic_v2_n5'
TAG = 'server_v0_00196'
ARMS = {'gpt-6.1-sol_low': 'pilot250_gpt61sol_TI_n5', 'gpt-5.6-terra_low': 'pilot250_gpt56terra_TI_n5'}

def load(folder):
    rows = {}
    with open(MM / 'outputs' / folder / 'responses.jsonl', encoding='utf-8') as f:
        for line in f:
            r = json.loads(line)
            rows[r['case_id']] = r
    return rows

arms = {model: load(folder) for model, folder in ARMS.items()}
ids = sorted(set.intersection(*(set(a) for a in arms.values())))
cases = []
for cid in ids:
    r = arms['gpt-6.1-sol_low'][cid]
    primary = [g for g in r['gold']['diagnoses'] if g.get('role') == 'primary'] or r['gold']['diagnoses'][:1]
    cases.append({
        'id': cid,
        'case': (DS / cid / 'history.txt').read_text(encoding='utf-8').strip(),
        'complexity': None,
        'diagnoses': [{'name': g['name'], 'role': 'primary', 'accepted_names': [], 'medical_codes': {}} for g in primary],
        'metadata': {'source': 'MedReaMM', 'condition': 'T+I', 'image_count': r['metadata'].get('image_count'),
                     'classification': r['metadata'].get('classification')},
    })
DATASET.write_text(json.dumps(cases, ensure_ascii=False, indent=1), encoding='utf-8')
print('dataset', DATASET.name, len(cases), 'casos;', sum(len(c['diagnoses']) > 1 for c in cases), 'con más de un principal')

for model, rows in arms.items():
    out = OUT_ROOT / DATASET.stem / PROMPT / f"{model.replace('-', '_').replace('.', '_')}__{TAG}"
    out.mkdir(parents=True, exist_ok=True)
    emulated, empty = [], 0
    for c in cases:
        r = rows[c['id']]
        data = ((r.get('final_response') or {}).get('data')) or []
        names = [d.get('diagnosis') for d in data if d.get('diagnosis')]
        empty += not names
        emulated.append({**c, 'ddx_details': {n: {'normalized_text': n, 'position': j} for j, n in enumerate(names, 1)},
                         'emulator_time_seconds': r.get('duration_seconds')})
    prefix = f"{PROMPT}___{model.replace('-', '_').replace('.', '_')}"
    (out / f'{prefix}___ddxs_from_emulator.json').write_text(json.dumps(emulated, ensure_ascii=False, indent=2), encoding='utf-8')
    print(model, '->', out.relative_to(EVAL), 'listas vacías:', empty)
