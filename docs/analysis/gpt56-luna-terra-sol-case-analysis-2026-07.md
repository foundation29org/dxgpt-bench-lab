# Analisis caso a caso GPT-5.6: Luna, Terra y Sol

## Alcance

Comparacion de `gpt-5.6-luna`, `gpt-5.6-terra` y `gpt-5.6-sol` en `all_256_clean` (`n=256`), incluyendo la ablacion completa de `reasoning_effort` y las variantes de prompt rank-first. Todos los runs mantienen juez `gemini-2.5-pro` y los mismos umbrales del evaluador.

| Modelo | Match | R@1 | R@3 | R@5 | Avg pos |
|---|---:|---:|---:|---:|---:|
| Terra low | 251/256 | 74.6% | 94.9% | 98.1% | **1.382** |
| Terra high | 249/256 | 71.9% | 93.0% | 97.3% | 1.426 |
| Terra xhigh (20k corregido) | 248/256 | **76.2%** | 91.0% | 96.1% | 1.427 |
| Terra medium | 250/256 | 71.1% | 91.0% | 97.7% | 1.516 |
| Luna low | 250/256 | 69.1% | 90.2% | 97.7% | **1.540** |
| Luna high | 250/256 | 68.8% | 90.6% | 97.3% | 1.564 |
| Luna medium | 250/256 | 66.0% | 91.4% | 97.3% | 1.584 |
| Sol medium | 250/256 | 69.9% | 89.5% | 96.9% | 1.584 |
| Luna xhigh | 229/256 | 62.9% | 82.0% | 89.1% | 1.594 |
| Sol low | 252/256 | 68.4% | 88.7% | 98.4% | 1.619 |

Terra effort (serie cerrada): por avg_pos `low` > `high` > `xhigh` > `medium`. El run xhigh original tuvo 4 `EMPTY_RESPONSE` a 12k; se reejecutaron solo esos casos con 20k y se recuperaron todos (`R176` P2, `R193` P4, `R254` P1, `R549` P1). El agregado corregido queda en avg_pos `1.427`, coverage `96.9%`, R@1 `76.2%`, R@3 `91.0%` y R@5 `96.1%`. Xhigh confirma una mayor concentracion en P1 (+1.6 pp vs low), pero pierde en avg_pos, cobertura y recall acumulado; no reemplaza a `low`.

Sol: al contrario que Luna, `medium` mejora a `low` (`1.584` vs `1.619`, R@1 +1.5 pp). 0 truncaciones. Aun asi queda lejos de Mini (`1.526`) y Terra (`1.382`); no candidato.

En Luna, mas `reasoning_effort` no mejora el benchmark: `low` gana en avg_pos y R@1 frente a `high` y `medium`. En `xhigh` ademas colapsa la cobertura (`89.5%`, 27 unmatched frente a 6 en el resto).

**Causa del colapso xhigh (no es especificidad):** de los 27 unmatched, **22 son `EMPTY_RESPONSE`**: el modelo gasta los 12.000 `max_tokens` enteros en reasoning (`finish_reason=length`, `response=0`) y no emite JSON. No hay DDX que el juez pueda recuperar. Excluyendo esos 22, xhigh queda en cobertura `97.9%` y R@1 `68.8%` — casi como low en el mismo subconjunto. Los 2 unmatched con DDX donde low si matcheo (`B118`, `Q4774`) son falsos positivos del juez en low (p. ej. adenoma hepatico roto ↔ ectasia vascular; trisomia 18 ↔ valvula uretral posterior), no diagnosticos mas especificos rechazados.

## Ablacion de prompt rank-first

La hipotesis especifica para Sol fue atacar su relleno sistematico y su mala priorizacion sin fijar un numero exacto de diagnosticos. La variante `juanjo_classic_v2_rank_first` obliga a comparar y reordenar candidatos, priorizar la respuesta directa y omitir variantes solapadas o relleno poco probable.

| Modelo / prompt | Match | R@1 | R@3 | Avg pos | DDX/caso |
|---|---:|---:|---:|---:|---:|
| Sol medium historico | 250/256 | 69.9% | 89.5% | 1.584 | 4.69 |
| **Sol medium rank-first v1** | 250/256 | **71.9%** | **92.2%** | **1.476** | **3.89** |
| Sol medium rank-first canonical v2 | 248/256 | 65.2% | 89.5% | 1.593 | — |
| Terra low historico | 251/256 | **74.6%** | **94.9%** | **1.382** | 3.60 |
| Terra low rank-first v1 | 251/256 | 73.8% | 93.4% | 1.414 | — |

