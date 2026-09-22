# DxGPT — roadmap operativo

**Actualizado:** 2026-09-21
**Estado:** decisión de producto cerrada; Home y Preguntas médicas ya están separados.

## Decisión vigente de producto

DxGPT se simplifica a **un único modelo visible: `gpt-5.6-terra`**, para
todos los flujos: diagnóstico en Home y preguntas médicas generales en Beta.

- No habrá modo avanzado ni selector de modelo.
- No habrá segunda opinión basada en otro modelo.
- No habrá un camino de producto con Gemini.
- Home acepta texto, imágenes y documentos.
- Preguntas médicas es una página aparte, no un input mixto; Aragón igual.
- El fallback interno será entre deployments regionales de Terra, nunca a
  mini, gpt5 o Gemini. Cada región deberá validar disponibilidad, capacidad y
  soporte de visión antes de entrar en la cadena.

La separación Home / Preguntas médicas ya está en Client y Server. El flip
de Terra y el fallback regional siguen pendientes.

## Estado actual

### Producto

- La dirección de producto anterior (modelo normal + avanzado/Gemini) queda
  reemplazada por la decisión de modelo único.
- Terra ya tiene evidencia de evaluación en texto y texto+imagen, pero eso no
  equivale a un despliegue de producto. En MedReaMM, `T+I` obtuvo
  cobertura/R@1 84%/67% frente a 65%/50% con `T` (`p=0,00055`).
- Home ya acepta texto, imágenes y documentos; Preguntas médicas es una
  página aparte (también en Aragón). El fallback regional de Terra sigue
  pendiente.
- La estrategia regional de fallback Terra está por validar e implementar.

### Evaluación y publicación

- Los datasets, runs y métricas completados siguen siendo evidencia histórica.
- `strict_equivalence` es la métrica canónica para interpretación actual;
  `legacy_similarity` solo sirve de puente con resultados históricos.
- La calibración clínica del evaluador sigue abierta: la rúbrica, los golds
  ambiguos y las capas automáticas deben cerrarse antes de presentar cifras
  como precisión clínica definitiva.
- El trabajo de Julián sigue siendo necesario para publicación e
  interpretación clínica, **no para seleccionar el modelo de producto**.

## Trabajo pendiente de producto

> Implementación fuera del alcance de este cambio documental.

- [ ] Confirmar deployments regionales de `gpt-5.6-terra` y documentar por
  región: capacidad, cuota, latencia, soporte de visión y formatos admitidos.
- [ ] Diseñar routing con Terra primario y fallback Terra regional, sin
  degradación silenciosa a otra familia de modelos.
- [ ] Dejar un solo modelo diagnóstico visible en todos los puntos de entrada.
- [ ] Retirar de la experiencia de producto el modo avanzado, la segunda
  opinión y cualquier ruta/configuración de Gemini.
- [x] Habilitar en Home texto, imágenes y documentos: imágenes directas a
  Terra vision; documentos extraídos primero a texto; validación explícita
  de tipos, tamaño y errores.
- [x] Limitar Beta a preguntas médicas generales y separar ese flujo del
  diagnóstico de Home. Aragón/SaludGPT usa la misma separación.
- [ ] Añadir telemetría y pruebas de regresión que acrediten modelo solicitado,
  deployment final, modalidad recibida y fallback aplicado.
- [ ] Preparar despliegue gradual y rollback antes de cualquier flip real.

## Trabajo pendiente de evaluación/publicación

- [x] Preparar el benchmark sintético de imagen documental en
  [`bench/document_image_beta`](../bench/document_image_beta/README.md):
  10 casos sin PII, 50 variantes end-to-end y controles médicos MedReaMM.
- [x] Ejecutar la clasificación `document_image` / `medical_image` / `mixed`
  y el manifest end-to-end: ruta 45/45, 0/10 imágenes médicas a OCR; PDF
  nativo/escaneado conservó 100%/97,5% de hechos frente a 10% en escaneo PNG
  directo. En strict, ambos PDF lograron cobertura 10/10 frente a 1/10 del
  escaneo directo. [Informe](../bench/document_image_beta/RESULTS.md).
