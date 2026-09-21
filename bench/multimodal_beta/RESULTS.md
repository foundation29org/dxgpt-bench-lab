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
| 2026-08-28 | MedReaMM pilot100 | T+shuffled-I | gpt5 | strict | 100 | 46% | 57% | 60% | 62% | 1,597 | Provisional | [Informe](results/2026-08-28-medreamm-pilot100-t-shuffled-i-gpt5.md) |
| 2026-08-28 | MedReaMM pilot100 | I | gpt5 | strict | 100 | 32% | 42% | 49% | 50% | 1,860 | Provisional | [Informe](results/2026-08-28-medreamm-pilot100-i-gpt5.md) |
| 2026-09-08 | MedReaMM pilot100 | T+I | gpt56terra | strict | 100 | 67% | 82% | 84% | 84% | 1,310 | Provisional | [Informe](results/2026-09-08-medreamm-pilot100-t-plus-i-gpt56terra.md) |
| 2026-09-08 | MedReaMM pilot100 | T | gpt56terra | strict | 100 | 50% | 60% | 65% | 65% | 1,477 | Provisional | [Informe](results/2026-09-08-medreamm-pilot100-t-gpt56terra.md) |
| 2026-09-08 | MedReaMM pilot100 | T+I | gpt6astra | strict | 100 | 76% | 87% | 88% | 88% | 1,205 | Provisional | [Informe](results/2026-09-08-medreamm-pilot100-t-plus-i-gpt6astra.md) |
| 2026-09-08 | MedReaMM pilot100 | T | gpt6astra | strict | 100 | 54% | 66% | 67% | 67% | 1,313 | Provisional | [Informe](results/2026-09-08-medreamm-pilot100-t-gpt6astra.md) |
| 2026-09-09 | MedReaMM 32 resumidos | T+I sin resumen | gpt5 | strict | 32 | 68,8% | 75% | 84,4% | 84,4% | 1,407 | Provisional | [Informe](results/2026-09-09-medreamm-pilot32-t-plus-i-gpt5-nosummary.md) |

## Resultado técnico por inferencia

| Fecha | Cohorte | Entrada | Modelo real | Éxitos | Resumidos | Latencia media | Estado |
|---|---|---|---|---:|---:|---:|---|
| 2026-08-27 | MedReaMM pilot25 | T+I | gpt5 | 25/25 | 9/25 | ≈41 s | Completa |
| 2026-08-27 | MedReaMM pilot100 | T+I | gpt5 | 100/100 | 32/100 | 40,2 s | Completa |
| 2026-08-27 | MedReaMM pilot100 | T | gpt54mini | 100/100; 1 lista vacía | 32/100 | 14,3 s | Completa |
| 2026-08-27 | MedReaMM pilot100 | T | gpt5 | 100/100; 1 lista vacía | 32/100 | 35,6 s | Completa |
| 2026-08-28 | MedReaMM pilot100 | T+shuffled-I | gpt5 | 100/100 | 32/100 | 44,5 s | Completa |
| 2026-08-28 | MedReaMM pilot100 | I | gpt5 | 100/100; 1 lista vacía | 0/100 | 34,5 s | Completa |
| 2026-09-08 | MedReaMM pilot100 | T+I | gpt56terra | 100/100 | 32/100 | 24,3 s | Completa |
| 2026-09-08 | MedReaMM pilot100 | T | gpt56terra | 100/100; 1 lista vacía | 32/100 | 20,1 s | Completa |
| 2026-09-08 | MedReaMM pilot100 | T+I | gpt6astra | 100/100 | 32/100 | 55,1 s | Completa |
| 2026-09-08 | MedReaMM pilot100 | T | gpt6astra | 100/100; 1 lista vacía | 32/100 | 47,3 s | Completa |
| 2026-09-09 | MedReaMM 32 resumidos | T+I sin resumen | gpt5 | 32/32 | 0/32 | 43,2 s | Completa |

Las filas strict y legacy de una misma cohorte reutilizan exactamente las
mismas respuestas del modelo. Solo cambia la política del juez.

