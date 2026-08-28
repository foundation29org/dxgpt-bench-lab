# Evaluación end-to-end de DxGPT beta

Este directorio contiene un track independiente del benchmark narrativo
`pipeline_v4`. Su objetivo no es llamar directamente a un modelo, sino
reproducir el producto beta completo cuando un usuario sube texto, documentos
y/o imágenes.

La selección y preparación de datasets se documenta en [DATASETS.md](DATASETS.md).
La revisión clínica pendiente está preparada en
[MEDICAL_REVIEW.md](MEDICAL_REVIEW.md).
El historial consolidado de ejecuciones y métricas se mantiene en
[RESULTS.md](RESULTS.md).
El estado y orden de las tareas pendientes se mantiene en
[ROADMAP.md](ROADMAP.md).

## Qué se evalúa

El flujo reproducido es:

```text
POST /api/pubsub/negotiate con myuuid
        |
        v
abrir WebSocket de Azure Web PubSub
        |
        v
POST multipart /api/medical/analyze
  text, document[0..5], image[0..5], lang, myuuid, timezone
        |
        v
extracción de documentos y posible resumen
        |
        v
diagnóstico asíncrono
        |
        v
mensaje WebSocket type=result con el resultado final
```

El POST inicial normalmente responde:

```json
{"result":"processing","description":"...","imageUrls":[],"isImageOnly":false}
```

Esa respuesta no contiene todavía el diferencial. El runner abre el WebSocket
antes de enviar el multipart, igual que el cliente beta, y espera el mensaje
final. Guarda ambos objetos para no confundir errores de extracción,
resumen/transporte y diagnóstico.

## Diferencias respecto al benchmark anterior

- Evalúa el endpoint real `Server/routes/index.js`, no un prompt aislado.
- Incluye Blob Storage, Document Intelligence, resumen, traducción,
  anonimización, modelo diagnóstico y Web PubSub.
- Con alguna imagen, `multimodalInput.js` selecciona `gpt5`; sin imágenes
  selecciona `gpt54mini`.
- Si el texto combinado supera 1.000 caracteres, el servidor lo resume antes
  del diagnóstico.
- El modelo no se elige desde el manifest. Una comparación de modelos exige
  cambiar/configurar el servidor; este track mide exactamente la versión
  desplegada.
- La ejecución genera telemetría, blobs y registros de coste. Debe usarse un
  tenant de evaluación y, preferentemente, un despliegue no productivo.

Por estos motivos sus métricas no se deben mezclar directamente con
`all_256_clean`.

## Estructura

```text
multimodal_beta/
├── README.md
├── DATASETS.md
├── config.example.yaml
├── manifest.example.yaml
├── run_beta_api.py
├── datasets/
│   ├── raw/          # dump completo; ignorado por git
│   └── processed/    # vistas MedReaMM (público, MIT); se pueden commitear
└── outputs/          # respuestas del modelo por ejecución; ignoradas por git
```

El manifest conserva el *gold* junto al caso para evaluar después, pero
`run_beta_api.py` nunca lo envía a la API.

## Contrato de entrada reproducido

Campos multipart:

- `text`: historia clínica o cadena vacía;
- `document`: campo repetido, máximo 5;
- `image`: campo repetido, máximo 5;
- `lang`: idioma de la petición;
- `myuuid`: UUID único usado también para Web PubSub;
- `timezone`: zona horaria.

Cabeceras:

- llamada directa al servidor: `X-Tenant-Id`;
- llamada mediante API Management: `Ocp-Apim-Subscription-Key`;
- el servidor comprueba internamente `X-Tenant-Id` o `x-subscription-id`.

La URL base debe incluir `/api`, por ejemplo
`http://localhost:3000/api`.

### Límites y formatos

El cliente y el servidor aceptan ahora la misma lista:

- documentos: PDF, DOC, DOCX, XLS, XLSX y TXT;
- imágenes: JPEG, PNG, TIFF, BMP y WEBP.

El runner usa esa misma lista. El cliente sigue limitando 20 MB en total; el
servidor, 20 MB por fichero.

## Flujo de producto frente a ablaciones

La primera ejecución mide el beta tal como está:

- resumen si texto+documentos superan 1.000 caracteres;
- `gpt54mini` sin imágenes y `gpt5` con imágenes.

No subas el umbral de resumen todavía. Ese corte existía para que modelos
antiguos no se dispersaran. Puede seguir siendo útil. El runner anota si el
caso se resumió (`pipeline.summarized`) para no mezclar fallos de resumen con
fallos diagnósticos. La ablación —mismo caso sin resumen, o con umbral más
alto— va después, cuando ya exista una línea base.

