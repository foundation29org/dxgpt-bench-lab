# Tarea 2 · Validar la escala del juez (2/1/0)

**Estado:** lista para empezar (hoja del 4-nov) · **Tiempo:** ≈ 2 h · **Depende de:** tarea 1 (hecha)

## Para qué sirve

El evaluador actual (Pipeline V5) le pide a un LLM juez, Gemini 3.8 Flash
(antes, Gemini 2.5 Pro), que compare cada diagnóstico de la lista del modelo con el diagnóstico de
referencia y ponga una nota:

| Nota | Significado |
|---|---|
| **2** | Misma enfermedad: sinónimo, abreviatura, un subtipo de la referencia, o una respuesta que nombra la referencia aunque añada una causa o una complicación |
| **1** | Relacionada, pero no la misma: categoría más amplia, otro subtipo, causa, complicación… |
| **0** | Otra enfermedad |

Criterio de Julián (30-oct) para decidir qué es «la misma enfermedad»: lo es
si está **relacionada con la referencia y se trata de la misma forma**. Hacen
falta las dos cosas. Es el criterio con el que hay que poner las notas.

La cifra que se publica solo cuenta los 2 (nota estricta). La que cuenta
también los 1 (nota laxa) es mucho más alta: en `narrative_v2`, Terra 5.6
acierta entre los 5 primeros el 78 % con la estricta y el 96 % con la laxa.
Esa diferencia depende de dónde pone el juez la frontera entre 1 y 0, y entre
2 y 1. Nadie la ha validado todavía con criterio clínico.

Con tus notas se decide:

1. si el juez acierta lo bastante como para fiarse de la nota estricta;
2. si la nota laxa se puede publicar o se queda como uso interno;
3. qué juez usar (paso 6 del [ROADMAP](../ROADMAP.md)). Google retira
   Gemini 2.5 Pro el 1-dic-2026 (las peticiones pasan a contestarse con
   3.8 Flash), así que quedan dos candidatos, que con las mismas listas
   ordenan igual a los modelos y coincidían con Pro en «¿es un 2?» en el 98 %
   de las opciones:
   - Gemini 3.8 Flash, el juez de referencia desde ahora, unas 30 veces más
     barato que Pro;
   - Claude Opus 5.5, de otra familia (Anthropic), para no depender solo de
     Gemini.

   Con el gold de la v0.2 y `graded_v3`, sobre las listas de los seis modelos
   en los 164 casos reales validados, Flash y Opus 5.5 coinciden en «¿es un
   2?» en el 98,3 % de las opciones (kappa 0,94), y Flash y Pro en el 97,4 %.
   Discrepan en unas 200 opciones en las que ninguno es claramente mejor. En
   raras, donde las discrepancias venían de sinónimos poco usados, el
   problema se resuelve pasando al juez los sinónimos del gold (tarea 3,
   bloque F). Lo que queda por decidir está en `narrative_v2`.
4. si la rúbrica se queda como está. Si tus discrepancias con el juez son
   casos sueltos, no se toca: con cualquier dataset saldrá alguno. Si siguen
   un patrón (por ejemplo, el juez da un 2 a otro subtipo que se trata
   distinto), se cambia una sola vez a partir de tus notas.

## Qué habrá que hacer

Poner tu propia nota (2, 1 o 0) a unas **100 parejas** «diagnóstico de
referencia / diagnóstico propuesto» sacadas de los seis modelos evaluados en
`narrative_v2`, con las notas del juez adoptado (`graded_v3`). **No verás la
nota del juez**, para no condicionarte. La
muestra llevará sobre todo los casos difíciles:

- unas 35 parejas a las que el juez puso un 1 (la frontera que más mueve la cifra);
- unas 25 con un 2 que no viene de un código idéntico;
- unas 25 con un 0, sobre todo aquellas a las que otro juez puso un 1 o un 2
  (los gold de `narrative_v2` no llevan códigos, así que no se puede filtrar
  por ICD-10);
- unas 15 «notas dobles»: listas en las que el juez da un 2 a más de una
  opción para la misma referencia (pasa en el 10–17 % de las listas). No se
  cuentan dos veces, pero el segundo 2 a veces es generoso, por ejemplo
  «insuficiencia aórtica crónica por dilatación de la raíz» para «aneurisma
  aórtico». Si uno de esos 2 dudosos queda el primero de la lista, infla la
  nota;
- y, dentro de cada grupo, un 60 % de parejas en que Gemini 3.8 Flash,
  Claude Opus 5.5 y el juez anterior (Gemini 2.5 Pro) ponen notas distintas,
  para ver cuál acierta, y un 40 % en que coinciden, para medir también el
  caso habitual (los tres coinciden en el 83 % de las parejas).

Las notas que se comparan son las de Flash, que es el juez de referencia. Los
grupos se cuentan por la nota de Flash, y en la hoja van mezclados.

Cada pareja irá con el caso (texto o resumen) por si hace falta contexto, pero
la pregunta es solo si las dos son la misma enfermedad.

Reglas acordadas con Julián que conviene aplicar igual (§12 de
[JULIAN_HARNESS_REVIEW.md](../../bench/multimodal_beta/JULIAN_HARNESS_REVIEW.md)):

- «X con Y» (Y es una complicación o manifestación) se acierta con «X»;
- al revés también: una respuesta que nombra la referencia y añade una causa
  o una complicación se acierta («colangitis por una fístula
  coledocoduodenal» para «fístula coledocoduodenal»);
- una referencia amplia («Ovarian tumor») se acierta con una forma más
  específica de ella;
- con varias referencias, basta con acertar una;
- ante la duda, el criterio de Julián: relacionada y tratada de la misma
  forma.

Si alguna de estas reglas te parece clínicamente mal, dilo: es parte de la
validación.

## Material

- **Hoja:**
  `data29/data-repos/curated-datasets/narrative_v2/validacion_clinica_escala.md`
  (fuera de git).
- **Muestra:** 100 parejas de 75 casos reales ya validados de la v0.2, 54
  `L-` y 21 `U-`, 34 de ellos raros. Hay como mucho dos parejas por caso, y
  las de un mismo caso van juntas, con el texto del caso plegado.
- **Clave privada:** el modelo que propuso cada diagnóstico y las notas de los
  tres jueces están en
  `data29/data-repos/narrative-v2/work/escala_v0.2_key.json` (fuera de git),
  con el tamaño de cada grupo para poder ponderar.

## Cómo se devuelve

La hoja rellena, por canal privado. Al repo vuelven solo las notas
(identificador de la pareja y nota), y con ellas se mide cuánto coincide cada
juez contigo en cada frontera.

## Hecho cuando

Las ~100 parejas tienen nota, y las dudas están marcadas como CONSULTAR MÉDICO
con una línea de explicación. Si ves un patrón en lo que el juez puntúa
distinto que tú, apúntalo en una frase: es lo que decide si la rúbrica cambia.
