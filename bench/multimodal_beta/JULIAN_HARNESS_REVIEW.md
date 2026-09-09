# Encargo para Julián — revisar el examen (harness + juez)

No es código. Es decidir **qué cuenta como acierto** y **cómo lo
publicamos**. David ya etiquetó 35 casos del paso 7 (el LLM). Falta
cerrar el diseño del evaluador.

Tiempo estimado: 45–60 min. Devuelves comentarios en este fichero o
en un mail; no hace falta un PR.

---

## 1. Qué te pedimos que contestes

Al final hay un bloque de preguntas. Lo de en medio es el contexto
para no discutir a ciegas.

---

## 2. Dos cosas distintas (no mezclar)

| | Alumno | Examen |
|---|---|---|
| Qué es | DxGPT (gpt5, Terra, mini…) | Pipeline V4: códigos → BERT → LLM |
| Prompt | `juanjo_classic_v2` | prompt del **juez** (strict o legacy) |
| Nota típica | R@1, cobertura | acuerdo con David en 35 ids |

Mismo alumno, distinto examen → distinta nota. El 98% narrativo era el
examen facilón (`legacy_similarity`), no que Gemini diagnosticara mejor.

Guía corta del examen: [HARNESS_EVAL.md](HARNESS_EVAL.md).

---

## 3. Cobertura no es precisión

Julián: si en una tabla ves “cobertura 80%”, **no es precisión**.

Un caso tiene **un gold** y una lista DDX (P1…Pn). El harness marca
*match* si **alguna** propuesta es el gold (según las capas de abajo).

| Nombre que usamos | Qué es de verdad | Fórmula |
|---|---|---|
| **R@1** | acierto del diagnóstico #1 | gold en P1 / N |
| **R@3 / R@5** | recall@k | gold en top-k / N |
| **Cobertura** | recall de la lista entera | hay match en cualquier posición / N |
| **Pos. media** | ranking entre los que aciertan | media de la posición del match |

Con un gold por caso, **R@1 = Precision@1 = top-1 accuracy**. Esa es
la cifra más cercana a “precisión” del alumno.

**Cobertura** responde: “¿el gold está *en algún sitio* de la lista?”.
Un modelo puede tener cobertura alta y R@1 flojo: acierta, pero lo
entierra en P4.

Ranking que estamos usando en strict: **R@1, luego cobertura**. Pos.
media solo si empatan las dos.

### Precisión del juez (otra cosa)

Cuando comparamos árbitros (Pro vs Flash vs David), “precisión” sí
encaja: de los sí que dice el juez, cuántos David también dice sí
(VPP). Y recall: de los sí de David, cuántos pilla el juez.

Eso **no** es la columna “Cobertura” de las 100. Las 100 mezclan
SNOMED/ICD/BERT (no se mueven al cambiar de juez) + los ~36 que sí
decide el LLM.

Propuesta para tablas públicas: dejar de vender “cobertura” como nota
única; titular **R@1** y llamar a la otra **recall de lista** (o
seguir diciendo cobertura, pero con glosa).

---

## 4. El juez es binario hoy. Julián pide grado.

Hoy el LLM del paso 7 responde **un entero**: `0` (nada) o `1…n`
(posición equivalente). No hay “parecido”.

Eso fuerza el diseño a **dos prompts**:

- **Viejo** (`legacy_similarity`) — “más similar o intercambiable”:
  presentación, fisiopatología, tratamiento, diagnóstico diferencial.
  Archivo: `bench/pipelines/pipeline_v4 - fork/main/evaluator.py`
  (`_get_llm_judgment`).
- **Actual** (`strict_equivalence`) — “misma entidad”: sinónimos sí;
  familia / sitio / complicación no.
  Archivo: `bench/multimodal_beta/evaluate_v4.py`
  (`StrictMultimodalEvaluator`).

