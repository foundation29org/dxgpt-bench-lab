# Entregable — David

Rellena las tablas y las preguntas. La guía está en
[../MEDICAL_REVIEW.md](../MEDICAL_REVIEW.md). No hace falta código.

Etiquetas permitidas:

- Fuga: `mantener` | `sanear` | `excluir`
- Posición equivalente: `1`–`5` o `0`
- Juez: `correcto` | `falso_positivo` | `falso_negativo` | `gold_ambiguo`
- Gold: `gold_valido` | `demasiado_amplio` | `demasiado_especifico` | `no_es_entidad_diagnostica` | `rol_incorrecto` | `segunda_opinion`
- Lista: `A` | `B` | `empate` | `ninguna`
- Imagen: `util` | `distrae` | `no_cambia`
- Confianza: `alta` | `media` | `baja`

Si no encaja, `segunda_opinion` y una frase.

---

## Tarea 1 — Fuga (10 casos)

Carpeta de cada id: `datasets/processed/medreamm_pilot25/<id>/`
(`history.txt` + `images/`).

Ejemplo de formato (inventado; no copies el veredicto):

`24174966 | mantener | — | La historia describe una masa ventricular sin nombrar el tumor. Las imágenes no llevan el diagnóstico escrito. | alta`

| id | Decisión | Fuente de fuga (si hay) | Justificación | Confianza |
|---|---|---|---|---|
| 24174966 | mantener | - | No hay nada en las imágenes que pueda generar una fuga, sobre todo porque no hay texto. | alta |
| 25995698 | mantener | - | No hay nada en las imágenes que pueda generar una fuga, sobre todo porque no hay texto. | alta |
| 23553973 | mantener | - | No hay nada en las imágenes que pueda generar una fuga, sobre todo porque no hay texto. | alta |
| 27656661 | mantener | - | No hay nada en las imágenes que pueda generar una fuga, sobre todo porque no hay texto. | alta |
| N-10000022 | mantener | - | No hay nada en las imágenes que pueda generar una fuga, sobre todo porque no hay texto. | alta |
| 27380346 | mantener | - | No hay nada en las imágenes que pueda generar una fuga, sobre todo porque no hay texto. | alta |
| 28126713 | mantener | - | No hay nada en las imágenes que pueda generar una fuga, sobre todo porque no hay texto. | alta |
| 23449674 | mantener | - | No hay nada en las imágenes que pueda generar una fuga, sobre todo porque no hay texto. | alta |
| case-19003 | mantener | - | No hay nada en las imágenes que pueda generar una fuga, sobre todo porque no hay texto. | alta |
| 20052363 | mantener | - | No hay nada en las imágenes que pueda generar una fuga, sobre todo porque no hay texto. | alta |

---

## Tareas 2 y 3 — Juez y gold (7 casos)

Paquete: [piloto25_juez.md](piloto25_juez.md)

Ejemplo de formato (Hodgkin vs Burkitt; este id no está en la tabla):

  `ejemplo | 0 | correcto | gold_valido | Burkitt no es Hodgkin de celularidad mixta. El rechazo del juez es correcto. | alta`

| id | Posición equivalente | Veredicto juez | Calidad gold | Justificación | Confianza |
|---|---|---|---|---|---|
| 24174966 | 0 | correcto | gold_valido | Un hemangioma cavernoso no es un angiofibroma cardíaco primario; son tumores vasculares distintos. El rechazo del juez es correcto. | alta |
| 27656661 | 1 |  |  |  |  |
| 30687305 |  |  |  |  |  |
| 27074070 |  |  |  |  |  |
| 27068836 |  |  |  |  |  |
| 21424749 |  |  |  |  |  |
| 23281978 |  |  |  |  |  |

Sinónimos o diagnósticos secundarios que también deberían aceptarse:

-

Si has marcado 2 o más `falso_positivo` o `falso_negativo`, escríbelo aquí
y no abras el paquete de 100 por tu cuenta:

-

---

## Tarea 4 — Comparación ciega (8 casos)

Paquete: [ciego_t_vs_ti_muestra8.md](ciego_t_vs_ti_muestra8.md)

Historias e imágenes: `datasets/processed/medreamm_pilot100/<id>/`

No abras ningún `coordinator_key.md`.

Ejemplo de formato (inventado):

`23553973 | B | util | si | B nombra el absceso amebiano; A no. El TAC ayuda a localizar el absceso. | media`

| id | Mejor lista | Imagen | Matches automáticos correctos | Justificación | Confianza |
|---|---|---|---|---|---|
| 23553973 |  |  |  |  |  |
| 27380346 |  |  |  |  |  |
| 27068836 |  |  |  |  |  |
| 23281978 |  |  |  |  |  |
| N-10000083 |  |  |  |  |  |
| 24054536 |  |  |  |  |  |
| 27709474 |  |  |  |  |  |
| 23574122 |  |  |  |  |  |

Si 2 o más decisiones contradicen el match automático, avisa aquí:

-

---

## Tarea 5 — Política de equivalencia

1. ¿Debe aceptarse una propuesta más específica que el gold?

2. ¿Cuándo son equivalentes síndrome, causa y manifestación?

3. ¿Pueden aceptarse subtipos histológicos diferentes?

4. ¿Cómo tratar golds fenotípicos o morfológicos?

5. ¿Debe evaluarse solo el gold primario o cualquier diagnóstico final?

6. ¿Conviene publicar dos métricas: equivalencia y utilidad clínica?

---

## Cierre

- ¿Pueden publicarse 80/100 y la ganancia de imágenes? `si` / `no` / `condicionado`
- Condiciones o casos que bloquean publicación:
- Casos que requieren segunda opinión:
