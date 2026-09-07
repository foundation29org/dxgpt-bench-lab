# Documentacion del repo

Mapa corto de donde vive cada tipo de informacion y que documentos son canonicos.

## Canonicos

| Documento | Tipo | Uso |
|---|---|---|
| `README.md` | Entrada general | Punto de partida del repo |
| `bench/pipelines/pipeline_v4 - fork/main/README.md` | Benchmark | Estado actual del benchmark y recomendaciones |
| `bench/pipelines/pipeline_v4 - fork/main/GUIA_EVALUACION.md` | Runbook | Ejecucion, reanudacion y lectura de outputs |
| `docs/ROADMAP.md` | Roadmap | Fases, decisiones y trazabilidad |
| `docs/benchmark-report.html` | Informe ejecutivo | Resumen para stakeholders |
| `bench/pipelines/pipeline_v4 - fork/main/output/rankingV2.txt` | Historial | Ranking completo de runs |

## Soporte y auditoria

| Documento | Uso |
|---|---|
| `docs/pipeline/experiment-log.md` | Bitacora tecnica del pipeline y de los experimentos |
| `docs/pipeline/methodology-notes.md` | Alineacion de metricas publicas y claims historicos |
| `docs/analysis/run-analysis-notes.md` | Analisis cualitativo de runs |
| `bench/datasets/README.md` | Estado y uso de datasets de trabajo |
| `.squad/decisions.md` | Decisiones multidisciplinares y auditoria interna |

## Historico archivado

La documentacion historica o claramente desalineada con `pipeline_v4 - fork/main` se mueve a `docs/archive/`.

Ejemplos:

- README antiguos o demasiado genericos
- especificaciones de MVP o versiones previas
- notas conceptuales o informes historicos que ya no deben guiar trabajo actual

Antes de borrar un Markdown, la regla del repo es:

1. Si sigue aportando contexto unico, se conserva.
2. Si duplica informacion viva, se recorta o se fusiona.
3. Si solo vale como referencia historica, se archiva.
