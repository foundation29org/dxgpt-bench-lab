# Tareas pendientes de la rama `feature/improve_files` (Server + Client)

Actualizado: 25/09/2026. Solo las tareas abiertas.

---

## 1. Alto

### A4. Configuración de despliegue que falta fuera del código

1. **APIM:** la operación nueva `DELETE /medical/upload/{uploadId}` tiene que existir en la API que usa la web. Si APIM la rechaza (404/405), el cliente ignora el error en silencio y las imágenes se quedan hasta que actúe `blobCleanup`. Comprobar también que APIM **no descarta el body** de los DELETE: el cliente solo manda `myuuid` en el body, y el fallback por query existe en el servidor pero el cliente no lo usa.
2. **`billing-fn/blobCleanup`:** el cambio está **sin commitear** en `develop` de billing-fn. Las dos versiones son compatibles: la antigua borra *todo* lo que tenga más de 24 h y la nueva solo `/files/uploads/`. Hay que commitearlo y desplegarlo.
3. **Alertas de Application Insights:** fallos > 5 %, documentos fallidos > 10 %, p95 > 45 s y `ocr_failed`. Mientras no existan, revisar a mano la consulta de `customEvents` (una vez al día la primera semana).

### A5. Validación clínica y benchmark (según el propio roadmap)

- Falta la firma del biomédico sobre las etiquetas y los 41 hechos.
- La muestra es pequeña (45 imágenes, 9 mixtas) y uno de los jueces dio 8/9.
- El benchmark multimodal (MedReaMM) **no se ha ejecutado contra un despliegue con estos cambios**.

Riesgo concreto: una imagen marcada `document_only` o `not_medical` con confianza ≥ 0,9 **no llega nunca al modelo de visión** (la primera solo con su OCR; la segunda se descarta). Un falso `document_only` (un ECG impreso, una foto de dermatología con rótulo o una gráfica) haría perder la evidencia visual sin que nadie se entere. Hasta que haya alertas, mirar el reparto de rutas (`documentImageRoutes`, `mixedImageRoutes`, `visionImageRoutes`, `imageFallbacks`).

### A6. Orden de despliegue

Con el servidor antiguo, el cliente nuevo no recibe `uploadId`: recalcular o pedir información de una enfermedad pierde las imágenes y el DELETE da 404. Además, el cliente nuevo ya no pega la frase de imagen: en un caso de solo imagen envía la descripción vacía, que el servidor antiguo rechaza con 400. Y dentro de un iframe manda `iframeParams` como texto JSON, que el servidor antiguo pasa tal cual a Diagnose y acaba en 400.

→ **Desplegar primero Server (con APIM), comprobar, y después Client.**

### A7. Análisis lentos: decidir un límite con datos reales

Document Intelligence no tiene timeout y el clasificador puede tardar ~6 min en el peor caso (180 s × 2 endpoints) antes de caer a visión. De momento no se corta nada: si un análisis sigue en marcha a los 90 s, se registra `MultimodalAnalysisSlow` y llega un email con el `correlationId`.

**Tarea:** tras unas semanas en producción, revisar si ha llegado algún email. Si no llega ninguno, no hace falta límite. Si llegan, fijar el límite en 2–3 veces el p99 real de `durationMs`.

---

## 2. Medio

### M1. `.doc` y `.xls`

Document Intelligence no lee formatos OLE antiguos. `.xls` ya no se acepta. `.doc` se convierte a PDF con la app `gotenberg` de `dxgpt-env-apim`, compartida por dev y prod (`GOTENBERG_URL`). Su ingress tiene que seguir siendo interno, porque abre ficheros de usuarios anónimos. Probado en dev el 25 sep.

**Tarea (en unos meses):** medir el uso de `.doc` con el evento `LegacyWordDocumentProcessed`:

```kusto
customEvents
| where name == "LegacyWordDocumentProcessed"
| summarize docs = count(), failed = countif(tostring(customDimensions.status) == "failed")
    by bin(timestamp, 7d)
```

Si el uso es residual frente a `MultimodalAnalysisCompleted`, quitar `.doc` y retirar Gotenberg.

### M3. Cambios de contrato en la API pública (posibles clientes B2B por APIM)

- `/medical/analyze` exige ahora `myuuid` con formato UUID (antes era opcional) y responde `processing` al momento: el resultado llega por Web PubSub, no en el HTTP.
- `/diagnose` y `/disease/info` rechazan `imageUrls` y `assetIds` no vacíos. Es una mejora de seguridad, pero un integrador que los usara recibirá 400.

**Tarea:** consultar en App Insights las llamadas de los últimos 30 días a esos endpoints con `x-subscription-id` (tráfico de APIM que no es de la web). Comunicarlo en el changelog del portal.

---

## 3. Bajo

1. **B3 · Caducidad de las imágenes y RGPD:** `blobCleanup` corre cada hora (se borran entre 24 y 25 h). Hay un aviso junto a la subida y la política recoge las 24 h y el respaldo a East US 2 (`p6.4`, `p7.5`, `p8.3`). **Pendiente fuera del código:** añadir las imágenes al registro de actividades de tratamiento (art. 30), revisar o hacer la EIPD con la herramienta de la AEPD (art. 35) y consultar a un DPO externo si la fundación está obligada a nombrar uno (art. 37).
2. **B7 · Docs:** `docs/dxgptapi-dev-yaml` no tiene extensión y, como `dxgptapi-prod.yaml`, es JSON y no YAML. Reimportar en APIM los cambios de TIFF/BMP.
3. **B10 · Heredado:**
    - cancelar en el cliente no detiene el procesamiento en el servidor (coste). Arreglarlo exige propagar la cancelación a OCR, clasificador y Diagnose; no compensa hasta ver en App Insights cuántos análisis se abandonan;
    - faltan tests de `helpDiagnose` con `uploadId` (incluida la cola). El controlador y `multimodalUploadService` sí están cubiertos.

---

## 4. Checklist antes de producción

**Bloqueantes**

- [ ] A4: operación DELETE en APIM (probar que el body llega).
- [ ] A4: commitear y desplegar `billing-fn/blobCleanup`.
- [ ] A4: alertas de App Insights.

**Muy recomendables**

- [ ] A5: firma clínica y benchmark MedReaMM contra el despliegue de dev.
- [ ] M3: revisar si hay integradores que usen `imageUrls` o `myuuid` que no sean UUID.

**Orden:** Server + APIM → *smoke test* → Client → monitorizar 48 h.

**Smoke test en dev con la misma cadena APIM:**

| Caso | Esperado |
|---|---|
| PDF nativo, PDF escaneado, DOCX, XLSX | Texto extraído y diagnóstico |
| DOC | Texto extraído (vía Gotenberg) |
| XLS | 400, formato no admitido |
| TXT UTF-8, ANSI y UTF-16 con tildes | OK, tildes y eñes intactas |
| Foto de informe (JPG) | Ruta `ocr_text`, sin blob |
| Radiografía o dermatología (PNG/JPG) | Ruta `vision` |
| Imagen mixta (informe + imagen) | Ruta `vision` + OCR |
| WEBP | `vision` (sin OCR) |
| TIFF, BMP | Rechazados antes de diagnosticar |
| 5 imágenes con 20 MB en total | Tiempo total y memoria del App Service |
| PDF grande que tarde más de 45 s | El POST responde `processing` al momento y el diagnóstico llega igual |
| Recalcular, "cargar más", pregunta de información de enfermedad con imagen | Mismo `uploadId` y la imagen llega |
| Solo un logo o una foto de paisaje | Mensaje "La imagen no parece médica", sin llamada a Terra |
| Texto clínico + un logo | Diagnóstico con el texto y aviso de que el logo no se ha usado |
| Foto de piel, ojo o boca sin rótulos | Ruta `vision`, nunca descartada |
| Solo una radiografía, sin texto (primer análisis) | Sale el modal de imágenes sin "hacer preguntas"; "Continuar con las imágenes subidas" da diagnóstico |
| Radiografía + historia clínica completa | Diagnóstico directo; la descripción que ve el usuario ya no lleva la frase de imagen |
| Radiografía + texto, recalcular dejando el texto vacío o "dolor" | Sin 400. Sale el modal de imágenes; "Continuar con las imágenes subidas" da diagnóstico en el idioma de la página |
| Radiografía + texto, recalcular dejando "fiebre" | Sin 400. Diagnóstico (o el modal de imágenes, si el clasificador lo ve vago) |
| Nuevo paciente / quitar fichero | Evento `MultimodalUploadDeleted` con `deletedBlobs > 0` |
| Borrar el blob a mano y recalcular | 400 `INVALID_UPLOAD_REFERENCE` y mensaje de "vuelve a subir" |
| TXT de más de 400 000 caracteres | Mensaje de "demasiado texto", sin llamadas a la IA y email al equipo |
| Cambiar de idioma y "empezar de nuevo" | Ver M6 |
| Cancelar durante el análisis | UI limpia y sin errores |
| Solo radiografía → "Continuar con las imágenes" → cancelar → "Search" | Vuelve a salir el modal de imágenes, no el aviso de texto obligatorio |
| Análisis con fichero dentro de un iframe con `centro` | El registro de coste lleva `iframeParams.centro` |
| Análisis con fichero con la cola forzada (`queueUtilizationThreshold` bajo en dev) | Sale el modal de cola y el diagnóstico llega al terminar |
| 100 peticiones seguidas desde dos IPs distintas | Cada IP tiene su propio cupo |
