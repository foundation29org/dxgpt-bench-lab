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


| id         | Posición equivalente | Veredicto juez | Calidad gold     | Justificación                                                                                                                                                                                                                                                                                                                                                                                                  | Confianza |
| ---------- | -------------------- | -------------- | ---------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------- |
| 24174966   | 0                    | correcto       | gold_valido      | Ninguna propuesta llega a encajar del todo con el gold.                                                                                                                                                                                                                                                                                                                                                        | alta      |
| 25995698   | 0                    | correcto       | gold_valido      | Ninguna propuesta llega a encajar del todo con el gold.                                                                                                                                                                                                                                                                                                                                                        | alta      |
| 27656661   | 1                    | falso_negativo | gold_valido      | P1 PPMS es forma más específica del gold MS-like; el juez dijo 0. (ronda 1; confirma)                                                                                                                                                                                                                                                                                                                          | media     |
| 30687305   | 0                    | correcto       | gold_valido      | Ninguna propuesta es RCMD. El juez dijo 0. (ronda 1; confirma)                                                                                                                                                                                                                                                                                                                                                 | baja      |
| 27074070   | 0                    | correcto       | gold_valido      | Ninguna propuesta llega a encajar del todo con el gold.                                                                                                                                                                                                                                                                                                                                                        | alta      |
| 24054536   | 0                    | correcto       | demasiado_amplio | El gold no es una enfemredad, es un fenotipo, por ello en teoria todas las opciones de propuesta menos la última (Acute pulmonary embolism) pueden ser correctas porque de una manera u otra encajan con el fenotipo.                                                                                                                                                                                          | alta      |
| 29748223   | 0                    | correcto       | gold_valido      | Ninguna propuesta llega a encajar del todo con el gold.                                                                                                                                                                                                                                                                                                                                                        | alta      |
| 27332906   | 0                    | correcto       | gold_valido      | Ninguna propuesta llega a encajar del todo con el gold.                                                                                                                                                                                                                                                                                                                                                        | alta      |
| 32340587   | 0                    | correcto       | gold_valido      | Ninguna propuesta llega a encajar del todo con el gold.                                                                                                                                                                                                                                                                                                                                                        | alta      |
| N-10000032 | 0                    | correcto       | gold_valido      | Ninguna propuesta llega a encajar del todo con el gold.                                                                                                                                                                                                                                                                                                                                                        | alta      |
| 26819809   | 1                    | falso_negativo | gold_valido      | El error estaba en que debido a que el grado de malignidad no era el mismo, lo ha tomado como diferente pero la enfermedad es la misma.                                                                                                                                                                                                                                                                        | alta      |
| 24910386   | 0                    | incorrecto     | demasiado_amplio | El diagnóstico es un patrón de lesión, no una enfermedad. Por ello todas las entidades que produzcan isquemia real del cuero cabelludo son equivalentes y todas las que no lo produzcan se deben rechazar. Por ello tanto Critical proximal common carotid artery stenosis/occlusion with scalp ischemia cómo Giant cell arteritis (temporal arteritis) with scalp necrosis podrían ser diagnósticos correctos | alta      |
| 23752113   | 0                    | correcto       | gold_valido      | Ninguna propuesta llega a encajar del todo con el gold.                                                                                                                                                                                                                                                                                                                                                        | alta      |
| N-10000050 | 0                    | correcto       | gold_valido      | Ninguna propuesta llega a encajar del todo con el gold.                                                                                                                                                                                                                                                                                                                                                        | alta      |
| 23574122   | 0                    | correcto       | gold_valido      | Ninguna propuesta llega a encajar del todo con el gold.                                                                                                                                                                                                                                                                                                                                                        | alta      |
| 19721837   | 1                    | falso_negativo | gold_valido      | La opción 1 es exactamente la misma enfermedad madre. Siendo el gold la forma aguda y la propuesta la forma idiopática crónica pero ambas son Idiopathic hypereosinophilic syndrome (HES).                                                                                                                                                                                                                     | alta      |
| 26958738   | 0                    | correcto       | gold_valido      | Ninguna propuesta llega a encajar del todo con el gold.                                                                                                                                                                                                                                                                                                                                                        | alta      |
| 28620010   | 0                    | correcto       | gold_valido      | Ninguna propuesta llega a encajar del todo con el gold.                                                                                                                                                                                                                                                                                                                                                        | alta      |
| 28706431   | 0                    | correcto       | gold_valido      | Ninguna propuesta llega a encajar del todo con el gold.                                                                                                                                                                                                                                                                                                                                                        | alta      |
| 28104685   | 0                    | correcto       | gold_valido      | Ninguna propuesta llega a encajar del todo con el gold.                                                                                                                                                                                                                                                                                                                                                        | alta      |


---



## B — Matches del juez LLM (16)

