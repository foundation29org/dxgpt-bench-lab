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
- ¿Qué nombres alternativos aceptarías como la misma entidad?: Anemia por deficiencia de hierro, Anemia por déficit de hierro, Anemia microcítica hipoferrémica, Anemia hipoferrémica, Anemia sideropénica, Anemia microcítica por déficit de hierro, Anemia ferropénica severa / moderada / leve.
- Justificación o corrección necesaria: 
- Confianza — alta / media / baja: ALTA



### B2 — Cetoacidosis diabética

![Informe de cetoacidosis](generated/assets/diabetic-ketoacidosis-pattern/scan.png)

Contexto: vómitos, dolor abdominal, respiración profunda y deshidratación.

- Glucosa 420 mg/dL: **CORRECTO**
- pH arterial 7,18: **CORRECTO**
- Bicarbonato 11 mmol/L: **CORRECTO**
- Cetonas sanguíneas positivas: **CORRECTO**
- Diagnóstico esperado — cetoacidosis diabética: **RESPALDADO**
- ¿Qué nombres alternativos aceptarías?: Cetoacidosis diabética (CAD), Cetoacidosis diabética aguda, Cetoacidosis diabética tipo 1, Cetoacidosis diabética hiperglucémica, Cetoacidosis diabética con acidosis metabólica, Cetoacidosis diabética con cetonemia, Cetoacidosis diabética con anión gap elevado, CAD moderada / severa.
- Justificación o corrección necesaria: 
- Confianza — alta / media / baja: **ALTA**



### B3 — Hipotiroidismo primario

![Informe tiroideo](generated/assets/primary-hypothyroid-pattern/scan.png)

Contexto: intolerancia al frío, estreñimiento y lentitud mental.

- TSH 18,6 mIU/L: **CORRECTO**
- T4 libre 0,6 ng/dL: **CORRECTO**
- Anticuerpos anti-TPO positivos: **CORRECTO**
- Ausencia de fiebre: **CORRECTO**
- Diagnóstico esperado — hipotiroidismo primario: **RESPALDADO**
- ¿Qué nombres alternativos aceptarías?: Hipotiroidismo primario, Hipotiroidismo por enfermedad de Hashimoto, Hipotiroidismo autoinmune, Hipotiroidismo clínico, Hipotiroidismo manifiesto, Hipotiroidismo primario autoinmune, Tiroiditis de Hashimoto con hipotiroidismo.
- Justificación o corrección necesaria: 
- Confianza — alta / media / baja: **ALTA**



### B4 — Neumonía adquirida en la comunidad

![Informe respiratorio](generated/assets/community-pneumonia-pattern/scan.png)

Contexto: tos productiva, dolor pleurítico y crepitantes focales derechos.

- Fiebre de 38,7 °C: **CORRECTO**
- Saturación de oxígeno del 91%: **CORRECTO**
- Opacidad de espacio aéreo en lóbulo inferior derecho: **CORRECTO**
- Alergia a penicilina: **CORRECTO**
- Diagnóstico esperado — neumonía adquirida en la comunidad: **RESPALDADO**
- ¿Aceptarías “neumonía bacteriana adquirida en la comunidad”?: **SI**
- ¿Aceptarías “neumonía del lóbulo inferior derecho”?: **SI**
- Justificación o corrección necesaria: 
- Confianza — alta / media / baja: **ALTA**



### B5 — Déficit de vitamina B12

![Informe de vitamina B12](generated/assets/vitamin-b12-pattern/scan.png)

Contexto: entumecimiento distal, inestabilidad de la marcha y glositis.

- MCV 112 fL: **CORRECTO**
- Vitamina B12 118 pg/mL: **CORRECTO**
- Folato normal: **CORRECTO**
- Anticuerpo contra factor intrínseco positivo: **CORRECTO**
- Diagnóstico esperado — déficit de vitamina B12: **RESPALDADO**
- ¿Aceptarías “déficit de cobalamina”?: **SI**
- ¿Aceptarías “anemia perniciosa con déficit de B12”?: **SI**
- Justificación o corrección necesaria: 
- Confianza — alta / media / baja: **ALTA**



