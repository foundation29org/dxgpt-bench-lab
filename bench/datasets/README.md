# Datasets — Directorio de trabajo del pipeline

Este directorio contiene los datasets médicos usados en los experimentos de evaluación.
Los archivos `.json` están excluidos de git (`.gitignore`) por privacidad de datos.

Los datasets canónicos (con metadata y trazabilidad completa) viven en
`data29/data-repos/curated-datasets/`. Este directorio es una copia de trabajo.

## Datasets de evaluación (benchmarking)

| Dataset | Casos | Estado | Nota |
|---------|-------|--------|------|
| `all_256_clean.json` | 256 | ✅ **Línea base publicable** | Sin leakage, sin boilerplate — usar para nuevos runs |
| `all_275.json` | 275 | ⚠️ Solo referencia histórica | Contiene 19 casos con label leakage |
| `all_256.json` | 256 | ⚠️ Intermedio — no usar | Post-leakage pero pre-boilerplate |
| `all_250.json` | 250 | ⚠️ Histórico | Dataset anterior al módulo de limpieza |
| `all_150.json` | 150 | ⚠️ Histórico | Subset para runs rápidos |
| `all_450.json` | 450 | ⚠️ Sin validar para publicación | Pool sin QA |

### Origen del track narrativo

El pipeline ETL fusionó 9.583 casos procedentes de MedQA/USMLE, MedBullets,
urgencias hospitalarias, Ramebench y ProCheck. Ese corpus se redujo a
`all_997`, un conjunto representativo equilibrado por fuente, capítulo ICD-10,
complejidad y severidad. De él se derivaron conjuntos operativos más pequeños.

`all_256_clean` no representa todo el banco: es la línea base compacta y
reproducible usada para las comparaciones publicables actuales. Parte de
`all_275`; elimina 19 casos con label leakage y limpia el boilerplate de 49
casos. El track HPO de 3.017 casos de enfermedades raras se evalúa por separado.

### Track multimodal

El corpus seleccionado, [MedReaMM](../multimodal_beta/DATASETS.md), contiene
625 casos validados por expertos y 1.746 imágenes. El benchmark emparejado
actual usa una cohorte curada de 100 casos para comparar texto (`T`) con texto
más imágenes (`T+I`) manteniendo el mismo modelo.

También se estudió MultiCaRe (>90.000 narrativas y >130.000 imágenes), pero no
se usa como benchmark de modelos porque no ofrece un diagnóstico canónico
limpio y exige resolver riesgos de fuga y segmentación temporal.

## Datasets de testing

| Dataset | Casos | Uso |
|---------|-------|-----|
| `all_10.json` | 10 | Smoke test ultra-rápido |
| `all_5.json` | 5 | Debug de pipeline |
| `ukranian.json` | 437 | Validación on/off de funcionalidad (idioma ucraniano) |
| `largest_summarized_demo.json` | ~4K líneas | Probar reacción del prompt ante prompts largos |
| `largest_extended.json` | ~4K líneas | Validar función resumidora en producción |
| `product_mixed_24.json` | 24 | Mini-set sintético para evaluar texto mixto: síntomas, antecedentes, medicación y analíticas |

## Dataset recomendado para nuevos runs

```yaml
# config.yaml
DATASET_PATH: bench/datasets/all_256_clean.json
```

`all_256_clean.json` es el dataset de referencia desde Abril 2026:
- Pasa todos los QA gates de `bench/validation_checks.py`
- Sin label leakage (19 casos eliminados respecto a `all_275`)
- Sin boilerplate español (49 casos limpiados a solo lista HPO)
- Metadata completa en `data29/data-repos/curated-datasets/all_256_clean/`
