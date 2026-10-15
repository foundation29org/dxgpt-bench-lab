# Frase de ubicación como único texto (solo imágenes) - 2026-10-08

Pregunta: con imágenes y sin texto, ¿conviene añadir `The patient is in <país>.`?
Hasta este experimento el Server no la añadía (regla `MIN_TEXT_CHARS_WITHOUT_IMAGES`: con menos de
10 caracteres de texto no se añade ni la frase de imágenes ni la de ubicación).

## Condiciones

- Casos: MedReaMM `pilot250` (los mismos 250), condición `I` (solo imágenes,
  `forceDiagnosis`), endpoint real `/api/medical/analyze`.
- Modelo: `gpt56terra` en 250/250, mismo día, mismo código, mismo juez
  (`strict_equivalence`, `gemini-2.5-pro`, thinking low, evaluación primaria).
- Brazos emparejados:
  - `none`: sin `countryCode`. Prompt de producción: sin ninguna frase.
  - `ES`: `countryCode=ES`, y la frase `The patient is in Spain.` como **único
    texto** del prompt. Para poder probarlo hubo que saltarse la regla de
    producción con un gancho temporal en el Server (variable de entorno solo en
    el contenedor local), ya retirado. El país no es el del caso: es la situación
    real de un usuario cuyo país no tiene relación con la imagen.
- Respuestas: 250/250 en ambos brazos. Una lista vacía con ES, ninguna sin país.
- Latencia media: 23,3 s sin país, 24,0 s con país.

## Resultado

| Brazo | R@1 | R@3 | R@5 | Sin match |
|---|---|---|---|---|
| none | 72/250 (28,8 %) | 105 (42,0 %) | 109 (43,6 %) | 141 |
| ES | 68/250 (27,2 %) | 100 (40,0 %) | 105 (42,0 %) | 145 |

Comparación emparejada (McNemar exacto, bilateral):

| Corte | Solo con ES | Solo sin país | p |
|---|---:|---:|---:|
| R@1 | 20 | 24 | 0,65 |
| R@3 | 15 | 20 | 0,50 |
| R@5 | 16 | 20 | 0,62 |

El rango juzgado cambia en 69 de 250 casos. La diferencia de R@1 es -1,6 puntos
con un intervalo aproximado del 95 % de [-6,8; +3,6] (aproximación normal con 44
pares discordantes).

## Lectura

- **No hay mejora**, y la dirección es ligeramente negativa en los tres cortes, como
  ocurrió con la frase de imágenes en `pilot100` (R@1 35 % -> 27 %, p=0,096). Con
  este tamaño no se puede distinguir de ruido.
- Cambiar el rango en 69 de 250 casos solo con una frase indica que, sin texto
  clínico, el modelo es muy sensible al texto que recibe. No se ha medido el ruido
  de repetir el mismo brazo, así que ese número no es un efecto del país.
- Decisión de producto (Julián): **sí se añade la frase de ubicación con solo
  imágenes**. La pérdida medida no es significativa y clínicamente la misma imagen
  (p. ej. una neumonía) no significa lo mismo en África que en Europa, algo que
  este dataset no puede medir. La frase de imágenes sigue como estaba (solo con
  texto de 10 o más caracteres); queda anotado explorar por qué empeora como único
  texto.
- Límites: un solo país (`ES`) irrelevante para los casos; no se probó un caso cuya
  imagen dependa del país (no hay dataset con ese diseño); un solo modelo.

## Trazabilidad

- `bench/multimodal_beta/outputs/pilot250_gpt56terra_I_nolocation/`
- `bench/multimodal_beta/outputs/pilot250_gpt56terra_I_location_ES/`
- Runner: `bench/multimodal_beta/run_beta_api.py --condition I --force-diagnosis [--country-code ES]`.
- Comparación: `py bench\location_context\analyze_regression.py --baseline none --arms "none=<dir>" "ES=<dir>"`.