### B6 — Enfermedad celíaca

![Informe de celiaquía](generated/assets/celiac-pattern/scan.png)

Contexto: diarrea crónica, pérdida de peso y déficit de hierro.

- Transglutaminasa tisular IgA 86 U/mL: **CORRECTO**
- IgA total normal: **CORRECTO**
- Atrofia vellositaria: **CORRECTO**
- Hiperplasia de criptas: **CORRECTO**
- Diagnóstico esperado — enfermedad celíaca: **RESPALDADO**
- ¿Qué nombres alternativos aceptarías?: Enfermedad celíaca, Celiaquía, Enteropatía por gluten, Enteropatía sensible al gluten, Enteropatía inducida por gluten, Enfermedad celíaca autoinmune, Enteropatía autoinmune por gluten, Enfermedad celíaca con atrofia vellositaria, Enfermedad celíaca clásica. 
- Justificación o corrección necesaria: 
- Confianza — alta / media / baja: **ALTA**



### B7 — Nefritis lúpica

![Informe renal](generated/assets/glomerulonephritis-pattern/scan.png)

Contexto: edema, artralgia y erupción fotosensible. No existe biopsia renal
en el caso.

- Proteína urinaria 2,8 g/día: CORRECTO
- Eritrocitos dismórficos presentes: CORRECTO
- C3 48 mg/dL: **CORRECTO**
- Anti-dsDNA 156 IU/mL: **CORRECTO**
- Diagnóstico esperado — nefritis lúpica: **RESPALDADO**
- ¿Aceptarías “nefritis por lupus eritematoso sistémico”?: **SI**
- ¿La ausencia de biopsia obliga a cambiar el gold o solamente impide asignar una clase histológica?: **CONSULTAR MÉDICO**
- Justificación o corrección necesaria: 
- Confianza — alta / media / baja: **ALTA**



### B8 — Embolia pulmonar

![Informe cardiopulmonar](generated/assets/pulmonary-embolism-pattern/scan.png)

Contexto: disnea súbita y dolor pleurítico después de cirugía reciente.

- Frecuencia cardiaca 118 lpm: **CORRECTO**
- Saturación de oxígeno del 89%: **CORRECTO**
- Dímero D 3,2 mg/L FEU: **CORRECTO**
- Defecto de llenado segmentario en angiografía CT: **CORRECTO**
- Diagnóstico esperado — embolia pulmonar: **RESPALDADO**
- ¿Qué nombres alternativos aceptarías?: Tromboembolia pulmonar (TEP), Embolia pulmonar aguda, Tromboembolia pulmonar aguda, Embolia pulmonar segmentaria, Tromboembolia pulmonar segmentaria, Embolia pulmonar por trombo venoso profundo, Embolia pulmonar sintomática, Embolia pulmonar con defecto de llenado en angio‑TC.
- Justificación o corrección necesaria: 
- Confianza — alta / media / baja: **ALTA**



### B9 — Insuficiencia cardiaca aguda descompensada

![Informe cardiológico](generated/assets/heart-failure-pattern/scan.png)

Contexto: ortopnea, edema bilateral de tobillos y ganancia rápida de peso.

- BNP 1450 pg/mL: **CORRECTO**
- Fracción de eyección ventricular izquierda del 30%: **CORRECTO**
- Opacidades intersticiales bilaterales: **CORRECTO**
- Troponina no elevada: **CORRECTO**
- Diagnóstico esperado — insuficiencia cardiaca aguda descompensada: **RESPALDADO**
- ¿Aceptarías “insuficiencia cardiaca sistólica aguda”?: **SI**
- ¿Consideras “edema pulmonar cardiogénico” equivalente al gold completo o solamente una posible manifestación?: NO, NO ES EQIVALENTE AL GOLD COMPLETO, ES ÚNICAMNETE UNA MANIFESTACIÓN DEL GOLD.
- Justificación o corrección necesaria: 
- Confianza — alta / media / baja: **ALTA**



### B10 — Lesión renal aguda con hiperpotasemia resuelta

![Paneles metabólicos fechados](generated/assets/dated-potassium-contradiction/scan.png)

