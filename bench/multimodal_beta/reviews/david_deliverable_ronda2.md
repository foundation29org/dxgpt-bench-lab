# Entregable — David, ronda 2

Rellena las tablas. La guía está en
[../MEDICAL_REVIEW_RONDA2.md](../MEDICAL_REVIEW_RONDA2.md).
Paquete: [piloto100_juez_unmatched_llm.md](piloto100_juez_unmatched_llm.md).

No hace falta código. No abras `outputs/` ni ningún `coordinator_key.md`.

Etiquetas permitidas:

- Posición equivalente: `1`–`5` o `0`
- Juez: `correcto` | `falso_positivo` | `falso_negativo` | `gold_ambiguo`
- Gold: `gold_valido` | `demasiado_amplio` | `demasiado_especifico` | `no_es_entidad_diagnostica` | `rol_incorrecto` | `segunda_opinion`
- Confianza: `alta` | `media` | `baja`

Si no encaja, `segunda_opinion` y una frase.

Estas listas son las de la corrida de **100 casos**, no las del piloto de 25.
Cinco ids de ronda 1 están copiados como punto de partida (la propuesta que
importa no cambió). `24174966` y `27074070` van vacíos: la lista sí cambió.

Ejemplo: `27074070 | 0 | correcto | gold_valido | Ninguna propuesta es Hodgkin de celularidad mixta. | alta`

Tiempo estimado: ~29 casos nuevos, 4–6 horas.

---

## A — Sin match automático (20)

Si el programa dijo 0 y tú también: `correcto`.
Si el programa dijo 0 y tú ves el gold en la lista: `falso_negativo`.

| id | Posición equivalente | Veredicto juez | Calidad gold | Justificación | Confianza |
|---|---|---|---|---|---|
| 24174966 |  |  |  |  |  |
| 25995698 |  |  |  |  |  |
| 27656661 | 1 | falso_negativo | gold_valido | P1 PPMS es forma más específica del gold MS-like; el juez dijo 0. (ronda 1; confirma) | media |
| 30687305 | 0 | correcto | gold_valido | Ninguna propuesta es RCMD. El juez dijo 0. (ronda 1; confirma) | baja |
| 27074070 |  |  |  |  |  |
| 24054536 |  |  |  |  |  |
| 29748223 |  |  |  |  |  |
| 27332906 |  |  |  |  |  |
| 32340587 |  |  |  |  |  |
| N-10000032 |  |  |  |  |  |
| 26819809 |  |  |  |  |  |
| 24910386 |  |  |  |  |  |
| 23752113 |  |  |  |  |  |
| N-10000050 |  |  |  |  |  |
| 23574122 |  |  |  |  |  |
| 19721837 |  |  |  |  |  |
| 26958738 |  |  |  |  |  |
| 28620010 |  |  |  |  |  |
| 28706431 |  |  |  |  |  |
| 28104685 |  |  |  |  |  |

---

## B — Matches del juez LLM (16)

Si el programa aceptó Pn y tú estás de acuerdo: `correcto`.
Si aceptó Pn y esa propuesta **no** es el gold: `falso_positivo`.

| id | Posición equivalente | Veredicto juez | Calidad gold | Justificación | Confianza |
|---|---|---|---|---|---|
| 27068836 | 0 | falso_positivo | gold_valido | El juez aceptó P1 (perforación/fístula por hardware). No es destrucción de espesor completo. (ronda 1; confirma) | baja |
| 21424749 | 1 | correcto | gold_valido | P1 es enfermedad mitocondrial, forma específica del gold. (ronda 1; confirma) | alta |
| 23281978 | 1 | correcto | gold_valido | STEMI anterior por LAD es una forma más específica del gold. (ronda 1; confirma) | alta |
| 27709474 |  |  |  |  |  |
| 27514369 |  |  |  |  |  |
| 30766756 |  |  |  |  |  |
| 32046748 |  |  |  |  |  |
| 23482507 |  |  |  |  |  |
| N-10000086 |  |  |  |  |  |
| 23800107 |  |  |  |  |  |
| 28302624 |  |  |  |  |  |
| 27797319 |  |  |  |  |  |
| 22563559 |  |  |  |  |  |
| 25336332 |  |  |  |  |  |
| 25282086 |  |  |  |  |  |
| 28472977 |  |  |  |  |  |

---

## Recuento (36 casos de esta corrida)

- Falsos positivos:
-
- Falsos negativos:
-
- Golds que no sirven (`demasiado_amplio` / `demasiado_especifico` / `no_es_entidad_diagnostica` / `rol_incorrecto`):
-
- Casos `segunda_opinion`:
-

Sinónimos o diagnósticos secundarios que también deberían aceptarse:

-

## Cierre

- Tras esta tira, ¿el 80/100 se puede publicar? `si` / `no` / `condicionado`
-
- Condiciones:
-
