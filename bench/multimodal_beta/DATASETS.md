# Datasets para la evaluación multimodal de DxGPT beta

Revisión: 27 de agosto de 2026.

## Requisitos del track

Un dataset es apto para esta evaluación si permite separar, por caso:

1. historia clínica disponible antes del diagnóstico;
2. una o varias imágenes médicas vinculadas al mismo paciente/caso;
3. diagnóstico final ocultable durante la inferencia;
4. identificador estable y licencia compatible con la evaluación;
5. información suficiente para detectar y retirar fugas del diagnóstico.

No basta con que existan imágenes y texto. El diagnóstico final debe ser un
*gold standard* independiente del texto enviado a DxGPT.

## Recomendación principal: MedReaMM

Fuente: [Hugging Face](https://huggingface.co/datasets/thomasweiX/MedReaMM) ·
[artículo](https://arxiv.org/html/2608.22323)

- 625 casos clínicos validados por expertos.
- 1.746 imágenes, con una media de 2,79 imágenes por caso.
- 1.042 diagnósticos normalizados con ICD-11, incluyendo distinción entre
  diagnósticos primarios y secundarios.
- Cada registro enlaza información del paciente, imágenes, captions,
  diagnóstico original y diagnóstico normalizado.
- Distribución directa y licencia MIT según la ficha actual del dataset.

Es la mejor primera opción porque ya resuelve la vinculación caso-imágenes y
proporciona un objetivo diagnóstico explícito. Aun así, los casos proceden de
publicaciones y pueden haber aparecido en el entrenamiento de los modelos; el
resultado mide reproducibilidad de producto, no rendimiento clínico
prospectivo libre de contaminación.

### Vista que debe recibir DxGPT

Incluir:

- `patient_info.basic_info`, después de una revisión de fuga;
- las rutas de imagen de `supplementary_info[].path`;
- solo datos obtenidos antes de confirmar el diagnóstico.

Retener exclusivamente para evaluación:

- `diagnosis`;
- `standardized_diagnosis`;
- captions y explicaciones que nombren o hagan trivial el diagnóstico;
- tratamiento, anatomía patológica concluyente o evolución posterior cuando
  revelen directamente el objetivo.

Para el primer piloto es preferible no enviar captions. Después se puede crear
una condición separada con captions purificados que solo indiquen modalidad,
plano y región anatómica.

## Segunda opción: MedPix 2.0

Fuente: [Zenodo](https://zenodo.org/records/12624810) ·
[GitHub](https://github.com/CHILab1/MedPix-2.0/tree/main/MedPix-2-0)

- Casos con `History`, `Exam`, `Findings`, `Differential Diagnosis` y
  `Case Diagnosis`.
- Imágenes CT/MRI vinculadas mediante `U_id`.
- El diagnóstico final está disponible de forma estructurada.
- Es más grande que MedReaMM y resulta útil para confirmar resultados en un
  corpus distinto.

Requiere construir una vista propia libre de fuga. No se deben enviar
`Title`, `Case Diagnosis`, `Differential Diagnosis`, la discusión del tópico
ni captions que revelen el diagnóstico. Sus códigos ACR no sustituyen por sí
solos una normalización diagnóstica ICD; habrá que mapear o usar un juez
semántico.

## MultiCaRe: corpus útil, pero no primer benchmark

Fuente: [GitHub](https://github.com/mauro-nievoff/MultiCaRe_Dataset) ·
[casos en Hugging Face](https://huggingface.co/datasets/OpenMed/multicare-cases) ·
[imágenes en Hugging Face](https://huggingface.co/datasets/OpenMed/multicare-images)

- Más de 90.000 narrativas clínicas y más de 130.000 imágenes procedentes de
  case reports abiertos de PubMed Central.
- Los casos y las imágenes se pueden enlazar mediante `case_id` /
  `patient_id`.
- Ofrece captions y una taxonomía rica para clasificación de imágenes.
- La licencia global es abierta, pero se debe conservar y auditar la
  procedencia/licencia de cada artículo o imagen.

Su esquema de casos no ofrece un campo canónico y estructurado de diagnóstico
final equivalente al de MedReaMM o `Case Diagnosis` de MedPix. En muchos casos
el diagnóstico está dentro de la propia narrativa; usarla sin segmentación
produciría fuga directa. MultiCaRe es adecuado para crear en el futuro un
benchmark interno, pero exige:

1. extraer el diagnóstico final desde el artículo fuente;
2. separar cronológicamente información pre y postdiagnóstica;
3. normalizar el objetivo a una ontología;
4. revisar clínicamente una muestra;
5. comprobar captions, nombres de fichero y texto incrustado en las imágenes.

## Otros candidatos

### Eurorad curado

Ofrece historia, hallazgos radiológicos, imágenes y diagnóstico final. Es
clínicamente interesante, pero la descarga masiva y la licencia
CC BY-NC-SA añaden fricción. Queda como validación posterior.

Referencia:
[benchmark curado](https://www.nature.com/articles/s41746-025-01488-3).

### MIMIC-IV + MIMIC-CXR

Es la opción posterior para validación retrospectiva más cercana a práctica
real: EHR, radiografías e información diagnóstica vinculable. Requiere acceso
acreditado de PhysioNet y una definición cuidadosa del momento diagnóstico;
los códigos de alta o facturación no siempre equivalen al diagnóstico causal
de la imagen.

Referencia:
[MIMIC-CXR](https://physionet.org/content/mimic-cxr/2.1.0/).

### PadChest y BIMCV-COVID19+

Son útiles para subtareas radiológicas o pruebas técnicas, pero sus etiquetas
son hallazgos/patologías más estrechos y no reproducen bien una búsqueda de
diagnóstico diferencial general.

## Decisión y secuencia

1. Usar MedReaMM para el primer piloto de 25 casos.
   Preparación: `py bench/multimodal_beta/prepare_medreamm.py --limit 25`.
   El manifest queda en `datasets/processed/medreamm_pilot25/manifest.yaml`.
   No se envían captions. El *gold* ICD-11 se guarda solo en local.
2. Auditar manualmente 10 casos antes de ejecutar para asegurar fuga cero.
   La lista y la regla están en `datasets/processed/medreamm_pilot25/audit.yaml`.
3. Ejecutar condiciones emparejadas: texto, imagen, texto+imagen e imagen
   intercambiada.
4. Ampliar a 100 casos solo si las 25 respuestas son técnicamente completas y
   parseables.
5. Usar MedPix 2.0 como segunda cohorte externa.
6. No usar MultiCaRe para comparar modelos hasta disponer de diagnósticos
   finales extraídos y revisados.