Si el programa aceptó Pn y tú estás de acuerdo: `correcto`.
Si aceptó Pn y esa propuesta **no** es el gold: `falso_positivo`.


| id         | Posición equivalente | Veredicto juez | Calidad gold | Justificación                                                                                                                                                                                                                                                                                                          | Confianza |
| ---------- | -------------------- | -------------- | ------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------- |
| 27068836   | 0                    | falso_positivo | gold_valido  | El juez aceptó P1 (perforación/fístula por hardware). No es destrucción de espesor completo. (ronda 1; confirma)                                                                                                                                                                                                       | baja      |
| 21424749   | 1                    | correcto       | gold_valido  | P1 es enfermedad mitocondrial, forma específica del gold. (ronda 1; confirma)                                                                                                                                                                                                                                          | alta      |
| 23281978   | 1                    | correcto       | gold_valido  | STEMI anterior por LAD es una forma más específica del gold. (ronda 1; confirma)                                                                                                                                                                                                                                       | alta      |
| 27709474   | 1                    | correcto       | gold_valido  | Es el mismo diagnóstico madre. “TIO por PMT” = PMT. Solo cambia la forma de nombrarlo (fenotipo vs etiología), pero es la misma enfermedad.                                                                                                                                                                            | alta      |
| 27514369   | 1                    | correcto       | gold_valido  | Misma enfermedad madre (IE en válvula nativa).                                                                                                                                                                                                                                                                         | alta      |
| 30766756   | 1                    | correcto       | gold_valido  | Misma enfermedad madre (yolk sac tumor primario intestinal)                                                                                                                                                                                                                                                            | alta      |
| 32046748   | 1                    | correcto       | gold_valido  | Es exactamente la misma enfermedad madre. PML siempre es por JC virus; solo cambia la forma de nombrarlo                                                                                                                                                                                                               | alta      |
| 23482507   | 1                    | correcto       | gold_valido  | Misma enfermedad madre (hemangioma cavernoso óseo)                                                                                                                                                                                                                                                                     | alta      |
| N-10000086 | 2                    | correcto       | gold_valido  | Misma toxicidad farmacológica (BRAF inhibitor toxicity)                                                                                                                                                                                                                                                                | alta      |
| 23800107   | 1                    | correcto       | gold_valido  | Es exactamente la misma enfermedad madre. Triple A = Allgrove = AAAS mutation. Solo cambia la forma de nombrarlo.                                                                                                                                                                                                      | alta      |
| 28302624   | 1                    | correcto       | gold_valido  | Misma enfermedad madre (disc prolapse)                                                                                                                                                                                                                                                                                 | alta      |
| 27797319   | 1                    | correcto       | gold_valido  | Misma enfermedad madre (germinoma)                                                                                                                                                                                                                                                                                     | alta      |
| 22563559   | 1                    | falso_positivo | gold_valido  | Los linfocitos T verdaderos no expresan TCR de superficie. Si un tumor expresa TCR de superficie, ya no es linfoblástico, sino una neoplasia T madura. Por ello aunque el nombre empieza con "T_lymphhoblastic leukemia/lymphoma", la descripción lo convierte en potra enfermedad (una neoplasia T madura con TCRAD). | media     |
| 25336332   | 1                    | correcto       | gold_valido  | Misma enfermedad madre (SCC de amígdala)                                                                                                                                                                                                                                                                               | alta      |
| 25282086   | 1                    | correcto       | gold_valido  | Misma enfermedad madre (secundaria)                                                                                                                                                                                                                                                                                    | alta      |
| 28472977   | 1                    | correcto       | gold_valido  | Misma enfermedad madre                                                                                                                                                                                                                                                                                                 | alta      |


---



## Recuento (36 casos de esta corrida)

- Falsos positivos:
- 27068836 y 22563559
- Falsos negativos:
- 27656661, 26819809 y 19721837
- Golds que no sirven (`demasiado_amplio` / `demasiado_especifico` / `no_es_entidad_diagnostica` / `rol_incorrecto`):
- 24054536 y 24910386
- Casos `segunda_opinion`:
- 

Sinónimos o diagnósticos secundarios que también deberían aceptarse:

- **Acute hypereosinophilic syndrome es el gold y la propuesta 1 de ese caso debería estar aceptada siendo esta** Idiopathic hypereosinophilic syndrome (HES) with central nervous system involvement (**19721837).**

La opción 1 (Critical proximal common carotid artery stenosis/occlusion with scalp ischemia) es exactamente la misma enfermedad madre (**Ischaemic scalp lesions)**. Siendo el gold la forma aguda y la propuesta la forma idiopática crónica pero ambas son Idiopathic hypereosinophilic syndrome (HES) (**24910386)**.

## Cierre

- Tras esta tira, ¿el 80/100 se puede publicar? `si` / `no` / `condicionado`
- Si
- Condiciones:
- 