## Interpretación vigente

- `strict_equivalence` es la métrica canónica.
- `legacy_similarity` se conserva únicamente para enlazar con evaluaciones
  históricas; aceptó 99/100 casos frente a 80/100 con strict.
- Todos los resultados son provisionales hasta completar
  [MEDICAL_REVIEW.md](MEDICAL_REVIEW.md).
- Con `gpt5`, `T+I` (80%) supera a `T` (64%). El control shuffled lo explica:
  misma historia con imágenes de otro caso baja a 62%, indistinguible de `T`
  (McNemar `p=0,79`). Frente a `T+I`, shuffled pierde 18 puntos de cobertura
  (`p=0,00053`). El producto no gana por «llevar imágenes»; gana cuando las
  imágenes pertenecen al mismo caso.
- Solo imágenes (`I`) llega al 50%: hay señal visual, pero no sustituye a la
  historia. La revisión clínica sigue pendiente.
- `gpt56terra` T+I (WestUS, override de eval): cobertura 84%, R@1 67%,
  24,3 s/caso, frente a gpt5 T+I 80% / 61% / 40,2 s. McNemar de cobertura
  `p≈0,45`: la ventaja entre modelos no es significativa.
- Terra **usa la imagen**: T 65% / R@1 50% vs T+I 84% / 67% (24 vs 5;
  McNemar `p=0,00055`). En texto solo, Terra T y gpt5 T son
  indistinguibles (65% vs 64%, `p≈1`).
- `gpt6astra` T+I: cobertura 88%, R@1 76%, 55,1 s/caso. Frente a gpt5 T+I
  el R@1 sí es significativo (21 vs 6, `p=0,0059`); la cobertura +8 pp no
  (`p=0,057`). Frente a Terra T+I, ni cobertura ni R@1 lo son.
- Astra **usa la imagen**: T 67% / R@1 54% vs T+I 88% / 76% (22 vs 1;
  McNemar `p=0,00001`). En texto solo, cobertura indistinguible de Terra
  y gpt5; el R@1 vs gpt5 T sí (54% vs 43%, `p=0,007`).
- Ablación de resumen (32 casos gpt5 T+I que superaban 1.000 caracteres):
  sin resumen, cobertura 27/32 vs 30/32 con resumen (3 vs 0; McNemar
  `p=0,25`). R@1 22 vs 21 (`p=1,0`). **El umbral se queda.** Informe:
  [results/2026-09-09-medreamm-pilot32-t-plus-i-gpt5-nosummary.md](results/2026-09-09-medreamm-pilot32-t-plus-i-gpt5-nosummary.md).
- Las tareas y su orden están en el
  [roadmap general](../../docs/ROADMAP.md).

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
casos fallidos desaparecen del promedio. La comparación narrativa justa exige reevaluar sus respuestas existentes
con el juez strict. Hecho para mini, Terra, Sol medium, gemini-3-pro-preview
low, gemini-3.1-pro-preview low, gemini-3.5-flash low, gemini-3.1-flash-lite
low, gpt-4o, Astra low, gpt-5.4, Terra high, Terra medium y gemini-2.5-pro
low: el 98% era `legacy_similarity`. Rank por R@1: Terra low 63,3% >
gpt-5.4 62,9% > Terra high = medium = xhigh 62,5% (cobertura high 85,2% >
medium 84,4% > xhigh 79,7%) > Astra = Flash 62,1%. Low sigue 1º. xhigh no
usar. gemini-2.5-pro low (2026-09-15): 59,4% / cobertura 75,4%, empata con
3-pro; es el avanzado **real** de producción porque el slug 3-pro devuelve
404 y el Server cae al fallback. Informes:
[results/2026-09-09-all256-judge-audit-strict-terra-medium.md](results/2026-09-09-all256-judge-audit-strict-terra-medium.md),
[results/2026-09-09-all256-judge-audit-strict-terra-xhigh.md](results/2026-09-09-all256-judge-audit-strict-terra-xhigh.md),
[results/2026-09-15-all256-judge-audit-strict-gemini25pro.md](results/2026-09-15-all256-judge-audit-strict-gemini25pro.md).
HPO Terra completo (2026-09-16): 3.017 listas congeladas de DDD, RAMEDIS,
LIRICAL, MME, MyGene2 y HMS reevaluadas con strict, sin nueva inferencia,
MedLabeler ni SapBERT. Total ponderado: R@1 29,8%, R@3 42,4%, R@5 46,6% y
cobertura 46,7%. Por dataset, la cobertura va de 40,7% (DDD) a 65,0% (MME);
HMS queda en R@1 42,0% y cobertura 64,8%. La diferencia frente al 95–99%
legacy mide el cambio de criterio, no una regresión de Terra. Cero errores
finales; coste retenido del juez $37,39. Informe:
[results/2026-09-16-rare-hpo-terra-strict.md](results/2026-09-16-rare-hpo-terra-strict.md).

