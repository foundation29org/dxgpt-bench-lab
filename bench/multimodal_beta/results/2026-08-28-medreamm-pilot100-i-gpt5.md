# MedReaMM pilot100 — I con gpt5

Estado: **en cola tras T+shuffled-I**.

## Condiciones

- Fecha: 2026-08-28.
- Casos: los mismos 100 de las condiciones anteriores.
- Entrada: únicamente las imágenes correctas.
- Texto y documentos: eliminados.
- Modelo solicitado: `gpt5`.
- Objetivo: medir cuánta señal diagnóstica contienen las imágenes sin historia.

## Interpretación prevista

Este control no representa el uso recomendado del producto. Sirve para separar:

- evidencia disponible directamente en la imagen;
- información aportada exclusivamente por la historia;
- complementariedad entre ambas modalidades.

## Trazabilidad

- Manifest: `datasets/processed/medreamm_pilot100/manifest.yaml`.
- Respuestas previstas: `outputs/pilot100_gpt5_I/responses.jsonl`.
- Evaluación prevista:
  `outputs/pilot100_gpt5_I/evaluation_v4_primary_strict/`.
