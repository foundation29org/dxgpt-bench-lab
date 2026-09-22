# Benchmark de jueces — Terra all_256_clean

Estado: **completado, incluida la revisión clínica ciega Pro vs Flash;
DeepSeek no ejecutado**.

## Qué mide

Se reutilizó la lista diagnóstica congelada de Terra low
(`20260710140614`) en los 256 casos de `all_256_clean`. Los 133 prompts que
llegaron al juez fueron idénticos para todas las configuraciones. Se registraron
tokens y latencia de cada llamada.

Este ensayo mide coste, velocidad y estabilidad del resultado frente al juez
de referencia. **No mide precisión clínica del juez**, porque las 256
decisiones no tienen adjudicación humana. La ablación anterior sí usó los 100
casos multimodales T+I, pero solo 35 decisiones tenían una etiqueta humana
utilizable de David.

La repetición de Pro produjo 214 matches frente a los 213 del re-score
anterior. El prompt y las listas son los mismos; la diferencia de un caso
confirma que el juez con temperatura 0,1 y thinking dinámico no es totalmente
determinista.

## Resultado sobre 256 casos

### Gemini 2.5 Pro

- R@1 62,9%; R@3 80,1%; R@5 y cobertura 83,6%.
- Posición media 1,416; MRR 0,713.
- 133 llamadas; latencia mediana 9,60 s y p95 17,05 s.
- 27.730 tokens de entrada y 176.529 de salida facturable, incluidos
  176.397 tokens de razonamiento.
- Coste estimado: **$1,800**.

### Gemini 2.5 Flash

- R@1 66,4%; R@3 84,4%; R@5 y cobertura 87,9%.
- Posición media 1,404; MRR 0,752.
- Acuerdo binario con Pro 94,9%; acuerdo exacto match+posición 93,8%.
- 133 llamadas; latencia mediana 4,08 s y p95 18,18 s.
- 27.730 tokens de entrada y 151.463 de salida facturable, incluidos
  151.330 tokens de razonamiento.
- Coste estimado: **$0,387**: 78,5% menos que Pro.

Flash produce 11 matches más que Pro. Eso no demuestra que sea mejor: en este
test equivale a ser más permisivo. En las etiquetas humanas iniciales de
MedReaMM obtuvo 31/35 de acuerdo frente a 30/35 de Pro, pero esa referencia
contiene casos ambiguos o mal etiquetados y sigue pendiente de readjudicación.

### Gemini 2.5 Flash sin thinking

- R@1 65,2%; R@3 82,4%; R@5 y cobertura 85,5%.
- Posición media 1,393; MRR 0,736.
- Acuerdo binario con Pro 95,7%; acuerdo exacto match+posición 94,9%.
- 133 llamadas; latencia mediana 0,57 s y p95 0,77 s.
- 27.730 tokens de entrada, 133 de salida y **0 de razonamiento**.
- Coste estimado: **$0,0087**: unas 208 veces menos que Pro.
- En las etiquetas humanas iniciales: 30/35, igual que Pro; cobertura 84/100.

Fue el candidato operativo a revisión. La adjudicación clínica posterior de
las 13 discrepancias rechazó su promoción y mantiene Pro como juez.

## Adjudicación clínica ciega · 22 de septiembre de 2026

David revisó los 13 casos sin conocer qué respuesta pertenecía a Pro o Flash.
Consideró válidos los 13 diagnósticos de referencia y estableció 6 matches y
7 no-matches.

- Pro: 3 TP, 5 TN, 2 FP y 3 FN; 8/13 decisiones binarias correctas,
  precisión 60% y recall 50%.
- Flash sin thinking: 3 TP, 0 TN, 7 FP y 3 FN; 3/13 correctas,
  precisión 30% y recall 50%.
- En las 11 discrepancias binarias, Pro gana 8–3.
- En las dos discrepancias que eran solo de posición (`T208` y `T795`),
  ambos jueces produjeron falsos positivos.

El formulario exigía una sola posición, pero en cinco justificaciones se
declaran varias opciones clínicamente aceptables. Por ello la posición exacta
no se usa para decidir la promoción: leída literalmente sería 6/13 para Pro y
2/13 para Flash; aceptando todas las posiciones mencionadas en la prosa sería
8/13 frente a 3/13. La conclusión binaria no cambia.

Flash incumple el criterio fijado antes de abrir la clave —como máximo un
error adicional y ningún falso positivo clínicamente relevante—: comete cinco
errores y cinco falsos positivos más que Pro. El ahorro de coste y latencia no
compensa este deterioro.

### Grok 4.6 low

