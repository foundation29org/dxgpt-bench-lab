"""MedReaMM pilot250 T+I con el modo avanzado (12-nov-2026) al formato del evaluador V5.

Cada caso se pasó por el Server local como lo hace la web: /medical/analyze con Sol
(el diagnóstico normal) y después /diagnose con advanced (Claude Fable 5.2), con la
misma subida de imágenes y el texto que la web manda en la segunda petición
(run_beta_api.py --advanced). Salen dos brazos con el mismo código y el mismo día:

- gpt-6.1-sol_low: la primera petición;
- claude-fable-5-2_low: la segunda. Si Sol no devolvió lista, la web no ofrece el
  modo avanzado y el caso cuenta como lista vacía.

Usa el dataset y el gold de medreamm_to_v5.py (bench/datasets/medreamm_pilot250_ti.json).
Uso (desde eval/): python bench/pipelines/pipeline_v5/main/medreamm_advanced_to_v5.py
y después main.py --config con config_claudefable52_medreamm250_ti_adv.yaml y
config_gpt61sol_medreamm250_ti_adv.yaml.
"""
import json
from pathlib import Path

EVAL = Path(__file__).resolve().parents[4]
RUN = EVAL / 'bench' / 'multimodal_beta' / 'outputs' / 'pilot250_fable52_advanced_TI_n5'
OUT_ROOT = EVAL / 'bench' / 'pipelines' / 'pipeline_v5' / 'main' / 'output'
DATASET = EVAL / 'bench' / 'datasets' / 'medreamm_pilot250_ti.json'
PROMPT = 'juanjo_classic_v2_n5'
TAG = 'server_v0_00200_advanced'

# Las partes de cada proceso se juntan en responses.jsonl (el último registro de cada
# caso, prefiriendo los correctos: --resume añade líneas). Sin partes, se lee ese fichero.
parts = sorted(p for p in RUN.glob('*.jsonl') if p.name != 'responses.jsonl')
records = {}
for path in parts or [RUN / 'responses.jsonl']:
    for line in path.read_text(encoding='utf-8').splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        prev = records.get(r['case_id'])
        if prev is None or r['status'] == 'success' or prev['status'] != 'success':
            records[r['case_id']] = r
if parts:
    with (RUN / 'responses.jsonl').open('w', encoding='utf-8') as f:
        for cid in sorted(records):
            f.write(json.dumps(records[cid], ensure_ascii=False) + '\n')

cases = json.loads(DATASET.read_text(encoding='utf-8'))
missing = [c['id'] for c in cases if c['id'] not in records]
failed = [cid for cid, r in records.items() if r['status'] != 'success']
print('casos', len(cases), 'con registro', len(records), 'sin registro', len(missing), 'con error', len(failed))


def sol(r):
    data = ((r.get('final_response') or {}).get('data')) or []
    adv_s = ((r.get('advanced') or {}).get('duration_seconds')) or 0
    return data, round((r.get('duration_seconds') or 0) - adv_s, 3)


def fable(r):
    adv = r.get('advanced') or {}
    data = ((adv.get('final_response') or {}).get('data')) or []
    return data, adv.get('duration_seconds')


for model, pick in {'gpt-6.1-sol_low': sol, 'claude-fable-5-2_low': fable}.items():
    slug = model.replace('-', '_').replace('.', '_')
    out = OUT_ROOT / DATASET.stem / PROMPT / f'{slug}__{TAG}'
    out.mkdir(parents=True, exist_ok=True)
    emulated, empty = [], 0
    for c in cases:
        r = records.get(c['id']) or {}
        data, seconds = pick(r) if r else ([], None)
        names = [d.get('diagnosis') for d in data if d.get('diagnosis')]
        empty += not names
        emulated.append({**c, 'ddx_details': {n: {'normalized_text': n, 'position': j} for j, n in enumerate(names, 1)},
                         'emulator_time_seconds': seconds})
    (out / f'{PROMPT}___{slug}___ddxs_from_emulator.json').write_text(
        json.dumps(emulated, ensure_ascii=False, indent=2), encoding='utf-8')
    print(model, '->', out.relative_to(EVAL), 'listas vacías:', empty)
