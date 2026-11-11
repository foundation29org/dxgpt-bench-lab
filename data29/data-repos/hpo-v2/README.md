# HPO v2 — nombre sin gen y limpieza T3

Segunda versión del gold de los seis datasets de raras en lista HPO (3.017
casos). Las listas HPO no cambian: solo cambia el gold. Es el paso 2 del
[ROADMAP](../../../docs/ROADMAP.md), necesario para evaluar raras con Pipeline V5.
Solo se aplica a raras: en `narrative_v2` el gold ya se dejó al nivel de
enfermedad al construir el dataset.

## En una frase

El gold v2 es el gold original (con gen) **más** el nombre de la enfermedad
sin el gen; vale acertar cualquiera de los dos. Además salen 11 casos de gold
dudoso.

Ejemplo, caso DDD_G2P00025. Terra pone en P1 «Leber congenital amaurosis»:

| | Qué vale como correcto | Nota del juez | ¿Acierto estricto? |
|---|---|---|---|
| Gold con gen (original) | «RPGRIP1-related Leber congenital amaurosis» | 1 (relacionado, le falta el gen) | No |
| Gold con gen o sin gen (v2) | lo anterior **o** «Leber congenital amaurosis» | 2 (misma enfermedad) | Sí, en P1 |

## Por qué

El modelo solo ve una lista de términos HPO, sin genes ni variantes. Muchos
gold, en cambio, llevan información que solo da un estudio genético:

- el gen: «BBS9-related Bardet-Biedl syndrome», casi todo DDD;
- un subtipo definido por el gen: «Maple Syrup Urine Disease, Type Ia»,
  «Retinitis Pigmentosa 11»;
- el grupo de complementación: «Methylmalonic acidemia with homocystinuria,
  type cblC».

Con la rúbrica de V5, una respuesta que acierta el síndrome sin el gen recibe
un 1 («otro subtipo o gen de la misma familia»), así que el caso cae por un
motivo que el modelo no puede resolver. En V4 parte de esos aciertos entraban
por SapBERT. David lo vio en la revisión de fallos de Terra en raras (T3): en
4 de 30 fallos Terra daba el síndrome correcto en P1 (MSUD, Hallermann-Streiff,
amaurosis congénita de Leber, agnatia-otocefalia).

## Qué cambia

1. **Nombre sin gen.** Cada caso puede llevar un segundo gold con el nombre de
   la enfermedad sin el gen ni el subtipo genético. En el dataset va con
   `"role": "clinical"` y `"derived_from"` (el gold con gen del que sale). V5
   puntúa todos los gold y se queda con el mejor (regla C3), así que el gold
   con gen sigue contando. Solo se añade si:
   - es distinto del original;
   - sigue siendo una enfermedad o síndrome con entidad propia
     (Bardet-Biedl, Leber, MSUD, Treacher Collins), no un rasgo genérico
     («intellectual disability», «epilepsy», «atrial septal defect») ni una
     lista de rasgos;
   - no es uno de los términos HPO del caso («Methylmalonic aciduria»,
     «Nephronophthisis»), porque regalaría el acierto.

   Se mantienen los subtipos que son enfermedades clínica o bioquímicamente
   distintas: tipos de mucopolisacaridosis, de tirosinemia, de glucogenosis,
   Usher 1 frente a 2.

2. **Nombres legibles.** V5 enseña al juez el gold tal como está escrito. Las
   siglas y los nombres repetidos («DA8», «MODY», «Neurofibromatosis, Type
   2,Neurofibromatosis type 2») reciben un nombre completo en
   `accepted_names`. Los códigos se resuelven a mano en `MANUAL_READABLE`,
   porque el LLM se equivoca con ellos: llamó «Phenylketonuria» a ORPHA:761
   (es vasculitis IgA, según ORDO) y «Cardiofaciocutaneous syndrome» a CFM1
   (OMIM 603855, modificador de fibrosis quística).