- [x] Validar V1 end-to-end sobre las mismas 50 entradas: ruta 30/30,
  documentos-imagen puros con 100% de hechos y cobertura 21/21; strict global
  sube de cobertura/R@1 54%/44% a 86%/68%. Las imágenes mixtas con visión
  directa solo conservan 22,2% de los hechos.
- [x] Comparar `OCR + imagen original` frente a visión directa en nueve
  imágenes mixtas: hechos, cobertura y R@1 pasan de 2/9 a 9/9; coste por caso
  cubierto baja de 0,0361 a 0,0263 USD; latencia híbrida media 27,84 s.
- [x] Implementar la ruta híbrida mixta y su fallback OCR → visión en Server,
  manteniendo imagen original y resumen por encima de 1.000 caracteres.
- [x] Repetir las nueve regresiones mixtas contra el flujo real actualizado:
  OCR + visión 9/9, hechos y cobertura 9/9, strict repetido 9/9, 28,18 s de
  latencia media y 0,02676 USD por caso. El primer juez dio 8/9 y el segundo
  aceptó la misma equivalencia, por lo que se documenta su inestabilidad.
- [ ] Cerrar la segunda revisión antes de convertir el piloto en gate:
  preauditoría completada sobre 12 etiquetas MedReaMM, 10 casos y 41 hechos;
  11 etiquetas confirmadas y `N-10000022` corregida a mixta, con ruta híbrida
  confirmada por Terra y GPT-5.4-mini. Falta la firma independiente del
  biomédico y resolver sus posibles desacuerdos.
- [x] Reevaluar `o3-dxgpt high` en `all_256_clean` con strict como referencia
  del otro tenant: R@1 56,6%, cobertura 80,9%; no supera a Terra.
- [x] Evaluar `grok-4.6 low` y `claude-opus-5 low` sobre los 256 casos
  narrativos con el mismo prompt y strict. Grok queda 3º: R@1 62,9%,
  cobertura 81,6%, 17,0 s/caso. Claude, tras corregir el parseo de
  `thinking`: R@1 59,4%, cobertura 87,1%, 22,7 s/caso. El 35,2% era inválido.
  [Informe](../bench/multimodal_beta/results/2026-09-17-all256-strict-grok46-claude-opus5.md).
- [x] Reevaluar con strict las 3.017 respuestas HPO congeladas de Terra:
  DDD, RAMEDIS, LIRICAL, MME, MyGene2 y HMS. Total ponderado R@1 29,8%,
  cobertura 46,7%; cero errores finales. No hubo nueva inferencia, MedLabeler
  ni SapBERT. [Informe](../bench/multimodal_beta/results/2026-09-16-rare-hpo-terra-strict.md).
- [x] Medir jueces Pro, Flash dinámico/sin thinking, Grok y Kimi sobre las 256
  listas congeladas de Terra, incluyendo tokens, latencia y coste. Flash sin
  thinking: $0,0087 y p50 0,57 s vs $1,800 y 9,60 s de Pro.
- [x] Ejecutar `Kimi-K2.6` mediante el deployment Azure de `dxgptbot`:
  $1,125, p50 6,09 s, p95 39,62 s y 28/35 frente a las etiquetas humanas
  iniciales. No promover.
- [ ] **David — nueva tarea, no continuación de ronda 2:** revisar las
  13 discrepancias que deciden Pro vs Flash sin thinking en la
  [tarea ciega](../bench/multimodal_beta/reviews/david_review_all256_pro_vs_flash_blind.md).
  Entrega: gold válido/ambiguo, posición equivalente o 0 y justificación
  breve. Las discrepancias adicionales de Kimi/Grok quedan fuera porque no son
  candidatos a juez.
- [ ] DeepSeek V4 Flash está retirado y V4 Pro redirige actualmente a V4.1
  Flash: probar solo `deepseek-flash` cuando exista acceso verificable.
- [ ] Mantener una tarea continua de radar, no de selección de producto:
  evaluar modelos nuevos únicamente cuando estén disponibles por API y aporten
  una hipótesis concreta. Próximos candidatos: Kimi K3/K2.6, Grok posterior a
  4.6, DeepSeek V4.1 Pro, próximos Gemini Flash y lanzamientos médicos o
  multimodales de Qwen/Alibaba. Metodología: strict, regresión congelada,
  coste/latencia y auditoría humana del juez. Terra sigue siendo el único
  modelo de producto salvo decisión explícita posterior.
