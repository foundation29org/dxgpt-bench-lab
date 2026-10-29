# Tarea 2 · Validar la escala del juez (2/1/0)

**Estado:** pendiente de preparar · **Tiempo:** ≈ 2 h · **Depende de:** tarea 1

## Para qué sirve

El evaluador actual (Pipeline V5) le pide a un LLM juez, Gemini 2.5 Pro, que
compare cada diagnóstico de la lista del modelo con el diagnóstico de
referencia y ponga una nota:

| Nota | Significado |
|---|---|
| **2** | Misma enfermedad: sinónimo, abreviatura, o un subtipo de la referencia |
| **1** | Relacionada, pero no la misma: categoría más amplia, otro subtipo, causa, complicación… |
| **0** | Otra enfermedad |

La cifra que se publica solo cuenta los 2 (nota estricta). La que cuenta
también los 1 (nota laxa) es mucho más alta: en `narrative_v2`, Terra 5.6
acierta entre los 5 primeros el 78 % con la estricta y el 96 % con la laxa.
Esa diferencia depende de dónde pone el juez la frontera entre 1 y 0, y entre
2 y 1. Nadie la ha validado todavía con criterio clínico.

Con tus notas se decide:

1. si el juez acierta lo bastante como para fiarse de la nota estricta;
2. si la nota laxa se puede publicar o se queda como uso interno;
3. qué juez usar (paso 6 del [ROADMAP](../ROADMAP.md)): si uno más barato da
   notas tan parecidas a las tuyas como Gemini 2.5 Pro, se usa el barato. El
   candidato es Gemini 3.8 Flash: con las mismas listas ordena igual a los
   modelos, cuesta unas 30 veces menos, y discrepa de Pro en unas 200
   opciones en las que ninguno de los dos es claramente mejor.

## Qué habrá que hacer

Poner tu propia nota (2, 1 o 0) a unas **100 parejas** «diagnóstico de
referencia / diagnóstico propuesto» sacadas de los seis modelos evaluados en
`narrative_v2`. **No verás la nota del juez**, para no condicionarte. La
muestra llevará sobre todo los casos difíciles:

- unas 40 parejas a las que el juez puso un 1 (la frontera que más mueve la cifra);
- unas 30 con un 2 que no viene de un código idéntico;
- unas 30 con un 0, sobre todo las que comparten código ICD-10 con la referencia;
- y, dentro de esas, las parejas en que Gemini 2.5 Pro y Gemini 3.8 Flash
  ponen notas distintas, para ver cuál de los dos acierta.

Cada pareja irá con el caso (texto o resumen) por si hace falta contexto, pero
la pregunta es solo si las dos son la misma enfermedad.

Reglas acordadas con Julián que conviene aplicar igual (§12 de
[JULIAN_HARNESS_REVIEW.md](../../bench/multimodal_beta/JULIAN_HARNESS_REVIEW.md)):

- «X con Y» (Y es una complicación o manifestación) se acierta con «X»;
- una referencia amplia («Ovarian tumor») se acierta con una forma más
  específica de ella;
- con varias referencias, basta con acertar una.

Si alguna de estas reglas te parece clínicamente mal, dilo: es parte de la
validación.

## Material

Se prepara cuando termine la tarea 1, porque la muestra tiene que salir del
gold ya corregido. Irá en
`data29/data-repos/curated-datasets/narrative_v2/validacion_clinica_escala.md`
(fuera de git).

## Cómo se devuelve

La hoja rellena, por canal privado. Al repo vuelven solo las notas
(identificador de la pareja y nota), y con ellas se mide cuánto coincide el
juez contigo en cada frontera.

## Hecho cuando

Las ~100 parejas tienen nota, y las dudas están marcadas como CONSULTAR MÉDICO
con una línea de explicación.