Lo mismo con el modelo. Hoy, si comparas texto solo contra texto+imagen,
comparas `gpt54mini` contra `gpt5`. Eso no dice si la imagen ayuda: dice que
cambió el motor. Un override de eval, solo en tenants `dxgpt-local` /
`dxgpt-eval` / `dxgpt-dev`, permite más adelante forzar Terra (u otro) en
todas las condiciones. Hoy solo `gpt5` adjunta las URLs de imagen al prompt;
antes de sustituir Terra en multimodal hay que cablear visión en ese modelo.

```powershell
$env:DXGPT_EVAL_MODEL = "gpt5"   # más adelante, cuando el servidor sepa enviarle imágenes
```

## Preparar MedReaMM

```powershell
py "bench\multimodal_beta\prepare_medreamm.py" --limit 25
```

Escribe el piloto en `datasets/processed/medreamm_pilot25/`. El *gold* y las
imágenes no se suben a git. El filtro automático excluye el diagnóstico
explícito del texto enviado; no sustituye una revisión clínica de los
primeros 10 casos.

Para preparar una cohorte mayor sin reemplazar el piloto:

```powershell
py "bench\multimodal_beta\prepare_medreamm.py" `
  --limit 100 `
  --output-name "medreamm_pilot100"
```

El preparador no elimina una cohorte existente salvo que se indique
explícitamente `--overwrite`.

## Preparación

Desde la raíz de `eval`:

```powershell
py -m venv .venv
.venv\Scripts\activate
py -m pip install -r requirements.txt
```

Copiar la configuración y el manifest:

```powershell
Copy-Item "bench\multimodal_beta\config.example.yaml" "bench\multimodal_beta\config.yaml"
```

Definir credenciales. Para una llamada directa:

```powershell
$env:DXGPT_API_BASE_URL = "http://localhost:8443/api"
$env:DXGPT_TENANT_ID = "dxgpt-local"
```

Para API Management:

```powershell
$env:DXGPT_API_BASE_URL = "https://example.invalid/api"
$env:DXGPT_SUBSCRIPTION_KEY = "<secret>"
```

No guardar secretos en `config.yaml`.

## Manifest

Cada caso requiere:

- `id`;
- al menos uno de `text`, `text_file`, `documents` o `images`;
- `gold.diagnoses`, retenido localmente;
- rutas relativas a la ubicación del manifest o rutas absolutas.

`text` y `text_file` son mutuamente excluyentes. El ejemplo completo está en
[manifest.example.yaml](manifest.example.yaml).

Antes de enviar datos:

```powershell
py "bench\multimodal_beta\run_beta_api.py" `
  --config "bench\multimodal_beta\config.yaml" `
  --manifest "bench\multimodal_beta\datasets\processed\medreamm_pilot25\manifest.yaml" `
  --dry-run
```

## Ejecución

Piloto de 25 casos:

```powershell
py "bench\multimodal_beta\run_beta_api.py" `
  --config "bench\multimodal_beta\config.yaml" `
  --manifest "bench\multimodal_beta\datasets\processed\medreamm_pilot25\manifest.yaml"
```

Cohorte de 100 casos:

```powershell
py "bench\multimodal_beta\run_beta_api.py" `
  --config "bench\multimodal_beta\config.example.yaml" `
  --manifest "bench\multimodal_beta\datasets\processed\medreamm_pilot100\manifest.yaml" `
  --output "bench\multimodal_beta\outputs\pilot100_product\responses.jsonl"
```

Para reanudar un fichero concreto, solo se omiten los casos que ya tengan una
respuesta exitosa:

```powershell
py "bench\multimodal_beta\run_beta_api.py" `
  --config "bench\multimodal_beta\config.yaml" `
  --manifest "bench\multimodal_beta\manifest.yaml" `
  --output "bench\multimodal_beta\outputs\pilot\responses.jsonl" `
  --resume
```

El proceso devuelve código 1 si algún caso falla y escribe cada resultado
inmediatamente para tolerar interrupciones.

Si el servidor responde HTTP 429, el runner espera el valor de `Retry-After` y
reintenta el mismo caso. Una ejecución interrumpida puede continuar con
`--resume`; el evaluador consolida el intento fallido y su posterior respuesta
correcta como un único caso.

## Diseño experimental mínimo

Crear cuatro entradas emparejadas por caso:

1. `T`: texto clínico saneado, sin imágenes;
2. `I`: imágenes y metadatos no diagnósticos, sin historia;
3. `T+I`: texto e imágenes correctas;
4. `T+shuffled-I`: el mismo texto con imágenes de otro caso.

