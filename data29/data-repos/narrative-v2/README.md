# narrative_v2 — dataset narrativo nuevo

Sustituye a `all_256_clean` como banco narrativo de DxGPT. Los tracks de raras
(HPO, 3.017 casos) y multimodal (MedReaMM) no cambian.

## Por qué

La revisión de octubre de 2026 (`bench/pipelines/pipeline_v5/main/README.md`)
encontró que alrededor de un tercio de `all_256_clean` no mide diagnóstico:

- **63 % son preguntas de examen** (MedQA, MedBullets). Unas 75 no preguntan
  por un diagnóstico, sino por un mecanismo, un fármaco o una estructura
  embrionaria. El gold se reconstruyó a partir de esa respuesta («Decreased
  release of glycine», «pol gene mutation»), y la pregunta final le llega al
  modelo.
- **24 gold no son una enfermedad** («Chest pain», «Tumor stage»). 18 no se
  aciertan nunca.
- **Los 49 casos de RAMEDIS son listas HPO**, no narrativas, y algunos delatan
  el diagnóstico («Decreased methylmalonyl-CoA mutase activity»).
- **El gold normalizado y sus códigos están mal.** `extract_medical_codes`
  (`bench/pipelines/pipeline_v2 - icd10 + bert/run.py`) se queda con la última
  entidad que reconoce Azure y acumula los códigos de todas. En 194 de 355 gold
  el texto normalizado no coincide con el original.
- **Hay riesgo de contaminación.** MedQA y MedBullets son públicos desde hace
  años.
- **Hay poco uso real:** solo un 11 % son casos reales y un 26 % son raras.

## Composición

| Bloque | Fuente | Casos | Para qué |
|---|---|---:|---|
| `live` | Case reports de PubMed Central en acceso abierto que entraron en PubMed **desde el 1-jul-2026** | 150 | Casos reales y diversos que los modelos no han podido ver en entrenamiento. Al menos un tercio de enfermedades raras |
| `urg` | Urgencias Hospital de la Torre (`raw/urgtorre.json`), en español | 60 | Práctica real en el idioma de los usuarios |
| `exam` | MedQA USMLE y MedBullets, **solo** viñetas que preguntan por el diagnóstico, sin la pregunta final | 60 | Control comparable con la literatura y con el histórico. Marcado como contaminado |
| `synth` | Raras sintéticas (`raw/rare_synthetic.json`) | 30 | Raras en narrativa |
| **Total** | | **300** | |

Quedan fuera los casos RAMEDIS en lista HPO, que ya están en el track de raras.

## Criterios de un caso válido

1. **El gold es una enfermedad o un diagnóstico clínico**, no un síntoma, un
   hallazgo, un mecanismo, un gen ni un estadio.
2. **Un diagnóstico principal** al nivel de entidad que se pone en un
   diferencial, más nombres alternativos aceptados. En urgencias, los otros
   diagnósticos de la misma visita también cuentan como acierto (regla C3.2 A
   de la rúbrica). En el resto de bloques, las comorbilidades se guardan sin
   puntuar.
3. **Sin fuga del diagnóstico:** ni el gold ni sus nombres alternativos
   aparecen en el texto, ni pruebas que lo nombren («biopsy confirmed X»).
4. **El texto es una presentación clínica** (historia, exploración, pruebas
   iniciales), sin pregunta de examen, sin opciones y sin la discusión del
   artículo.
5. **Información suficiente** para plantear un diferencial: al menos unos 400
   caracteres de presentación.
6. **Trazabilidad:** fuente, identificador, fecha de publicación y licencia.
   En `live`, solo licencias que permiten extractos (CC sin «ND»).

## Formato

Compatible con Pipeline V4/V5 (`id`, `case`, `diagnoses[].name`). Campos nuevos:

```json
{
  "id": "PMC13712715",
  "case": "A 34-year-old woman presented with ...",
  "complexity": null,
  "diagnoses": [{"name": "Erdheim-Chester disease", "role": "principal",
                 "accepted_names": ["ECD"], "medical_codes": {}}],
  "secondary_diagnoses": [],
  "metadata": {
    "block": "live", "source": "pmc_oa", "language": "en",
    "pmid": "...", "pmcid": "...", "journal": "...", "license": "CC BY 4.0",
    "entrez_date": "2026-07-14", "rare_disease": true, "specialty": "...",
    "contamination_risk": "low"
  }
}
```

