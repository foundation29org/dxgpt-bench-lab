# Nivel 2 — normalized-by-source/

Este directorio contiene datasets externos (fuentes públicas o papers de investigación) convertidos al schema DxGPT estándar, antes de ser combinados en datasets de evaluación curados.

## Schema estándar (DxGPT v1)

```json
{
  "id": "source_001",
  "case": "texto original en el idioma fuente",
  "case_en": "texto pre-traducido al inglés (igual que case si ya era inglés)",
  "complexity": "C3",
  "diagnoses": ["diagnosis_name"],
  "source": "source_name",
  "lang": "en"
}
```

## Reglas de este nivel

- Los archivos son **inmutables** una vez creados. Si hay cambios, crear nueva versión (`v1 → v2`).
- Cada fuente tiene su propia subcarpeta con `qa_report_*.txt` y `provenance.yaml`.
- El campo `case_en` **debe estar pre-poblado** (pre-traducción al inglés antes de guardar aquí).
- Los datasets deben pasar **todos los gates** de `bench/validation_checks.py` antes de
  promocionarse a Nivel 3 (`curated-datasets/`).

## Diferencia respecto a `raw/`

| `raw/` (Nivel 1) | `normalized-by-source/` (Nivel 2) |
|-----------------|-----------------------------------|
| Archivos originales sin modificar | Convertidos al schema DxGPT |
| Idioma original | `case_en` pre-traducido |
| Formatos heterogéneos | Schema JSON unificado |
| Nunca se modifican | Versionados (v1, v2...) |

## Fuentes pendientes de normalización (Fase 2)

| Fuente | Carpeta | Estado | Casos | Origen real |
|--------|---------|--------|-------|-------------|
| RAMEDIS HPO | `ramedis_hpo/` | ✅ Completado | 624 | `chenxz/RareBench` en Hugging Face |
| MyGene2 | `mygene2_hpo/` | ✅ Completado | 146 | Harvard Dataverse `doi:10.7910/DVN/TZTPFL` (file ID 6689035) |
| MME | `mme_hpo/` | ✅ Completado | 40 | `chenxz/RareBench` en Hugging Face |
| HMS | `hms_hpo/` | ✅ Completado | 88 | `chenxz/RareBench` en Hugging Face |
| LIRICAL | `lirical_hpo/` | ✅ Completado | 370 | `chenxz/RareBench` en Hugging Face |

> ⚠️ **RareCrowds (Foundation29) NO usar**: desactualizado (2022), no contiene los datasets del paper DeepRare.
> ⚠️ `ramedis_hpo/` es DISTINTO de `data29/data-repos/raw/ramedis.json` — este último tiene boilerplate español artificial añadido durante el ETL interno.
