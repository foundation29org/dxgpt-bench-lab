# Pipeline V4 - Medical Diagnosis Evaluation System

Pipeline de evaluacion de modelos LLM para diagnostico diferencial medico, con foco especial en enfermedades raras.

Este README es la fuente canonica del estado actual del benchmark. Para ejecutar el pipeline paso a paso usa `GUIA_EVALUACION.md`. Para la historia completa del proyecto usa `docs/ROADMAP.md`.

## Rol de cada documento

| Documento | Uso |
|---|---|
| `README.md` | Estado actual del benchmark, tablas y recomendaciones |
| `GUIA_EVALUACION.md` | Runbook operativo |
| `output/rankingV2.txt` | Historial completo de runs |
| `docs/ROADMAP.md` | Fases, decisiones y trazabilidad |

## Estado actual (2026-07-10)

- `gemini-3-pro-preview low` es el mejor modelo HPO del benchmark actual
- En texto narrativo (`all_256_clean`) empata en calidad con `gemini-2.5-pro low` y es mucho mas rapido
- `gpt-5.4-mini low` es la mejor opcion OpenAI por velocidad/calidad
- `gpt-5.5 low` fue probado en `all_256_clean` y no mejora a `gpt-5.4` (`1.548`, `97.7%`, `13.9s/caso`)
- `gpt-5.6-luna low` es competitivo, pero no reemplaza a `gpt-5.4-mini` (`1.540`, `97.7%`, `6.4s/caso`)
- `gpt-5.6-luna medium` empeora (`1.584`, `97.7%`, `7.8s/caso`): mantener `low` y no ejecutar `high` completo
- `gpt-5.6-terra low` es el mejor OpenAI narrativo hasta ahora (`1.382`, `98.1%`, `6.9s/caso`)
- `gpt-5.6-terra medium` empeora (`1.516`, `97.7%`, `8.4s/caso`): mantener `low` y no ejecutar `high` completo
- `gpt-5.6-sol low` no compite (`1.619`, `98.4%`, `14.1s/caso`): no ampliar a `medium` por ahora
- `gemini-3.1-pro-preview low` es el nuevo líder narrativo (`1.267`, `98.1%`, `9.3s/caso`)
- `gemini-3.5-flash low` casi iguala a Pro (`1.284`, `97.7%`, `6.1s/caso`): mejor candidato calidad/latencia
- `gemini-3.1-flash-lite low` iguala el avg de `gpt-5.4-mini`, mejora cobertura (`98.8%`) y baja a `2.8s/caso`: candidato económico
- `thinking_level=medium` en Gemini no aporta: degrada en 4/4 datasets HPO y empata en narrativa

## Datasets evaluados

| Dataset | Tipo | Casos | Uso |
|---|---|---:|---|
| `all_256_clean` | Texto narrativo | 256 | Track narrativo publicable |
| `ramedis_hpo` | HPO | 624 | Comparativa DeepRare |
| `lirical_hpo` | HPO | 370 | Comparativa DeepRare |
| `hms_hpo` | HPO | 88 | Comparativa DeepRare |
| `mme_hpo` | HPO | 40 | Comparativa DeepRare |
| `mygene2_hpo` | HPO | 146 | Comparativa DeepRare |
| `ddd_hpo` | HPO | 1749 | Resultado HPO mas solido |

## Track A - Narrative Clinical Text

Dataset: `all_256_clean`  
Juez de referencia: `gemini-2.5-pro`  
Prompt: `juanjo_classic_v2`

| Rank | Model | Avg Pos | Success% | ~s/case | Nota |
|---|---|---:|---:|---:|---|
| 1 | `gemini-3.1-pro-preview low` | **1.267** | 98.1% | 9.3 | Nuevo líder narrativo |
| 2 | `gemini-3.5-flash low` | 1.284 | 97.7% | 6.1 | Casi Pro, más rápido; candidato calidad/latencia |
| 3 | `gemini-2.5-pro low` | 1.299 | 98.1% | 27.9 | Empate histórico con Gemini 3 Pro |
| 3 | `gemini-3-pro-preview low` | 1.299 | 98.1% | 10.3 | Anterior modo avanzado |
| 5 | `gemini-3-pro-preview medium` | 1.315 | 98.1% | ~35 | Casi empate, no compensa |
| 6 | `gpt-5.6-terra low` | 1.382 | 98.1% | 6.9 | Mejor OpenAI narrativo; gana la ablación Terra |
| 7 | `gemini-2.5-flash low` | 1.434 | 98.1% | 21.1 | Buen equilibrio |
| 8 | `grok-4-1-fast-reasoning` | 1.448 | 97.7% | 20.4 | Mejor alternativa no Google |
| 9 | `gpt-5.4 full low` | 1.502 | 98.8% | 17.3 | Superado por Terra low en avg_pos |
| 10 | `gpt-5.6-terra medium` | 1.516 | 97.7% | 8.4 | Peor que Terra low; no compensa |
| 11 | `gpt-5.4-mini low` | 1.526 | 98.1% | **4.7** | Produccion actual; mejor latencia/coste |
| 11 | `gemini-3.1-flash-lite low` | 1.526 | 98.8% | **2.8** | Mismo avg, +2 matches y 40% más rápido |
| 12 | `o3 high` | 1.530 | 98.8% | 15.9 | Obsoleto |
| 13 | `gpt-5.6-luna low` | 1.540 | 97.7% | 6.4 | R@1 mejora, pero pierde R@3 y un caso vs `gpt-5.4-mini` |
| 14 | `gpt-4o low` | 1.545 | 96.1% | 10.3 | Superado |
| 15 | `gpt-5.5 low` | 1.548 | 97.7% | 13.9 | No mejora a `gpt-5.4` |
| 16 | `gpt-5.6-luna medium` | 1.584 | 97.7% | 7.8 | Peor que Luna low; no compensa |
| 17 | `gpt-5.6-sol low` | 1.619 | 98.4% | 14.1 | Buena cobertura, mala ordenación; no compite |

