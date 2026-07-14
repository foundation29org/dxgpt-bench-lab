# Analisis caso a caso GPT-5.6: Luna, Terra y Sol

## Alcance

Comparacion de `gpt-5.6-luna`, `gpt-5.6-terra` y `gpt-5.6-sol` con `reasoning_effort: low` en `all_256_clean` (`n=256`), usando el mismo prompt `juanjo_classic_v2`, juez `gemini-2.5-pro` y umbrales del evaluador.

| Modelo | Match | R@1 | R@3 | R@5 | Avg pos |
|---|---:|---:|---:|---:|---:|
| Terra | 251/256 | 74.6% | 94.9% | 98.1% | **1.382** |
| Luna | 250/256 | 69.1% | 90.2% | 97.7% | 1.540 |
| Sol | 252/256 | 68.4% | 88.7% | 98.4% | 1.619 |

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

1. Terra low es el mejor GPT-5.6 para este benchmark.
2. No ejecutar Luna high, Terra high ni Sol medium: los resultados previos no justifican ampliar coste o latencia.
3. Las futuras variantes de prompt deben validar primero con Terra y fijar la cantidad de diagnósticos.

## Implicaciones para el prompt

El prompt actual pide `N` diagnosticos sin fijar `N`. La siguiente variante debe probar:

- exactamente cuatro diagnósticos, ordenados por probabilidad;
- etiquetas especificas y apoyadas por el caso;
- no rellenar la lista con mimicos solapados;
- priorizar una lista corta y precisa frente a un diferencial exhaustivo.

Esta hipotesis se evaluara primero en `product_mixed_24`, junto con las reglas para separar sintomas activos, antecedentes, medicacion y analiticas.

## Limitaciones

- Se analizan artefactos post-labeling; no es una revision clinica independiente.
- Los matches por `LLM_JUDGMENT` o `ICD10_PARENT` pueden sobreestimar cobertura.
- El resultado aplica a este prompt, dataset y `reasoning_effort: low`; no es un ranking general de capacidad medica.
