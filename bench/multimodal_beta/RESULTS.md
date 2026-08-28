# Resultados de evaluación multimodal

Índice compacto de ejecuciones. Cada fila enlaza un informe individual con
condiciones, incidencias, casos sin match y conclusiones.

## Resumen diagnóstico

| Fecha | Cohorte | Entrada | Modelo | Juez | N | R@1 | R@3 | R@5 | Cobertura | Pos. media | Estado | Detalle |
|---|---|---|---|---|---:|---:|---:|---:|---:|---:|---|---|
| 2026-08-27 | MedReaMM pilot25 | T+I | gpt5 | strict | 25 | 64% | 76% | 84% | 84% | 1,571 | Provisional | [Informe](results/2026-08-27-medreamm-pilot25-t-plus-i-gpt5.md) |
| 2026-08-27 | MedReaMM pilot25 | T+I | gpt5 | legacy | 25 | 72% | 88% | 100% | 100% | 1,720 | Solo puente | [Informe](results/2026-08-27-medreamm-pilot25-t-plus-i-gpt5.md) |
| 2026-08-27 | MedReaMM pilot100 | T+I | gpt5 | strict | 100 | 61% | 74% | 78% | 80% | 1,462 | Provisional | [Informe](results/2026-08-27-medreamm-pilot100-t-plus-i-gpt5.md) |
| 2026-08-27 | MedReaMM pilot100 | T+I | gpt5 | legacy | 100 | 72% | 89% | 96% | 99% | 1,586 | Solo puente | [Informe](results/2026-08-27-medreamm-pilot100-t-plus-i-gpt5.md) |
| 2026-08-27 | MedReaMM pilot100 | T | gpt54mini | strict | 100 | 43% | 56% | 58% | 58% | 1,397 | Provisional | [Informe](results/2026-08-27-medreamm-pilot100-t-gpt54mini.md) |
| 2026-08-27 | MedReaMM pilot100 | T | gpt54mini | legacy | 100 | 55% | 82% | 93% | 93% | 1,774 | Solo puente | [Informe](results/2026-08-27-medreamm-pilot100-t-gpt54mini.md) |
| 2026-08-27 | MedReaMM pilot100 | T | gpt5 | strict | 100 | 43% | 58% | 63% | 64% | 1,641 | Provisional | [Informe](results/2026-08-27-medreamm-pilot100-t-gpt5.md) |
| 2026-08-27 | MedReaMM pilot100 | T | gpt5 | legacy | 100 | 54% | 75% | 92% | 95% | 2,105 | Solo puente | [Informe](results/2026-08-27-medreamm-pilot100-t-gpt5.md) |
| 2026-08-28 | MedReaMM pilot100 | T+shuffled-I | gpt5 | strict | 100 | — | — | — | — | — | En curso | [Informe](results/2026-08-28-medreamm-pilot100-t-shuffled-i-gpt5.md) |
| 2026-08-28 | MedReaMM pilot100 | I | gpt5 | strict | 100 | — | — | — | — | — | En cola | [Informe](results/2026-08-28-medreamm-pilot100-i-gpt5.md) |

## Resultado técnico por inferencia

| Fecha | Cohorte | Entrada | Modelo real | Éxitos | Resumidos | Latencia media | Estado |
|---|---|---|---|---:|---:|---:|---|
| 2026-08-27 | MedReaMM pilot25 | T+I | gpt5 | 25/25 | 9/25 | ≈41 s | Completa |
| 2026-08-27 | MedReaMM pilot100 | T+I | gpt5 | 100/100 | 32/100 | 40,2 s | Completa |
| 2026-08-27 | MedReaMM pilot100 | T | gpt54mini | 100/100; 1 lista vacía | 32/100 | 14,3 s | Completa |
| 2026-08-27 | MedReaMM pilot100 | T | gpt5 | 100/100; 1 lista vacía | 32/100 | 35,6 s | Completa |

Las filas strict y legacy de una misma cohorte reutilizan exactamente las
mismas respuestas del modelo. Solo cambia la política del juez.

## Interpretación vigente

- `strict_equivalence` es la métrica canónica.
- `legacy_similarity` se conserva únicamente para enlazar con evaluaciones
  históricas; aceptó 99/100 casos frente a 80/100 con strict.
- Todos los resultados son provisionales hasta completar
  [MEDICAL_REVIEW.md](MEDICAL_REVIEW.md).
- Con `gpt5`, `T+I` supera a `T` en 16 puntos de cobertura; falta confirmar
  causalidad visual con `I`, `T+shuffled-I` y revisión clínica.
- Las tareas y su orden están en [ROADMAP.md](ROADMAP.md).

## Comparación con el benchmark narrativo

El 58% de `gpt54mini T` no es comparable directamente con el 98,1% y posición
media 1,526 de `all_256_clean`:

- MedReaMM contiene historias prediagnósticas deliberadamente incompletas y
  reserva parte de la evidencia para las imágenes;
- `all_256_clean` usa casos narrativos curados y un prompt directo;
- el flujo beta incluye clasificación de intención, posible resumen y lógica
  de producto;
- MedReaMM usa gold ICD-11 y este track aplica equivalencia estricta;
- el histórico narrativo usa `legacy_similarity`, que acepta relaciones
  clínicas no equivalentes.

La posición media se calcula solo entre casos con match. Por ello, una posición
1,397 con 58% de cobertura no es mejor que 1,526 con cobertura alta: los 42
casos fallidos desaparecen del promedio. La comparación narrativa justa exige
reevaluar sus respuestas existentes con el juez strict.

## Ubicación de los jueces

- Legacy:
  `bench/pipelines/pipeline_v4 - fork/main/evaluator.py`,
  `DiagnosticEvaluator._get_llm_judgment`.
- Strict:
  `bench/multimodal_beta/evaluate_v4.py`,
  `StrictMultimodalEvaluator._get_llm_judgment`.

No se deben comparar como si midieran lo mismo: legacy busca similitud clínica;
strict exige equivalencia de entidad diagnóstica.

## Cómo registrar una nueva ejecución

1. Crear un informe en `results/AAAA-MM-DD-dataset-condicion-modelo.md`.
2. Registrar condiciones, resultado técnico, métricas, trazabilidad y
   limitaciones.
3. Añadir una fila a las tablas de este índice.
4. Marcar el resultado como `En curso`, `Provisional`, `Validado`,
   `Solo puente` o `Descartado`.

Los artefactos detallados permanecen en `outputs/` y no sustituyen este
registro.