Hay una ambigüedad en el prompt actual que hay que resolver: primero
acepta «una forma más específica que preserve el diagnóstico», pero
después dice que no se acepte «un subtipo diferente». Casos como
PPMS frente a MS-like, GIST frente a GIST maligno o una fractura
bilateral frente a una derecha caen justo en esa frontera.

Idea de Julián: **un** juez con escala, por ejemplo:

| Grado | Significa | ¿Cuenta en la nota publicada? |
|---|---|---|
| 2 | misma entidad (sinónimo, abreviatura, forma más específica) | sí (strict) |
| 1 | relacionado (padre, hermano, fenotipo, subtipo distinto) | no en strict; sí en un informe “laxo” |
| 0 | otra enfermedad | no |

Ventaja: un solo árbitro, dos lecturas. El 98% vs 80% dejaría de ser
“cambiamos el prompt a escondidas”.

Coste: hay que etiquetar de nuevo con David (o recodificar las 35) en
esa escala. El formulario actual es binario (`correcto` /
`falso_positivo` / `falso_negativo`).

---

## 5. El LLM no es todo el examen

`strict` **solo cambia el paso 7**. Siguen ON:

1. SNOMED exacto
2. ICD exacto
3. ICD hijo (más específico)
4. ICD padre (más amplio)
5. ICD **hermano** (otra enfermedad, mismo padre ICD)
6. SapBERT ≥ 0,90 → match sin LLM
7. SapBERT + LLM (y BERT ≥ 0,80 puede **pisar** al LLM)

Ejemplo: gold *Inclusion Body Myositis*, lista *Dermatomyositis* en
P1. No son la misma enfermedad. ICD las marca hermanas → match en P1
**sin preguntar al juez**.

Si el juez pasa a escala 0/1/2 y las capas 4–6 siguen igual, el grado
no se aplica a esos casos: el hermano ICD ya cerró.

---

## 6. Ablación del modelo y auditoría de las etiquetas (2026-09-09)

Mismas 100 T+I gpt5, mismo `labeled_input.json`, prompt strict.
Gold = David ronda 2, **35 ids** (`24910386` fuera: etiqueta inválida
`incorrecto`; mail ya enviado).

Estas cifras miden **acuerdo con las etiquetas iniciales de David**,
no precisión clínica definitiva:

| Juez | Acuerdo bruto con David | Cobertura 100 |
|---|---:|---:|---|
| gemini-2.5-pro | 30/35 | 80 |
| gemini-2.5-flash | 31/35 | 85 |
| gpt-5.4-mini | 30/35 | 78 |
| gemini-3.8-flash | 28/35 | 72 |
| gemini-3.5-flash-lite | 28/35 | 75 |
| DeepSeek-V4-Pro / 2.5-flash-lite | — | — |

### 6.1 La revisión humana también necesita adjudicación

Después de obtener esos números se contrastaron los desacuerdos con
los artículos fuente, el manifest y el prompt literal. Hay errores
humanos claros y varios casos donde el gold o la política no permiten
una respuesta binaria limpia:

| ID | Problema encontrado | Acción propuesta |
|---|---|---|
| `22563559` | David llamó neoplasia T madura a un caso cuyo artículo y gold dicen explícitamente T-lymphoblastic leukemia. Un reordenamiento `TCRAD` no implica por sí solo ese cambio de entidad. | Readjudicar; inclinado a aceptar P1. |
| `24054536` | David puso posición 0, pero escribió que P1–P4 podían contar. | Corregir contradicción; inclinado a P1 o marcar gold ambiguo. |
| `28620010` | P2 dice fracturas bilaterales subcapitales: incluye necesariamente la fractura derecha del gold. | Fijar si añadir afectación contralateral invalida; con el prompt actual, aceptar P2. |
| `27068836` | Gold = destrucción de un segmento esofágico; P1 = perforación con mediastinitis. El artículo distingue la pérdida segmentaria de sus entidades secundarias. | Inclinado a rechazar P1; revisar calidad/granularidad del gold. |
| `27656661` | El artículo describe un trastorno MS-like asociado a `OPA1`, no simplemente PPMS. | Inclinado a rechazar P1 o marcar gold fenotípico. |
| `26819809` | Gold maligno; P1 solo GIST gástrico. | Decidir si omitir malignidad sigue siendo misma entidad; strict literal se inclina a rechazar. |
| `21424749` | Gold “mitochondrial disease” es demasiado amplio; el caso real es mt-tRNA-Phe y P1 afirma MERRF/tRNA-Lys. | Gold ambiguo; no usar para elegir juez. |
| `25336332` | Gold amígdala; P1 deja “tonsil/base of tongue” sin resolver el sitio. | Decidir si una opción disyuntiva cuenta; strict literal se inclina a rechazar. |
| `19721837` | La explicación de David dice “crónica”, pero P1 no lo dice. La equivalencia HES sí es defendible. | Mantener P1, corregir justificación. |
| `27709474` | P1 nombra explícitamente el tumor mesenquimal fosfatúrico del gold. | Mantener P1. |