- R@1 59,0%; R@3 75,0%; R@5 y cobertura 78,1%.
- Posición media 1,415; MRR 0,667.
- Acuerdo binario con Pro 94,5%; acuerdo exacto match+posición 93,8%.
- 133 llamadas; latencia mediana 4,90 s y p95 11,67 s.
- 110.685 tokens de entrada, 67.328 de ellos cacheados, y 41.587 de salida
  facturable, incluidos 41.454 tokens de razonamiento.
- Coste estimado: **$0,370**.
- En la cohorte multimodal revisada: **27/35** de acuerdo inicial con David y
  cobertura 74/100, por debajo de Pro y Flash.

Grok es barato y tiene mejor cola p95, pero con la evidencia humana disponible
es el peor de los modelos probados. No sustituir el juez actual.

### Kimi K2.6

- Deployment `Kimi-K2.6` de Azure Foundry en `dxgptbot`; funcionó con el
  wrapper Azure existente.
- R@1 61,3%; R@3 77,7%; R@5 y cobertura 80,5%.
- Posición media 1,398; MRR 0,691.
- Acuerdo binario y exacto con Pro 95,3%.
- 133 llamadas; latencia mediana 6,09 s y p95 39,62 s.
- 28.882 tokens de entrada y 274.504 tokens de salida facturable.
- Coste estimado: **$1,125**.
- En las etiquetas humanas iniciales: 28/35; cobertura 73/100.

Kimi es más estricto, lento en la cola y queda por debajo de Pro y ambas
variantes de Flash en el pequeño conjunto humano. No promover como juez.
Azure contabilizó el razonamiento dentro de `completion_tokens` sin separarlo;
por eso se trata toda la salida como facturable.

## Precios usados

Precios por millón de tokens, consultados el 2026-09-16:

- Gemini 2.5 Pro: $1,25 entrada y $10 salida, incluyendo razonamiento, para
  prompts de hasta 200k tokens.
- Gemini 2.5 Flash: $0,30 entrada y $2,50 salida, incluyendo razonamiento.
- Grok 4.6: $2 entrada no cacheada, $0,50 entrada cacheada y $6 salida para
  prompts de menos de 200k tokens.
- Kimi K2.6 Thinking Global en Azure Foundry: $0,95 entrada y $4 salida.

La tarifa oficial vigente de Flash no es $0,60 de salida: Google publica
$2,50 incluyendo thinking. Desactivar thinking puede reducir tokens generados,
pero no cambia esa tarifa unitaria.

Fuentes oficiales:

- https://ai.google.dev/gemini-api/docs/pricing
- https://docs.x.ai/developers/pricing
- https://azure.microsoft.com/pricing/details/ai-foundry-models/kimi/

## Kimi y DeepSeek

- `Kimi-K2.6`: ejecutado correctamente mediante Azure Foundry; no necesitó
  `MOONSHOT_API_KEY` ni un adaptador nuevo.
- `DeepSeek-V4-Flash`: fue retirado; el identificador vigente es
  `deepseek-flash` y sirve DeepSeek V4.1 Flash.
- `DeepSeek-V4-Pro`: desde el 2026-09-14 el endpoint oficial se redirige
  temporalmente a V4.1 Flash. Pro vs Flash ya no sería una comparación de dos
  jueces distintos.
- Este entorno tampoco tiene `DEEPSEEK_API_KEY` ni adaptador DeepSeek. No se
  fabrican resultados a través del fallback Azure, que ya produjo una prueba
  inválida el 2026-09-09.

Fuente oficial DeepSeek:
https://api-docs.deepseek.com/quick_start/pricing

## Decisión

**Mantener Gemini 2.5 Pro como juez strict. No promover Flash sin thinking.**
Flash reduce el coste unas 208 veces y la mediana unas 16,9 veces, pero la
revisión ciega demuestra que su cobertura adicional procede principalmente de
falsos positivos. Puede conservarse como opción experimental para nuevas
ablaciones, no como árbitro canónico.

La
[tarea ciega completada](../reviews/david_review_all256_pro_vs_flash_blind.md)
contiene las 13 adjudicaciones. La
[clave interna](../reviews/david_deliverable_all256_judge_discrepancies.md)
conserva las decisiones automáticas que se abrieron después de la entrega.

## Trazabilidad

- `outputs/judge_benchmark/all256_terra_gemini25pro/`
- `outputs/judge_benchmark/all256_terra_gemini25flash/`
- `outputs/judge_benchmark/all256_terra_gemini25flash_nothinking/`
- `outputs/judge_benchmark/all256_terra_grok46/`
- `outputs/judge_benchmark/all256_terra_kimik26/`
- `outputs/judge_benchmark/pilot100_product_grok46/`
- `outputs/judge_benchmark/pilot100_product_gemini25flash_nothinking/`
- `outputs/judge_benchmark/pilot100_product_kimik26/`

