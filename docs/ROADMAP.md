# DxGPT — roadmap operativo

## Plan del evaluador (pendiente de revisión por Julián)

Términos:

- **Strict**: la cifra oficial, que solo cuenta «la misma enfermedad».
- **Capas**: las comprobaciones por códigos (ICD, SNOMED) y BERT que se
  aplican antes del juez. Si una dice que sí, el juez ni lo ve.
- **Juez**: el LLM que decide los casos que las capas no resuelven.

Regla: un cambio cada vez, sobre las mismas listas ya generadas (sin pedir
diagnósticos de nuevo), y una tabla antes/después en cada paso.

1. **Acordar con Julián**
   - Alcance: solo el juez, o también las capas y las métricas.
   - Qué significa acierto / casi / fallo (borrador en el §9 del brief).
   - Qué hacer con el hijo ICD: acierto directo, o que lo decida el juez.
   - Criterio para aceptar cada cambio: no se pierde ningún acierto que David
     o Julián consideren correcto.

2. **Mirar cuánto pesa cada capa**
   - Ya sale en cada informe («Resolución: SNOMED, ICD exacto, padre,
     hermano, BERT, juez»). No hay que ejecutar nada.
   - Revisarlo en el conjunto de texto `all_256_clean` para decidir por qué
     capa empezar.

3. **Probar los cambios de las capas, uno por uno**
   - Dejar de contar como acierto el hermano ICD → re-puntuar → ver qué
     casos cambian. Después, lo mismo con el padre ICD.
   - Después, dejar de contar BERT ≥ 0,80 por encima del juez, y por último
     el BERT ≥ 0,90 automático.

4. **Revisar con David o Julián los casos que dejan de ser acierto**
   - Si se cae uno que consideran correcto, se revierte ese cambio.
   - Lo que se quite pasa a «casi» (se publica aparte, no cuenta en la nota).

5. **Cambiar el juez a acierto / casi / fallo**
   - Un solo prompt con esa escala (borrador en el §9), y/o probar JEVIA como
     juez o apoyo.
   - Re-puntuar los 133 casos de `all_256_clean` que llegan al juez y
     compararlos con el resultado actual.
   - La nota oficial cuenta solo los aciertos; los «casi» van en una columna
     aparte.

6. **David etiqueta de nuevo con la escala nueva**
   - Los casos dudosos del §6.1 del brief, más una muestra de casos en los
     que los jueces coinciden, para detectar aciertos falsos comunes.
   - Una segunda persona etiqueta una parte, para medir cuánto coinciden dos
     humanos.

7. **Elegir juez**
   - Ejecutar las mismas listas con distintos jueces (Pro, Flash, etc.) y
     comparar cada uno con las etiquetas de David y consigo mismo (3 veces).
   - Repetir con las listas de otros modelos, no solo Terra, para ver si el
     orden entre modelos cambia según el juez.
   - Si el orden no cambia, usar el más barato; si cambia, mantener Pro.

8. **Cerrar y publicar**
   - Etiquetar toda cifra como `strict_equivalence` o `legacy_similarity`.
   - Titular el acierto del primer diagnóstico (R@1) y llamar a la otra cifra
     «acierto en cualquier posición de la lista» (la lista a veces tiene
     menos de 5).
   - Revisar fugas y calidad de los gold, actualizar informes y mantener la
     trazabilidad (manifest, respuestas, configuración y juez).

## Fuentes

- [Brief Julián](../bench/multimodal_beta/JULIAN_HARNESS_REVIEW.md)
- [Guía del harness](../bench/multimodal_beta/HARNESS_EVAL.md)
- [Benchmark de jueces all_256](../bench/multimodal_beta/results/2026-09-16-judge-benchmark-all256-terra.md)
- [Historial](ROADMAP_HISTORY.md)
