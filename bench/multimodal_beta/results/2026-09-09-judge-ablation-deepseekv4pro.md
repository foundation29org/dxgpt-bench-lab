# Juez DeepSeek-V4-Pro — inválido

No es un resultado clínico. `get_llm("DeepSeek-V4-Pro")` acabó en Azure
OpenAI y cada llamada LLM devolvió `DeploymentNotFound` (404). Cero
`llm_judgment`. Cobertura 58/100 = solo SNOMED/ICD/BERT autoconfirm.
Acuerdo 18/35 porque todos los casos del juez salieron unmatched.

El run histórico de DeepSeek como **alumno** usa el endpoint de Hugging
Face, no este camino. Hasta no enrutar el juez a ese endpoint, DeepSeek
no está medido como árbitro.
