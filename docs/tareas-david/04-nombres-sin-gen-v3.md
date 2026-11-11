# Tarea 4 · Raras: comprobar los nombres sin gen rehechos

**Estado:** hecha (10-nov) · **Tiempo:** ≈ 45 min · **Depende de:** tarea 3

## Para qué sirve

En la [tarea 3](03-nombres-sin-gen-raras.md) revisaste una muestra al azar de
los nombres sin gen que había propuesto un LLM. Cerca de la mitad de sus
decisiones estaban mal o se podían mejorar:

| Bloque | Bien en la tarea 3 |
|---|---:|
| A. Nombre sin gen en DDD | 16 de 25 |
| B. Se quita un subtipo genético | 5 de 10 |
| C. No se añadió por ser un rasgo genérico | 4 de 10 |

Como pedía la tarea, se ha ajustado la regla y se han rehecho los nombres de
todos los casos (HPO v3). Las instrucciones del LLM llevan ahora tus
criterios:

- se quitan los tipos que se numeran por gen;
- si el nombre sin gen engloba varias enfermedades, se usa el nombre propio
  sin gen: un subtipo anterior al gen o un epónimo;
- se mantienen los calificativos que no dependen del gen, y la herencia
  cuando separa enfermedades distintas;
- un título descriptivo es una entidad si tiene dos o más rasgos
  obligatorios.

Tus respuestas de la tarea 3 se aplican tal cual a esos casos. Con los
criterios nuevos, el LLM coincide contigo en 37 de las 41 referencias que
revisaste, frente a 25 de 41 antes. Pero las reglas salen de esa misma
muestra, así que esa cifra es optimista. Para saber cómo de bien funcionan
hace falta una muestra nueva.

## Qué hay que hacer

1. **24 casos nuevos al azar**, ninguno de la tarea 3, con las mismas
   preguntas de los bloques A, B y C: 12, 6 y 6 casos.
2. **8 preguntas que dejó abiertas la tarea 3**: dos casos con la marca
   desplazada o sin marcar, los dos CONSULTAR MÉDICO, el criterio del bloque
   D, la lista de términos de tu regla de la causa C, la alcaptonuria de
   RAMEDIS, la regla de ruido de RAMEDIS y el nombre de dos gold de HMS.

No se enseña ningún resultado de los modelos, como piden las
[reglas congeladas](../../bench/pipelines/pipeline_v5/main/README.md#reglas-congeladas-desde-el-5-nov-2026).

## Material

- **Hoja:** `data29/data-repos/curated-datasets/hpo_v2/validacion_clinica_nombres_sin_gen_v3.md`
  (fuera de git; sale de `data29/data-repos/hpo-v2/review_sheet_v3.py`, con
  semilla fija).
- Contexto: [hpo-v2/README.md](../../data29/data-repos/hpo-v2/README.md).

## Cómo se devuelve

La hoja rellena, por canal privado. Si los nombres de los bloques A–C salen
bien, la v3 sustituye a la v2: se vuelven a puntuar las listas de Terra y Sol
y se publican las cifras de antes y de después. Si fallan mucho, se ajusta la
regla otra vez.

## Hecho cuando

Los 24 casos tienen una casilla marcada y las 8 preguntas tienen respuesta.