El runner construye estas variantes sin duplicar manifests mediante
`--condition T`, `--condition I`, `--condition T+I` o
`--condition T+shuffled-I`. En una comparación controlada sin imágenes hay que
definir `DXGPT_EVAL_MODEL=gpt5`; de lo contrario, el producto selecciona
`gpt54mini` y cambia simultáneamente modalidad y modelo.

No basta con que `T+I` acierte. Para demostrar que la imagen aporta evidencia,
debería mejorar respecto a `T` y degradarse al intercambiar las imágenes.

Las condiciones deben mantener por separado:

- el identificador del caso fuente;
- el identificador de la condición;
- las imágenes reales usadas;
- el diagnóstico primario y los secundarios;
- cualquier exclusión por fuga o incompatibilidad técnica.

## Outputs y métricas

Cada línea de `responses.jsonl` contiene:

- entradas efectivamente enviadas;
- respuesta HTTP inicial, incluida la descripción resumida;
- mensajes de progreso;
- respuesta diagnóstica final;
- latencia total;
- *gold standard* local;
- error técnico, si existe.

El diferencial se encuentra normalmente en
`final_response.data`, una lista ordenada de objetos con `diagnosis`.

Métricas previstas:

- Recall@1, Recall@3 y Recall@5;
- posición media y MRR;
- coincidencia exacta y jerárquica ICD-11;
- cobertura y tasa de respuesta parseable;
- latencia end-to-end;
- ganancia visual: `T+I - T`;
- sensibilidad al intercambio: `T+I - T+shuffled-I`.

`evaluate_v4.py` adapta esas respuestas y ejecuta el mismo stack del benchmark
narrativo:

```powershell
py "bench\multimodal_beta\evaluate_v4.py" `
  --responses "bench\multimodal_beta\outputs\pilot25_product\responses.jsonl" `
  --output-dir "bench\multimodal_beta\outputs\pilot25_product\evaluation_v4_primary_strict"
```

MedLabeler normaliza tanto el diagnóstico primario de MedReaMM como el
diferencial generado. El evaluador aplica SNOMED, ICD-10 jerárquico, SapBERT
0,80/0,90 y `gemini-2.5-pro`.

Después de evaluar, `build_review_packet.py` genera dentro del output un
`clinical_review.md` con casos sin match, matches del juez LLM, diferenciales,
BERT y campos para adjudicación. También puede crear una comparación ciega
entre dos ejecuciones. Las rutas preparadas para David están centralizadas en
[MEDICAL_REVIEW.md](MEDICAL_REVIEW.md).

## Resultado del piloto de producto

Ejecución del 27 de agosto de 2026:

- inferencia completa en 25/25 casos, sin errores técnicos;
- 9/25 historias resumidas por superar 1.000 caracteres;
- latencia media end-to-end de 41 segundos;
- R@1 primario: 16/25 (64%);
- R@3 primario: 19/25 (76%);
- R@5 y cobertura: 21/25 (84%);
- posición media entre casos con match: 1,571.

El prompt histórico del juez aceptaba el diagnóstico «más parecido» y produjo
25/25, incluyendo falsos positivos evidentes como Hodgkin frente a Burkitt.
El resultado canónico de este piloto usa `StrictMultimodalEvaluator`, definido
en `evaluate_v4.py`, que exige la misma entidad diagnóstica. Pipeline V4 no se
modifica: este track reutiliza sus capas mediante imports y mantiene aisladas
la normalización adicional del gold ICD-11 y la política estricta del juez.

Queda una cautela: MedLabeler asigna varios códigos a algunos gold compuestos.
En el caso `22389885`, el gold primario es un linfoma intermedio DLBCL/Burkitt
y el SNOMED exacto acepta Burkitt aislado. Por ello, 84% debe considerarse
provisional hasta completar la revisión clínica y añadir comprobación ICD-11.

La ampliación a 100 casos terminó sin errores técnicos: R@1 61%, R@3 74%,
R@5 78% y cobertura 80%, con posición media 1,462 entre los matches. El
desglose, los 20 casos sin match y las cautelas metodológicas se mantienen en
[RESULTS.md](RESULTS.md).

El control emparejado de texto solo con el mismo `gpt5` obtuvo R@1 43%, R@3
58%, R@5 63% y cobertura 64%. Añadir las imágenes correctas mejoró la cobertura
en 16 puntos —20 casos ganados frente a 4 perdidos; McNemar exacto
`p=0,00154`—. La señal visual sigue siendo provisional hasta completar revisión
clínica y `T+shuffled-I`.
