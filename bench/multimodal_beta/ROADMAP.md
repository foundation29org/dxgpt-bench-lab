# Roadmap de evaluación multimodal

Este documento mantiene el estado, las decisiones y las tareas pendientes del
track end-to-end de DxGPT beta. Las métricas ejecutadas se registran en
[RESULTS.md](RESULTS.md) y la adjudicación clínica en
[MEDICAL_REVIEW.md](MEDICAL_REVIEW.md).

## Principios

- Separar este track de Pipeline V4 narrativo.
- Mantener una métrica canónica de equivalencia diagnóstica estricta.
- Usar `legacy_similarity` solo como puente con resultados históricos.
- Comparar modalidades con el mismo caso, texto, modelo, gold y evaluador.
- No atribuir una mejora a las imágenes sin comparar `T`, `I`, `T+I` y
  `T+shuffled-I`.
- No publicar una cifra clínica sin revisar fuga, calidad del gold y casos
  decididos por el juez.

## Estado actual

### 1. Infraestructura end-to-end — completada

- [x] Replicar negociación Web PubSub y `POST /medical/analyze`.
- [x] Guardar petición, progreso, respuesta, modelo y latencia.
- [x] Alinear formatos admitidos por cliente y servidor.
- [x] Permitir override de modelo únicamente en tenants de evaluación.
- [x] Mantener normalización y juez estricto dentro de `multimodal_beta`.
- [x] Añadir condiciones de modalidad al runner.
- [x] Añadir reintentos de HTTP 429 respetando `Retry-After`.
- [x] Hacer compatible la evaluación con ficheros reanudados.
- [x] Generar paquetes `clinical_review.md` por ejecución y comparación.

### 2. Dataset MedReaMM — completada técnicamente

- [x] Preparar piloto de 25 casos.
- [x] Preparar cohorte de 100 casos sin reemplazar el piloto.
- [x] Excluir captions y aplicar filtro automático de fuga.
- [ ] Completar revisión manual de fuga.
- [ ] Confirmar calidad, rol y granularidad de los gold ICD-11.

### 3. Línea base T+I con gpt5 — provisional

- [x] Ejecutar 25 casos.
- [x] Ejecutar 100 casos.
- [x] Evaluar con SNOMED, ICD-10, SapBERT y juez estricto.
- [x] Registrar métricas y casos sin match.
- [ ] Adjudicar rechazos clínicamente próximos.
- [ ] Auditar una muestra de matches del LLM y de métodos jerárquicos.

Resultado provisional de 100 casos: R@1 61%, R@3 74%, R@5 78% y cobertura
80%.

### 4. Ablación de modalidad — técnica completa, revisión pendiente

- [x] `T+I`: 100 casos con `gpt5`.
- [x] `T`: completar 100 respuestas con el modelo de producto `gpt54mini`.
  - Un caso devolvió una lista vacía y se contabilizará como no match.
  - Evaluación strict: R@1 43%, R@3 56%, R@5 y cobertura 58%.
- [x] `T`: completar 100 casos con `gpt5`.
  - El primer intento utilizó realmente `gpt54mini` porque el contenedor no
    había recargado el override.
  - Tras reiniciar, un caso de control confirmó entrada `T`, cero imágenes y
    `gpt5` como modelo solicitado y final.
  - Resultado strict: R@1 43%, R@3 58%, R@5 63% y cobertura 64%.
- [x] Comparar de forma emparejada `T` frente a `T+I`.
  - `T+I` mejora la cobertura en 16 puntos y R@1 en 18 puntos.
  - 20 casos hacen match solo con imágenes y 4 solo con texto.
  - McNemar exacto sobre discordantes: `p=0,00154`.
- [x] Ejecutar `I` — 100/100 con `gpt5`.
  - Resultado strict: R@1 32%, R@3 42%, R@5 49% y cobertura 50%.
  - Un caso devolvió lista vacía (`23613701`).
