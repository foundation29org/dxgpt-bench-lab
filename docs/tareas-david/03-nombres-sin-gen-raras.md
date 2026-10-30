# Tarea 3 · Raras: nombres sin gen y casos con HPO insuficientes

**Estado:** lista para empezar · **Tiempo:** ≈ 1 h 25 min · **Depende de:** nada

## Para qué sirve

En el benchmark de raras, el modelo solo ve una **lista de síntomas** (términos
HPO), nunca un estudio genético. Pero muchos diagnósticos de referencia llevan
el gen en el nombre. Ejemplo:

| Referencia original | El modelo dice | Nota del juez |
|---|---|---|
| «RPGRIP1-related Leber congenital amaurosis» | «Leber congenital amaurosis» | 1: relacionado, le falta el gen. No cuenta como acierto |

Esto ya lo viste en tu revisión T3 (MSUD frente a MSUD tipo Ia). Para
arreglarlo, a cada referencia con gen se le ha añadido el **nombre de la
enfermedad sin el gen** («Leber congenital amaurosis»), y vale acertar
cualquiera de los dos. Con eso, el acierto de Terra en el primer diagnóstico
pasa del 27 % al 41 % en los 3.006 casos de raras.

Los nombres sin gen los propuso un LLM con estas reglas:

- se quita el gen y los subtipos que solo distingue la genética (Bardet-Biedl
  9 → Bardet-Biedl; MSUD tipo Ia → MSUD; grupo de complementación C de
  Fanconi → Fanconi);
- se mantienen los subtipos que son enfermedades distintas (tipos de
  mucopolisacaridosis, de tirosinemia, de glucogenosis; Usher 1 frente a 2);
- **no** se acepta el nombre sin gen si lo que queda es un rasgo genérico: de
  «SETD5-related intellectual disability» quedaría «intellectual disability»,
  y cualquier síndrome con retraso contaría como acierto;
- **no** se acepta si el nombre sin gen ya es uno de los síntomas de la lista,
  porque regalaría el acierto.

Hace falta que un clínico revise una muestra para saber si el LLM ha trazado
bien esas líneas. Si falla mucho, se ajusta la regla y se repite para todos.

Además, en T3 marcaste **9 casos cuyos síntomas no bastan para llegar al
diagnóstico** (causa C). Siguen en el benchmark y falta decidir qué hacer con
ellos.

Por último, **sinónimos del gold** (añadido el 30-oct). El juez solo ve el
nombre de la referencia, y a veces no reconoce un sinónimo poco usado. Por
ejemplo, no daba por buena «distal arthrogryposis type 5» para «Arthrogryposis
with oculomotor limitation and electroretinal anomalies», que es la misma
enfermedad (OMIM 108145). Se ha probado a añadir a cada referencia los
sinónimos exactos que da MONDO, una ontología curada, para su código OMIM. Con
eso el juez corrige ese tipo de error, pero el sinónimo es tan bueno como el
código del dataset: en HMS, «Reactive arthritis» lleva el código del síndrome
de Sjögren. Antes de meter los sinónimos en el gold hace falta tu visto bueno
sobre una muestra.

## Qué hay que hacer

En la hoja, 69 casos con la lista de síntomas, la referencia con gen y el
nombre sin gen propuesto, o la referencia y sus sinónimos en el bloque F. Una
casilla por caso:

| Bloque | Casos | Pregunta |
|---|---:|---|
| A. DDD, nombre sin gen añadido | 25 | ¿Es la misma enfermedad sin el gen, y algo que un clínico pondría en un diferencial con esos síntomas? |
| B. Otros datasets, se quita un subtipo genético | 10 | ¿Se puede quitar ese subtipo sin cambiar de enfermedad? |
| C. No se añadió por ser un rasgo genérico | 10 | ¿Bien así, o sí es una enfermedad con entidad propia? |
| D. No se añadió porque ya es un síntoma de la lista | 5 | ¿Bien así, o el caso debería salir del benchmark? |
| E. Causa C de T3 | 9 | ¿Mantener, excluir, o mantener pero contar aparte como «no diagnosticable sin genética o metabolitos»? |
| F. Sinónimos de MONDO | 10 | ¿El diagnóstico del modelo es la misma enfermedad que la referencia? ¿Algún sinónimo añadido está mal? Son parejas en las que añadir los sinónimos cambia si la respuesta cuenta como acierto; no se dice en qué sentido |

Si de los casos E sale una regla general (por ejemplo, «menos de N síntomas y
ninguno específico»), escríbela al final de la hoja: se aplicaría a todo el
dataset, no solo a esos 9.

La muestra es fija y sale de `data29/data-repos/hpo-v2/review_sheet.py`.

## Material

- **Hoja:** `data29/data-repos/curated-datasets/hpo_v2/validacion_clinica_nombres_sin_gen.md`
  (fuera de git; las listas de síntomas vienen de datasets públicos, pero se
  sigue la misma regla que con el resto de hojas).
- Contexto y resultados: [hpo-v2/README.md](../../data29/data-repos/hpo-v2/README.md).
- Tu revisión T3: `General/portfolio/DxGPT/research/tarea_finetuning_DxGPT.md`.

## Cómo se devuelve

La hoja rellena, por canal privado. Las correcciones se meten en
`clinical_gold.py` (como ya se hace con los códigos que el LLM no resolvía
bien), se reconstruye HPO v2 y se re-puntúan las listas de Terra.

## Hecho cuando

Los 69 casos tienen una casilla marcada, y los 9 de la causa C tienen decisión.
