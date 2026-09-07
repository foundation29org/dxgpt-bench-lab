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
- [ ] Adjudicar los 20 unmatched y los 16 matches LLM de la corrida T+I de
  100. Guía: [MEDICAL_REVIEW_RONDA2.md](MEDICAL_REVIEW_RONDA2.md).
  Entregable:
  [reviews/david_deliverable_ronda2.md](reviews/david_deliverable_ronda2.md).
- [ ] Fijar una política para golds amplios, fenotípicos o morfológicos.
- [ ] Decidir si se publican dos métricas: equivalencia exacta y utilidad
  clínica.

### 5b. Ablación del modelo del juez — ⏳ PENDIENTE (después de la ronda 2)

Ingeniería tuya, no de David. Bloqueada hasta que cierre
[reviews/david_deliverable_ronda2.md](reviews/david_deliverable_ronda2.md).

Cuando David cierre los 36 casos, esas etiquetas son el gold del **árbitro**,
no de DxGPT. Entonces se prueban otros `JUDGE_MODEL` con el mismo prompt
`strict_equivalence`, las mismas 100 respuestas y el mismo
`labeled_input.json`. No se repite inferencia.

Objetivo: un juez más rápido y barato que **acuerde con David** en esos 36
casi tanto como `gemini-2.5-pro`. No es “poner el último modelo”. Un Flash
que cubra 80/100 pero se equivoque en sitios distintos no vale.

Métrica: precisión / FP / FN frente a David en unmatched + LLM. La cobertura
de los 100 es secundaria (SNOMED/ICD/BERT no se mueven; solo esos 36 pueden
cambiar).

- [ ] Esperar ronda 2 de David (36 veredictos = gold del juez).
- [ ] Reusar `labeled_input.json` de T+I; no repetir inferencia ni MedLabeler.
- [ ] Probar primero jueces baratos/rápidos (Flash / mini), no flagships.
- [ ] Medir acuerdo con David en los 36, no si la cobertura vuelve a 80/100.
- [ ] Conservar `gemini-2.5-pro` como referencia; un flagship nuevo solo si
  los baratos fallan el criterio de David.
- [ ] Si un barato empata con Pro vs David, documentar y considerar
  sustituir el juez de evaluación.

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
- [ ] Tras calibración clínica, aplicar el mismo juez a:
  - gemini-3-pro-preview low;
  - GPT-5.6 Sol medium;
  - principal baseline histórico.
- [ ] Comparar cambios de ranking y falsos positivos.
- [ ] Reevaluar todo el histórico solo si cambia una conclusión o ranking
  relevante.
- [ ] Etiquetar explícitamente cada resultado como `legacy_similarity` o
  `strict_equivalence`.

### 7. Comparación de modelos multimodales — pendiente

- [x] Establecer `gpt5` como primera línea base con visión.
- [ ] Confirmar qué modelos reciben realmente las imágenes en el servidor.
- [ ] Integrar visión para GPT-5.6 Terra antes de evaluarlo como multimodal.
- [ ] Ejecutar Terra low con `T` y `T+I` cuando ambas condiciones usen el mismo
  modelo y el mismo contenido.
- [ ] Comparar Terra con `gpt5` sin mezclar cambios de prompt, juez o resumen.

Terra no debe evaluarse todavía como sustituto multimodal si el servidor no le
envía las imágenes. Una ejecución Terra `T` mediría únicamente texto.

### 8. Ablación de resumen — pendiente

- [ ] Identificar los casos resumidos en la cohorte de 100.
- [ ] Repetir esos mismos casos sin resumen o con umbral superior.
- [ ] Comparar pérdidas de información, latencia y acierto.
- [ ] Decidir si el umbral de 1.000 caracteres debe mantenerse.

## Orden recomendado

1. David completa [MEDICAL_REVIEW.md](MEDICAL_REVIEW.md) y devuelve
   [reviews/david_deliverable.md](reviews/david_deliverable.md).
   **Hecho.**
2. David recorre los 20 unmatched y los 16 LLM
   ([MEDICAL_REVIEW_RONDA2.md](MEDICAL_REVIEW_RONDA2.md)).
3. Decidir si 80/100 y la ganancia visual se pueden publicar.
4. Tras David: probar jueces baratos/rápidos contra sus 36 etiquetas
   (§5b). No lanzar antes.
5. Aplicar el juez strict a artefactos narrativos ya etiquetados (puente
   con producción, Terra low, Sol medium y baseline).
6. Integrar visión para Terra y entonces comparar `T` frente a `T+I`.
7. Medir el efecto del resumen de 1.000 caracteres.

## Criterio de cierre

El track estará listo para una conclusión de producto cuando:

- las cuatro condiciones de modalidad estén completas sobre casos válidos;
- la política de equivalencia esté clínicamente adjudicada;
- exista una estimación del efecto de las imágenes con intervalo de confianza;
- se conozcan falsos positivos y falsos negativos del evaluador;
- el modelo comparado reciba realmente las mismas modalidades;
- los resultados sean reproducibles desde manifest, respuestas y
  configuración guardada.