3. **Limpieza T3.** Salen los 11 casos que David marcó como gold dudoso
   (causa B): 7 fenilcetonurias de RAMEDIS cuyos HPO describen hipertirosinemia,
   una alcaptonuria con convulsiones y muerte en la infancia, y 3 de DDD cuyos
   HPO o herencia contradicen el gold. Están en `T3_DOUBTFUL_GOLD`, con el
   motivo. Los 9 casos con HPO insuficientes (causa C) se quedan: el criterio
   para marcarlos está pendiente.

   **Pendiente (5-nov):** los 11 salieron de revisar solo fallos de Terra. Las
   7 fenilcetonurias no tienen nada especial: en RAMEDIS, 115 de los 148 casos
   de fenilcetonuria llevan «Hypertyrosinemia» junto a «Hyperphenylalaninemia»,
   y los otros 109 siguen dentro. Parece cosa de cómo RAMEDIS codifica estos
   casos. Se resuelve con una regla para los 115: se quedan todos o salen todos.
   Lo decide David en la tarea 3, bloque G, sin ver resultados de los modelos
   (ver las reglas congeladas en el README de Pipeline V5).

El nombre sin gen lo propone Gemini 2.5 Pro (el LLM de curación de
`narrative_v2`), una vez por nombre de gold único (2.152), con las reglas de
arriba en el prompt.

## Versión v3 (10-nov-2026, validada en la tarea 4)

David revisó una muestra al azar de la v2 en la
[tarea 3](../../../docs/tareas-david/03-nombres-sin-gen-raras.md). Cerca de la
mitad de las decisiones del LLM estaban mal o se podían mejorar: bien 16 de 25
en el bloque A, 5 de 10 en el B y 4 de 10 en el C. Fallaban en los dos
sentidos:

- **Demasiado amplio.** Quedaba un nombre que engloba varias enfermedades
  («tyrosinemia» para TAT, en lugar de «Tyrosinemia type II»).
- **Demasiado estricto.** Se descartaba como rasgo genérico una enfermedad con
  epónimo («Coffin-Siris syndrome» para SMARCC2).

Por eso la v3 rehace los nombres de todos los casos:

- **Instrucciones con los criterios de David.** Se quitan los tipos que se
  numeran por gen, también cuando parecen tipos clínicos («Kleefstra syndrome
  2»). Si el nombre sin gen engloba varias enfermedades, se usa el nombre propio
  sin gen: un subtipo anterior al gen o un epónimo. Se mantienen los
  calificativos que no dependen del gen, y la herencia cuando separa
  enfermedades distintas. Un título descriptivo con dos o más rasgos
  obligatorios es una entidad. El nombre de una serie numerada por gen, sin el
  número, es una entidad («Developmental and epileptic encephalopathy»,
  «Autosomal recessive primary microcephaly»), salvo las de discapacidad
  intelectual.
- **Gemini 3.8 Flash** en lugar de 2.5 Pro, que Google retira el 1-dic-2026.
  Los 2.152 nombres costaron 0,44 $, y repasar 335 con el criterio de las series,
  0,07 $ (`refine`). Con razonamiento `medium` salió peor que con `low`: lotes
  sin JSON y más fallos.
- **Respuestas de David tal cual.** Sus 70 decisiones de las tareas 3 y 4
  (`REVIEWED_CLINICAL`) se aplican a todos los casos con esos gold.
- **Validación (tarea 4).** Una muestra nueva al azar de 24 casos, sin ver
  resultados de los modelos. Bien 19 de 24 (79 %): 10 de 12 en el bloque A, 5 de
  6 en el B y 4 de 6 en el C. Los fallos eran el número de una serie y series
  dadas por genéricas, y de ahí sale el repaso con `refine`, que cambió 167
  nombres y no se ha validado aparte.
- **Vuelven las 7 fenilcetonurias con hipertirosinemia y la alcaptonuria
  RAMEDIS_132.** David decidió que la hipertirosinemia de RAMEDIS y los términos
  de muerte son ruido de la codificación.
