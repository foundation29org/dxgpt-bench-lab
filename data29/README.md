# Data29 - Procesamiento y Gestión de Datos Médicos 📊

Este módulo es el núcleo de procesamiento de datos del proyecto, donde casos médicos de múltiples fuentes se transforman mediante pipelines ETL en datasets estructurados y validados para evaluación de modelos de IA médica.

## 🎯 Propósito

Gestionar el ciclo completo de datos médicos: desde fuentes heterogéneas hasta datasets normalizados listos para benchmarking, garantizando trazabilidad, calidad y diversidad.

## 🏗️ Arquitectura de datos en tres niveles

```
data29/data-repos/
│
├── raw/                              ← NIVEL 1: fuentes originales (en .gitignore)
│   ├── SOURCE_MANIFEST.yaml          ← documenta cada fuente (origen, licencia, idioma)
│   ├── ramedis.json
│   ├── urgtorre.json
│   └── ...  (7 fuentes en total)
│
├── pre-normalization/                ← ETL pipeline (scripts de transformación)
│   ├── v1-narrow/                   ← RAMEDIS + URGTorre
│   ├── v2-wide/                     ← MedBulltes, MedQA-USMLE
│   └── v3-merge/                    ← Fusión y deduplicación
│
├── post-normalization (server)/      ← Datasets internos normalizados + serve.py
│   └── served/                      ← Subsets generados con criterio de diversidad
│
├── normalized-by-source/             ← NIVEL 2: datasets externos (Nature paper, etc.)
│   └── README.md                    ← schema estándar y reglas de este nivel
│                                    ← (mygene2/, ramedis_hpo/ — pendientes en Fase 2)
│
└── curated-datasets/                 ← NIVEL 3: datasets de evaluación definitivos
    ├── README.md
    └── all_256_clean/               ← primera línea base publicable de DxGPT
        ├── _metadata.yaml           ← composición, QA gates, historial de runs
        └── _lineage.txt             ← trazabilidad caso a caso hasta raw/
```

## 🔄 Flujo de datos

```
raw/ → pre-normalization/ → post-normalization/ → curated-datasets/  ← bench/datasets/
                                                                              ↓
                            normalized-by-source/ ──────────────────→  pipeline eval
```

Los datasets en `curated-datasets/` y `normalized-by-source/` alimentan directamente
los experimentos de benchmarking en `bench/`.

## 📊 Datasets de evaluación disponibles

| Dataset | Casos | Estado | Nivel |
|---------|-------|--------|-------|
| `all_256_clean` | 256 | ✅ Publicable — 2 runs documentados | Nivel 3 |

## 🚀 Servidor de Datasets internos

`post-normalization (server)/serve.py` crea subconjuntos balanceados con:
- Control de tamaño total
- Reglas de muestreo por fuente
- Maximización de diversidad (capítulos ICD-10, complejidad, severidad)

## 📦 Fuentes raw disponibles

7 fuentes normalizadas totalizando ~9.600 casos médicos:
- `ramedis.json` — casos raros anonimizados (español)
- `urgtorre.json` — urgencias hospitalarias (español)
- `medbulltes5op.json` — casos educativos médicos (inglés)
- `medqausmle4op.json` — exámenes USMLE (inglés)
- `new_england_med_journal.json` — NEJM cases (inglés)
- `rare_synthetic.json` — casos sintéticos de enfermedades raras
- `ukranian.json` — casos clínicos ucranianos (testing)