- [x] Ejecutar `T+shuffled-I` — 100/100 con `gpt5`; 100/100 usaron imágenes
  de otro caso.
  - Resultado strict: R@1 46%, R@3 57%, R@5 60% y cobertura 62%.
- [x] Medir ganancia visual y sensibilidad al intercambio.
  - `T+shuffled-I` es indistinguible de `T` (McNemar `p=0,79`).
  - `T+I` supera a shuffled en 18 puntos de cobertura (`p=0,00053`).
  - 22 casos hacen match solo con imágenes correctas y 4 solo con shuffled.
  - `I` solo (50%) queda por debajo de `T` (64%; `p=0,049`).

### 5. Calibración del evaluador — encargo a David

- [x] Conservar el resultado legacy del piloto como diagnóstico metodológico.
- [x] Documentar los cuatro falsos positivos que desaparecen con equivalencia
  estricta.
- [x] Adjudicar clínicamente los 7 casos que alcanzaron el juez en el piloto
  ([reviews/david_deliverable.md](reviews/david_deliverable.md)).
  Recuento limpio: 1 `falso_positivo` (`27068836`) y 1 `falso_negativo`
  (`27656661`).
- [x] Adjudicar los 20 unmatched y los 16 matches LLM de la corrida T+I de
  100 (David, 2026-09-09, `91163da`). Entregable:
  [reviews/david_deliverable_ronda2.md](reviews/david_deliverable_ronda2.md).
  Recuento inicial de David: 2 FP, 3 FN y 2 golds amplios; daba una
  recodificación provisional de 81/100. No usarla como cifra clínica
  cerrada: al contrastar los desacuerdos con los artículos aparecieron
  etiquetas inconsistentes y casos que la rúbrica no resuelve. Pendiente
  `24910386` y readjudicación corta tras la revisión de Julián (§5c).
- [ ] Fijar una política para golds amplios, fenotípicos o morfológicos.
- [ ] Decidir si se publican dos métricas: equivalencia exacta y utilidad
  clínica.

### 5b. Ablación del modelo del juez — ejecutada, adjudicación abierta

Se probaron otros `JUDGE_MODEL` con el mismo prompt `strict_equivalence`,
las mismas 100 respuestas y el mismo `labeled_input.json`. No se repitió
inferencia. `24910386` quedó fuera.

Objetivo: encontrar un juez rápido y barato que concuerde con una referencia
humana estable. Los números siguientes solo miden acuerdo con las **etiquetas
iniciales** de David; no son precisión clínica definitiva porque la auditoría
posterior encontró errores/ambigüedades en esa referencia.

Métrica: precisión / FP / FN frente a David en unmatched + LLM. La cobertura
de los 100 es secundaria (SNOMED/ICD/BERT no se mueven; solo esos 36 pueden
cambiar).

- [x] Esperar ronda 2 de David (36 veredictos iniciales).
  5b cerrado (2026-09-09): segunda tira de jueces baratos, mismas 100 T+I.
  DeepSeek-V4-Pro inválido (Azure). `gemini-2.5-flash-lite` 404; sustituto
  `gemini-3.5-flash-lite`. `24910386` fuera.
- [x] Reusar `labeled_input.json` de T+I; no repetir inferencia ni MedLabeler.
- [x] Probar primero jueces baratos/rápidos (Flash / mini), no flagships.
  Flash (2026-09-09): 31/35 vs David (Pro 30/35), cobertura 85/100.
  Recupera los 3 FN; añade 2 matches que David dejó en 0. Informe:
  [results/2026-09-09-judge-ablation-gemini25flash.md](results/2026-09-09-judge-ablation-gemini25flash.md).
  Mini (2026-09-09): 30/35, cobertura 78/100. Empata el recuento de Pro
  en casos distintos. Informe conjunto:
  [results/2026-09-09-judge-ablation-flash-mini.md](results/2026-09-09-judge-ablation-flash-mini.md).
  gemini-3.5-flash-lite (2026-09-09): 28/35, cobertura 75/100. Más
  estricto y peor que Pro. Informe:
  [results/2026-09-09-judge-ablation-gemini35flashlite.md](results/2026-09-09-judge-ablation-gemini35flashlite.md).
