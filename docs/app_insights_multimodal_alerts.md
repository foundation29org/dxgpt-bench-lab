# Workbook y alertas multimodales (Application Insights)

Hacerlo al subir a producción, cuando `insightsdxgpt` ya reciba análisis reales. Antes la consulta sale vacía y no se puede comprobar el recurso.

No tocar las reglas que ya existen: `errors dxgpt` y `Failure Anomalies - insightsdxgpt`.

El `ocr_failed` de la consulta diaria no sube: el servidor no escribe `customDimensions.code = "ocr_failed"` en esos tres eventos. Cuando el OCR de una imagen de documento falla, queda un evento `Error` con el mensaje `Document image OCR failed`. Esa es la señal de la cuarta alerta.

## 1. Comprobar que hay datos

En `insightsdxgpt`, **Logs**:

```kusto
customEvents
| where timestamp > ago(1d)
| where name in ("MultimodalAnalysisCompleted", "MultimodalAnalysisFailed", "MultimodalInputRejected")
| summarize
    completed = countif(name == "MultimodalAnalysisCompleted"),
    failed = countif(name == "MultimodalAnalysisFailed"),
    rejected = countif(name == "MultimodalInputRejected"),
    p95ms = percentile(todouble(customMeasurements.durationMs), 95),
    failedDocs = sum(todouble(customMeasurements.failedDocuments)),
    ocrFailed = countif(tostring(customDimensions.code) == "ocr_failed")
```

Si salen filas, seguir. Si sale vacío, este recurso no está recibiendo la telemetría del servidor.

La primera semana, ejecutar esta consulta una vez al día aunque las alertas ya existan.

## 2. Workbook

**Workbooks** → **New**. Nombre: `Multimodal analysis`.

En cada bloque: **Add** → **Add query**, Time range = **Set in query**. Timechart en las series, grid en las tablas.

Volumen por hora:

```kusto
customEvents
| where timestamp > ago(1d)
| where name in ("MultimodalAnalysisCompleted", "MultimodalAnalysisFailed", "MultimodalInputRejected")
| summarize count() by bin(timestamp, 1h), name
| render timechart
```

Latencia p50 y p95. Los rechazos de validación no entran: son rápidos y bajan el percentil.

```kusto
customEvents
| where timestamp > ago(1d)
| where name in ("MultimodalAnalysisCompleted", "MultimodalAnalysisFailed")
| summarize
    p50ms = percentile(todouble(customMeasurements.durationMs), 50),
    p95ms = percentile(todouble(customMeasurements.durationMs), 95)
    by bin(timestamp, 1h)
| render timechart
```

Porcentaje de documentos fallidos:

```kusto
customEvents
| where timestamp > ago(1d)
| where name in ("MultimodalAnalysisCompleted", "MultimodalAnalysisFailed")
| summarize
    failedDocs = sum(todouble(customMeasurements.failedDocuments)),
    okDocs = sum(todouble(customMeasurements.succeededDocuments))
    by bin(timestamp, 1h)
| extend total = failedDocs + okDocs
| extend failedPct = iff(total == 0, 0.0, round(100.0 * failedDocs / total, 1))
| project timestamp, failedPct, failedDocs, okDocs
```

Rutas de imagen y fallbacks:

```kusto
customEvents
| where timestamp > ago(1d)
| where name == "MultimodalAnalysisCompleted"
| summarize
    analyses = count(),
    ocrText = sum(todouble(customMeasurements.documentImageRoutes)),
    mixed = sum(todouble(customMeasurements.mixedImageRoutes)),
    vision = sum(todouble(customMeasurements.visionImageRoutes)),
    fallbacks = sum(todouble(customMeasurements.imageFallbacks)),
    notMedical = sum(todouble(customMeasurements.notMedicalImages))
```

Fallos recientes, solo con `correlationId`:

```kusto
customEvents
| where timestamp > ago(1d)
| where name == "MultimodalAnalysisFailed"
| project
    timestamp,
    correlationId = tostring(customDimensions.correlationId),
    phase = tostring(customDimensions.phase),
    code = tostring(customDimensions.code),
    durationMs = todouble(customMeasurements.durationMs)
| order by timestamp desc
| take 50
```

**Save**.

## 3. Grupo de acciones

Abrir `errors dxgpt` → **Actions** y anotar el action group. Las cuatro alertas nuevas usan ese mismo grupo.

## 4. Alertas

**Alerts** → **Create** → **Alert rule**. Scope: `insightsdxgpt`. Condición: **Custom log search**.

En las cuatro: evaluar cada **5 minutos**, ventana de **15 minutos**, **Auto-mitigate** activado. La consulta ya lleva el umbral. Lógica: **Number of results greater than 0**.

### Análisis fallidos > 5 %

Severidad 2. Nombre: `Multimodal analysis failure rate > 5%`.

Los rechazos de validación (`MultimodalInputRejected`) no cuentan. `total >= 10` evita que un solo fallo con poco tráfico dispare la alerta; bajar ese 10 si el volumen diario es bajo.

```kusto
customEvents
| where timestamp > ago(15m)
| where name in ("MultimodalAnalysisCompleted", "MultimodalAnalysisFailed")
| summarize
    failed = countif(name == "MultimodalAnalysisFailed"),
    total = count()
| extend failPct = iff(total == 0, 0.0, 100.0 * failed / total)
| where total >= 10 and failPct > 5
```

### Documentos fallidos > 10 %

Severidad 3. Nombre: `Multimodal failed documents > 10%`.

```kusto
customEvents
| where timestamp > ago(15m)
| where name in ("MultimodalAnalysisCompleted", "MultimodalAnalysisFailed")
| summarize
    failedDocs = sum(todouble(customMeasurements.failedDocuments)),
    okDocs = sum(todouble(customMeasurements.succeededDocuments))
| extend totalDocs = failedDocs + okDocs
| extend failPct = iff(totalDocs == 0, 0.0, 100.0 * failedDocs / totalDocs)
| where totalDocs >= 5 and failPct > 10
```

### p95 por encima de 45 s

Severidad 3. Nombre: `Multimodal p95 duration > 45s`.

A los 90 s ya existe `MultimodalAnalysisSlow` y el email. Esta alerta cubre el tramo de 45 a 90 s.

```kusto
customEvents
| where timestamp > ago(15m)
| where name in ("MultimodalAnalysisCompleted", "MultimodalAnalysisFailed")
| summarize n = count(), p95ms = percentile(todouble(customMeasurements.durationMs), 95)
| where n >= 5 and p95ms > 45000
```

### Subida de OCR fallido

Severidad 3. Nombre: `Multimodal ocr_failed spike`.

Dispara con al menos 3 fallos de OCR en 15 minutos y el doble que en los 15 minutos anteriores.

```kusto
let current = toscalar(
    customEvents
    | where timestamp > ago(15m)
    | where name == "Error"
    | where customDimensions.message startswith "Document image OCR failed"
    | count);
let previous = toscalar(
    customEvents
    | where timestamp between (ago(30m) .. ago(15m))
    | where name == "Error"
    | where customDimensions.message startswith "Document image OCR failed"
    | count);
print current, previous
| where current >= 3 and current > previous * 2
```

Si el portal rechaza `let` o `print`:

```kusto
customEvents
| where timestamp > ago(15m)
| where name == "Error"
| where customDimensions.message startswith "Document image OCR failed"
| summarize ocrFailed = count()
| where ocrFailed >= 3
```

Con las cuatro en **Enabled**, marcar A4 (alertas de App Insights) en `review_improve_files.md`.
