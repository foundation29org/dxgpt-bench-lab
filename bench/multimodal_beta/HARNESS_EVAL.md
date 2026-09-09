# Harness del evaluador — guía corta

DxGPT es el alumno. Este documento es del **examen**, no del alumno.
Mismo modelo, distinto examen → distinta nota. Ya lo vimos: el 98%
narrativo era el examen facilón (`legacy_similarity`), no que Gemini
acertara más.

## El examen, en una frase

Un caso es “match” si **alguna capa** dice sí. Las capas van en orden y
la primera que acierta gana. Las de atrás ni se enteran.

```text
1. SNOMED exactamente el mismo código
2. ICD-10 exactamente el mismo código
3. ICD-10 hijo  (el DDX es más específico que el gold)
4. ICD-10 padre (el DDX es más amplio que el gold)     ← aún ON
5. ICD-10 hermano (mismo padre ICD, otra enfermedad)  ← aún ON
6. SapBERT ≥ 0,90 → match automático, sin LLM         ← aún ON
7. SapBERT + LLM juez
```

`strict_equivalence` **solo cambia el paso 7**. Los pasos 1–6 siguen
igual que en el ranking oficial. Por eso un run “strict” de gemini-3.1-pro
sigue teniendo 18 matches por **hermano ICD**. El juez estricto no los
vio: el hermano ganó antes.

## Ejemplo tonto: miositis vs dermatomiositis

Gold: *Inclusion Body Myositis*.
Lista: *Dermatomyositis* en P1.

No son la misma enfermedad. Comparten familia de miopatías inflamatorias,
así que ICD-10 las marca **hermanas**. El flujo actual cuenta match en
P1 y se va. El juez estricto, si llegara, diría 0.

Eso no es “el LLM es permisivo”. Es una regla del harness que el LLM
ni toca. BERT 0,80 es el primo: no es un match automático, pero si BERT
pone un 0,82 en P1 y el LLM elige P3, **gana BERT** (posición mejor y
score ≥ 0,80). El juez estricto opina y el código lo ignora.

BERT ≥ 0,90 ni pregunta: match directo.

## Qué hemos arreglado y qué no

| Cosa | Estado |
|---|---|
| Prompt del juez (“parecido clínico” → “misma entidad”) | Hecho. Cae el 98% al 75–83%. |
| Hermanos / padres ICD | Siguen aceptando relacionados |
| BERT 0,90 automático | Sigue |
| BERT 0,80 puede pisar al juez | Sigue |
| Paquete de 36 casos de David | Entregado; referencia inicial en readjudicación |

El flujo **sí se puede endurecer**. No hace falta un producto nuevo.
Hay palancas ya en el `config.yaml` / `reeval_traditional_strict.py`.

## El loop (fallo → sensor → palanca → re-medir)

No se “mejora el prompt a ojo”. Se identifica **qué capa mintió**, se
mueve **una** palanca, se vuelve a puntuar **las mismas listas DDX**.

1. Un caso sale match y David (o tú) dice: eso no es la misma enfermedad.
2. Abres `evaluation_details.txt` de ese id. Miras `final_resolution.method`.
3. Según el método, una palanca:

| Sensor (`method`) | Palanca | Qué estás diciendo |
|---|---|---|
| `ICD10_SIBLING` | `ENABLE_ICD10_SIBLING_SEARCH: false` | Hermanos ICD no son equivalencia |
| `ICD10_PARENT` | `ENABLE_ICD10_PARENT_SEARCH: false` | “Es un cáncer” no vale por el cáncer concreto |
| `BERT_AUTOCONFIRM` | subir `BERT_AUTOCONFIRM_THRESHOLD` (0,90 → 0,93) o quitarlo | El embedding ya no cierra el caso |
| `BERT_MATCH` | subir `BERT_ACCEPTANCE_THRESHOLD` o no dejar que BERT pise al LLM | El 0,80 deja de vetar al juez |
| `LLM_JUDGMENT` | prompt o modelo del juez | Aquí sí es el árbitro |
| `SNOMED_MATCH` / `ICD10_EXACT` | casi nunca se toca | Misma entidad por código |

4. Re-ejecutas `reeval_traditional_strict.py` sobre el mismo
   `evaluation_details.txt`. Cero inferencia nueva. Cinco minutos.
5. Miras cuántos matches caen y **en qué casos**. Si cae un match que
   David considera correcto, la palanca se ha pasado. Se revierte o se
   afina. No se apilan tres palancas a la vez.

La referencia de este loop debe ser una adjudicación humana estable sobre
los 36 (unmatched + LLM), no el 80/100. La primera tira de David encontró
casos inconsistentes y golds ambiguos; no se trata como gold definitivo
hasta cerrar la rúbrica con Julián y readjudicar esos ids. Subir cobertura
apretando el examen al revés es volver a legacy.

## Ablación pendiente de las capas 4–6

El criterio de producto ya es equivalencia, no parentesco. Las palancas
ICD/BERT no necesitan a David para **medirlas**. Sí para **cerrarlas**.

Experimento barato, una palanca:

- Coger Terra low (o mini) ya etiquetado.
- Apagar solo hermanos ICD.
- Re-scorear.
- Tabla: cobertura / R@1 antes y después, y la lista de casos que
  cambian.

Eso responde: “¿cuánto del 83% strict de Terra es aún parentesco ICD?”
Si el delta es 2 puntos, el harness ya está bastante limpio. Si es 8,
el ranking Gemini-vs-Terra de hoy está inflado igual para todos… o no
igual: un modelo que nombra hermanos ICD se beneficia más de esa regla.

Lo mismo, otro día, con padres ICD. Otro día, BERT autoconfirm. Nunca
los tres el mismo viernes.

## Qué no se hace

- Una regla por caso (“Hodgkin cuenta si dice linfoma”). Eso es el 98%.
- Optimizar el harness para que MedReaMM vuelva a 80/100.
- Tocar `evaluator.py` histórico de pipeline_v4. Las palancas se
  cambian en el config del re-score `multimodal_beta`, igual que el
  prompt strict.
- Mezclar este loop con el producto (resumen, routing, visión). Eso es
  otro harness: el del alumno, no el del examen.

## Relación con la ronda 2 de David

David etiquetó FP/FN del **juez** (paso 7). Eso no calibra hermanos ICD:
esos casos no llegan al juez. Por eso siguen existiendo dos colas:

- **Capas 4–6:** ablación sibling / parent / BERT, una palanca cada vez,
  listas congeladas e informe de delta.
- **Paso 7:** Julián fija la rúbrica; David readjudica la tira corta
  conflictiva; después se comparan Pro, Flash 2.5 y Flash 3.8 por
  precisión, recall, matriz de confusión y concordancia.

Hasta que esa referencia esté cerrada, el paso 7 no tiene un sensor fiable.
Las capas 4–6 sí pueden medirse: el método ya está en cada
`evaluation_details`.