- [x] Medir acuerdo con David en los 36, no si la cobertura vuelve a 80/100.
  Hecho sobre 35 ids.
- [ ] Readjudicar los casos conflictivos con la rúbrica cerrada y recalcular
  precisión, recall, matriz de confusión y concordancia de todos los jueces.
- [ ] Elegir juez. Hasta entonces Pro se conserva solo por continuidad; no
  está demostrado que sea más preciso que Flash 2.5 o Flash 3.8.

### 5c. Revisión de Julián del examen — pendiente

No es un run. Es cerrar diseño: métricas, juez binario vs grado,
capas ICD/BERT, y si Flash / `gemini-3.8-flash` pueden sustituir a
Pro. Brief:

[JULIAN_HARNESS_REVIEW.md](JULIAN_HARNESS_REVIEW.md).

- [ ] Julián responde las preguntas del brief (cobertura ≠ precisión;
  R@1 como P@1; escala 2/1/0; hermanos ICD; modelo del juez).
- [ ] No poner Flash como juez publicado hasta esa respuesta.
- [x] Curiosidad (2026-09-09): `gemini-3.8-flash` low, mismo 5b.
  Acuerdo bruto 28/35 con las etiquetas iniciales de David y cobertura
  72/100. No interpretarlo como peor precisión: varios desacuerdos favorecen
  a 3.8 al contrastarlos con el artículo fuente.
  Informe:
  [results/2026-09-09-judge-ablation-gemini38flash.md](results/2026-09-09-judge-ablation-gemini38flash.md).
- [ ] Tras cerrar la política, apagar **solo** hermanos ICD en las listas
  congeladas de Terra low y mini, y medir el delta de R@1/cobertura y los
  ids afectados. Después, en experimentos separados, parent y BERT.

```powershell
py "bench\multimodal_beta\evaluate_v4.py" `
  --responses "bench\multimodal_beta\outputs\pilot100_product\responses.jsonl" `
  --reuse-labeled "bench\multimodal_beta\outputs\pilot100_product\evaluation_v4_primary_strict\labeled_input.json" `
  --judge-model "gemini-2.5-flash" `
  --judge-mode strict_equivalence `
  --output-dir "bench\multimodal_beta\outputs\judge_audit\pilot100_ti_gemini25flash"
