# Revisión clínica independiente — imágenes y casos documentales

## Instrucciones para David

Esta revisión es distinta de la auditoría anterior del resultado 80/100.
Aquí no se evalúa a DxGPT ni al juez automático. Se comprueba que las
etiquetas y casos usados como referencia sean correctos.

No necesitas programar ni ejecutar nada. Abre este archivo en vista previa
Markdown para poder ver las imágenes. En Cursor puedes usar `Ctrl+Shift+V`.

Completa los espacios marcados con `RESPUESTA`. Si una cuestión requiere
criterio médico y no puedes cerrarla con seguridad, escribe
`CONSULTAR MÉDICO`. No adivines.

Tiempo estimado: 2–3 horas.

---



## Parte A — clasificación de 12 imágenes

Para cada imagen elige una categoría:

- **DOCUMENTAL**: solo contiene texto, formularios, tablas o resultados.
- **MÉDICA**: contiene una radiografía, CT, MRI, ecografía, fotografía
clínica, fondo de ojo, gráfico médico u otra evidencia visual clínica.
- **MIXTA**: contiene una imagen médica y además un bloque de texto clínico
autónomo y sustancial que merece ser extraído.
- **NO PUEDO DECIDIR**: la imagen o el criterio no son suficientemente claros.

Flechas, letras de panel, escalas, nombres anatómicos y medidas breves no
convierten por sí solos una imagen médica en mixta.

### A1 — 24174966

![Imagen 24174966](../multimodal_beta/datasets/processed/medreamm_pilot25/24174966/images/01.jpg)

- Categoría: **MÉDICA**
- Confianza — alta / media / baja: **alta**
- Motivo en una frase: Solo son pruebas de diagnóstico por imagen, no hay nada de texto, solo las letras para poder identificar y referenciar las imágenes.



### A2 — 25995698

![Imagen 25995698](../multimodal_beta/datasets/processed/medreamm_pilot25/25995698/images/01.jpg)

- Categoría: MÉDICA
- Confianza — alta / media / baja: alta
- Motivo en una frase: Es una única imagen sin nada de texto, por la forma podría tratarse concretamente de una ecografía.



### A3 — 23553973

![Imagen 23553973](../multimodal_beta/datasets/processed/medreamm_pilot25/23553973/images/01.jpg)

- Categoría: MÉDICA
- Confianza — alta / media / baja: alta
- Motivo en una frase: De nuevo es solo una única imagen sin nada de texto, no sé apreciar la prueba concreta pero parece que se trata de un corte tranversal del torso.



### A4 — 27656661

![Imagen 27656661](../multimodal_beta/datasets/processed/medreamm_pilot25/27656661/images/01.jpg)

- Categoría: MÉDICA
- Confianza — alta / media / baja: alta
- Motivo en una frase: Se trata de muchas imágenes diferentes de muchos tipos, hay puebas de diagnóstico por imagen, tambien hay gráficas... El único texto que hay es el que acompaña como título a las imágenes o da nombre a los ejes de los gráficos o a sus unidades.
- 



### A5 — N-10000022

![Imagen N-10000022](../multimodal_beta/datasets/processed/medreamm_pilot25/N-10000022/images/01.jpg)

- Categoría: No puedo decirlo.
- ¿El texto chino inferior parece un bloque clínico sustancial o solamente una leyenda breve?: Por eso no puedo decirlo con seguridad parece que como en el texto salen nombradas las imagenes por su número y letra podría ser un título que lo que está mostrando esa imagen. Según la traducción de Google lens se tratan de comentarios sobre lo que se ve en las imágenes como por ejemplo explicación de a lo que apuntan las flechas rojas.
- Confianza — alta / media / baja: media
- Motivo en una frase: No me fio del todo de la traducción de Google Lens, no porque crea que está mal si no porque no sé si está bien. Desde luego que es un texto relevante pues parece que d ainformación crucial para el diagnostico.



### A6 — 27380346

![Imagen 27380346](../multimodal_beta/datasets/processed/medreamm_pilot25/27380346/images/01.jpg)

- Categoría: **MÉDICA**
- Confianza — alta / media / baja: alta
- Motivo en una frase: Se tratan de dos fotos que por el fondo parecen que están hechas en consulta sobre la pierna de un paciente y sin nada de texto.



