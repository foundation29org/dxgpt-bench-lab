# Tarea 1 · Validación clínica de `narrative_v2`

**Estado:** encargada · **Tiempo:** ≈ 5 h (1–2 min por caso) · **Depende de:** nada

## Para qué sirve

`narrative_v2` es el banco de casos narrativos nuevo con el que se compara a
los modelos (sustituye a `all_256_clean`). Un LLM sacó de cada artículo o
informe de urgencias el diagnóstico final y el texto de presentación. Antes de
publicar cifras con él, un clínico tiene que confirmar que cada caso sirve.

Ya hay seis modelos evaluados sobre la versión sin validar. Sus listas no
cambian: cuando vuelvan tus decisiones, se corrige el gold, se quitan los
casos excluidos y se re-puntúa. Con eso sale la línea base oficial.

## Qué hay que hacer

Revisar los **210 casos** de la hoja:

- 150 case reports publicados en PubMed entre julio y octubre de 2026 (`L-`,
  en inglés, con enlace al artículo);
- 60 casos de urgencias (`U-`, en español, con el diagnóstico de alta
  original).

En cada caso:

| Campo | Qué mirar |
|---|---|
| Diagnóstico principal | El diagnóstico final, al nivel que se escribe en un diferencial: sin grado, estadio, tamaño ni sub-localización, salvo que definan otra enfermedad. Corrígelo si es demasiado amplio, demasiado específico o no es una enfermedad |
| Nombres aceptados | Sinónimos de exactamente la misma enfermedad. Quita categorías amplias y enfermedades relacionadas |
| Fuga | Hay fuga si el texto nombra el diagnóstico o da un resultado que por sí solo lo establece (biopsia, mutación, enzima que lo define) |
| Diagnosticable | Con ese texto, un clínico podría incluir el diagnóstico en su diferencial |
| Decisión | Mantener o excluir |

### Cómo decidir

- **Excluir si hay fuga**, aunque el resto esté bien: el caso ya no mide si
  el modelo llega al diagnóstico. Basta con marcar «Fuga: sí», escribir qué la
  delata y marcar «excluir»; no hace falta revisar los demás campos.
  Excepción: si la fuga es una sola frase que se puede quitar sin perder el
  caso (por ejemplo, el resultado de la biopsia al final), escribe «se arregla
  quitando: …» y lo decidimos al aplicar tus cambios.
- **Excluir si no es diagnosticable** con ese texto, o si el diagnóstico no es
  una enfermedad y no se puede corregir a una.
- **Mantener, corrigiendo,** si solo hay que cambiar el diagnóstico principal
  o los nombres aceptados.
- Las «pistas a revisar» no son fuga por sí solas: una zona anatómica o el
  fármaco causante no dan el diagnóstico. Solo hay fuga si el texto lo nombra o
  da una prueba que por sí sola lo establece.

Los casos excluidos se sustituyen por casos de reserva, así que excluir no deja
huecos.

Conviene mirar con más cuidado:

- los **4 gold que el juez marcó como «no es una enfermedad»**: `L-PMC13364497`
  (Type 2 pneumocyte hyperplasia), `L-PMC13540781` (Blindness), `U-T1241` y
  `U-T1073` (Bronchial hyperreactivity);
- los **78 casos `live` con «pistas a revisar»**: palabras del diagnóstico que
  aparecen en el texto, casi siempre anatomía o el fármaco causante.

Se puede hacer por partes: primero los `L-` y después los `U-`.

## Material

- **Hoja:** `data29/data-repos/curated-datasets/narrative_v2/validacion_clinica.md`
  (fuera de git; se comparte por canal privado).
- Contexto del dataset: [narrative-v2/README.md](../../data29/data-repos/narrative-v2/README.md).

## Cómo se devuelve

La hoja rellena, por canal privado. De ella se saca un fichero de decisiones
sin texto de casos (identificador, decisión y gold corregido) que sí se
versiona, y con él se construye `narrative_v2` v0.2. Las bajas se cubren con
casos de reserva; esos casos nuevos te llegarían en una tanda corta aparte.

## Hecho cuando

Los 210 casos tienen marcada la decisión (mantener o excluir), y los que se
mantienen tienen el diagnóstico principal y la fuga revisados.
