# Tarea 1 · Validación clínica de `narrative_v2`

**Estado:** hecha el 4-nov-2026, también la tanda de reserva; faltan 3 recambios (ver al final) · **Tiempo:** ≈ 5 h (1–2 min por caso) · **Depende de:** nada

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
| Rara | Si el diagnóstico principal es una enfermedad rara (en Orphanet o con prevalencia menor de 1 por 2.000). La hoja muestra «Rara: sí/no», que puso el LLM; corrígelo si está mal |
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
- **Revisa también «Rara: sí/no».** Desde el 30-oct, la cifra principal del
  benchmark se publica por separado para casos reales de enfermedades raras y
  de no raras, así que esa etiqueta decide en qué cifra cuenta cada caso. Si tu
  hoja no tiene casilla para ello, escribe «rara: cambiar a sí/no» junto a la
  decisión.

Los casos excluidos se sustituyen por casos de reserva, así que excluir no deja
huecos.

Conviene mirar con más cuidado:

- los **4 gold que el juez marcó como «no es una enfermedad»**: `L-PMC13364497`
  (Type 2 pneumocyte hyperplasia), `L-PMC13540781` (Blindness), `U-T1241` y
  `U-T1073` (Bronchial hyperreactivity);
- los **78 casos `live` con «pistas a revisar»**: palabras del diagnóstico que
  aparecen en el texto, casi siempre anatomía o el fármaco causante;
- los **32 casos que ninguno de los seis modelos pone entre sus 5 primeras
  opciones**. En 29 algún modelo da una enfermedad relacionada, y casi siempre
  el gold pide un detalle que solo da la biopsia o el laboratorio («Chondroid
  meningioma» cuando los modelos dicen meningioma). Mira si el gold está a
  demasiado nivel de detalle, si el texto se recortó de más o si el caso es
  difícil de verdad: `L-PMC13316698`, `L-PMC13317807`, `L-PMC13331383`,
  `L-PMC13332505`, `L-PMC13355527`, `L-PMC13387059`, `L-PMC13391426`,
  `L-PMC13440813`, `L-PMC13448005`, `L-PMC13456877`, `L-PMC13461623`,
  `L-PMC13477540`, `L-PMC13500259`, `L-PMC13510912`, `L-PMC13511275`,
  `L-PMC13520939`, `L-PMC13543876`, `L-PMC13552804`, `L-PMC13586463`,
  `L-PMC13588688`, `L-PMC13595072`, `L-PMC13599191`, `L-PMC13605063`,
  `L-PMC13616667`, `L-PMC13647891`, `L-PMC13649838`, `L-PMC13653543`,
  `L-PMC13691139`, `U-T1055`, `U-T1292`, `U-T740`, `U-T805`.

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
mantienen tienen el diagnóstico principal, la fuga y la etiqueta de rara
revisados.

## Resultado (4-nov-2026)

Hoja devuelta con los 210 casos y aplicada en `narrative_v2` v0.2
(`data29/data-repos/narrative-v2/decisions_v0.2.yaml`):

- **Exclusiones:** 39 casos, 9 por fuga, 25 por no ser diagnosticables y 5 de
  urgencias con un gold que es un signo o una categoría amplia.
- **Duplicados:** otros 7 de urgencias quedan repetidos al corregir el gold.
- **En los que se mantienen:** se corrige el gold de 21, se quitan las frases
  que daban el diagnóstico en 22 y cambian 12 etiquetas de rara.
- **Datos identificativos:** los cuatro casos de urgencias que señalaste se
  han limpiado.

Al aplicarla se fijaron cuatro criterios, que ya van en la hoja de reserva:

- **Fuga:** solo la biopsia, citología, cultivo, serología, prueba
  confirmatoria o mutación, o una frase que nombra el diagnóstico. Un dato de
  laboratorio o de imagen que hay que interpretar no es fuga (6 casos se
  dejaron sin tocar).
- **No diagnosticable → excluir**, aunque no haya fuga.
- **Rara:** las intoxicaciones, las reacciones a fármacos, las lesiones y las
  complicaciones de procedimientos no cuentan, salvo que Orphanet las recoja.
- **Una sola casilla** de decisión por caso.

## Tanda de reserva

Los 46 casos que cubrían las bajas (28 `L-` y 18 `U-`) se devolvieron y se
aplicaron el 4-nov, con las decisiones al final de `decisions_v0.2.yaml`:

- **Exclusiones:** ninguna.
- **Duplicados:** 3 casos de urgencias quedan repetidos al corregir el gold
  (crup, bronquitis aguda y sinusitis aguda).
- **En los que se mantienen:**
  - se corrige el gold de 11, uno porque estaba mal: la anatomía patológica del
    artículo es un neurofibroma plexiforme benigno, no un tumor maligno;
  - se quita la frase que daba el diagnóstico en 3;
  - cambian 3 etiquetas de rara.
- **Criterios de la hoja:** dos fugas marcadas por un dato de laboratorio o de
  imagen se dejan sin tocar, con el mismo criterio de arriba.

La revisión caso a caso está en
`data29/data-repos/curated-datasets/narrative_v2/validacion_clinica_reserva_revision.md`
(fuera de git). La v0.2 queda con 207 casos reales validados (150 `L-` y
57 `U-`).

## Recambios

Los 3 duplicados se cubren con 3 casos nuevos de urgencias (≈ 5 min), en
`data29/data-repos/curated-datasets/narrative_v2/validacion_clinica_reserva.md`
(fuera de git; la hoja sustituye a la de la tanda de reserva). Se rellena y
se devuelve igual, por canal privado. Si alguno sale excluido o repetido, se
cubre con otro y la vuelta siguiente es de uno o dos casos.
