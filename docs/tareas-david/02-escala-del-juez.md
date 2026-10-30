# Tarea 2 · Validar la escala del juez (2/1/0)

**Estado:** pendiente de preparar · **Tiempo:** ≈ 2 h · **Depende de:** tarea 1

## Para qué sirve

El evaluador actual (Pipeline V5) le pide a un LLM juez, Gemini 2.5 Pro, que
compare cada diagnóstico de la lista del modelo con el diagnóstico de
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
3. qué juez usar (paso 6 del [ROADMAP](../ROADMAP.md)): si uno más barato da
   notas tan parecidas a las tuyas como Gemini 2.5 Pro, se usa el barato. Hay
   tres candidatos, que con las mismas listas ordenan igual a los modelos y
   coinciden con Pro en «¿es un 2?» en el 98 % de las opciones:
   - Gemini 3.8 Flash, unas 30 veces más barato que Pro;
   - Claude Opus 5.5, de otra familia (Anthropic), para no depender solo de
     Gemini;
   - Gemini 2.5 Flash, como referencia.

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
- unas 25 con un 0, sobre todo las que comparten código ICD-10 con la referencia;
- unas 15 «notas dobles»: listas en las que el juez da un 2 a más de una
  opción para la misma referencia (pasa en el 10–17 % de las listas). No se
  cuentan dos veces, pero el segundo 2 a veces es generoso, por ejemplo
  «insuficiencia aórtica crónica por dilatación de la raíz» para «aneurisma
  aórtico». Si uno de esos 2 dudosos queda el primero de la lista, infla la
  nota;
- y, dentro de esas, sobre todo las parejas en que Gemini 2.5 Pro, Gemini 3.8
  Flash y Claude Opus 5.5 ponen notas distintas, para ver cuál acierta.

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

Se prepara cuando termine la tarea 1, porque la muestra tiene que salir del
gold ya corregido. Irá en
`data29/data-repos/curated-datasets/narrative_v2/validacion_clinica_escala.md`
(fuera de git).

## Cómo se devuelve

La hoja rellena, por canal privado. Al repo vuelven solo las notas
(identificador de la pareja y nota), y con ellas se mide cuánto coincide cada
juez contigo en cada frontera.

## Hecho cuando

Las ~100 parejas tienen nota, y las dudas están marcadas como CONSULTAR MÉDICO
con una línea de explicación. Si ves un patrón en lo que el juez puntúa
distinto que tú, apúntalo en una frase: es lo que decide si la rúbrica cambia.