## Track B - HPO Datasets

Comparativa principal entre familias en los datasets HPO ya cerrados:

| Dataset | Casos | gpt-4o R@1 | gpt-5.4-mini R@1 | gemini-2.5-pro R@1 | gemini-3-pro-preview R@1 |
|---|---:|---:|---:|---:|---:|
| RAMEDIS | 624 | 49.2% | 46.3% | 54.2% | **54.3%** |
| LIRICAL | 370 | 37.0% | 55.1% | 61.9% | **67.8%** |
| HMS | 88 | 34.1% | 53.4% | 56.8% | **72.7%** |
| MyGene2 | 146 | 23.3% | 38.4% | 55.5% | **61.0%** |
| MME | 40 | 42.5% | 22.5% | 65.0% | **77.5%** |
| DDD | 1749 | 44.9% | 52.4% | 63.5% | **70.3%** |

### Conclusiones HPO

- `gemini-3-pro-preview` gana en los 6 datasets HPO en `Recall@1`
- `DDD` es el resultado mas robusto: `R@1=70.3%`
- `gpt-5.4-mini` supera a `gpt-4o` en 4/6 datasets HPO y sigue siendo la mejor opcion OpenAI para produccion normal

### Ablacion `thinking_level=medium`

Evaluado sobre MME, HMS, MyGene2, LIRICAL y `all_256_clean`:

| Subconjunto | n | Delta R@1 | Delta R@3 | Delta avg_pos |
|---|---:|---:|---:|---:|
| HPO weighted | 644 | -5.1pp | -8.8pp | +0.22 |
| Narrativa | 256 | +1.2pp | -2.7pp | +0.02 |
| Total | 900 | -3.3pp | -7.1pp | +0.17 |

Decision: mantener `low`.

## Referencia de tiempos

Tiempo de emulacion aproximado por caso:

| Model | ~s/case |
|---|---:|
| `gpt-5.4-mini low` | **~5** |
| `gpt-5.6-luna low` | ~6.4 |
| `gpt-5.6-terra low` | ~6.9 |
| `gpt-5.6-luna medium` | ~7.8 |
| `gpt-5.6-terra medium` | ~8.4 |
| `gemini-3.5-flash low` | ~6.1 |
| `gemini-3.1-flash-lite low` | **~2.8** |
| `gemini-3.1-pro-preview low` | ~9.3 |
| `gpt-5.6-sol low` | ~14.1 |
| `gpt-4o low` | ~8-10 |
| `gemini-3-pro-preview low` | ~10 |
| `gpt-5.5 low` | ~14 |
| `gpt-5.4 full low` | ~17 |
| `grok-4-1-fast-reasoning` | ~20 |
| `gemini-2.5-flash low` | ~21 |
| `gemini-2.5-pro low` | ~28-34 |
| `gpt-5-mini low` | ~48 |

## Recomendaciones de produccion

### Modo normal

Usar `gpt-5.4-mini low`.

Motivos:

- mejor que `gpt-4o` en calidad
- mucho mas rapido que `gpt-5-mini`
- mejor coste/latencia dentro del ecosistema OpenAI

### Modo avanzado

Usar `gemini-3-pro-preview low`.

Motivos:

- mejor calidad HPO del benchmark actual
- empate con `gemini-2.5-pro` en narrativa
- mucha mejor latencia

## Como ejecutar un benchmark

Para instrucciones operativas completas:

- `GUIA_EVALUACION.md`

Comandos minimos:

```powershell
cd "C:\repos\DxGPT\eval\bench\pipelines\pipeline_v4 - fork\main"
py validate.py
py main.py --config config_mi_experimento.yaml
```

## Reproducibilidad

Cada run guarda su snapshot de configuracion dentro de `output/`. Tras la limpieza del repo, esos snapshots son la fuente de verdad de cada experimento:

- `output/<dataset>/<prompt>/<model>/<prompt>___<model>___config.yaml`
- `output/<dataset>/<prompt>/<model>/<timestamp>/<prompt>___<model>___config.yaml`

No hace falta conservar decenas de `config_*.yaml` sueltos en la raiz del pipeline para reejecutar runs cerrados.
