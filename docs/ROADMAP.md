# DxGPT — roadmap operativo

**Actualizado:** 2026-09-15
**Estado:** decisión de producto cerrada; implementación UI/Server pendiente.

## Decisión vigente de producto

DxGPT se simplifica a **un único modelo visible: `gpt-5.6-terra`**, para
todos los flujos: diagnóstico en Home y preguntas médicas generales en Beta.

- No habrá modo avanzado ni selector de modelo.
- No habrá segunda opinión basada en otro modelo.
- No habrá un camino de producto con Gemini.
- Home evolucionará para aceptar texto, imágenes y documentos con Terra.
- Beta quedará solo para preguntas médicas generales, no para diagnóstico.
- El fallback interno será entre deployments regionales de Terra, nunca a
  mini, gpt5 o Gemini. Cada región deberá validar disponibilidad, capacidad y
  soporte de visión antes de entrar en la cadena.

Esta edición es exclusivamente documental. **No cambia producción, no activa
Terra y no modifica UI, Server, routing ni deployments.**

## Estado actual

### Producto

- La dirección de producto anterior (modelo normal + avanzado/Gemini) queda
  reemplazada por la decisión de modelo único.
- Terra ya tiene evidencia de evaluación en texto y texto+imagen, pero eso no
  equivale a un despliegue de producto. En MedReaMM, `T+I` obtuvo
  cobertura/R@1 84%/67% frente a 65%/50% con `T` (`p=0,00055`).
- La implementación de Home multimodal/documental y la simplificación de Beta
  están pendientes.
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
- [ ] Habilitar en Home texto, imágenes y documentos: imágenes directas a
  Terra vision; documentos extraídos primero a texto; validación explícita
  de tipos, tamaño y errores.
- [ ] Limitar Beta a preguntas médicas generales y separar ese flujo del
  diagnóstico de Home.
- [ ] Añadir telemetría y pruebas de regresión que acrediten modelo solicitado,
  deployment final, modalidad recibida y fallback aplicado.
- [ ] Preparar despliegue gradual y rollback antes de cualquier flip real.

## Trabajo pendiente de evaluación/publicación

- [ ] Julián cierra la rúbrica: métrica principal, escala binaria o 2/1/0,
  tratamiento de especificidad/subtipos y papel de ICD/BERT.
- [ ] David readjudica únicamente los casos conflictivos con la rúbrica
  cerrada; recalcular acuerdo, precisión/recall y matriz de confusión del juez.
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
- [x] **DDD strict para decidir el avanzado:** cancelado; no está bloqueado ni
  pendiente. No se justifica gastar horas de juez para una decisión eliminada.
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
- [ ] Home acepta texto e imágenes con Terra; los documentos se extraen a
  texto antes de enviarlos a Terra.
- [ ] Beta ofrece únicamente preguntas médicas generales.
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
- [Log histórico del pipeline](pipeline/experiment-log.md)