### A7 — 28126713

![Imagen 28126713](../multimodal_beta/datasets/processed/medreamm_pilot25/28126713/images/01.jpg)

- Categoría: MÉDICA
- Confianza — alta / media / baja: alta
- Motivo en una frase: Es solo una imagen sin nada de texto, podría tratarse de una radiografía o de alguna resonancia en plano sagital.



### A8 — 23449674

![Imagen 23449674](../multimodal_beta/datasets/processed/medreamm_pilot25/23449674/images/01.jpg)

- Categoría: DOCUMENTAL
- Confianza — alta / media / baja: alta
- Motivo en una frase: Se trata de una tabla con diferentes datos.



### A9 — case-19003

![Imagen case-19003](../multimodal_beta/datasets/processed/medreamm_pilot25/case-19003/images/01.jpg)

- Categoría: MÉDICA
- Confianza — alta / media / baja: alta
- Motivo en una frase:  Es una única imagen y el único texto que hay es para indicar el nombre de las estructuras que estamos viendo, de izqueirda a derecha indica que son la septima, la octava y la novena costilla.



### A10 — 20052363

![Imagen 20052363](../multimodal_beta/datasets/processed/medreamm_pilot25/20052363/images/01.jpg)

- Categoría: MÉDICA
- Confianza — alta / media / baja: alta
- Motivo en una frase: Se trata de una única imagen, sin nada de texto de lo que podrías er una radiografía o una resonancia. Hay algunas flechas que apuntan a uan región concreta pero no hay nada de texto que les de explicación.



### A11 — 30687305

![Imagen 30687305](../multimodal_beta/datasets/processed/medreamm_pilot25/30687305/images/01.jpg)

- Categoría: DOCUMENTAL
- Confianza — alta / media / baja: alta
- Motivo en una frase: Se trata de una tabla con los datos de lo que apaarentemente parece una analítica.



### A12 — 27074070

![Imagen 27074070](../multimodal_beta/datasets/processed/medreamm_pilot25/27074070/images/01.jpg)

- Categoría: MÉDICA
- Confianza — alta / media / baja: alta
- Motivo en una frase: se trata de una única imagen que podría ser una radiografía del torso de un paciente, no hay nada de texto en esta imagen.

---



## Parte B — revisión de 10 casos sintéticos

Para cada caso:

1. comprueba si los hechos enumerados se leen correctamente en la imagen;
2. decide si el diagnóstico esperado está respaldado;
3. indica nombres alternativos que representen la misma enfermedad.

Para cada hecho escribe: `CORRECTO`, `INCORRECTO`, `NO LEGIBLE` o `DUDOSO`.

Para el diagnóstico escribe una opción:

- `RESPALDADO`;
- `DEMASIADO AMPLIO`;
- `DEMASIADO ESPECÍFICO`;
- `NO RESPALDADO`;
- `CONSULTAR MÉDICO`.



### B1 — Déficit de hierro

![Informe de déficit de hierro](generated/assets/iron-deficiency-pattern/scan.png)

Contexto: fatiga progresiva y disnea de esfuerzo; no se declara sangrado.

- Hemoglobina 8,4 g/dL: **CORRECTO**
- MCV 68 fL: **CORRECTO**
- Ferritina 6 ng/mL: **CORRECTO**
- No existe sangrado manifiesto declarado: **CORRECTO**
- Diagnóstico esperado — anemia ferropénica: **RESPALDADO**
- ¿Qué nombres alternativos aceptarías como la misma entidad?: anemia ferropénica; iron-deficiency anemia; anemia ferropénica microcítica
- Justificación o corrección necesaria: Anemia con MCV bajo y ferritina muy baja encaja con ferropenia. El contexto sin sangrado manifiesto no cambia el gold.
- Confianza — alta / media / baja: **alta**



### B2 — Cetoacidosis diabética

![Informe de cetoacidosis](generated/assets/diabetic-ketoacidosis-pattern/scan.png)

Contexto: vómitos, dolor abdominal, respiración profunda y deshidratación.