- **Regla de la causa C (David, tareas 3 y 4).** Sale el caso que, tras quitar
  los términos que no describen al paciente y los genéricos del neurodesarrollo,
  no conserva ningún término específico (`specific_terms`):
  - Términos que no describen al paciente: herencia, modificadores, edad de
    inicio, obsoletos y los que repiten el gold o su nombre sin gen.
  - Genéricos del neurodesarrollo: discapacidad intelectual, retrasos, crisis
    sin tipo, hipotonía, autismo y sus conductas, EEG anormal y los términos
    «Abnormality of…».
  - En RAMEDIS se quitan también los términos de muerte.
  - Dos términos opuestos (macrocefalia y microcefalia) no cuentan.

  Salen 107 casos. Reproduce 8 de sus 9 decisiones: el caso CHD8 de autismo
  (DDD_G2P01363), que él marcó «contar aparte», sale con la lista ampliada.
- **Gold corregido en HMS_011 y HMS_035.** El nombre «Reactive arthritis» venía
  de un grupo de códigos de artritis del origen. Pasa a ser la enfermedad de su
  código OMIM: síndrome de Sjögren y fiebre mediterránea familiar.
- **Bloque D.** El término HPO igual al nombre sin gen es una fuga del
  diagnóstico. Si sin él no queda fenotipo, el caso sale (regla de la causa C).
  Si queda, no se acepta ese nombre. En los 3 casos que revisó David se usa uno
  más específico (cutis laxa autosómica recesiva tipo I, aciduria
  metilmalónica por déficit de mutasa, paraplejia espástica con cuerpo calloso
  fino).
- **Corregida una errata del gold:** «isobutryl» por «isobutyryl».

| Dataset | Casos | Excluidos (T3) | Excluidos (causa C) | Con nombre sin gen | Sin él: rasgo genérico | Sin él: está en los HPO |
|---|---:|---:|---:|---:|---:|---:|
| DDD | 1.749 | 3 | 98 | 1.459 | 169 | 43 |
| RAMEDIS | 624 | 0 | 3 | 134 | 0 | 2 |
| LIRICAL | 370 | 0 | 0 | 157 | 3 | 1 |
| MyGene2 | 146 | 0 | 6 | 40 | 1 | 2 |
| HMS | 88 | 0 | 0 | 12 | 0 | 1 |
| MME | 40 | 0 | 0 | 7 | 0 | 0 |
| **Total** | **3.017** | **3** | **107** | **1.809** | **173** | **49** |

En RAMEDIS bajan los nombres sin gen porque muchos solo reescribían el mismo
nombre («Glutaric acidemia type I») y ahora salen igual que el gold: no cambia
la nota.

**Puntuación (10-nov-2026).** Sobre los mismos casos, con el mismo juez y la
misma rúbrica, los nombres de la v3 suben el R@1 de Terra del 41,6 % al 43,3 %
y el de Sol del 47,7 % al 49,3 %. El total, con los 107 casos fuera, pasa al
43,1 % en Terra y al 49,2 % en Sol. Detalle en el README de Pipeline V5 («HPO
v3: Terra y Sol con el gold nuevo»).

**Pendiente:**
- **Nombre legible que en realidad es el nombre sin gen.** En algunos gold, el
  nombre legible (`readable_name`, que solo debía desarrollar abreviaturas)
  quita el gen: «Constitutional mismatch repair deficiency syndrome» para el
  gold de PMS2. Va en `accepted_names` del gold con gen y cuenta en la nota
  «solo con gen». Corregirlo en la siguiente versión: no aceptar un nombre
  legible que quite el gen.
- **«Contar aparte».** Hay dos grupos de casos que siguen dentro pero se cuentan
  por separado:
  - los que solo se distinguen por un metabolito, una enzima o un gen ausentes
    del caso (causa C);
  - los del bloque D sin un nombre más específico.

  Para marcarlos hace falta un clasificador y que el informe lo separe.
