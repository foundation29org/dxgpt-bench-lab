# Benchmark de imagen documental

Este track decide si merece la pena añadir OCR híbrido a las imágenes subidas
a DxGPT. No cambia el servidor ni activa OCR en producción.

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
document_image o mixed con confianza >= 0,90 → OCR + imagen original
medical_image o unknown                       → imagen original directa a Terra
fallo del clasificador                        → imagen original directa a Terra
```

OCR sería siempre aditivo: nunca sustituiría la imagen original.

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
  `multimodal_beta/run_beta_api.py`.

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
  --config "bench\multimodal_beta\config.yaml" `
  --manifest "bench\document_image_beta\generated\product_manifest.yaml" `
  --output "bench\document_image_beta\outputs\product-responses.jsonl"

py "bench\document_image_beta\evaluate.py" `
  --product-responses "bench\document_image_beta\outputs\product-responses.jsonl"
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
  --responses "bench\document_image_beta\outputs\product-responses.jsonl" `
  --output-dir "bench\document_image_beta\outputs\evaluation-v4-primary-strict" `
  --judge-mode strict_equivalence `
  --gold-scope primary `
  --experiment-name "document-image-beta-v1" `
  --experiment-description "Synthetic document-image routing benchmark"
```

## Qué falta antes de producción

El piloto de Terra y las 50 entradas end-to-end ya se ejecutaron. Los
resultados están en [RESULTS.md](RESULTS.md).

1. Realizar una segunda revisión de las etiquetas MedReaMM.
2. Revisar clínicamente los diez casos y sus hechos esperados.
3. Ampliar los controles médicos difíciles y reales.
4. Implementar el enrutado en el servidor detrás de un feature flag.
5. Comparar realmente `OCR + imagen` con la imagen directa antes de rollout.
6. Solo si se mantienen los umbrales, activar el enrutado
   detrás de un feature flag.

Este benchmark mide el riesgo. No constituye todavía un detector de
producción.