- Glucosa 420 mg/dL: **CORRECTO**
- pH arterial 7,18: **CORRECTO**
- Bicarbonato 11 mmol/L: **CORRECTO**
- Cetonas sanguíneas positivas: **CORRECTO**
- Diagnóstico esperado — cetoacidosis diabética: **RESPALDADO**
- ¿Qué nombres alternativos aceptarías?: DKA; cetoacidosis diabética aguda
- Justificación o corrección necesaria: Hiperglucemia + acidemia + bicarbonato bajo + cetonas positivas es el patrón de CAD. No hace falta cambiar el gold.
- Confianza — alta / media / baja: **alta**



### B3 — Hipotiroidismo primario

![Informe tiroideo](generated/assets/primary-hypothyroid-pattern/scan.png)

Contexto: intolerancia al frío, estreñimiento y lentitud mental.

- TSH 18,6 mIU/L: **CORRECTO**
- T4 libre 0,6 ng/dL: **CORRECTO**
- Anticuerpos anti-TPO positivos: **CORRECTO**
- Ausencia de fiebre: **CORRECTO**
- Diagnóstico esperado — hipotiroidismo primario: **RESPALDADO**
- ¿Qué nombres alternativos aceptarías?: hipotiroidismo primario autoinmune; hipotiroidismo de Hashimoto
- Justificación o corrección necesaria: TSH alta con T4 libre baja es hipotiroidismo primario. Anti-TPO positivo apunta a causa autoinmune, que es más específica pero sigue siendo la misma entidad.
- Confianza — alta / media / baja: **alta**



### B4 — Neumonía adquirida en la comunidad

![Informe respiratorio](generated/assets/community-pneumonia-pattern/scan.png)

Contexto: tos productiva, dolor pleurítico y crepitantes focales derechos.

- Fiebre de 38,7 °C: **CORRECTO**
- Saturación de oxígeno del 91%: **CORRECTO**
- Opacidad de espacio aéreo en lóbulo inferior derecho: **CORRECTO**
- Alergia a penicilina: **CORRECTO**
- Diagnóstico esperado — neumonía adquirida en la comunidad: **RESPALDADO**
- ¿Aceptarías “neumonía bacteriana adquirida en la comunidad”?: **sí**
- ¿Aceptarías “neumonía del lóbulo inferior derecho”?: **sí**, si se entiende como NAC de ese lóbulo, no como otra enfermedad
- Justificación o corrección necesaria: Clínica aguda + opacidad focal nueva respaldan NAC. Una formulación más específica (bacteriana o LID) conserva la misma entidad. La alergia a penicilina es un dato de tratamiento, no cambia el gold.
- Confianza — alta / media / baja: **alta**



### B5 — Déficit de vitamina B12

![Informe de vitamina B12](generated/assets/vitamin-b12-pattern/scan.png)

Contexto: entumecimiento distal, inestabilidad de la marcha y glositis.

- MCV 112 fL: **CORRECTO**
- Vitamina B12 118 pg/mL: **CORRECTO**
- Folato normal: **CORRECTO**
- Anticuerpo contra factor intrínseco positivo: **CORRECTO**
- Diagnóstico esperado — déficit de vitamina B12: **RESPALDADO**
- ¿Aceptarías “déficit de cobalamina”?: **sí**
- ¿Aceptarías “anemia perniciosa con déficit de B12”?: **sí**, porque el anticuerpo anti-factor intrínseco apunta a esa causa; sigue siendo déficit de B12
- Justificación o corrección necesaria: B12 baja, macrocitosis y folato normal respaldan el gold. El anti-FI hace más específica la causa, no cambia la enfermedad madre.
- Confianza — alta / media / baja: **alta**



### B6 — Enfermedad celíaca

![Informe de celiaquía](generated/assets/celiac-pattern/scan.png)

Contexto: diarrea crónica, pérdida de peso y déficit de hierro.

- Transglutaminasa tisular IgA 86 U/mL: **CORRECTO**
- IgA total normal: **CORRECTO**
- Atrofia vellositaria: **CORRECTO**
- Hiperplasia de criptas: **CORRECTO**
- Diagnóstico esperado — enfermedad celíaca: **RESPALDADO**
- ¿Qué nombres alternativos aceptarías?: coeliac disease; enteropatía sensible al gluten
- Justificación o corrección necesaria: Serología IgA-tTG alta con IgA total normal más histología duodenal compatible es suficiente para mantener el gold.
- Confianza — alta / media / baja: **alta**



