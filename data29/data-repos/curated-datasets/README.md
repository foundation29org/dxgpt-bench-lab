# Nivel 3 — curated-datasets/

Este directorio contiene los **datasets de evaluación definitivos**, listos para ejecutar en el pipeline. Son el producto final del proceso ETL y sirven como fuente canónica para los experimentos de benchmarking.

## Estructura de cada dataset

```
curated-datasets/
└── <dataset_name>/
    ├── <dataset_name>.json   ← dataset (excluido de git por *.json — gestión separada)
    ├── _metadata.yaml        ← composición, QA gates, historial de runs
    └── _lineage.txt          ← trazabilidad caso a caso (qué fuente, qué transformaciones)
```

## Datasets disponibles

| Dataset | Casos | Estado | Runs documentados | Nota |
|---------|-------|--------|-------------------|------|
| `all_256_clean` | 256 | ✅ Publicable | 2 (gpt-4o, gpt-5-mini) | Primera línea base honesta de DxGPT |

## Criterio de promoción a este nivel

Un dataset puede entrar en `curated-datasets/` solo si cumple:

1. ✅ Pasa QA checker (`bench/validation_checks.py`) con `OVERALL: PASS`
2. ✅ Tiene `_metadata.yaml` completo (composición, fuentes, gates)
3. ✅ Tiene `_lineage.txt` con trazabilidad hasta `raw/`
4. ✅ Al menos un run documentado en `rankingV2.txt`

## Relación con `bench/datasets/`

Los archivos `.json` de este nivel se copian (o referencian) desde `bench/datasets/` para que el
pipeline los pueda consumir via `config.yaml`. Los archivos canónicos **viven aquí**; `bench/datasets/`
es un directorio de trabajo.
