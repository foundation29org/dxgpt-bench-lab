# MedReaMM 32 resumidos — T+I gpt5 sin resumen

Estado: **provisional**. Ablación emparejada del umbral de producto de
1.000 caracteres. Mismos 32 casos que se resumieron en gpt5 T+I
(`pilot100_product`), misma entrada T+I, mismo modelo, mismo juez
`strict_equivalence`. Solo cambia que el servidor no resume.

## Condiciones y resultado técnico

- Fecha: 2026-09-09.
- Casos: 32 (los que superaron 1.000 caracteres en el T+I de gpt5).
- Entrada: historia saneada e imágenes del mismo caso (`T+I`).
- Tenant: `dxgpt-local`. Flag eval-only `skipSummarize`.
- Modelo pedido y final: `gpt5` en 32/32.
- Peticiones completadas: 32/32, sin listas vacías, `summarized=false`.
- Latencia media: 43,2 s. Mediana: 41,3 s. P95: 50,4 s. Rango: 34,3–102,2 s.
  (el T+I original de 100 casos: 40,2 s de media).
- Diferencial: 5 diagnósticos en 17 casos, 6 en 9, 7 en 5 y 8 en 1.

## Resultado strict_equivalence

- R@1: 22/32 — 68,8%.
- R@3: 24/32 — 75%.
- R@5: 27/32 — 84,4%.
- Cobertura: 27/32 — 84,4%.
- Posición media entre matches: 1,407.
- MRR: 0,742.

Resolución: 17 SNOMED, 1 ICD-10 exacto, 3 BERT contrastados y 6 decisiones
del juez LLM.

Casos sin match:

- `N-10000083`: Intralobar bronchopulmonary sequestration.
- `23509306`: Nodular sclerosis classical Hodgkin lymphoma.
- `N-10000032`: Pancreatic ductal adenocarcinoma.
- `N-10000086`: BRAF inhibitor-related toxic effects.
- `N-10000050`: Cryptococcal pneumonia.

`N-10000032` y `N-10000050` ya fallaban con resumen.

## Frente a los mismos 32 con resumen (inferencia original)

Los números «con resumen» salen del T+I de 100 casos de 2026-08-27,
restringidos a estos IDs. No es una inferencia nueva.

| Condición | R@1 | R@3 | R@5 | Cobertura | Pos. media | MRR |
|---|---:|---:|---:|---:|---:|---:|
| Con resumen (original) | 21/32 — 65,6% | 26/32 — 81,3% | 29/32 — 90,6% | 30/32 — 93,8% | 1,667 | 0,758 |
| Sin resumen (esta run) | 22/32 — 68,8% | 24/32 — 75% | 27/32 — 84,4% | 27/32 — 84,4% | 1,407 | 0,742 |

Emparejado por cobertura: ambos 27, solo resumen 3, solo sin resumen 0,
ninguno 2. McNemar exacto sobre discordantes: `p=0,25`. La cobertura **no
mejora** al saltar el umbral; los tres flips van a favor del resumen.

Emparejado por R@1: ambos 19, solo resumen 2, solo sin resumen 3, ninguno
8. McNemar `p=1,0`. El +1 de R@1 es ruido de una inferencia nueva.

Los tres matches que se pierden sin resumen:

- `N-10000083` (intralobar BPS): era P4 SNOMED.
- `23509306` (Hodgkin esclerosis nodular): era P6 ICD-10 parent.
- `N-10000086` (toxicidad por inhibidor BRAF): era P2 LLM.

La posición media baja (1,667 → 1,407) porque desaparecen matches tardíos;
no es una mejora. El MRR, que pone a cero los no matched, baja 0,758 →
0,742.

## Decisión de producto

**El umbral de 1.000 caracteres se queda.** Saltar el resumen no gana
cobertura y pierde tres matches que el flujo actual sí aceptaba. n=32 no
da potencia para declarar daño, pero tampoco hay señal a favor de enviar
el texto largo crudo. No subir el umbral; no quitarlo.

## Trazabilidad y cautelas

- Respuestas: `outputs/pilot100_gpt5_TI_nosummary/responses.jsonl`.
- Strict: `outputs/pilot100_gpt5_TI_nosummary/evaluation_v4_primary_strict/`.
- Baseline emparejado: `outputs/pilot100_product/evaluation_v4_primary_strict/`.
- Informe original de los 100: [2026-08-27-medreamm-pilot100-t-plus-i-gpt5.md](2026-08-27-medreamm-pilot100-t-plus-i-gpt5.md).
- Inferencia nueva ⇒ ruido de muestreo; el McNemar emparejado es la cifra
  que cuenta, no el 84% suelto frente al 80% de los 100.
- El juez sigue siendo `gemini-2.5-pro` + `strict_equivalence`.
  Provisional hasta la ronda 2 de David.
