# Benchmark de imagen documental

Este track valida la ruta V1 de OCR y visión para las imágenes subidas a
DxGPT. La implementación ya existe en el servidor; el benchmark decide si
puede avanzar como gate de producción.

## Decisión que evalúa

No se intenta detectar simplemente «si hay texto». Una radiografía, un ECG o
una preparación de anatomía patológica pueden contener etiquetas. El
clasificador usa cuatro clases:

- `document_image`: foto o escaneo cuyo contenido principal es un informe,
  tabla o texto;
- `medical_image`: radiografía, CT, MRI, ecografía, patología, dermatología,
  fondo de ojo, ECG, endoscopia u otra evidencia visual clínica;
- `mixed`: texto documental sustancial e imagen médica sustancial en el mismo
  lienzo;
- `unknown`: no hay evidencia suficiente.

La regla de seguridad es deliberadamente asimétrica:

```text
document_image con confianza >= 0,90 → OCR; no enviar imagen al diagnóstico
mixed con confianza >= 0,90          → OCR + imagen original
medical_image o unknown              → imagen original directa a Terra
fallo del clasificador               → imagen original directa a Terra
```

OCR es aditivo para imágenes mixtas. En una imagen exclusivamente documental,
el texto extraído sustituye al visual en la llamada diagnóstica; el blob
original se conserva.

## Datos

`cases.yaml` contiene diez casos clínicos completamente sintéticos y sin PII.
El generador crea para cada caso:

- PDF nativo;
- PDF rasterizado;
- escaneo PNG;
- fotografía JPEG;
- manuscrito simulado.

También genera ejemplos `mixed` con texto e imagen sintética. Añade una
muestra revisada del piloto local MedReaMM para comprobar radiografías, CT,
MRI, ecografía, dermatología y otras imágenes clínicas. La verdad esperada se
asigna por contenido, no por procedencia: dos imágenes MedReaMM son tablas de
laboratorio y, correctamente, se etiquetan como `document_image`.

La primera revisión queda en `medreamm_labels.yaml` y requiere una segunda
revisión antes de usar el resultado como evidencia clínica definitiva.

El formulario autosuficiente para esa segunda revisión está en
[`DAVID_CLINICAL_REVIEW_FORM.md`](DAVID_CLINICAL_REVIEW_FORM.md). Incluye las
instrucciones, imágenes y campos en lenguaje natural. El revisor devuelve ese
mismo Markdown rellenado y no edita directamente el gold ni la preauditoría.

Los binarios generados viven en `generated/` y no se versionan. Las
definiciones, semillas y scripts sí se versionan.

## Preparación

Desde la raíz de `eval`:

```powershell
py -m pip install -r requirements.txt
py "bench\document_image_beta\generate_dataset.py"
```

Para regenerar:

```powershell
py "bench\document_image_beta\generate_dataset.py" --overwrite
```

La salida incluye:

- `generated/classification_manifest.yaml`: imágenes y ruta esperada;
- `generated/product_manifest.yaml`: 50 entradas compatibles con
  `multimodal_beta/run_beta_api.py`;
- `generated/mixed_hybrid_manifest.yaml`: nueve controles mixtos con el PDF
  escaneado equivalente como OCR proxy y la imagen original.

Si no existe el piloto MedReaMM local, el generador sigue funcionando, pero
avisa de que faltan controles médicos reales. Ese resultado no sirve para
aprobar el clasificador.

## Evaluar el clasificador

Primero validar sin realizar llamadas:

```powershell
py "bench\document_image_beta\run_classifier.py" --dry-run
```

Para ejecutar un deployment visual compatible con Azure OpenAI:

```powershell
$env:AZURE_OPENAI_ENDPOINT = "https://<recurso>.openai.azure.com"
$env:AZURE_OPENAI_API_KEY = "<secreto>"
$env:DOCUMENT_IMAGE_CLASSIFIER_DEPLOYMENT = "<deployment-visual>"

py "bench\document_image_beta\run_classifier.py"
py "bench\document_image_beta\evaluate.py"
```

