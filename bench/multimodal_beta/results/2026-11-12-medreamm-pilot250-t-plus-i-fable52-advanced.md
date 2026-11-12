# MedReaMM pilot250 — T+I, análisis en profundidad (Claude Fable 5.2) tras Sol

Estado: **completado**. Referencia anterior:
[2026-11-03-medreamm-pilot250-t-plus-i-sol-vs-terra-n5.md](2026-11-03-medreamm-pilot250-t-plus-i-sol-vs-terra-n5.md).

## Pregunta

En la web, «Análisis en profundidad» pide otra lista a Claude Fable 5.2 cuando la de
Sol no convence. En `narrative_v2` (solo texto) Fable acierta más que Sol. La pregunta
es si mantiene la ventaja con imágenes y por el camino real del Server.

## Condiciones

- **Fecha:** 2026-11-12.
- **Casos:** los mismos 250 de `medreamm_pilot250`, condición `T+I`.
- **Servidor:** Server en local (`NODE_ENV=local`, tenant `dxgpt-local`), con el
  código del análisis en profundidad (`services/advancedDiagnose.js` y
  `services/claudeFoundry.js`).
  - Fable recibe el mismo prompt («5») y las mismas imágenes que Sol, con esfuerzo
    `low` y `max_tokens` 12000.
  - Va por el despliegue `claude-fable-5-2` de Microsoft Foundry.
- **Flujo por caso**, como la web (`run_beta_api.py --advanced`):
  1. `/medical/analyze` con Sol, que sube las imágenes y diagnostica;
  2. `/diagnose` con `advanced`, la misma subida y el texto que manda la web en la
     segunda petición: el anonimizado si Sol encontró datos personales (6 casos), si
     no la descripción del preprocesado.
- **Ejecución:** cuatro procesos en paralelo; 0 errores.
- **Evaluador:** V5 (labeler, SNOMED idéntico y juez Gemini 3.8 Flash con
  `graded_v3`), con el diagnóstico principal como gold. Es el mismo que se aplicó al
  Sol del 3-nov. La conversión la hace
  `bench/pipelines/pipeline_v5/main/medreamm_advanced_to_v5.py`.

## Resultado

| Listas | R@1 | R@3 | R@5 | Pos. media |
|---|---:|---:|---:|---:|
| Claude Fable 5.2, análisis en profundidad | 78,0 % | 86,0 % | 86,4 % | 1,134 |
| gpt-6.1-sol, misma pasada | 71,2 % | 80,4 % | 82,8 % | 1,251 |
| gpt-6.1-sol (3-nov) | 68,4 % | 79,2 % | 82,0 % | 1,298 |
| gpt-5.6-terra (3-nov) | 62,0 % | 72,8 % | 78,0 % | 1,421 |

| Comparación | R@1 gana / pierde | p | R@5 gana / pierde | p |
|---|---:|---:|---:|---:|
| Fable frente a Sol, misma pasada | 30 / 13 | 0,014 | 15 / 6 | 0,078 |
| Fable frente a Sol, 3-nov | 40 / 16 | 0,002 | 20 / 9 | 0,061 |
| Sol de hoy frente a Sol del 3-nov | 14 / 7 | 0,19 | 11 / 9 | 0,82 |

- **Fable acierta más que Sol también con imágenes:** entre 7 y 10 puntos más en
  R@1, como en `narrative_v2`. En R@5 la ventaja es menor y no llega a ser
  significativa.
- **Listas vacías:** 3 casos, los mismos que el 3-nov. Sol no devuelve lista
  porque el filtro previo los toma por pregunta o con datos insuficientes. Como la
  web no ofrece entonces el análisis en profundidad, cuentan como fallo en los dos
  brazos.

## Tiempos y coste

- **Espera del análisis en profundidad:**
  - mediana 20,6 s, p95 24,5 s y máximo 42,1 s;
  - el primer paso (Sol, con la subida) tardó 33,8 s de mediana.
- **Coste real, sumado de los registros de coste del Server local:**
  - Fable: 25,7 $ (10,4 c$ por caso; unos 11k tokens de entrada con imágenes);
  - Sol: 5,1 $ (2,0 c$ por caso);
  - juez: 0,23 $, más el labeler.

## Ficheros

- Respuestas: `outputs/pilot250_fable52_advanced_TI_n5/responses.jsonl` (uno por
  caso, con la respuesta de Sol en `final_response` y la de Fable en
  `advanced.final_response`).
- Evaluación: `bench/pipelines/pipeline_v5/main/output/medreamm_pilot250_ti/juanjo_classic_v2_n5/`
  `claude_fable_5_2_low__server_v0_00200_advanced` y
  `gpt_6_1_sol_low__server_v0_00200_advanced`.