### Conclusiones de la ablacion

- **Rank-first v1 mejora Sol de forma material:** avg_pos `-0.108`, R@1 `+2.0 pp`, misma cobertura y 0 truncaciones. Reduce la lista media de `4.69` a `3.89`, confirmando que el principal problema de Sol era relleno y ordenacion.
- La mejora es **especifica del comportamiento de Sol**, no una mejora general del prompt. En Terra low, que ya genera listas cortas y bien priorizadas, rank-first empeora avg_pos `+0.032` y R@1 `-0.8 pp`.
- La variante canonical v2 no recupera matches automaticos: SNOMED baja de `105` a `96`, R@1 cae a `65.2%` y avg_pos vuelve a `1.593`. Exigir nombres canonicos y adaptar el nivel de respuesta introduce demasiadas decisiones adicionales y perturba el ranking.
- En comparacion pareada, rank-first v1 mejora `42` casos de Sol, empeora `33` y empata `181`. Frente a Terra low, Terra sigue mejor en `43` casos, Sol rank-first en `37` y empatan `176`.
- Sol rank-first v1 supera a `gpt-5.4-mini` por avg_pos (`1.476` vs `1.526`), pero sigue por detras de Terra low (`1.382`) y no tiene validacion HPO independiente.
- No continuar iterando prompts sobre `all_256_clean`: despues de usar el mismo dataset para diagnosticar y ajustar el comportamiento, una v3 aumentaria el riesgo de sobreajuste. La siguiente prueba valida debe ser rank-first v1 en un dataset independiente.

## Hallazgo principal

La diferencia procede principalmente de la forma y la ordenacion de las listas de diagnosticos, no de un cambio de juez:

- Terra produce una media de `3.6` candidatos y suele priorizar etiquetas mecanisticas y especificas.
- Luna produce `4.55` candidatos de media y tiende a listas amplias de sindromes cercanos.
- Sol produce `4.65` candidatos; en `170/256` casos devuelve cinco, lo que desplaza el diagnostico correcto hacia posiciones tardias.

Terra logra `191` aciertos en primera posicion, frente a `177` de Luna y `175` de Sol. En los casos resueltos por juez LLM, las posiciones medias son `1.47`, `1.63` y `2.04`, respectivamente: el juez es constante; cambia la calidad y el orden de las candidaturas.

## Comparacion pareada: Terra vs `gpt-5.4-mini`

En `all_256_clean`, con el mismo prompt y juez, Terra mejora la posicion en `50/256` casos, Mini mejora `32/256` y empatan `174/256`. La señal favorece a Terra, pero no basta por si sola para demostrar superioridad clinica:

- Terra devuelve `3.60` diagnosticos por caso frente a `4.09` de Mini.
- Las rutas automaticas son casi identicas: `181` matches para Terra y `180` para Mini.
- El juez LLM interviene casi igual: `70` casos Terra y `71` Mini. Cuando interviene, Terra tiene `48` P1 con avg_pos `1.471`; Mini, `40` P1 con avg_pos `1.845`.
- Ejemplos de mejora literal o clinicamente coherente de Terra: `B13` (hemolisis TMP-SMX/G6PD, P4→P1), `Q280` (antrax inhalatorio), `R804` (ATR-X), `R108` (deficiencia de holocarboxilasa sintetasa) y `R132` (Pearson).
- Mini prioriza mejor algunos diagnosticos literales en casos conocidos: `B122` (Waldenstrom), `Q3964` (neuroblastoma), `Q5239` (meningococemia), `Q6130` (HFrEF) y `R398` (citrulinemia I).

La metrica contiene una limitacion relevante: una gran parte de los casos discordantes se resuelve por SNOMED, relaciones ICD o juez LLM. Hay matches sensibles a taxonomia, por ejemplo `R664`, donde Terra obtiene P1 con Omenn frente al gold trichohepatoenteric y Mini contiene el diagnostico literal en P5. Por tanto, la ventaja `50` frente a `32` es una hipotesis fuerte para un A/B de producto, no evidencia suficiente para cambiar el default sin revision humana y datos de uso real.

## Control cualitativo: `product_mixed_24`

Con el prompt historico, ambos modelos coinciden en `17/20` diagnósticos activos esperados en primera posicion o equivalente. No hay una superioridad general de Terra en inputs mixtos:

- Mini: `16/20` casos activos con el diagnostico esperado primero; `4.17` diagnósticos por caso.
- Terra: `15/20`; `4.00` diagnósticos por caso.
- Terra formula con más claridad la causalidad farmacológica en estatinas, IECA, furosemida e ibuprofeno, y mejora hiper­viscosidad de P4 a P2; Mini es ligeramente más exhaustivo.
- Ambos fallan los cuatro casos solo de antecedentes (`P013`–`P016`): generan diferenciales basados en enfermedades conocidas sin un hallazgo activo. Este fallo pertenece al prompt histórico, no permite diferenciar los modelos.
- Ambos manejan correctamente hipotiroidismo, lesión renal aguda por AINE e hiponatremia grave; en `P017` ninguno devuelve primero el gold amplio de trastorno del metabolismo del hierro.

Conclusión: el mini-set no confirma una ventaja de producto de Terra suficiente para el cambio. Sirve para conservar como requisito de un futuro prompt o capa de entrada que los antecedentes sin una queja activa no generen un diferencial.

## Ejemplos representativos

| Caso | Terra | Luna / Sol | Lectura |
|---|---|---|---|
| `B7` — infarto mesencefalico | Etiqueta anatomica especifica en P1 | Variantes de sindrome en P4 | La especificidad y la priorizacion ayudan |
| `B13` — hemolisis por G6PD | Relacion TMP-SMX/G6PD en P1 | Diferenciales genericos de hemolisis en P4 | Terra incorpora mejor la causa |
| `B82` — rasgo falciforme con hematuria | Un unico candidato, P1 | Luna P5; Sol P2 | Las listas largas diluyen el diagnostico |
| `B100` — rotura de triceps | P2 | Sol: unica respuesta distinta aceptada por juez | Recordatorio de revisar matches LLM aislados |

La mayor cobertura de Sol incluye matches discutibles por taxonomia o juez; no debe interpretarse como superioridad clinica sin revision manual.

## Decisiones

1. Terra low es el mejor GPT-5.6 para este benchmark (mejor avg_pos, coverage y R@3/R@5).
2. Luna: serie effort cerrada. Mantener `low`. El colapso de `xhigh` es tecnico (22 respuestas vacias por `max_tokens` agotados en reasoning), no especificidad ni juez. Aun sin esos vacios, no mejora a low.
3. Terra effort cerrado tras reparar las 4 truncaciones de xhigh con 20k: `low` > `high` > `xhigh` > `medium` por avg_pos. Xhigh logra el mejor R@1 (`76.2%`), pero pierde coverage, R@3/R@5 y avg_pos; no adoptar.
4. Sol: conservar `medium + rank-first v1` como mejor configuracion experimental (`1.476`); descartar canonical v2. No ejecutar `high` ni crear una v3 sobre el mismo dataset.
5. Terra: mantener prompt historico + `low`; rank-first no generaliza y empeora su resultado.
6. Cualquier validacion adicional de Sol rank-first debe hacerse en un dataset independiente antes de considerarlo para producto.

## Implicaciones para el prompt

Las ablaciones de cantidad fija (`exactly 4`, `exactly 5`, `up to 4`) y de contexto ya se probaron y degradaron o forzaron diagnosticos en entradas sin queja activa. No deben repetirse.

Rank-first v1 confirma una conclusion mas precisa: **el prompt debe corregir el comportamiento concreto del modelo, no imponer una politica global**. Sol necesita una instruccion anti-relleno y de priorizacion; Terra ya exhibe ese comportamiento con el prompt historico y empeora al reforzarlo.

Por tanto:

- produccion y Terra conservan `juanjo_classic_v2`;
- `juanjo_classic_v2_rank_first` queda como variante experimental exclusiva de Sol;
- no adoptar canonical v2;
- no seguir optimizando contra `all_256_clean`; validar generalizacion en HPO u otro conjunto no utilizado para ajustar el prompt.

## Limitaciones

- Se analizan artefactos post-labeling; no es una revision clinica independiente.
- Los matches por `LLM_JUDGMENT` o `ICD10_PARENT` pueden sobreestimar cobertura.
- El resultado aplica a estos prompts, efforts y dataset; no es un ranking general de capacidad medica.
- Las variantes rank-first se diseñaron despues de inspeccionar errores de `all_256_clean`; sus mejoras requieren confirmacion fuera de muestra.