Contexto: oliguria después de gastroenteritis. Recibió fluidoterapia
intravenosa. No se proporciona creatinina basal.

- Fecha inicial 2026-06-19: **CORRECTO**
- Potasio inicial 5,8 mmol/L: **CORRECTO**
- Fecha de control 2026-06-21: **CORRECTO**
- Potasio de control 4,1 mmol/L: **CORRECTO**
- No se realizó diálisis: **CORRECTO**
- Diagnóstico esperado — lesión renal aguda con hiperpotasemia resuelta: **RESPALDADO**
- ¿La falta de creatinina basal impide diagnosticar lesión renal aguda o solo reduce la certeza?: **SOLO REDUCE LA CERTEZA, NO IMPIDE EL DIAGNÓSTICO.**
- ¿Queda resuelta únicamente la hiperpotasemia o también la lesión renal?: **LA HIPERPOTASEMIA ESTÁ RESUELTA, LA LESIÓN RENAL NO PUEDE CONSIDERARSE RESUELTA SIN CREATININA DE CONTROL.**
- Justificación o gold alternativo: 
- Confianza — alta / media / baja: **ALTA**

---



## Parte C — calidad general del conjunto



### C1 — imágenes recortadas

Los escaneos de cetoacidosis, celiaquía e insuficiencia cardiaca recortan
parte del margen izquierdo, aunque los hechos evaluados siguen visibles.

- ¿Pueden mantenerse como pruebas de documentos imperfectos?: **SI**
- ¿Deben añadirse versiones sin recorte antes de producción?: **NO**
- Motivo: **NO SE PIERDE INFROMACIÓN POR EL RECORTE DEL MARGEN IZQUIERDO.**



### C2 — paneles médicos esquemáticos

Las imágenes médicas de los tres casos mixtos son dibujos sintéticos. Sirven
para comprobar que el sistema conserva el visual, pero no para medir capacidad
de interpretación radiológica.

- ¿Está de acuerdo con esa limitación?: **si**
- ¿Exigiría imágenes mixtas reales antes de producción?: **NO** 
- Motivo: **me parece que así está bien por lo menos con los casos tratados por ahora.**



### C3 — equivalencias diagnósticas

Un juez automático rechazó una vez “neumonía bacteriana adquirida en la
comunidad, lóbulo inferior derecho” frente a “neumonía adquirida en la
comunidad”, pero la aceptó al repetir exactamente la evaluación.

- ¿Representan la misma entidad diagnóstica en este caso?: **SI**
- ¿Los desacuerdos inestables deben pasar a revisión humana?: **SI**
- Motivo: **PORQUE EL DESACUERDO ES INESTABLE Y NO SE BASA EN UN CAMBIO REAL DE ENTIDAD DIAGNÓSTICA.**



### C4 — dificultad de los casos

Los diez casos son deliberadamente claros y no representan toda la
incertidumbre de la práctica clínica.

- ¿Pueden validar la conservación de texto y el routing?: **SI**
- ¿Son suficientes para afirmar precisión clínica general?: **SI**
- ¿Qué controles difíciles añadirías?: **PRUEBAS MÁS DIFÍCILES ASÍ CÓMO POR EJEMPLO GOLDS DOBLES, GOLDS FENOTÍPICOS O MÁS ÁMPLIOS, DOS DIAGNÓSTICOS QUE COMPITAN...**

---



## Decisión final

Elige una opción:

- `APROBAR`: las etiquetas y golds pueden usarse sin cambios.
- `APROBAR CON CAMBIOS`: pueden usarse después de aplicar los cambios
enumerados.
- `CONSULTAR MÉDICO`: quedan decisiones clínicas que requieren adjudicación.
- `RECHAZAR`: existen problemas que invalidan este conjunto.
- Decisión: **APROBAR**
- Cambios obligatorios antes de usar el benchmark: **NO**
- Cuestiones que requieren médico: **EN B7:**¿La ausencia de biopsia obliga a cambiar el gold o solamente impide asignar una clase histológica?
- Comentario final: **FUNCIONA MUY BIEN**
- Firma o nombre del revisor: **DAVID ISLA MIRANDA**

