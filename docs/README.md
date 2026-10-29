# Documentacion del repo

Mapa corto de donde vive cada tipo de informacion y que documentos son canonicos.

## Canonicos

| Documento | Tipo | Uso |
|---|---|---|
| `README.md` | Entrada general | Punto de partida del repo |
| `docs/pipeline/pipeline-v5.md` | Pipeline | Como funciona el evaluador vigente (Pipeline V5): etapas, rubrica del juez, gold, ejecucion y salidas |
| `bench/pipelines/pipeline_v5/main/README.md` | Benchmark | Resultados de V5 (`narrative_v2`, raras HPO v2) y cambios respecto a V4 |
| `docs/benchmark-report-v5.html` | Informe | Informe con graficas de V5; se regenera con `bench/pipelines/pipeline_v5/main/build_report.py` |
| `docs/ROADMAP.md` | Roadmap | Fases, decisiones y trazabilidad |
| `docs/tareas-david/` | Revision clinica | Una ficha por encargo a David: para que sirve, que hacer, material, como se devuelve |
| `bench/pipelines/pipeline_v4 - fork/main/README.md` | Benchmark historico | Serie historica con Pipeline V4 (`all_256_clean`) |
| `bench/pipelines/pipeline_v4 - fork/main/GUIA_EVALUACION.md` | Runbook V4 | Ejecucion, reanudacion y lectura de outputs de V4 |
| `docs/benchmark-report-strict-texto.html` | Informe historico | V4 strict sobre `all_256_clean` y HPO |
| `docs/benchmark-report.html` | Informe ejecutivo | Resumen para stakeholders (juez legacy) |
| `bench/pipelines/pipeline_v4 - fork/main/output/rankingV2.txt` | Historial | Ranking completo de runs V4 |

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
