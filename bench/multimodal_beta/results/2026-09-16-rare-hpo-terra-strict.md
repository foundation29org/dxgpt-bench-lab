# Terra low — benchmark HPO completo con strict

Fecha: 2026-09-16  
Estado: snapshot canónico de referencia; no es un gate de producto.

## Condiciones

- Modelo evaluado: `gpt-5.6-terra`, `reasoning_effort: low`.
- Se reutilizan las 3.017 listas diagnósticas, normalizaciones y puntuaciones
  BERT congeladas de los runs de julio de 2026.
- No hay inferencia nueva de Terra, MedLabeler ni llamadas nuevas a SapBERT.
- Único cambio evaluado: `legacy_similarity` → `strict_equivalence`.
- Juez LLM: `gemini-2.5-pro`; temperatura 0,1; máximo 10.000 tokens.
- Los códigos SNOMED/ICD, umbrales BERT y orden de los DDX no cambian.

## Resultado strict

| Dataset | n | R@1 | R@3 | R@5 | Cobertura | Pos. media |
|---|---:|---:|---:|---:|---:|---:|
| DDD | 1.749 | 27,3% | 38,0% | 40,7% | 40,7% | 1,579 |
| RAMEDIS | 624 | 32,7% | 50,5% | 57,1% | 57,1% | 1,820 |
| LIRICAL | 370 | 28,4% | 40,5% | 46,5% | 46,8% | 1,855 |
| MME | 40 | 50,0% | 60,0% | 65,0% | 65,0% | 1,423 |
| MyGene2 | 146 | 38,4% | 50,7% | 58,2% | 58,2% | 1,706 |
| HMS | 88 | 42,0% | 58,0% | 64,8% | 64,8% | 1,737 |
| **Total ponderado** | **3.017** | **29,8%** | **42,4%** | **46,6%** | **46,7%** | — |

La caída respecto a legacy no es una regresión de Terra: son las mismas
respuestas. Legacy aceptaba enfermedades relacionadas, subtipos distintos y
proximidad clínica; strict exige la misma entidad diagnóstica.

## Puente legacy → strict

| Dataset | Cobertura legacy | Cobertura strict | Δ |
|---|---:|---:|---:|
| DDD | 98,1% | 40,7% | −57,4 pp |
| RAMEDIS | 97,3% | 57,1% | −40,2 pp |
| LIRICAL | 99,2% | 46,8% | −52,4 pp |
| MME | 95,0% | 65,0% | −30,0 pp |
| MyGene2 | 98,6% | 58,2% | −40,4 pp |
| HMS | 98,9% | 64,8% | −34,1 pp |

## Telemetría del juez conservada

Coste estimado con precio de Gemini 2.5 Pro de $1,25/M tokens de entrada y
$10/M tokens de salida, incluyendo tokens de razonamiento.

| Dataset | Llamadas | p50 | p95 | Coste estimado |
|---|---:|---:|---:|---:|
| DDD | 1.515 | 11,06 s | 21,41 s | $22,21 |
| RAMEDIS | 543 | 10,54 s | 15,59 s | $7,03 |
| LIRICAL | 328 | 11,35 s | 21,41 s | $4,82 |
| MME | 34 | 12,11 s | 18,74 s | $0,44 |
| MyGene2 | 137 | 11,77 s | 21,18 s | $2,01 |
| HMS | 70 | 10,98 s | 16,59 s | $0,87 |
| **Total** | **2.627** | — | — | **$37,39** |

Este coste corresponde a la telemetría retenida en los artefactos canónicos,
incluidos sus reintentos y cuatro reparaciones puntuales. No representa el
total facturado durante el trabajo: excluye ejecuciones abortadas o
sobrescritas.

## Validación y límites

- 3.017/3.017 casos únicos; cero `worker_error` en los artefactos finales.
- Cuatro respuestas inválidas del juez se repararon por caso, sin repetir
  datasets completos.
- Si el juez devuelve varias posiciones equivalentes, se conserva la de menor
  rango. Una respuesta que mezcla `0` y posiciones sigue siendo inválida.
- Gemini 2.5 Pro no es completamente determinista. Con BERT congelado,
  LIRICAL osciló entre 168 y 173 matches en dos ejecuciones. El snapshot
  canónico es 173/370; no debe interpretarse una diferencia de pocos casos
  como señal clínica.
- Estos datasets contienen listas HPO, no historias narrativas. No se comparan
  directamente con `all_256_clean` ni con MedReaMM.

## Artefactos

- `outputs/judge_audit/rare_hpo_terra_strict_gemini25pro/{ddd,ramedis,lirical,mme,mygene2}/`
- `outputs/judge_audit/hms88_gpt56terra_low_strict/`

