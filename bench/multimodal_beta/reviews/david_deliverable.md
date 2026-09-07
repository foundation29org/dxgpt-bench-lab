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
| 24174966 | mantener | - | Historia: masa ventricular incidental, sin nombrar angiofibroma. David: las imágenes no llevan el diagnóstico escrito. | alta |
| 25995698 | mantener | - | Historia: dolor en hipocondrio izquierdo, fiebre y tos; no nombra secuestro pulmonar. David: imágenes sin texto diagnóstico. | alta |
| 23553973 | mantener | - | Historia: fiebre tras viaje a Australia; no nombra absceso amebiano. David: imágenes sin texto diagnóstico. | alta |
| 27656661 | mantener | - | Historia: marcha espástica, bandas oligoclonales, AQP4 negativo; no nombra EM ni «MS-like». David: imágenes sin texto diagnóstico. | alta |
| N-10000022 | mantener | - | Historia: prurito, ictericia y hierbas chinas; no nombra Wilson. David: imágenes sin texto diagnóstico. | alta |
| 27380346 | mantener | - | Historia: fiebre y rash a los 10 días de azatioprina; no nombra eritema nodoso. David: imágenes sin texto diagnóstico. | alta |
| 28126713 | mantener | - | Historia: traumatismo cervical, disfonía e hinchazón; no nombra hematoma retrofaríngeo. David: imágenes sin texto diagnóstico. | alta |
| 23449674 | mantener | - | Historia: hipoglucemias y lesión pancreática hipervascular; no nombra insulinoma. David: imágenes sin texto diagnóstico. | alta |
| case-19003 | mantener | - | Historia: dolor torácico atraumático con CrossFit; no nombra slipping rib. David: imágenes sin texto diagnóstico. | alta |
| 20052363 | mantener | - | Historia: enema de bario en chequeo, asintomática; no nombra linfangiomatosis. David: imágenes sin texto diagnóstico. | alta |

---

## Tareas 2 y 3 — Juez y gold (7 casos)

Paquete: [piloto25_juez.md](piloto25_juez.md)

Ejemplo de formato (Hodgkin vs Burkitt; este id no está en la tabla):

  `ejemplo | 0 | correcto | gold_valido | Burkitt no es Hodgkin de celularidad mixta. El rechazo del juez es correcto. | alta`

| id | Posición equivalente | Veredicto juez | Calidad gold | Justificación | Confianza |
|---|---|---|---|---|---|
| 24174966 | 0 | correcto | gold_valido | Un hemangioma cavernoso no es un angiofibroma cardíaco primario; son tumores vasculares distintos. El rechazo del juez es correcto. | alta |
| 27656661 | 1 | falso_negativo | gold_valido | Gold: Multiple sclerosis-like disorder. P1: PPMS, forma más específica. El juez dijo no-match (0); David sí ve equivalencia. | media |
| 30687305 | 0 | correcto | gold_valido | Ninguna propuesta es RCMD ni una forma más específica. El juez también dijo 0: acertó. | baja |
| 27074070 | 0 | correcto | gold_valido | Burkitt no es Hodgkin de celularidad mixta. El juez dijo 0: acertó. | baja |
| 27068836 | 0 | falso_positivo | gold_valido | El juez aceptó P1 (fístula faringoesofágica por hardware). Eso no es destrucción esofágica de espesor completo. | baja |
| 21424749 | 1 | correcto | gold_valido | Una miopatía mitocondrial heredada por vía materna sí es una enfermedad mitocondrial; es una forma específica dentro del espectro del gold. | alta |
| 23281978 | 1 | correcto | gold_valido | Un STEMI anterior por oclusión de la LAD sí es un infarto con elevación del ST; es una forma más específica del gold. | alta |

Sinónimos o diagnósticos secundarios que también deberían aceptarse:

-

Si has marcado 2 o más `falso_positivo` o `falso_negativo`, escríbelo aquí
y no abras el paquete de 100 por tu cuenta:

- Recuento limpio (mismos veredictos de David, etiquetas del formulario): `falso_positivo` `27068836`; `falso_negativo` `27656661`. `30687305` y `27074070` quedan `correcto` porque él mismo dijo que ninguna propuesta es el gold y el juez también dijo 0.

---

## Tarea 4 — Comparación ciega (8 casos)

Paquete: [ciego_t_vs_ti_muestra8.md](ciego_t_vs_ti_muestra8.md)

Historias e imágenes: `datasets/processed/medreamm_pilot100/<id>/`

