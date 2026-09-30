# Tareas pendientes de la rama `feature/improve_files` (Server + Client)

Actualizado: 29/09/2026. Server, Client, Aragón, Pricing y la Azure Function ya están en producción. El smoke test está hecho.

---

## 1. Ahora: correos (A8)

Ninguno envía nada si no se le pasa `--send`. Leer el texto antes. No nombran el modelo. Server y `pricing.dxgpt.app` ya están publicados, así que el enlace de precios ya no enseña la tabla de abril.

1. **Cuentas de la API** (`billing-fn/scripts/announce-terra.js`). Suscripciones activas de billing (Freemium, Stripe y Marketplace). Prueba: `--send --to=tu@email`.
2. **Usuarios de la app** (`billing-fn/scripts/announce-app-news.js`). SharePoint, con `az login`: General Feedback si tiene email, y Support DxGPT solo con `subscribe` en true. Primero `--inspect` (si el recuento sale a 0, la columna no se llama `email` o `subscribe`). El texto lleva la evaluación interna del 24 sep (250 casos, texto+imagen: 76 % en la lista, 59 % en el primer puesto; 100 casos solo texto: 65 % y 50 %) y las cifras de uso hasta el 1 sep (4,2/5, 88,4 % de votos positivos).

## 2. Sigue abierto

### A4. Alertas de Application Insights del análisis de ficheros

Workbook y alertas: [app_insights_multimodal_alerts.md](app_insights_multimodal_alerts.md). Las de Azure OpenAI (500 de Terra, mini y nano en `dxgptbot`) son otra regla: el servidor reintenta en la otra región y el diagnóstico sale; el usuario nota la espera.

### A5. Validación clínica

Falta la firma del biomédico sobre las etiquetas y los 41 hechos. La muestra del clasificador es pequeña (45 imágenes, 9 mixtas). Una imagen marcada `document_only` o `not_medical` con confianza ≥ 0,9 no llega al modelo de visión.

### A7. Análisis lentos

Document Intelligence no tiene timeout. Si un análisis sigue a los 90 s, se registra `MultimodalAnalysisSlow` y llega un email con el `correlationId`. Tras unas semanas, si no ha llegado ninguno, no hace falta límite. Si llegan, fijarlo en 2–3 veces el p99 de `durationMs`.

### M1. `.doc`

Probado. Dentro de unos meses, medir `LegacyWordDocumentProcessed`. Si es residual frente a `MultimodalAnalysisCompleted`, quitar `.doc` y retirar Gotenberg. El ingress de Gotenberg tiene que seguir interno.

### M3. Contrato de la API

`/medical/analyze` exige `myuuid` UUID y responde `processing`. `/diagnose` y `/disease/info` rechazan `imageUrls` y `assetIds`. Mirar en App Insights las llamadas de los últimos 30 días con `x-subscription-id` y, si hay integradores, decirlo en el changelog del portal.

### B3. RGPD

`blobCleanup` borra las imágenes entre 24 y 25 h. Fuera del código: registro de actividades (art. 30), EIPD (art. 35) y consultar si hace falta DPO (art. 37).

### B10. Heredado

Cancelar en el cliente no detiene el coste en el servidor. Faltan tests de `helpDiagnose` con `uploadId`.