- [ ] Julián cierra la rúbrica: métrica principal, escala binaria o 2/1/0,
  tratamiento de especificidad/subtipos y papel de ICD/BERT.
- [ ] Al recibir la nueva revisión de David, recalcular acuerdo,
  precisión/recall y matriz de confusión Pro vs Flash sin thinking.
- [ ] Ablacionar por separado hermanos ICD, padres ICD y umbrales BERT sobre
  listas congeladas; no mezclar cambios en una sola medición.
- [ ] Etiquetar toda cifra publicada como `strict_equivalence` o
  `legacy_similarity` y distinguir R@1, recall de lista y posición media.
- [ ] Actualizar los informes publicables solo cuando la política clínica y la
  readjudicación estén cerradas.
- [ ] Cerrar la revisión manual de fugas y la calidad, el rol y la granularidad
  de los gold antes de presentar una conclusión clínica.
- [ ] Mantener trazabilidad desde manifest, respuestas, configuración y juez.

## Cancelado por simplificación de producto

- [x] **Selección de un modelo avanzado/Gemini:** cancelada; ya no existe ese
  rol en el producto.
- [x] **DDD strict para decidir el avanzado:** cancelado como criterio de
  selección. Posteriormente se ejecutó dentro del benchmark HPO de Terra para
  documentar el modelo único de producción, no para recuperar un modo avanzado.
- [x] **Runs adicionales de Gemini/HPO destinados a elegir avanzado:**
  cancelados por la misma razón.
- [x] **Segunda opinión con un modelo distinto:** cancelada.
- [x] **Fallback a mini, gpt5 o Gemini:** descartado; el objetivo es fallback
  Terra entre regiones compatibles.

Los runs Gemini/HMS ya completados no se eliminan ni se invalidan: permanecen
como evidencia histórica y metodológica en el
[índice de resultados](../bench/multimodal_beta/RESULTS.md) y en el
[historial detallado](ROADMAP_HISTORY.md). No gobiernan la selección de
producto vigente.

## Fuera de alcance / diferido

- Código de UI o Server, configuración cloud y cambios de producción.
- MIMIC-IV, nuevos datasets y estratificaciones adicionales: opcionales para
  una futura publicación, no necesarios para la simplificación de producto.
- Validación clínica ampliada: deseable para publicación de mayor impacto,
  pero separada del lanzamiento del modelo único.
- Repetir todo el histórico: solo si cambia una conclusión publicable.

## Comprobaciones de aceptación

### Para este cambio documental

- [x] La decisión de modelo único Terra aparece primero y sin ambigüedad.
- [x] Producto y evaluación/publicación están separados.
- [x] Avanzado/Gemini y DDD-for-advanced figuran como **cancelados**.
- [x] El historial anterior se conserva íntegro en el documento complementario.
- [x] Se declara explícitamente que no hubo flip de producción.

### Para la futura implementación de producto

- [ ] Solo Terra es visible y solicitado en Home y Beta.
- [x] Home acepta texto e imágenes con Terra; los documentos se extraen a
  texto antes de enviarlos a Terra.
- [x] Beta ofrece únicamente preguntas médicas generales.
- [ ] No quedan controles ni rutas activas de avanzado, segunda opinión o
  Gemini en la experiencia de producto.
- [ ] Todo fallback termina en otro deployment Terra previamente validado.
- [ ] Logs y pruebas confirman modalidad, región, modelo solicitado y modelo
  final sin fallback oculto a mini/gpt5/Gemini.

## Fuentes y detalle

- [Historial completo del roadmap principal](ROADMAP_HISTORY.md)
- [Historial detallado del antiguo roadmap multimodal](../bench/multimodal_beta/ROADMAP_HISTORY.md)
- [Índice de resultados multimodales y strict](../bench/multimodal_beta/RESULTS.md)
- [Brief de Julián sobre el evaluador](../bench/multimodal_beta/JULIAN_HARNESS_REVIEW.md)
- [Informe strict de texto](benchmark-report-strict-texto.html)
- [Informe HPO completo de Terra con strict](../bench/multimodal_beta/results/2026-09-16-rare-hpo-terra-strict.md)
- [Informe de coste, latencia y acuerdo de jueces](benchmark-report-jueces.html)
- [Log histórico del pipeline](pipeline/experiment-log.md)