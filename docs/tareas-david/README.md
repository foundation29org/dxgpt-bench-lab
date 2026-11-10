# Tareas de revisión clínica — David

Encargos de revisión clínica del benchmark de DxGPT. Cada tarea tiene su ficha
en esta carpeta: para qué sirve, qué hay que hacer, dónde está el material,
cómo se devuelve y cuándo está hecha.

| # | Tarea | Estado | Depende de | Tiempo orientativo |
|---|---|---|---|---|
| 1 | [Validación clínica de `narrative_v2`](01-validacion-narrative-v2.md) | Hecha (4-nov, con la tanda de reserva; los 3 recambios, el 6-nov) | — | ≈ 5 h + ≈ 1 h + ≈ 5 min |
| 2 | [Validar la escala del juez (2/1/0)](02-escala-del-juez.md) | Hecha (6-nov): Flash coincide en «¿es un 2?» en el 90 %; la rúbrica no cambia | Tarea 1 | ≈ 2 h |
| 3 | [Raras: nombres sin gen, casos con HPO insuficientes y sinónimos del gold](03-nombres-sin-gen-raras.md) | Hecha (10-nov): los nombres sin gen fallaban en cerca de la mitad y se rehicieron (HPO v3); la fenilcetonuria con hipertirosinemia se queda | — | ≈ 1 h 30 min |
| 4 | [Raras: comprobar los nombres sin gen rehechos](04-nombres-sin-gen-v3.md) | Lista para empezar | Tarea 3 | ≈ 45 min |

Lo pendiente se puede hacer ya: la 4.

## Reglas comunes

- **Criterio: la misma enfermedad.** No «se parece» ni «estaría en el
  diferencial». Es el criterio de la nota estricta del juez (ver la
  [tarea 2](02-escala-del-juez.md) y
  [cómo funciona Pipeline V5](../pipeline/pipeline-v5.md)).
- **Dudas:** marca **CONSULTAR MÉDICO** y explica la duda en una línea, como
  en las revisiones anteriores.
- **Lo que no se marca queda pendiente**, no aprobado.
- **Las hojas con casos no van a git.** Este repositorio es público. Las hojas
  de revisión llevan texto o listas de síntomas de los casos (algunos son
  urgencias reales), así que están en rutas que `.gitignore` excluye y se
  comparten por canal privado. Al repo solo vuelven las decisiones, sin texto
  de casos.
- **Qué pasa después:** las decisiones se aplican al dataset y se vuelven a
  puntuar las mismas listas de los modelos, sin generarlas de nuevo. El
  informe ([benchmark-report-v5.html](../benchmark-report-v5.html)) se
  regenera con las cifras nuevas.

## Revisiones anteriores

- Fallos de Terra en raras (T3, octubre 2026):
  `General/portfolio/DxGPT/research/tarea_finetuning_DxGPT.md`. De ahí salen
  los 11 casos de gold dudoso que ya se quitaron y los 9 de la tarea 3.
- Juez del track multimodal (septiembre 2026):
  [MEDICAL_REVIEW.md](../../bench/multimodal_beta/MEDICAL_REVIEW.md),
  [MEDICAL_REVIEW_RONDA2.md](../../bench/multimodal_beta/MEDICAL_REVIEW_RONDA2.md)
  y las entregas en `bench/multimodal_beta/reviews/`.