La comparación histórica HMS entre modelos (2026-09-15) permanece en:
[results/2026-09-15-hms88-judge-audit-strict-mini-gemini3pro.md](results/2026-09-15-hms88-judge-audit-strict-mini-gemini3pro.md),
[results/2026-09-15-hms88-judge-audit-strict-gemini25pro-31pro.md](results/2026-09-15-hms88-judge-audit-strict-gemini25pro-31pro.md),
[results/2026-09-15-hms88-judge-audit-strict-gemini35-38flash.md](results/2026-09-15-hms88-judge-audit-strict-gemini35-38flash.md).
gemini-3.8-flash low (2026-09-15): R@1 59,8% / cobertura 77,7% / 4,4 s.
No gana a 3.5-flash en R@1 (62,1%); sube un poco el techo Gemini de
cobertura (75→78). No sustituye. Informe:
[results/2026-09-15-all256-judge-audit-strict-gemini38flash.md](results/2026-09-15-all256-judge-audit-strict-gemini38flash.md).
o3 high (2026-09-16): R@1 56,6% / R@3 74,2% / cobertura 80,9% /
posición media 1,614. No supera a Terra low con strict. Informe:
[results/2026-09-16-all256-o3-strict.md](results/2026-09-16-all256-o3-strict.md).
Grok 4.6 low y Claude Opus 5 low (2026-09-17) completaron inferencia nueva y
strict sobre los 256 casos. Grok queda 3º: R@1 62,9%, R@3 78,1%, cobertura
81,6%, posición media 1,373 y 17,0 s/caso. Claude, con el parseo de
`thinking` ya corregido (0 listas vacías): R@1 59,4%, R@3 76,2%, R@5 82,8%,
cobertura 87,1% (la más alta de la tabla), posición media 1,803 y 22,7 s/caso.
El 35,2% anterior era un fallo de wrapper, no del modelo. Informe:
[results/2026-09-17-all256-strict-grok46-claude-opus5.md](results/2026-09-17-all256-strict-grok46-claude-opus5.md).
Benchmark de jueces sobre las 256 listas congeladas de Terra (2026-09-16):
Flash sin thinking cuesta $0,0087 vs $1,800 de Pro y reduce la mediana
9,60→0,57 s; obtiene el mismo acuerdo humano inicial, 30/35. Kimi K2.6
funciona vía Azure: $1,125, p50 6,09 s, p95 39,62 s y 28/35. Grok queda en
27/35. David ya terminó la ronda 2 original; se creó una tarea ciega nueva
solo con las 13 discrepancias Pro vs Flash. Las discrepancias exploratorias de
Kimi/Grok quedan fuera. Informe:
[results/2026-09-16-judge-benchmark-all256-terra.md](results/2026-09-16-judge-benchmark-all256-terra.md).
Tabla HTML:
[benchmark-report-jueces.html](../../docs/benchmark-report-jueces.html).
Ronda 2 de David (36 casos) entregada: 2 FP, 3 FN; `24910386` =
`gold_ambiguo` (2026-09-14, no FN). 80/100 → 81 recodificado: no usar
como cifra clínica cerrada.

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