Por eso **no se puede concluir todavía que Flash 2.5 sea demasiado
generoso ni que 3.8 sea peor**. Una readjudicación provisional,
excluyendo `21424749` y `24054536`, deja aproximadamente 3.8 en
30/33, Flash 2.5 en 29/33 y Pro en 29/33. Una sola decisión sobre los
ambiguos vuelve a cambiar el orden.

**Decisión temporal:** no cambiar el juez publicado. Pro se conserva
solo por continuidad hasta fijar la rúbrica y readjudicar estos casos,
no porque haya demostrado ser más preciso.

Informes: `results/2026-09-09-judge-ablation-*.md`.

---

## 7. Ficheros a abrir

1. [HARNESS_EVAL.md](HARNESS_EVAL.md) — capas y palancas.
2. Prompts: `evaluate_v4.py` (strict) y `evaluator.py` de pipeline_v4
   (legacy). Textos en §4.
3. Etiquetas David: `reviews/david_deliverable_ronda2.md`.
4. Números de producto strict: `docs/benchmark-report-strict-texto.html`
   (narrativo) y `docs/benchmark-report-strict-multimodal.html`.
   `docs/benchmark-report.html` está congelado (legacy).

Detalles abiertos para David: recodificar `24910386` y readjudicar la
tabla de §6.1 una vez Julián haya cerrado la rúbrica.

---

## 8. Preguntas (contesta aquí)

**Métricas del alumno**

- [ ] ¿Publicamos **R@1** como precisión (P@1) y la cobertura como
  recall de lista, con glosa, en vez de una sola “cobertura”?
- [ ] ¿El ranking R@1 → cobertura te vale, o quieres otra primaria?

**Juez: binario vs grado**

- [ ] ¿Escala 2/1/0 (equivalente / relacionado / no) en el paso 7?
- [ ] Si sí: la nota pública, ¿solo grado 2, o publicamos las dos?

**Capas que el LLM no ve**

- [ ] ¿Apagamos hermanos ICD en el ranking “strict” publicado?
- [ ] ¿Padres ICD?
- [ ] ¿BERT ≥ 0,90 automático y BERT ≥ 0,80 pisando al juez?

**Modelo del juez**

- [ ] ¿Se queda `gemini-2.5-pro` temporalmente por continuidad mientras
  se readjudican los casos?
- [ ] Tras readjudicar, ¿comparamos Pro, Flash 2.5 y Flash 3.8 por
  precisión, recall, matriz de confusión y concordancia?

**Prompt**

- [ ] El texto strict (“misma entidad”) ¿está bien, o lo reescribes?
- [ ] Si hay escala 2/1/0, ¿un solo prompt con esa rúbrica?
- [ ] ¿Cómo resolvemos «más específico permitido» frente a «subtipo
  diferente prohibido», diagnósticos disyuntivos y hallazgos añadidos?

Cuando esto esté cerrado, ingeniería mueve **una** palanca, re-scorea
las mismas listas DDX, y enseña el delta. No se apilan tres cambios
el mismo día.
