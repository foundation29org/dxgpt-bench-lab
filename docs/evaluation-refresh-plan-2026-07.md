# Plan operativo de evaluación DxGPT — julio de 2026

## Estado de producción

- Modo normal: `gpt-5.4-mini low`
- Modo avanzado: `gemini-3-pro-preview low`
- Juez de benchmark: `gemini-2.5-pro`
- Prompt de producción: `bench/candidate-prompts/juanjo_classic_v2.txt`

No se cambia producción hasta cerrar los runs activos y superar los gates descritos abajo.

## Decisiones cerradas

### Prompt

- Mantener `juanjo_classic_v2.txt` sin cambios.
- Forzar cuatro o cinco diagnósticos, limitar a cuatro, y la variante mínima de contexto degradan `all_256_clean`.
- El mini-set mixto confirma un problema común: los inputs con solo antecedentes generan un diferencial aunque no exista queja activa. Ninguna variante probada mejora el benchmark sin regresión.
- No continuar variantes A/B/C ni pre-normalización salvo que exista una hipótesis nueva que mejore primero el mini-set y después `all_256_clean`.

### Modelos descartados o no prioritarios

- `DeepSeek-V3.2-Speciale`: el run histórico sin schema fue inválido (0/256 DDX parseables: razonamiento libre). La prueba técnica con `OUTPUT_SCHEMA: true` parseó 24/24 casos, pero produjo placeholders y campos como diagnósticos; descartado para el benchmark histórico.
- `DeepSeek-V4-Pro`: cumple el JSON histórico, pero en `all_256_clean` obtiene `avg_pos 1.753`, cobertura `98.1%` (251/256) y R@1 `63.3%`; pierde frente a Mini (`1.526`) y Terra (`1.382`). No extender a HPO.
- `gpt-5.6-luna`: serie `reasoning_effort` cerrada en `all_256_clean`. Mantener `low` (`avg_pos 1.540`, cov `97.7%`); `high`/`medium`/`xhigh` degradan. El colapso de `xhigh` (`89.5%` cov) es mayoritariamente técnico: 22/27 unmatched son respuestas vacías porque el reasoning agota `max_tokens=12000` (`finish_reason=length`). No es rechazo de diagnósticos más específicos. No candidato vs Mini.
- `gpt-5.6-sol`: peor ordenación y mucha más latencia; no continuar.
- `gpt-5.6-terra medium`: peor que `low`; no ejecutar `high`.
- `gemini-3-pro-preview medium`: no aporta mejora; mantener `low`.
- `gemini-3.1-pro-preview`: líder narrativo, pero ligeramente inferior a 3 Pro en el agregado de seis datasets HPO; no reemplaza el modo avanzado.
- `claude-opus-4-8`: recupera cobertura (`99.2%`) frente a Opus 4.7, pero su ordenación (`avg_pos 1.709`) no es competitiva; no ejecutar HPO con el prompt histórico.
- No usar aliases `*-latest`; rompen reproducibilidad.

## Evidencia consolidada

| Área | Resultado | Decisión |
|---|---|---|
| Narrativa (`all_256_clean`) | Gemini 3.1 Pro: `avg_pos 1.267`; Gemini 3.5 Flash: `1.284`; Terra: `1.382`; Mini: `1.526` | Aún no cambia producción |
| Raras HPO (3.017 casos) | Gemini 3 Pro supera ligeramente a Gemini 3.1 Pro: avg_pos `1.459` vs `1.470`, R@3 `~97.8%` vs `97.1%` | Mantener Gemini 3 Pro avanzado |
| Flash 3.5 en DDD | `avg_pos 1.465`, R@1 `66.3%`, R@3 `97.1%`; peor que 3 Pro (`1.394`, `70.3%`, `97.6%`) | No ampliar Flash a otros HPO |
| Terra en DDD | `avg_pos 1.853`, R@1 `56.6%`, R@3 `85.4%`, cov `98.1%`; mejor que Mini (`2.036`, `52.4%`, `79.6%`, `97.6%`) | DDD cerrado a favor de Terra; **faltan 5 HPO** antes de decidir default |
| Terra HPO (3.017 casos) | Pierde RAMEDIS/LIRICAL, pero gana DDD, MME, HMS y MyGene2; agregado ponderado `avg_pos 1.964` vs Mini `2.052`, R@1 `53.3%` vs `~50.5%`, R@3 `82.7%` vs `~79.7%` | Pasa el gate offline para A/B; no cambio global directo |
| Terra vs Mini, caso a caso | Terra mejora `50` casos, Mini `32`, empatan `174`; parte de las diferencias depende de matches de ontología/juez | Justifica A/B, no cambio directo |
| Mini-set mixto | Terra y Mini no tienen ganador claro; ambos fallan los cuatro casos solo de antecedentes | No usarlo para elegir modelo; usarlo como control de producto |

Resultados detallados:

- [Ranking reproducible](../bench/pipelines/pipeline_v4%20-%20fork/main/output/rankingV2.txt)
- [Informe público](benchmark-report.html)
- [Análisis Terra/Luna/Sol y comparación con Mini](analysis/gpt56-luna-terra-sol-case-analysis-2026-07.md)

## Runs activos y cola

### Terra HPO (gate modo normal — obligatorio si candidato a default)

DDD ✅; RAMEDIS ❌ (`avg_pos +0.114`); LIRICAL ❌ (`+0.101`); MME ✅ (`1.921` vs `2.757`); HMS ≈/✅ (`1.908` vs `1.909`, R@1 +4.6 pp); MyGene2 ✅ (`2.125` vs `2.282`). Los seis runs completaron con `summary`/salida final y sin fallos de parseo; los errores 500 del juez fueron transitorios.

Gate: agregado ponderado de los 6 HPO (3.017 casos) frente a Mini. Terra lo supera y pasa a A/B de producto; no exige superar al avanzado.

### DeepSeek

No ejecutar más DeepSeek para el gate de calidad/default: V3.2-Speciale no cumple el contrato de salida y V4-Pro, la variante de mayor capacidad disponible, pierde contra Mini. V4-Flash solo se justificaría por una hipótesis previa y medible de coste/latencia, no como sustituto de Mini.

Todos usan el prompt histórico, parámetros `low` del proveedor y juez `gemini-2.5-pro`.

## Próximas decisiones

### Modo avanzado

Mantener Gemini 3 Pro. Flash 3.5 no alcanza paridad práctica en DDD y no se amplía a otros HPO.

### Modo normal

Terra mejora narrativa y el agregado HPO completo, pero cuesta aproximadamente `$400/mes` a 1.000 consultas/día. Pasa a A/B de producto antes de cualquier cambio global:

- tráfico aleatorio Mini/Terra;
- mismas reglas de escalado al avanzado;
- medir tasa de escalado, latencia, coste, errores de formato, reconsultas y preferencia clínica ciega en una muestra de discordancias;
- adoptar Terra solo si la mejora se mantiene y compensa coste más posible reducción de escalados.

No desplegar Terra de forma global únicamente a partir del benchmark offline.

## Trabajo aplazado

- Comparar jueces LLM solo después de decidir los finalistas; una nueva serie con otro juez no es comparable con el histórico.
- Nuevas estrategias de prompt o pre-normalización solo con una hipótesis medible y sin mezclar el efecto de modelo, prompt y juez.