- David consulta todavía el nivel de Leigh por COX15. Mientras, se usa «Leigh
  syndrome due to cytochrome c oxidase deficiency».
- «Glycogen storage disease IXb» conserva la letra del gen tras `refine` (2
  casos).

## Versión v2 (28-oct-2026)

| Dataset | Casos | Excluidos (T3) | Con nombre sin gen | Sin él: quedaría un rasgo genérico | Sin él: está en los HPO |
|---|---:|---:|---:|---:|---:|
| DDD | 1.749 | 3 | 1.147 | 555 | 43 |
| RAMEDIS | 624 | 8 | 181 | 0 | 4 |
| LIRICAL | 370 | 0 | 138 | 37 | 6 |
| MyGene2 | 146 | 0 | 24 | 7 | 0 |
| HMS | 88 | 0 | 3 | 6 | 1 |
| MME | 40 | 0 | 2 | 1 | 0 |
| **Total** | **3.017** | **11** | **1.495** | **606** | **54** |

El resto de casos no tiene gen que quitar («Phenylketonuria») y no cambia.

En RAMEDIS, 146 de los 181 nombres sin gen solo reescriben el mismo nombre
(«Glutaric Acidemia I» → «Glutaric acidemia type I», «PMM2-CDG» → «Congenital
disorder of glycosylation type Ia»). Los otros 35 quitan el subtipo genético:
20 MSUD tipo Ia, 7 déficit del complejo IV tipo nuclear 1, 4 cblC y 4 sueltos.

En DDD quedan 555 casos a los que no se añade nombre sin gen porque quedaría un
rasgo genérico (de «SETD5-related intellectual disability» quedaría
«intellectual disability»). Sin estudio genético no tienen un diagnóstico
propio: conviene leerlos aparte, como casos que ningún modelo puede resolver
solo con los HPO.

**Sin validación clínica.** Los nombres sin gen y la línea entre «entidad
propia» y «rasgo genérico» son del LLM. `work/build_report.txt` lista cada
decisión por caso para que David revise una muestra.

## Cómo se construye

```powershell
cd "C:\repos\DxGPT\eval\data29\data-repos\hpo-v2"
py clinical_gold.py check     # el prompt frente a las respuestas de David (céntimos)
py clinical_gold.py propose   # Gemini 3.8 Flash, con caché en work/clinical_gold_proposals_v3.json
py clinical_gold.py refine    # repasa los genéricos y los nombres con número (tarea 4)
py clinical_gold.py build     # escribe bench/datasets/<dataset>_v3.json y work/build_report_v3.txt
py review_sheet_v3.py         # hoja de la tarea 4 de David
```

La v2 se hizo igual, con Gemini 2.5 Pro y las instrucciones anteriores. Su
caché (`work/clinical_gold_proposals.json`) y sus datasets (`*_v2.json`) se
conservan para comparar.

Los datasets y `work/` no se versionan (`*.json` en `.gitignore`).

Prueba de sinónimos (30-oct-2026, todavía no es una versión):

```powershell
py gold_synonyms.py fetch   # API de Monarch, con caché en work/mondo_synonyms.json
py gold_synonyms.py build   # escribe bench/datasets/<dataset>_v2_syn.json
```

Añade a `accepted_names` la etiqueta y los sinónimos exactos de MONDO de cada
gold con código OMIM. Solo lo hace si el nombre del gold comparte alguna
palabra significativa con la entrada MONDO: el código del dataset puede estar
mal («Reactive arthritis» con el OMIM del síndrome de Sjögren en HMS). Los
gold que quedan fuera van a `work/synonyms_skipped.txt`. `review_sheet.py`
saca 10 de esas parejas para la tarea 3 de David (bloque F). Resultados en el
README de Pipeline V5 («Prueba: sinónimos MONDO en el gold»).

## Cómo se evalúa

