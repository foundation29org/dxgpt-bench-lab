# MedReaMM pilot100 — T+shuffled-I con gpt5

Estado: **inferencia en curso**.

## Condiciones

- Fecha: 2026-08-28.
- Casos: los mismos 100 de `T` y `T+I`.
- Texto: historia clínica original de cada caso.
- Imágenes: pertenecen al siguiente caso de la cohorte, con rotación circular.
- Modelo solicitado: `gpt5`.
- Objetivo: comprobar si la ganancia depende de la imagen correcta.

Cada respuesta registra `image_source_case_id` para auditar qué imágenes se
utilizaron.

## Hipótesis

Si las imágenes aportan evidencia específica:

- `T+I` debería superar a `T+shuffled-I`;
- `T+shuffled-I` debería aproximarse a `T` o empeorarlo;
- los casos ganados únicamente por `T+I` deberían perder parte de la ventaja.

## Trazabilidad

- Manifest: `datasets/processed/medreamm_pilot100/manifest.yaml`.
- Respuestas previstas:
  `outputs/pilot100_gpt5_T_shuffled_I/responses.jsonl`.
- Evaluación prevista:
  `outputs/pilot100_gpt5_T_shuffled_I/evaluation_v4_primary_strict/`.