Para evaluar la política desplegada en V1 —solo las imágenes exclusivamente
documentales van a OCR— se usa:

```powershell
py "bench\document_image_beta\run_classifier.py" `
  --policy v1 `
  --deployment "<deployment-visual>" `
  --output "bench\document_image_beta\outputs\classification-v1.jsonl"

py "bench\document_image_beta\evaluate.py" `
  --classification-results `
    "bench\document_image_beta\outputs\classification-v1.jsonl" `
  --output "bench\document_image_beta\outputs\evaluation-v1.md"
```

El benchmark exige:

- cobertura >= 95%;
- al menos 90% de las imágenes documentales encaminadas a OCR;
- al menos 90% de las imágenes mixtas encaminadas a OCR + imagen;
- **0 imágenes médicas** encaminadas a OCR;

La precisión global no puede compensar una ruta médica insegura.

## Evaluación end-to-end actual

El manifest generado se puede ejecutar contra un entorno no productivo:

```powershell
py "bench\multimodal_beta\run_beta_api.py" `
  --config "bench\multimodal_beta\config.example.yaml" `
  --manifest "bench\document_image_beta\generated\product_manifest.yaml" `
  --output "bench\document_image_beta\outputs\product-responses-v1.jsonl"

py "bench\document_image_beta\evaluate.py" `
  --classification-results `
    "bench\document_image_beta\outputs\classification-v1-terra.jsonl" `
  --product-responses `
    "bench\document_image_beta\outputs\product-responses-v1.jsonl" `
  --output `
    "bench\document_image_beta\outputs\evaluation-v1-end-to-end.md"
```

Esto compara cuánto se conserva de fechas, valores, unidades y negaciones
entre PDF nativo, PDF escaneado e imágenes enviadas directamente a Terra. El
recall de hechos es conservador: exige que el dato esperado siga presente en
la descripción preparada por el producto.

El informe también muestra coincidencia literal del nombre diagnóstico en
top-1, pero **no debe interpretarse como exactitud clínica**: por ejemplo,
`Acute pulmonary embolism` y `Pulmonary embolism` no son cadenas idénticas.
La equivalencia diagnóstica requiere el evaluador strict y revisión clínica.

Evaluación diagnóstica canónica:

```powershell
$env:PYTHONUTF8 = "1"
py "bench\multimodal_beta\evaluate_v4.py" `
  --responses "bench\document_image_beta\outputs\product-responses-v1.jsonl" `
  --output-dir `
    "bench\document_image_beta\outputs\evaluation-v4-v1-primary-strict" `
  --judge-mode strict_equivalence `
  --gold-scope primary `
  --experiment-name "document-image-v1-end-to-end" `
  --experiment-description "V1 document OCR and mixed-image hybrid routing"
```

Para una regresión parcial del producto sin volver a evaluar el clasificador:

```powershell
py "bench\document_image_beta\evaluate.py" `
  --product-only `
  --product-responses "path\to\responses.jsonl" `
  --output "path\to\evaluation.md"
```

## Qué falta antes de producción

El piloto de Terra y las 50 entradas end-to-end ya se ejecutaron. Los
resultados están en [RESULTS.md](RESULTS.md).

1. Obtener la firma independiente del biomédico sobre
   `clinical_review_precheck.yaml`: la preauditoría confirmó 11/12 etiquetas,
   propuso una corrección y verificó 10/10 casos y 41/41 hechos.
2. Resolver las cautelas clínicas y visuales que el biomédico rechace.
3. Ampliar los controles médicos difíciles y reales.

La ruta mixta `OCR + imagen original`, su fallback a visión y la regresión
end-to-end de nueve entradas ya están completados. Esta evidencia todavía no
autoriza por sí sola un rollout de producción.
