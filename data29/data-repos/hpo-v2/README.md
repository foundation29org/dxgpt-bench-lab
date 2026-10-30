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

El nombre sin gen lo propone Gemini 2.5 Pro (el LLM de curación de
`narrative_v2`), una vez por nombre de gold único (2.152), con las reglas de
arriba en el prompt.

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
py clinical_gold.py propose   # LLM, con caché en work/clinical_gold_proposals.json
py clinical_gold.py build     # escribe bench/datasets/<dataset>_v2.json y work/build_report.txt
```

Los datasets y `work/` no se versionan (`*.json` en `.gitignore`).

Prueba de sinónimos (30-oct-2026, todavía no es una versión):

```powershell
py gold_synonyms.py fetch   # API de Monarch, con caché en work/mondo_synonyms.json
py gold_synonyms.py build   # escribe bench/datasets/<dataset>_v2_syn.json
```

Añade a `accepted_names` la etiqueta y los sinónimos exactos de MONDO de cada
gold con código OMIM. Resultados en el README de Pipeline V5 («Prueba:
sinónimos MONDO en el gold»).

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
