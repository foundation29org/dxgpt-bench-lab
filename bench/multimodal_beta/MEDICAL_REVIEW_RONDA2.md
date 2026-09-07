# Encargo para David — ronda 2 (juez del 80/100)

Esto no es trabajo nuevo de producto. Es auditar al **juez automático**
sobre la corrida T+I de 100 casos (`gpt5`, MedReaMM).

La ronda 1 ya está en
[reviews/david_deliverable.md](reviews/david_deliverable.md).
No la rellenes otra vez.

Cuando termines, devuelves relleno
[reviews/david_deliverable_ronda2.md](reviews/david_deliverable_ronda2.md).
Tiempo estimado: 4–6 horas (29 casos nuevos; 7 ya están copiados).

---

## Para qué sirve esto

El 80/100 **no es tu nota ni la del juez**. Es: en 80 de 100 casos, DxGPT
puso en la lista un diagnóstico que el programa consideró la misma
enfermedad que el gold.

De esos 100:

- 80 casaron por código (SNOMED, ICD-10, BERT alto) o por el LLM.
- **20 no casaron.** Ahí puede haber falsos negativos: el modelo acertó y
  el juez dijo que no.
- **16 casaron solo porque el LLM dijo que sí.** Ahí puede haber falsos
  positivos: el modelo no acertó y el juez coló un “parecido”.

Si recorres esos 36, el 80/100 deja de ser un número ciego. No hace falta
releer los 80 aciertos fáciles (p. ej. un SNOMED exacto).

Criterio: **la misma entidad**, no “se parece”, no “estaría en el
diagnóstico diferencial”. El ejemplo de ronda 1 sigue valiendo: Burkitt no
es Hodgkin; si el juez lo rechazó, acertó.

---

## Qué hacer

1. Abre [reviews/piloto100_juez_unmatched_llm.md](reviews/piloto100_juez_unmatched_llm.md).
2. Para cada id, si hace falta, lee historia e imágenes en
   `datasets/processed/medreamm_pilot100/<id>/`.
3. Escribe una fila en
   [reviews/david_deliverable_ronda2.md](reviews/david_deliverable_ronda2.md).

Por caso:

1. Primera propuesta que sea **la misma enfermedad** que el gold
   (`1`–`5`). Si ninguna lo es, `0`.
2. Compara con lo que hizo el programa:
   - él `0` y tú `0` → `correcto`
   - él aceptó Pn y tú dices que Pn no es el gold → `falso_positivo`
   - él `0` y tú ves el gold en la lista → `falso_negativo`
   - el gold no se puede juzgar → `gold_ambiguo`
3. Calidad del gold: `gold_valido`, `demasiado_amplio`,
   `demasiado_especifico`, `no_es_entidad_diagnostica`, `rol_incorrecto`
   o `segunda_opinion`.
4. Una frase. Confianza `alta` / `media` / `baja`.

Etiquetas: usa las del formulario (`falso_positivo`, no `Incorrecto`).

Cinco ids de ronda 1 están prellenados (`27656661`, `30687305`,
`27068836`, `21424749`, `23281978`): confirma en un vistazo. `24174966` y
`27074070` van vacíos porque la lista de la corrida de 100 no es la del
piloto de 25.

No hay fuga, ni ciego A/B, ni política nueva. Eso ya lo hiciste.

No abras `outputs/` ni ningún `coordinator_key.md`.

---

## Qué no es esta tarea

No estamos midiendo si DxGPT “acierta más”. Estamos midiendo si el
programa que puntúa esas listas se pasa o se queda corto. Con eso
decidimos si el 80/100 se puede citar o hay que recodificar unos casos.