No abras ningún `coordinator_key.md`.

Ejemplo de formato (inventado):

`23553973 | B | util | si | B nombra el absceso amebiano; A no. El TAC ayuda a localizar el absceso. | media`

| id | Mejor lista | Imagen | Matches automáticos correctos | Justificación | Confianza |
|---|---|---|---|---|---|
| 23553973 | B | util | si | La lista B si que nombra el amoebic liver abscess. | media |
| 27380346 | B | util | si | La lista B si que nombra el Erythema nodosum. | media |
| 27068836 | B | util | si | La lista B nombra diagnosticos más cercanos al gold que la lista A, así cómo Esophageal perforation with descending mediastinitis (likely secondary to cervical hardware erosion) o Retropharyngeal/paraesophageal abscess with mediastinal extension, siendo el primero de los dos el más cercano. | media |
| 23281978 | B | util | si | La lista B nombra directamente al gold y de forma más específica como una de sus opciones. | alta |
| N-10000083 | B | util | si | La lista B nombra directamente al gold pero sin especificar si se trata de intralobar o extralobar | media |
| 24054536 | B | util | si | La lista B se acerca más veces al gold que la lista A, pero ninguna de las dos es capaz de acertarlo.| media |
| 27709474 | B | util | si | La lista B nombra directamente al gold y además nombra como otra opción un diagnóstico muy cercano a diferencia de la lista A que no se acerca al gold con ningún diagnóstico. | alta |
| 23574122 | A | util | si | La lista A nombra directamente al gold. La lista B no dda diagnósticos cercanos ni acierta el gold. | media |

Si 2 o más decisiones contradicen el match automático, avisa aquí:

-

---

## Tarea 5 — Política de equivalencia

1. ¿Debe aceptarse una propuesta más específica que el gold?
En caso de que el modelo diga que la patología es un subtipo más especifico al gold, yo daría por correcto el gold inicial y mencionar que hay altas/medias/bajas probabilidades de que además se trate de el tipo concreto qeu sea en cada caso. 

2. ¿Cuándo son equivalentes síndrome, causa y manifestación?
Para ser equivalentes deben cumplir tres reglas simultaneamente. 1.Deben ser la misma entidad fisiológica, un síndrome una causa y una manifestación pueden ser quuivalentes si describen la misma enfermedad desde distintos niveles el ejemplo clásico es: 
Síndrome: Tumor‑induced osteomalacia
Causa: Phosphaturic mesenchymal tumor
Manifestación: Hipofosfatemia con osteomalacia
2.Relacion 1:1, quiere decir que la causa siempre produce ese síndrome y ese síndrome simepre implica esa manifestación. 
La causa produce ese síndrome de forma característica.
El síndrome siempre incluye esa manifestación.
La manifestación es prácticamente patognomónica del síndrome.
3.No hay otra interpretación posible, la manifestación no se explica por otra enfermedad, la causa no produce otros síndromes distintos, el síndrome no tiene múltiples etiologías divergentes.
Torus palatinus
Exostosis ósea del paladar duro
Masa ósea fija en línea media del paladar duro
No hay otra enfermedad que cumpla exactamente ese patrón.

3. ¿Pueden aceptarse subtipos histológicos diferentes?
Si pero el subtipo debe pertenecer exactamente a la misma enfermedad del gold.

4. ¿Cómo tratar golds fenotípicos o morfológicos?
Cuando el gold es fenotípico/morfológico, solo se aceptan entidades que describan la MISMA estructura, forma o patrón anatómico, aunque la causa sea distinta.

5. ¿Debe evaluarse solo el gold primario o cualquier diagnóstico final?
El gol es la única entidad contra la cual se comparan las propuestas. No importa si un apropuesta es un "diagnostico final" en la vida real. No importa si es una causa, una manifestación, un dubtipo, un síndrome. No importa si es más grave, más leve, más frecuente o más raro. Solo importa si se acerca al gold.

6. ¿Conviene publicar dos métricas: equivalencia y utilidad clínica?
Sí, conviene publicar dos métricas.
La equivalencia decide la validez conceptual. La utilidad clínica decide la relevancia práctica.
Separarlas hace tu sistema más preciso, más transparente y más robusto.
---

## Cierre

- ¿Pueden publicarse 80/100 y la ganancia de imágenes? `si` / `no` / `condicionado`
si
- Condiciones o casos que bloquean publicación:
.
- Casos que requieren segunda opinión:
Todos aquellos donde no se haya coincidido con el gold.
