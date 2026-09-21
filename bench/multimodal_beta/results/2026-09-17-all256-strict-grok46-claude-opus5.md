# Grok 4.6 y Claude Opus 5 · all_256 strict

Fecha: 2026-09-17  
Estado: completado

## Condiciones

- Dataset: `all_256_clean`, 256 casos narrativos.
- Prompt: `juanjo_classic_v2`.
- Inferencia nueva mediante las API directas de xAI y Anthropic.
- Juez: `gemini-2.5-pro`, `strict_equivalence`.
- Grok 4.6 `low`. Claude Opus 5 `low` (reejecución válida tras arreglar
  el parseo de bloques `thinking`).

## Resultados strict

| Modelo | R@1 | R@3 | R@5 | Cobertura | Posición media | Latencia media |
|---|---:|---:|---:|---:|---:|---:|
| grok-4.6 low | 62,9% | 78,1% | 81,6% | 81,6% | 1,373 | 17,0 s/caso |
| claude-opus-5 low | 59,4% | 76,2% | 82,8% | 87,1% | 1,803 | 22,7 s/caso |

La fila Claude de 35,2% R@1 / 52,3% cobertura era inválida: 108/256 listas
vacías por leer `content[0].text` cuando Opus 5 empieza por un bloque
`thinking`. Esta tabla sustituye esa cifra.

## Lectura

- Grok 4.6 empata con GPT-5.4 full en R@1 y queda por detrás al desempatar
  por cobertura. Es el tercer resultado global y la mejor alternativa fuera
  de OpenAI y Google en esta comparación.
- Claude Opus 5 low ya es comparable: 256/256 listas parseadas, 0 vacías.
  El R@1 (59,4%) queda por debajo de Grok y Terra. La cobertura (87,1%)
  es la más alta de la tabla narrativa: encuentra el diagnóstico más a
  menudo, pero lo sitúa peor (posición media 1,803 frente a 1,373 de Grok).
  No sustituye a Terra en producto.

## Artefactos

- Grok, inferencia:
  `bench/pipelines/pipeline_v4 - fork/main/output/all_256_clean/juanjo_classic_v2/grok_4_6_low_translated_en/`
- Grok, strict:
  `bench/multimodal_beta/outputs/judge_audit/all256_grok46_low_strict/`
- Claude, inferencia (corrida válida):
  `bench/pipelines/pipeline_v4 - fork/main/output/all_256_clean/juanjo_classic_v2/claude_opus_5_low_translated_en/`
- Claude, strict (corrida válida):
  `bench/multimodal_beta/outputs/judge_audit/all256_claude_opus5_low_strict/`
- Claude, corrida inválida (no usar):
  `.../claude_opus_5_translated_en/` y
  `outputs/judge_audit/all256_claude_opus5_strict/`
