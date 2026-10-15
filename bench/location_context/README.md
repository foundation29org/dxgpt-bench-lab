# Evaluación de la línea «El paciente está en <país>»

Mide qué hace el país cuando el servidor lo añade al prompt de diagnóstico.
El servidor compone una sola frase (`The patient is in India.`) a partir del
código ISO que envía el cliente (`Server/services/locationContext.js`). Sin
`countryCode` el prompt es el de siempre.

El runner llama al endpoint real `/api/diagnose` con `gpt56terra`, igual que la
web. Un **brazo** es el país enviado; `none` no envía ninguno. Todo lo demás es
idéntico entre brazos.

## Requisitos

- Servidor local en `http://localhost:8443/api` con el código nuevo. En Docker el
  proceso no recarga al editar: `docker restart server-app-local-1`.
- Variables opcionales: `DXGPT_API_BASE_URL`, `DXGPT_TENANT_ID`,
  `DXGPT_EVAL_MODEL` (las mismas que `multimodal_beta`).

## Suites

### `endemic` — sonda de sensibilidad

```powershell
py bench\location_context\run_location_eval.py --workers 4 endemic --reps 2
py bench\location_context\run_location_eval.py summarize-endemic
```

Viñetas escritas a mano en `endemic_vignettes.yaml`, **no es un benchmark
validado**:

- `classic`: 14 enfermedades geográficamente restringidas con sus rasgos típicos.
- `vague`: las mismas con los rasgos discriminantes quitados.
- `controls`: 5 enfermedades comunes, para ver si el país las distorsiona.

Brazos: `none`, `ES` y los países donde la enfermedad es frecuente. Ninguna
viñeta menciona viajes ni país. Resultado: posición del diagnóstico esperado
(regex sobre el nombre) por brazo y repetición.

### `regression` — no degradar casos corrientes

```powershell
py bench\location_context\run_location_eval.py --workers 5 regression --arms none IN NG
```

Envía los 100 casos de texto de MedReaMM `pilot100` con cada país. Escribe
`responses.jsonl` con el esquema que lee `multimodal_beta/evaluate_v4.py`; el
runner imprime el comando para puntuar cada brazo con el juez `strict_equivalence`.
Los casos no son de la India ni de Nigeria: es una prueba de robustez
(¿mueve el país un diagnóstico que no depende de él?).

`outputs/` está en `.gitignore`.

## Relación con el resto de `bench/`

- Los benchmarks existentes (`multimodal_beta`, `pipelines`) **no envían
  `countryCode`**, así que el prompt es el de siempre y sus resultados históricos
  siguen siendo comparables. No hay que tocar el prompt del juez
  (`strict_equivalence`): el país solo cambia lo que genera el modelo, no cómo se
  puntúa.
- Los datasets de MedReaMM no traen país del paciente, por eso la regresión
  inventa uno (`IN`, `NG`) para medir robustez, no para medir mejora.
- Este directorio es la comprobación a repetir si cambia la frase, el modelo de
  diagnóstico o la lógica de detección. Informes: `results/`.
- Solo imágenes (sin texto): `results/2026-10-08-image-only.md`. La frase como único
  texto no mejora ni empeora de forma significativa (R@1 28,8 % -> 27,2 %, p=0,65);
  el Server la añade igualmente por criterio clínico (ver el informe). `run_beta_api.py` acepta `--country-code` para repetirlo.
- Pendiente (no medido): paciente fuera de su país de residencia y otros
  modelos de diagnóstico. Para lo segundo basta `DXGPT_EVAL_MODEL=<modelo>`.