```

### 6. Comparabilidad con benchmarks narrativos — pendiente

No se debe convertir `legacy_similarity` en la métrica principal del track
multimodal. Para construir un puente:

- [x] Reevaluar las respuestas multimodales de 100 casos también con
  `legacy_similarity`, sin repetir inferencia ni MedLabeler.
- [x] Reevaluar `gpt-5.4-mini low` y `gpt-5.6-terra low` sobre `all_256_clean`
  sin repetir inferencia (2026-08-31).
  - Mini: 98,1% legacy → 79,7% strict.
  - Terra: 98,1% legacy → 83,2% strict.
  - Informe:
    [results/2026-08-31-all256-judge-audit-strict-mini-terra.md](results/2026-08-31-all256-judge-audit-strict-mini-terra.md).
- [x] Reevaluar gemini-3-pro-preview low, gpt-5.6-sol medium y gpt-4o low
  (2026-09-08). Informe:
  [results/2026-09-08-all256-judge-audit-strict-gemini3pro-sol-gpt4o.md](results/2026-09-08-all256-judge-audit-strict-gemini3pro-sol-gpt4o.md).
  Strict: Terra 83% > Sol 82% > mini 80% > gemini-3-pro = gpt-4o 75%.
  El 98% de gemini-3-pro era el juez legacy (listas DDX congeladas; solo
  cambia el árbitro).
- [x] Astra `all_256_clean` (2026-09-08): `gpt-6-astra` +
  `reasoning_effort: low` + `juanjo_classic_v2`. Inferencia nueva, luego
  re-score strict. Legacy 98,1% / R@1 72,3% / pos. 1,442. Strict: cobertura
  83,2% (empate con Terra), R@1 62,1% (Terra 63,3%). Informe:
  [results/2026-09-08-all256-judge-audit-strict-gpt6astra.md](results/2026-09-08-all256-judge-audit-strict-gpt6astra.md).
- [x] gemini-3.1-pro-preview low (2026-09-09). Informe:
  [results/2026-09-09-all256-judge-audit-strict-gemini31pro.md](results/2026-09-09-all256-judge-audit-strict-gemini31pro.md).
  Strict: R@1 61,3%, cobertura 75% (192/256), igual que 3-pro. LLM 75→17.
  El 98,1% / 1,267 del HTML oficial era el juez legacy.
- [x] gemini-3.5-flash low (2026-09-09). Informe:
  [results/2026-09-09-all256-judge-audit-strict-gemini35flash.md](results/2026-09-09-all256-judge-audit-strict-gemini35flash.md).
  Strict: R@1 62,1% (empate Astra), cobertura 75,4% (193/256). Gana a
  3.1-pro en R@1. LLM 72→14. El 97,7% legacy era el juez.
- [x] gemini-3.1-flash-lite low (2026-09-09). Informe:
  [results/2026-09-09-all256-judge-audit-strict-gemini31flashlite.md](results/2026-09-09-all256-judge-audit-strict-gemini31flashlite.md).
  Strict: R@1 57,8%, cobertura 78,1% (200/256). No gana a mini
  (58,2% / 79,7%). LLM 83→27.
- [x] gemini-2.5-flash low (2026-09-09). Informe:
  [results/2026-09-09-all256-judge-audit-strict-gemini25flash.md](results/2026-09-09-all256-judge-audit-strict-gemini25flash.md).
  Strict: R@1 56,6%, cobertura 74,2% (190/256). Por debajo de gpt-4o.
  LLM 82→20.
- [x] gpt-5.4 full low (2026-09-09). Informe:
  [results/2026-09-09-all256-judge-audit-strict-gpt54.md](results/2026-09-09-all256-judge-audit-strict-gpt54.md).
  Strict: R@1 62,9%, cobertura 86,3% (221/256, la más alta). Gana a mini.
  Terra sigue 1º por R@1 (63,3%). LLM 64→27.
- [x] gemini-3-pro-preview medium (2026-09-09). Informe:
  [results/2026-09-09-all256-judge-audit-strict-gemini3pro-medium.md](results/2026-09-09-all256-judge-audit-strict-gemini3pro-medium.md).
  Strict peor que low en R@1 y cobertura (59,4% / 73% vs 59,8% / 75%).
  Medium no usar. LLM 81→17.
- [x] gpt-5.6-terra high (2026-09-09). Informe:
  [results/2026-09-09-all256-judge-audit-strict-terra-high.md](results/2026-09-09-all256-judge-audit-strict-terra-high.md).
  Strict: R@1 62,5% < low 63,3%; cobertura 85,2% > low 83,2%. Low sigue
  1º por R@1. LLM 71→35.
- [x] gpt-5.6-terra medium (2026-09-09). Informe:
  [results/2026-09-09-all256-judge-audit-strict-terra-medium.md](results/2026-09-09-all256-judge-audit-strict-terra-medium.md).
  Strict: R@1 62,5% (empate high), cobertura 84,4% < high 85,2%. Low
  sigue 1º. LLM 73→32.
- [x] gpt-5.6-terra xhigh (2026-09-09, merge 20k). Informe:
  [results/2026-09-09-all256-judge-audit-strict-terra-xhigh.md](results/2026-09-09-all256-judge-audit-strict-terra-xhigh.md).
  Strict: R@1 62,5% (empate high/medium), cobertura 79,7% (peor Terra).
  LLM 75→29. No usar. Low sigue 1º. El HTML oficial no se toca.
- [x] gpt-5.6-sol low (2026-09-09). Informe:
  [results/2026-09-09-all256-judge-audit-strict-sol-low.md](results/2026-09-09-all256-judge-audit-strict-sol-low.md).
  Strict: R@1 59,0% < medium 60,9%; cobertura 80,9%. Gana a mini.
  Mantener medium. LLM 74→24. Cola luna+sol cerrada.
- [x] gpt-5.6-luna low (2026-09-09). Informe:
  [results/2026-09-09-all256-judge-audit-strict-luna-low.md](results/2026-09-09-all256-judge-audit-strict-luna-low.md).
  Strict: R@1 57,0% < mini 58,2%; cobertura 79,7% (igual que mini). No
  desplaza a mini. LLM 79→29.
- [x] gpt-5.6-luna medium (2026-09-09). Informe:
  [results/2026-09-09-all256-judge-audit-strict-luna-medium.md](results/2026-09-09-all256-judge-audit-strict-luna-medium.md).
  Strict: R@1 56,6% < low 57,0%; misma cobertura 79,7%. Medium no usar.
  LLM 80→31.
- [x] gpt-5.6-luna high (2026-09-09). Informe:
  [results/2026-09-09-all256-judge-audit-strict-luna-high.md](results/2026-09-09-all256-judge-audit-strict-luna-high.md).
  Strict: R@1 60,9% > low 57,0%; cobertura 83,6%. Invierte la decisión
  legacy (mantener low). Empate R@1 con Sol medium, más cobertura.
  LLM 71→31.
- [x] gpt-5.6-luna xhigh (2026-09-09). Informe:
  [results/2026-09-09-all256-judge-audit-strict-luna-xhigh.md](results/2026-09-09-all256-judge-audit-strict-luna-xhigh.md).
  Strict: R@1 55,5%, cobertura 75% (22 EMPTY a 12k). Inválido. No usar.
  LLM 73→34.
- [ ] Reevaluar todo el histórico solo si cambia una conclusión o ranking
  relevante.
- [ ] Etiquetar explícitamente cada resultado como `legacy_similarity` o
  `strict_equivalence`.
- `docs/benchmark-report.html` **no se reescribe**. Las cifras strict van
  a `docs/benchmark-report-strict-texto.html` y
  `docs/benchmark-report-strict-multimodal.html`.

### 7. Comparación de modelos multimodales — pendiente

- [x] Establecer `gpt5` como primera línea base con visión.
- [ ] Confirmar qué modelos reciben realmente las imágenes en el servidor.
- [x] Integrar visión para GPT-5.6 Terra en Server (`feature/terra-westus-vision`).
  Deployment `gpt-5.6-terra` solo en WestUS (`us1`). Slug interno
  `gpt56terra`. No es producto: solo override de eval.
- [x] Ejecutar Terra T+I en los mismos 100 casos (2026-09-08).
  Informe:
  [results/2026-09-08-medreamm-pilot100-t-plus-i-gpt56terra.md](results/2026-09-08-medreamm-pilot100-t-plus-i-gpt56terra.md).
- [x] Ejecutar Terra `T` (mismo modelo, sin imágenes) para la ablación.
  Informe:
  [results/2026-09-08-medreamm-pilot100-t-gpt56terra.md](results/2026-09-08-medreamm-pilot100-t-gpt56terra.md).
- [x] Comparar Terra con `gpt5` en T y en T+I, mismo juez.
  - T+I: Terra 84/67% vs gpt5 80/61%; McNemar cobertura `p≈0,45`.
  - T: Terra 65/50% vs gpt5 64/43%; McNemar cobertura `p≈1`.
  - Terra T vs T+I: +19 cobertura, 24 vs 5, `p=0,00055`. Usa la imagen.
- [x] Ejecutar Astra T+I (WestUS, slug `gpt6astra`). Informe:
  [results/2026-09-08-medreamm-pilot100-t-plus-i-gpt6astra.md](results/2026-09-08-medreamm-pilot100-t-plus-i-gpt6astra.md).
  R@1 76% vs gpt5 61% (`p=0,0059`); cobertura 88% vs 80% (`p=0,057`).
  vs Terra no significativo.
- [x] Ejecutar Astra `T`. Informe:
  [results/2026-09-08-medreamm-pilot100-t-gpt6astra.md](results/2026-09-08-medreamm-pilot100-t-gpt6astra.md).
  T 67/54% vs T+I 88/76%; 22 vs 1, `p=0,00001`. Usa la imagen.
- Decisión (2026-09-08, actualizada 09): **Astra no a producto ni a
  override de eval.** Quitar del Server. Terra sigue como override de
  eval; un A/B de producto Mini/Terra es otra decisión.
- [x] HMS HPO 88, Astra vs Terra, mismo juez strict (2026-09-09).
  Cobertura Terra 65,9% > Astra 59,1%; R@1 empatado 43,2%. No gana raras.
  Informe:
  [results/2026-09-09-hms88-gpt6astra.md](results/2026-09-09-hms88-gpt6astra.md).

### 8. Ablación de resumen — hecha

- [x] Ablación resumen (2026-09-09): los 32 casos de gpt5 T+I que se
  resumieron, mismos casos T+I, **sin resumen**, mismo gpt5. Flag
  eval-only `skipSummarize`. Informe:
  [results/2026-09-09-medreamm-pilot32-t-plus-i-gpt5-nosummary.md](results/2026-09-09-medreamm-pilot32-t-plus-i-gpt5-nosummary.md).
  Cobertura 27/32 vs 30/32 con resumen (3 vs 0, `p=0,25`); R@1 22 vs 21
  (`p=1,0`). **El umbral de 1.000 caracteres se queda.**

## Orden recomendado

1. David completa [MEDICAL_REVIEW.md](MEDICAL_REVIEW.md) y devuelve
   [reviews/david_deliverable.md](reviews/david_deliverable.md).
   **Hecho.**
2. David recorre los 20 unmatched y los 16 LLM: **hecho**, pendiente
   `24910386`.
3. Julián fija la rúbrica y las métricas
   ([JULIAN_HARNESS_REVIEW.md](JULIAN_HARNESS_REVIEW.md)).
4. David readjudica solo los casos conflictivos; recalcular 5b y elegir juez.
5. Publicar el 80/100 únicamente como resultado automático provisional
   (`strict_equivalence`, Pro) hasta cerrar esa adjudicación. No presentar
   80 ni 81 como precisión clínica final.
6. Aplicar el juez strict a artefactos narrativos ya etiquetados (puente
   con producción, Terra low, Sol medium y baseline).
7. ~~Integrar visión para Terra y comparar `T` frente a `T+I`.~~ Hecho
   (2026-09-08): Terra usa la imagen (`p=0,00055`).
8. ~~Medir el efecto del resumen de 1.000 caracteres.~~ Hecho
   (2026-09-09): saltarlo no gana cobertura. El umbral se queda.

## Criterio de cierre

El track estará listo para una conclusión de producto cuando:

- las cuatro condiciones de modalidad estén completas sobre casos válidos;
- la política de equivalencia esté clínicamente adjudicada;
- exista una estimación del efecto de las imágenes con intervalo de confianza;
- se conozcan falsos positivos y falsos negativos del evaluador;
- el modelo comparado reciba realmente las mismas modalidades;
- los resultados sean reproducibles desde manifest, respuestas y
  configuración guardada.
