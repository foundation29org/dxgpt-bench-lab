# Encargo para David — revisión clínica de DxGPT con imágenes

Este documento es la guía. No hace falta saber programar ni lanzar
evaluaciones. Abres ficheros, lees casos y escribes veredictos.

Cuando termines, devuelves relleno
[reviews/david_deliverable.md](reviews/david_deliverable.md).
Tiempo estimado: 3–4 horas.

---

## 1. De qué va esto

DxGPT recibe una historia clínica y, a veces, imágenes (TAC, RM, foto,
patología). Devuelve una lista ordenada de diagnósticos posibles, de más a
menos probable.

Estamos midiendo esa lista contra un **gold**: el diagnóstico final que
publicó el caso original. El corpus es [MedReaMM](https://huggingface.co/datasets/thomasweiX/MedReaMM):
casos clínicos públicos, licencia MIT. Por eso las historias y las imágenes
pueden estar en el repositorio. No son datos confidenciales de pacientes
reales no publicados.

Un programa ya comparó cada lista con su gold. Ese programa a veces acierta
y a veces se pasa de la raya: acepta dos enfermedades que se parecen, o
rechaza un sinónimo válido. Tu trabajo es decir, caso a caso, si esa
comparación automática es clínicamente correcta.

Hasta que tú no cierres esto, no publicamos el 80/100 ni decimos que las
imágenes “mejoran el diagnóstico”.

---

## 2. Qué vas a decidir, en cristiano

Hay cinco tareas, en este orden. No las mezcles.

1. **¿El caso está amañado?** Si el texto o la imagen ya dicen el
   diagnóstico, el modelo no está diagnosticando: está leyendo la respuesta.
2. **¿El juez automático acertó?** Mira el gold y la lista de DxGPT y di si
   alguna propuesta es *la misma enfermedad*, no solo “parecida”.
3. **¿El gold sirve?** A veces el gold es un hallazgo, un fenotipo o un
   cajón demasiado ancho. Entonces el fallo no es de DxGPT.
4. **¿Cuál de dos listas es mejor?** Vas a ver A y B sin saber cómo se
   generaron. Eliges la más útil para llegar al gold.
5. **Normas para el futuro.** Seis preguntas para que el equipo sepa qué
   aceptar como acierto a partir de ahora.

---

## 3. Cómo está montado un caso

Cada caso vive en una carpeta. Ejemplo:

`datasets/processed/medreamm_pilot25/24174966/`

Dentro:

- `history.txt` — lo que vería un médico antes de saber el diagnóstico.
- `images/` — las fotos, cortes o láminas de ese mismo caso.

El **gold** no está en `history.txt` a propósito. Te lo ponemos nosotros en
las tablas y en los paquetes de revisión, para que compares.

Cuando un paquete dice “Propuestas”, esa es la lista de DxGPT, ya ordenada:

1. lo más probable según el modelo  
2. la siguiente  
…  

Si el programa marcó match en la posición 1, cree que la primera propuesta
es el gold. Si marcó `0` / `NO_MATCH`, cree que ninguna lo es.

---

## 4. Qué cuenta como la misma enfermedad

Acepta:

- el mismo diagnóstico con otro nombre (*Wilson's disease* =
  degeneración hepatolenticular);
- una forma **más específica** del gold (*STEAMI anterior por LAD* cuando
  el gold es STEMI).

No aceptes:

- otra entidad del diagnóstico diferencial, aunque se presente igual
  (cavernoma frente a angiofibroma cardíaco);
- un subtipo distinto (Burkitt frente a Hodgkin de celularidad mixta);
- la causa cuando el gold es la manifestación, o al revés, salvo que en
  la práctica clínica sean intercambiables — eso lo decides tú y lo
  anotas en la política.

Ejemplo que ya vimos: gold *mixed-cellularity Hodgkin*, propuesta *Burkitt*.
El juez permisivo lo dio por bueno. El juez actual lo rechazó. Tú dices si
ese rechazo es correcto.

Si dudas, pon `segunda_opinion` y escribe por qué.

---

## 5. Ficheros que necesitas

Parte de la carpeta `eval/bench/multimodal_beta/`.

| Para qué | Fichero |
|---|---|
| Esta guía | `MEDICAL_REVIEW.md` (este) |
| Donde escribes | [reviews/david_deliverable.md](reviews/david_deliverable.md) |
| Historias e imágenes del piloto | `datasets/processed/medreamm_pilot25/<id>/` |
| Historias e imágenes de la muestra ciega | `datasets/processed/medreamm_pilot100/<id>/` |
| Listas de DxGPT del piloto | `outputs/pilot25_product/evaluation_v4_primary_strict/clinical_review.md` |
| Las dos listas A/B | [reviews/ciego_t_vs_ti_muestra8.md](reviews/ciego_t_vs_ti_muestra8.md) |

No abras ningún fichero que se llame `coordinator_key.md`. Ahí está qué
lista es cuál; si lo abres, la comparación ciega no vale.

No hace falta leer `RESULTS.md` ni el resto de `outputs/`.

MedReaMM es público. Puedes tener las carpetas `datasets/processed/` en el
repo. Lo que no hay que difundir como “resultado clínico de DxGPT” son las
listas del modelo y tus veredictos hasta que el equipo lo publique.

---

## 6. Etiquetas (usa solo estas)

Si un caso no encaja, `segunda_opinion` y una frase.

| Campo | Qué significa | Valores |
|---|---|---|
| Fuga | ¿El caso enseña la respuesta? | `mantener` = no la enseña; `sanear` = hay que recortar texto o una imagen; `excluir` = el caso no sirve |
| Posición equivalente | ¿En qué puesto de la lista está el gold? | `1` a `5`, o `0` si ninguno es el gold |
| Juez | ¿El programa acertó al aceptar o rechazar? | `correcto`, `falso_positivo` (aceptó algo que no es el gold), `falso_negativo` (rechazó algo que sí lo es), `gold_ambiguo` |
| Gold | ¿El diagnóstico de referencia sirve? | `gold_valido`, `demasiado_amplio`, `demasiado_especifico`, `no_es_entidad_diagnostica`, `rol_incorrecto`, `segunda_opinion` |
| Lista ciega | ¿Qué diferencial es más útil? | `A`, `B`, `empate`, `ninguna` |
| Imagen | ¿La foto cambia la decisión? | `util`, `distrae`, `no_cambia` |
| Confianza | Lo seguro que estás | `alta`, `media`, `baja` |

---

## Tarea 1 — ¿El caso está amañado? (10 casos)

Objetivo: pillar textos o imágenes que ya nombran el diagnóstico.

Para cada fila de la tabla 1 del entregable:

1. Abre `datasets/processed/medreamm_pilot25/<id>/history.txt`.
2. Abre todas las imágenes de `images/`.
3. Ten el gold de la tabla delante.
4. Pregúntate: si yo no supiera el gold, ¿el texto o una leyenda me lo
   estarían diciendo?

Eso **sí** es fuga (poner `sanear` o `excluir`):

- el texto dice “se diagnosticó angiofibroma cardíaco”;
- una diapositiva tiene el nombre de la enfermedad escrito encima;
- el desenlace revela el gold (“la biopsia confirmó Burkitt”).

Eso **no** es fuga (poner `mantener`):

- un TAC con un absceso hepático, si nadie escribe “amebiano”;
- síntomas y exploraciones que un médico usaría de verdad;
- una imagen típica que *sugiere* el diagnóstico sin etiquetarlo.

| id | Gold |
|---|---|
| 24174966 | Primary cardiac angiofibroma |
| 25995698 | Extralobar pulmonary sequestration |
| 23553973 | Amoebic liver abscess |
| 27656661 | Multiple sclerosis-like disorder |
| N-10000022 | Wilson's disease |
| 27380346 | Erythema nodosum |
| 28126713 | Retropharyngeal hematoma |
| 23449674 | Insulinoma |
| case-19003 | Slipping rib syndrome |
| 20052363 | Lymphangiomatosis of the colon |

Ejemplo de fila (inventada, no copies el veredicto):

`24174966 | mantener | — | Historia de masa ventricular, sin nombre del tumor. Las imágenes no llevan leyenda diagnóstica. | alta`

---

## Tarea 2 — ¿El juez automático acertó? (7 casos)

Objetivo: auditar al programa que decide “esto es el mismo diagnóstico”.

Abre
`outputs/pilot25_product/evaluation_v4_primary_strict/clinical_review.md`.

Verás dos bloques:

- **Casos sin match** — el programa dijo que nadie en la lista es el gold.
  Tus candidatos: `24174966`, `27656661`, `30687305`, `27074070`.
- **Matches del juez LLM** — el programa aceptó una propuesta, casi
  siempre la 1. Tus candidatos: `27068836`, `21424749`, `23281978`.

Para cada uno:

1. Lee gold, lista y, si hace falta, historia e imágenes de
   `medreamm_pilot25/<id>/`.
2. Elige la **primera** propuesta que sea la misma entidad que el gold.
   Si ninguna lo es, `0`.
3. Compara con lo que hizo el programa:
   - él puso `0` y tú también → `correcto`;
   - él aceptó P1 y tú crees que P1 no es el gold → `falso_positivo`;
   - él puso `0` y tú ves el gold en P2 → `falso_negativo`;
   - el gold no se puede juzgar → `gold_ambiguo`.

Ejemplo (Hodgkin vs Burkitt, no está en estos 7, solo para el criterio):

- Gold: mixed-cellularity Hodgkin.
- P1: Burkitt lymphoma.
- Posición equivalente: `0`.
- Juez que lo aceptó: `falso_positivo`.
- Juez que lo rechazó: `correcto`.

Haz primero estos 7. Si marcas **2 o más** `falso_positivo` o
`falso_negativo`, avisa y te pasamos el paquete de 100. No lo abras tú.

---

## Tarea 3 — ¿El gold sirve? (los mismos 7)

En la misma tabla del entregable, columna “Calidad gold”.

Preguntas:

- ¿Es el diagnóstico final del caso, o un síntoma / hallazgo / fenotipo?
- ¿Es el objetivo principal, o un secundario?
- ¿Está demasiado ancho (“trastorno tipo EM”) o demasiado fino
  (un subtipo histológico que el texto no permite distinguir)?
- ¿Hay sinónimos o diagnósticos secundarios que también deberíamos
  aceptar? Escríbelos debajo de la tabla.

Ejemplo: gold *Multiple sclerosis-like disorder*. Puede ser
`demasiado_amplio` si la lista tiene PPMS o MOGAD y tú consideras que
eso ya cumple el objetivo del caso. O `gold_valido` si el artículo
dejó el diagnóstico a propósito en esa forma.

---

## Tarea 4 — Cuál lista es mejor, a ciegas (8 casos)

Abre solo [reviews/ciego_t_vs_ti_muestra8.md](reviews/ciego_t_vs_ti_muestra8.md).

Cada caso tiene el gold, la carpeta de `medreamm_pilot100`, una lista A
y una lista B. Una se generó con texto solo y la otra con texto más
imágenes. **No te decimos cuál es cuál.**

Casos: `23553973`, `27380346`, `27068836`, `23281978`, `N-10000083`,
`24054536`, `27709474`, `23574122`.

Para cada uno:

1. Abre `datasets/processed/medreamm_pilot100/<id>/` (historia e imágenes).
2. Lee A y B.
3. Elige la lista con la que un clínico llegaría mejor al gold
   (`A`, `B`, `empate`, `ninguna`).
4. Di si las imágenes de esa carpeta ayudan, distraen o no cambian.
5. El paquete marca “Match automático: N” en cada lista. `0` significa
   que el programa no vio el gold. Tú dices si ese marcaje es correcto.

Si en **2 o más** casos tu elección contradice de forma clara el match
automático, avisa. Entonces te pasamos los 24. No los abras por tu cuenta.

---

## Tarea 5 — Normas (las 6 preguntas del entregable)

Responde en prosa corta. No hay respuesta “técnica” correcta: es criterio
clínico para el equipo.

1. Si el gold es “linfoma” y DxGPT dice “linfoma de Hodgkin clásico”,
   ¿cuenta como acierto?
2. ¿Cuándo un síndrome, su causa y su manifestación son lo mismo para
   esta evaluación?
3. ¿Hodgkin y Burkitt pueden ser equivalentes? ¿Y dos subtipos de
   Hodgkin entre sí?
4. ¿Qué hacemos con golds tipo “destrucción esofágica de espesor
   completo” o “trastorno tipo EM”?
5. Si el caso tiene un diagnóstico secundario también confirmado, ¿vale
   acertar ese o solo el primario?
6. ¿Quieres dos notas: una de equivalencia estricta y otra de “útil en
   consulta”?

Al final del entregable: ¿se pueden publicar el 80/100 y que las
imágenes mejoran el resultado? `si` / `no` / `condicionado`.

---

## Qué no toques

No forman parte de este encargo:

- el resto de `outputs/` (texto solo, solo imágenes, imágenes
  intercambiadas);
- cualquier `coordinator_key.md`;
- recalcular métricas o editar código.

---

## Cómo devolver el trabajo

1. Copia o edita [reviews/david_deliverable.md](reviews/david_deliverable.md).
2. Rellena las tres tablas, las seis preguntas y el cierre.
3. Envíalo al responsable técnico.

Él incorporará tus etiquetas. Tú no tienes que regenerar nada.