Con Pipeline V5 sobre las mismas listas de Terra low de julio
(`config_terra_low_<dataset>_v2.yaml`): `REUSE_LABELED_DDX` reutiliza las
listas y `REFRESH_GOLD_FROM_DATASET` les pone el gold v2. El juez puntúa cada
opción contra el gold con gen y contra el nombre sin gen, así que las dos
lecturas salen del mismo run: `score_blocks.py --without-clinical` ignora el
nombre sin gen y da la nota solo con el gold con gen.

## Resultados con Terra low (28-oct-2026)

Mismas listas que el benchmark HPO strict de septiembre
(`bench/multimodal_beta/results/2026-09-16-rare-hpo-terra-strict.md`). Las
tres columnas se calculan sobre los 3.006 casos de v2 (sin los 11 de T3).
Juez Gemini 2.5 Pro.

R@1 estricta:

| Dataset | Casos | V4 strict (sept) | V5, gold con gen (original) | V5, gold con gen o sin gen (v2) |
|---|---:|---:|---:|---:|
| DDD | 1.746 | 27,4 % | 24,0 % | **43,2 %** |
| RAMEDIS | 616 | 33,1 % | 31,8 % | **34,1 %** |
| LIRICAL | 370 | 28,4 % | 24,9 % | **41,6 %** |
| MyGene2 | 146 | 38,4 % | 37,0 % | 37,0 % |
| HMS | 88 | 42,0 % | 40,9 % | 40,9 % |
| MME | 40 | 50,0 % | 50,0 % | 50,0 % |
| **Total** | **3.006** | **29,9 %** | **27,2 %** | **40,9 %** |

R@5 estricta:

| Dataset | V4 strict (sept) | V5, gold con gen (original) | V5, gold con gen o sin gen (v2) |
|---|---:|---:|---:|
| DDD | 40,7 % | 34,4 % | **53,7 %** |
| RAMEDIS | 57,8 % | 54,2 % | 57,5 % |
| LIRICAL | 46,5 % | 38,1 % | **58,1 %** |
| MyGene2 | 58,2 % | 53,4 % | 53,4 % |
| HMS | 64,8 % | 58,0 % | 58,0 % |
| MME | 65,0 % | 67,5 % | 67,5 % |
| **Total** | **46,8 %** | **41,0 %** | **55,3 %** |

4.522 llamadas al juez, ≈ 64 $; 1 caso con error del juez (503 de Gemini),
reparado con `repair_judge_errors.py`.

- **Con el gold con gen, V5 baja 3 puntos de R@1 respecto a V4.** Es lo que
  avisaba el ROADMAP: sin SapBERT ni hermanos ICD, «Bardet-Biedl syndrome»
  frente a «BBS9-related BBS» pasa a ser un 1.
- **Aceptando también el nombre sin gen, R@1 sube 11 puntos sobre V4**
  (29,9 % → 40,9 %), sobre todo en DDD y LIRICAL, que son los datasets con gen
  o subtipo en el gold. En los 1.147 casos de DDD con nombre sin gen, R@1 pasa
  de 30,1 % a 59,3 %.
- **Los 599 casos de DDD sin nombre sin gen** (quedaría un rasgo genérico o el
  nombre está en los HPO) se quedan en 12,4 % de R@1: son casos que ningún
  modelo resuelve sin estudio genético. Conviene publicar DDD con y sin ellos.
- **Los 4 casos de la causa A de T3** (MSUD, Hallermann-Streiff, Leber,
  agnatia-otocefalia) pasan a acierto en P1.
- **Muestra de 24 casos que solo aciertan por el nombre sin gen:** 23 son lo
  esperado («Fanconi anemia» por «grupo de complementación C», «Joubert
  syndrome» por «ARMC9-related Joubert syndrome»). En uno el juez da un 2
  dudoso: síndrome WOREE frente a «Pontocerebellar hypoplasia».
- MyGene2, HMS y MME casi no cambian: tienen pocos gold con gen.