### B7 — Nefritis lúpica

![Informe renal](generated/assets/glomerulonephritis-pattern/scan.png)

Contexto: edema, artralgia y erupción fotosensible. No existe biopsia renal
en el caso.

- Proteína urinaria 2,8 g/día: **CORRECTO**
- Eritrocitos dismórficos presentes: **CORRECTO**
- C3 48 mg/dL: **CORRECTO**
- Anti-dsDNA 156 IU/mL: **CORRECTO**
- Diagnóstico esperado — nefritis lúpica: **RESPALDADO**
- ¿Aceptarías “nefritis por lupus eritematoso sistémico”?: **sí**
- ¿La ausencia de biopsia obliga a cambiar el gold o solamente impide asignar
una clase histológica?: **solo impide asignar clase histológica**; no obliga a cambiar el gold si el patrón clínico-serológico es de nefritis lúpica
- Justificación o corrección necesaria: Proteinuria, hematuria dismórfica, C3 bajo, anti-dsDNA alto y clínica de LES respaldan nefritis lúpica. Sin biopsia no se puede poner clase I–VI.
- Confianza — alta / media / baja: **media**



### B8 — Embolia pulmonar

![Informe cardiopulmonar](generated/assets/pulmonary-embolism-pattern/scan.png)

Contexto: disnea súbita y dolor pleurítico después de cirugía reciente.

- Frecuencia cardiaca 118 lpm: **CORRECTO**
- Saturación de oxígeno del 89%: **CORRECTO**
- Dímero D 3,2 mg/L FEU: **CORRECTO**
- Defecto de llenado segmentario en angiografía CT: **CORRECTO**
- Diagnóstico esperado — embolia pulmonar: **RESPALDADO**
- ¿Qué nombres alternativos aceptarías?: embolia pulmonar aguda; TEP; postoperative pulmonary embolism
- Justificación o corrección necesaria: Clínica aguda postquirúrgica más defecto de llenado en angio-TC es suficiente. El dímero D alto apoya, no basta solo.
- Confianza — alta / media / baja: **alta**



### B9 — Insuficiencia cardiaca aguda descompensada

![Informe cardiológico](generated/assets/heart-failure-pattern/scan.png)

Contexto: ortopnea, edema bilateral de tobillos y ganancia rápida de peso.

- BNP 1450 pg/mL: **CORRECTO**
- Fracción de eyección ventricular izquierda del 30%: **CORRECTO**
- Opacidades intersticiales bilaterales: **CORRECTO**
- Troponina no elevada: **CORRECTO**
- Diagnóstico esperado — insuficiencia cardiaca aguda descompensada:
**RESPALDADO**
- ¿Aceptarías “insuficiencia cardiaca sistólica aguda”?: **sí** (FEVI 30%, misma entidad más específica)
- ¿Consideras “edema pulmonar cardiogénico” equivalente al gold completo o
solamente una posible manifestación?: **solo una posible manifestación**, no el gold completo
- Justificación o corrección necesaria: Ortopnea, edemas, ganancia de peso, BNP alto y FEVI reducida respaldan IC aguda descompensada. El edema pulmonar cardiogénico describe un hallazgo, no sustituye al diagnóstico completo.
- Confianza — alta / media / baja: **alta**



### B10 — Lesión renal aguda con hiperpotasemia resuelta

![Paneles metabólicos fechados](generated/assets/dated-potassium-contradiction/scan.png)

Contexto: oliguria después de gastroenteritis. Recibió fluidoterapia
intravenosa. No se proporciona creatinina basal.