**El gold no lleva `normalized_text`.** Los códigos (`medical_codes`) se dejan
vacíos de momento, así que con V5 todos los casos los decide el juez. Si más
adelante se añaden, deben salir solo de la entidad principal.

## Cómo se construye

Scripts en esta carpeta, en este orden. Los datos intermedios van a
`data-repos/raw/pmc_live/` y a `work/`, que no se versionan. El LLM de curación
es Gemini 2.5 Pro.

1. `harvest_pmc.py`: busca case reports en PubMed por fecha de entrada,
   muestrea con un tope de 6 por revista, descarga el texto completo de PMC y
   descarta licencias ND.
2. `extract_live_cases.py`: decide si el caso es elegible (un único paciente
   humano y un diagnóstico establecido que no se conocía al presentarse) y
   extrae el diagnóstico final, los nombres aceptados y la presentación literal
   hasta antes del diagnóstico. Quita además el razonamiento de los autores
   («concerning for…»).
3. `select_internal_cases.py`: criba de `urg`, `exam` y `synth`. El principal
   sale de los gold o del diagnóstico de alta original, y se quitan la
   pregunta de examen y lo que revele el diagnóstico.
4. `audit_leakage.py`: segunda comprobación de fuga con LLM sobre los casos
   con pistas blandas (enzimas, patrones histológicos).
5. `set_entity_level.py`: lleva los gold de `live` al nivel de entidad que se
   escribe en un diferencial («Low-grade mucoepidermoid carcinoma of the
   palatine tonsil» → «Mucoepidermoid carcinoma of the tonsil») y vuelve a
   comprobar la fuga con los nombres nuevos. Después se repite el paso 4 sobre
   los casos renombrados.
6. `build_dataset.py`: aplica estas reglas y monta `narrative_v2.json`,
   `_metadata.yaml`, `_lineage.txt` y la hoja de validación clínica:
   - descarta casos veterinarios y diagnósticos principales inespecíficos
     («viral illness», «… pain»);
   - un caso por diagnóstico y un máximo del 15 % por especialidad;
   - selección estable por caso (hash del identificador), para que excluir
     uno no reordene los demás.

`leakage.py` es el control de fuga compartido. La fuga dura (el nombre, una
abreviatura, un epónimo o una palabra de enfermedad como «-osis» o «-itis»)
descarta el caso. La blanda (un fármaco, una zona anatómica) solo lo marca
para revisión.

## Versión 0.1 (28-oct-2026)

| Paso | `live` | `urg` | `exam` | `synth` |
|---|---:|---:|---:|---:|
| Pool de partida | 15.441 case reports (jul–oct 2026) | 1.398 | 1.216 que preguntan por el diagnóstico | 200 |
| Revisados por el LLM | 319 (de 450 descargados; 131 eran ND) | 200 | 150 | 60 |
| Aceptados tras fugas y auditoría | 194 | 183 | 135 | 54 |
| Tras veterinarios e inespecíficos | 186 | 170 | 135 | 54 |
| **Seleccionados** | **150** | **60** | **60** | **30** |
| De enfermedades raras | 115 | 1 | 21 | 24 |

Total: 300 casos (240 en inglés y 60 en español), 161 de raras y 57
especialidades. QA (`bench/validation_checks.py`): PASS, con 0 de 300 casos con
fuga literal.

Los diagnósticos secundarios solo puntúan en `urg`, donde son diagnósticos
simultáneos de la visita (17 casos). En los demás bloques son comorbilidades
(«Hypertension», «Atrial fibrillation») y se guardan en
`metadata.other_conditions` sin puntuar.

Pendiente antes de publicarlo como línea base: la validación clínica de los
210 casos `live` y `urg` (`curated-datasets/narrative_v2/validacion_clinica.md`).
78 casos `live` tienen pistas blandas que conviene mirar con especial cuidado.

**La hoja de validación no se versiona** (`.gitignore`). Este repositorio es
público y la hoja contiene el texto completo de los casos de urgencias, que son
confidenciales, y extractos de artículos. Se comparte con David por un canal
privado y al repo solo vuelven sus decisiones, sin texto de casos.

## Primera línea base: Terra low (28-oct-2026)

Pipeline V5 (`graded_v2`), juez Gemini 2.5 Pro, run
`bench/pipelines/pipeline_v5/main/output/narrative_v2/…/20261028124715`.
Versión 0.1, todavía sin validación clínica.

| Bloque | Casos | R@1 | R@5 | R@5 laxa |
|---|---:|---:|---:|---:|
| `live` (case reports jul–oct 2026) | 150 | 52,0 % | 71,3 % | 94,0 % |
| `urg` (urgencias, español) | 60 | 51,7 % | 76,7 % | 96,7 % |
| `exam` (MedQA, MedBullets) | 60 | 83,3 % | 88,3 % | 100 % |
| `synth` (raras sintéticas) | 30 | 83,3 % | 96,7 % | 100 % |
| Raras | 161 | 59,6 % | 73,9 % | 94,4 % |
| No raras | 139 | 63,3 % | 83,5 % | 98,6 % |
| **Total** | **300** | **61,3 %** | **78,3 %** | **96,3 %** |

320 llamadas al juez, 0 respuestas inválidas, ≈ 4,1 $.

- **En casos reales, Terra acierta en P1 unos 30 puntos menos** que en
  preguntas de examen o casos sintéticos. Eso explica en buena parte el R@1
  de 63–69 % de `all_256_clean`, que tiene un 63 % de preguntas de examen.
- **Conviene publicar por bloque**, con `live + urg` como cifra principal (uso
  real, sin contaminación). `exam` sirve de control comparable con la
  literatura y `synth` aporta poco: es demasiado fácil.
- **El juez marcó 4 gold como «no es una enfermedad»**: «Blindness», «Type 2
  pneumocyte hyperplasia» y dos «Bronchial hyperreactivity». Se resolverán en
  la validación clínica.

Los cinco modelos de referencia (gpt-6.1-sol, Claude Opus 5, gpt-6.1-terra,
gemini-3.1-pro-preview y gpt-5.4-mini), por bloque, están en el
[README de Pipeline V5](../../../bench/pipelines/pipeline_v5/main/README.md).
En `live`+`urg`, R@1 va de 41,9 % (gpt-5.4-mini) a 58,1 % (gpt-6.1-sol).

## Validación clínica

Antes de publicarse como línea base, David revisa cada caso de `live` y `urg`:
diagnóstico principal, nombres aceptados, fuga y si el caso es diagnosticable.
La hoja la genera `build_dataset.py`.

## Contaminación

Las fechas de corte de los modelos evaluados están en `model_cutoffs.yaml`,
con la fuente de cada una (comprobadas el 28-oct-2026). Las fuentes dan el
mes; se toma el último día del mes.

`entrez_date` es la entrada en PubMed, pero casi todas las revistas publican
el artículo online antes. `live_dates.py` consulta PubMed y guarda en
`work/live_dates.json` la primera fecha pública de cada caso (publicación
electrónica, entrada en PubMed o en PMC; no cuenta una fecha anterior a la
aceptación, que es la del número de la revista). Un caso queda «sin ver» para
un modelo si esa fecha es posterior a su corte.

| Modelo | Corte | Fuente | `live` sin ver por `entrez_date` | `live` sin ver por primera publicación |
|---|---|---|---:|---:|
| gemini-3.1-pro-preview | ene-2025 | Ficha de Google DeepMind (remite a la de Gemini 3 Pro) | 150 | 150 |
| gpt-5.4-mini | ago-2025 | Microsoft Learn, «Training Data (up to)» | 150 | 150 |
| gpt-5.6-terra | feb-2026 | Microsoft Learn | 150 | 150 |
| gpt-6.1-sol | abr-2026 | Microsoft Learn | 150 | 146 |
| claude-opus-5 | may-2026 | Ficha de Anthropic | 150 | 143 |
| gpt-6.1-terra | jun-2026 | Microsoft Learn | 150 | 129 |

Ningún modelo tiene un corte posterior al 1-jul-2026, así que por
`entrez_date` todo el bloque `live` es no visto. Por fecha de publicación,
21 casos ya estaban online antes de fin de junio. Para gpt-6.1-terra,
claude-opus-5 y gpt-6.1-sol hay que mirar también la cifra de `live` sin
esos casos (`score_blocks.py --live-dates`). Una fecha de corte es lo que
declara el proveedor: no descarta que el modelo haya visto un preprint o una
versión anterior del caso.

Para la renovación trimestral (paso 9 del ROADMAP), conviene seleccionar por
fecha de primera publicación y no por `entrez_date`.