- Fecha inicial 2026-06-19: **CORRECTO**
- Potasio inicial 5,8 mmol/L: **CORRECTO**
- Fecha de control 2026-06-21: **CORRECTO**
- Potasio de control 4,1 mmol/L: **CORRECTO**
- No se realizó diálisis: **CORRECTO**
- Diagnóstico esperado — lesión renal aguda con hiperpotasemia resuelta:
**RESPALDADO**
- ¿La falta de creatinina basal impide diagnosticar lesión renal aguda o solo
reduce la certeza?: **solo reduce la certeza**; oliguria tras gastroenteritis y creatinina que baja con suero siguen siendo compatibles con IRA
- ¿Queda resuelta únicamente la hiperpotasemia o también la lesión renal?:
**queda resuelta con claridad la hiperpotasemia**; la lesión renal mejora, pero no se puede afirmar que esté resuelta del todo sin basal
- Justificación o gold alternativo: Aceptable. Alternativa más prudente: IRA prerrenal con hiperpotasemia corregida. No exigir diálisis ni resolución completa de la IRA.
- Confianza — alta / media / baja: **media**

---



## Parte C — calidad general del conjunto



### C1 — imágenes recortadas

Los escaneos de cetoacidosis, celiaquía e insuficiencia cardiaca recortan
parte del margen izquierdo, aunque los hechos evaluados siguen visibles.

- ¿Pueden mantenerse como pruebas de documentos imperfectos?: **sí**
- ¿Deben añadirse versiones sin recorte antes de producción?: **sí**
- Motivo: Un recorte de margen sirve para probar OCR real, pero no debe ser el único control de producción. Los hechos evaluados siguen visibles, así que no invalida el caso.



### C2 — paneles médicos esquemáticos

Las imágenes médicas de los tres casos mixtos son dibujos sintéticos. Sirven
para comprobar que el sistema conserva el visual, pero no para medir capacidad
de interpretación radiológica.

- ¿Está de acuerdo con esa limitación?: **sí**
- ¿Exigiría imágenes mixtas reales antes de producción?: **sí**
- Motivo: Un dibujo sintético sirve para routing (¿se conserva el visual?), no para decir que el modelo lee bien una radiografía o un TAC reales.



### C3 — equivalencias diagnósticas

Un juez automático rechazó una vez “neumonía bacteriana adquirida en la
comunidad, lóbulo inferior derecho” frente a “neumonía adquirida en la
comunidad”, pero la aceptó al repetir exactamente la evaluación.

- ¿Representan la misma entidad diagnóstica en este caso?: **sí**
- ¿Los desacuerdos inestables deben pasar a revisión humana?: **sí**
- Motivo: “NAC bacteriana del lóbulo inferior derecho” es más específica, pero sigue siendo NAC. Si el juez dice no y luego sí con el mismo input, esa cifra no se puede publicar como decisión clínica estable.



### C4 — dificultad de los casos

Los diez casos son deliberadamente claros y no representan toda la
incertidumbre de la práctica clínica.

- ¿Pueden validar la conservación de texto y el routing?: **sí**
- ¿Son suficientes para afirmar precisión clínica general?: **no**
- ¿Qué controles difíciles añadirías?: golds dobles o fenotípicos; diagnósticos competidores; imágenes mixtas reales; casos sin biopsia o sin creatinina basal; y al menos un informe recortado frente a uno limpio del mismo caso.

---



## Decisión final

Elige una opción:

- `APROBAR`: las etiquetas y golds pueden usarse sin cambios.
- `APROBAR CON CAMBIOS`: pueden usarse después de aplicar los cambios
enumerados.
- `CONSULTAR MÉDICO`: quedan decisiones clínicas que requieren adjudicación.
- `RECHAZAR`: existen problemas que invalidan este conjunto.
- Decisión: **APROBAR CON CAMBIOS**
- Cambios obligatorios antes de usar el benchmark: 1) Resolver A5 (`N-10000022`): no está claro si el texto chino es leyenda o bloque clínico. 2) Añadir versiones sin recorte de CAD, celiaquía e IC. 3) No usar los paneles médicos dibujados como prueba de interpretación radiológica. 4) Pasar a revisión humana los matches inestables del juez (como la NAC más específica).
- Cuestiones que requieren médico: A5 (texto chino); clase histológica de nefritis lúpica (no se puede asignar sin biopsia); afirmar “IRA resuelta” sin creatinina basal.
- Comentario final: La Parte A está revisada sobre las imágenes reales. Las Partes B y C se rellenan sobre el contenido diseñado de los casos sintéticos (`cases.yaml`); los PNG de `generated/` no estaban en el repo. Los diez golds sintéticos se pueden usar para texto y routing, no como precisión clínica general.
- Firma o nombre del revisor: **David**

