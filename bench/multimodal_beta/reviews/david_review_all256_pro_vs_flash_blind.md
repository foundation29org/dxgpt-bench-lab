# Tarea clínica ciega — Pro vs Flash sin thinking en all_256_clean

**Estado:** New

**Responsable sugerido:** David o cualquier clínico que no haya visto
las respuestas automáticas antes de aplicar la regla.

**Contexto:** David ya terminó la ronda 2 original de MedReaMM. Esta es
una tarea nueva sobre `all_256_clean`, creada por discrepancias encontradas
después al comparar jueces.

## Objetivo

Decidir qué opción diagnóstica, si alguna, representa la misma enfermedad
que el diagnóstico de referencia. Solo se incluyen casos donde los jueces
automáticos dieron resultados finales distintos.

**Alcance:** 13 casos de 256. No hay que revisar los demás.


## Regla de equivalencia

- Aceptar sinónimos, abreviaturas, variantes ortográficas y una formulación
  más específica que conserve inequívocamente la enfermedad de referencia.
- Rechazar diagnósticos solo relacionados por síntomas, localización,
  mecanismo o tratamiento.
- Rechazar otra causa, complicación, precursor, subtipo incompatible o
  categoría amplia que cambie la entidad diagnóstica.
- Si el diagnóstico de referencia es ambiguo, incorrecto o no es una
  enfermedad, marcarlo explícitamente; no forzar una posición.

## Entregable

En cada caso:

1. marcar si el diagnóstico de referencia es válido;
2. escribir una sola posición `P1…Pn` o `0` si ninguna es equivalente;
3. justificar la decisión en una o dos frases;
4. marcar `consulta` si la regla no permite resolverlo.

## Casos

### 1. B110

**Complejidad:** C5

**Historia clínica**

> A 27-year-old woman presents to her primary care physician with new hair growth on her face and lower abdomen over the last month. She has started to develop pimples on her face and back over the last several months. Her last menstrual period was over 3 months ago and her periods have been irregular over the last year. She has been gaining weight recently. The patient has a medical history of obesity and prediabetes with a hemoglobin A1c of 6.0% last year. Her temperature is 98.5°F (36.9°C), pulse is 80/min, blood pressure is 139/88 mmHg, and respirations are 13/min. Cardiopulmonary exam is unremarkable, and the patient’s abdomen appears slightly distended but exhibits no tenderness to palpation. The patient’s face has coarse stubble along the jawline and on the upper lip, and there is similar hair along the midline of her lower abdomen. A pelvic exam reveals mild clitoromegaly, a normal anteverted uterus, and a large left adnexal mass that is mildly tender. Her laboratory test results are shown below: Hemoglobin: 13.9 g/dL Leukocyte count: 8,000 cells/mm^3 Platelet count: 142,000/mm^3 DHEAS: 73 ug/dL (Normal: 145-395 ug/dL) Testosterone: 256 ng/dL 17-hydroxyprogesterone: 214 ng/dL (Normal: < 200 ng/dL) Ultrasound findings are shown in Figure A. Which of the following is the most likely diagnosis in this patient?

**Diagnóstico de referencia:** Ovarian tumor

**Opciones diagnósticas**

1. Sertoli-Leydig cell tumor of the ovary
2. Ovarian steroid cell tumor, not otherwise specified
3. Polycystic ovary syndrome (PCOS)
4. Nonclassic congenital adrenal hyperplasia due to 21-hydroxylase deficiency

**Revisión clínica**

- Diagnóstico de referencia: `[ ] válido` `[ ] ambiguo` `[ ] incorrecto`
- Opción equivalente: `P__ / 0 / consulta`
- Justificación:

---

### 2. B126

**Complejidad:** C6

**Historia clínica**

> A 1-year-old girl is brought to a neurologist due to increasing seizure frequency over the past 2 months. She recently underwent a neurology evaluation which revealed hypsarrhythmia on electroencephalography (EEG) with a mix of slow waves, multifocal spikes, and asynchrony. Her parents have noticed the patient occasionally stiffens and spreads her arms at home. She was born at 38-weeks gestational age without complications. She has no other medical problems. Her medications consist of lamotrigine and valproic acid. Her temperature is 98.3°F (36.8°C), blood pressure is 90/75 mmHg, pulse is 94/min, and respirations are 22/min. Physical exam reveals innumerable hypopigmented macules on the skin and an irregularly shaped, thickened, and elevated plaque on the lower back. Which of the following is most strongly associated with this patient's condition?

**Diagnóstico de referencia:** Cardiac rhabdomyoma

**Opciones diagnósticas**

1. Tuberous sclerosis complex
2. West syndrome (infantile spasms syndrome)
3. Hypomelanosis of Ito

**Revisión clínica**

- Diagnóstico de referencia: `[ ] válido` `[ ] ambiguo` `[ ] incorrecto`
- Opción equivalente: `P__ / 0 / consulta`
- Justificación:

---

### 3. Q1103

**Complejidad:** C9

**Historia clínica**

> A 71-year-old man is brought to the emergency department by his daughter after she found him to be extremely confused at home. She says that he appeared to be fine in the morning; however, upon returning home, she found that he was slumped in his chair and was hard to arouse. She was worried that he may have taken too many medications and rushed him to the emergency department. His past medical history is significant for bipolar disorder and absence seizures. He does not smoke and drinks 4 alcoholic beverages per night on average. On physical exam, he is found to have a flapping tremor of his hands, pitting ankle edema, and gynecomastia. He does not appear to have any focal neurologic deficits. Which of the following lab findings would most likely be seen in this patient?

**Diagnóstico de referencia:** Increased prothrombin time due to liver dysfunction

**Opciones diagnósticas**

1. Hepatic encephalopathy due to decompensated cirrhosis
2. Alcohol-related cirrhosis with liver failure
3. Sedative or medication overdose
4. Uremic encephalopathy due to renal failure

**Revisión clínica**

- Diagnóstico de referencia: `[ ] válido` `[ ] ambiguo` `[ ] incorrecto`
- Opción equivalente: `P__ / 0 / consulta`
- Justificación:

---

### 4. Q3449

**Complejidad:** C9

**Historia clínica**

> A 6-year-old male presents to the pediatrician with seizures. His mother reports that the patient has had two seizures lasting about 30 seconds each over the last three days. She reports that the patient has previously had seizures a few times per year since he was 12 months of age. The patient’s past medical history is otherwise notable for intellectual disability. He rolled over at 14 months of age and walked at 24 months of age. The patient’s mother denies any family history of epilepsy or other neurologic diseases. The patient is in the 3rd percentile for height and the 15th percentile for weight. On physical exam, he has a happy demeanor with frequent smiling. The patient has strabismus and an ataxic gait accompanied by flapping of the hands. He responds intermittently to questions with one-word answers. This patient is most likely to have which of the following genetic abnormalities?

**Diagnóstico de referencia:** Paternal uniparental disomy of chromosome 15

**Opciones diagnósticas**

1. Angelman syndrome (maternal 15q11-q13 deletion or loss of maternal UBE3A expression)
2. Prader-Willi syndrome (paternal 15q11-q13 deletion or loss of paternal gene expression)
3. Rett syndrome (MECP2-related neurodevelopmental disorder)

**Revisión clínica**

- Diagnóstico de referencia: `[ ] válido` `[ ] ambiguo` `[ ] incorrecto`
- Opción equivalente: `P__ / 0 / consulta`
- Justificación:

---

### 5. Q4527

**Complejidad:** C9

**Historia clínica**

> Two weeks after undergoing allogeneic stem cell transplant for multiple myeloma, a 55-year-old man develops a severely pruritic rash, abdominal cramps, and profuse diarrhea. He appears lethargic. Physical examination shows yellow sclerae. There is a generalized maculopapular rash on his face, trunk, and lower extremities, and desquamation of both soles. His serum alanine aminotransferase is 115 U/L, serum aspartate aminotransferase is 97 U/L, and serum total bilirubin is 2.7 mg/dL. Which of the following is the most likely underlying cause of this patient's condition?

**Diagnóstico de referencia:** Graft-versus-host disease

**Opciones diagnósticas**

1. Acute graft-versus-host disease (acute GVHD)

**Revisión clínica**

- Diagnóstico de referencia: `[ ] válido` `[ ] ambiguo` `[ ] incorrecto`
- Opción equivalente: `P__ / 0 / consulta`
- Justificación:

---

### 6. Q6173

**Complejidad:** C9

**Historia clínica**

> A 12-year-old boy develops muscle weakness and pain, vomiting, seizures, and severe headache. Additionally, he presents with hemiparesis on one side of the body. A muscle biopsy shows 'ragged red fibers'. What is true about the mode of inheritance of the disease described?

**Diagnóstico de referencia:** Mitochondrial myopathy with ragged red fibers

**Opciones diagnósticas**

1. MELAS syndrome (Mitochondrial Encephalomyopathy, Lactic Acidosis, and Stroke-like Episodes)

**Revisión clínica**

- Diagnóstico de referencia: `[ ] válido` `[ ] ambiguo` `[ ] incorrecto`
- Opción equivalente: `P__ / 0 / consulta`
- Justificación:

---

### 7. Q6697

**Complejidad:** C9

**Historia clínica**

> A 48-year old man comes to the physician for the evaluation of an 8-month history of fatigue and profuse, watery, odorless diarrhea. He reports that he has had a 10.5-kg (23-lb) weight loss during this time. Physical examination shows conjunctival pallor and poor skin turgor. Laboratory studies show: Hemoglobin 9.8 g/dl Serum Glucose (fasting) 130 mg/dl K+ 2.5 mEq/L Ca2+ 12 mg/dl A CT scan of the abdomen with contrast shows a 3.0 × 3.2 × 4.4 cm, well-defined, enhancing lesion in the pancreatic tail. Further evaluation of this patient is most likely to show which of the following findings?"

**Diagnóstico de referencia:** Pancreatic Neuroendocrine Tumor

**Opciones diagnósticas**

1. VIPoma (vasoactive intestinal peptide-secreting pancreatic neuroendocrine tumor)
2. Carcinoid tumor with carcinoid syndrome
3. Gastrinoma (Zollinger-Ellison syndrome)
4. Somatostatinoma

**Revisión clínica**

- Diagnóstico de referencia: `[ ] válido` `[ ] ambiguo` `[ ] incorrecto`
- Opción equivalente: `P__ / 0 / consulta`
- Justificación:

---

### 8. S180

**Complejidad:** C7

**Historia clínica**

> The patient is a 7-year-old male who presents with symptoms of swelling and soft, non-painful masses in different areas of his body. His medical records indicate a history of recurrent infections and potential issues with his immune response. His skin seems pale and he occasionally exhibits signs of fatigue. Furthermore, he has experienced periodic bouts of diarrhea and weight loss. Upon closer examination, the masses appear to be filled with a clear, slightly yellowish fluid. His parents also reported occasional respiratory problems. Despite his symptoms, his cognitive development seems normal, with no signs of mental retardation. The patient's condition appears to be chronic, with symptoms having been present since his infancy. His family history is notable for similar symptoms in a distant relative.

**Diagnóstico de referencia:** Rare Lymphatic Malformation

**Opciones diagnósticas**

1. Hennekam lymphangiectasia-lymphedema syndrome
2. Primary intestinal lymphangiectasia (Waldmann disease)
3. Generalized lymphatic anomaly
4. Primary lymphedema with lymphatic malformations
5. Combined immunodeficiency with lymphatic dysplasia

**Revisión clínica**

- Diagnóstico de referencia: `[ ] válido` `[ ] ambiguo` `[ ] incorrecto`
- Opción equivalente: `P__ / 0 / consulta`
- Justificación:

---

### 9. T208

**Complejidad:** C7

**Historia clínica**

> Motivo de consulta: Paciente acude a consulta para ser diagnosticado Anamnesis: Paciente Mujer de 1 años. Ha pasado bronquiolitis 20 de Noviembre 2022, se ha quedado con mocos nasales y esta mañana han notado legañas en los ojos  e inflamación de los ojos. No fiebre , Tiene tos flemosa. Hace deposiciones diarreicas 4 por días , fétidas . Inapetencia de  varios días. Le huele ma el pis  Han suspendido el Ventolín . Antecedentes: No hay antecedentes Exploracion: Buen estado general. Normocoloreado. Bien hidratado, nutrido y perfundido. No exantemas ni petequias. ORL: Faringe hiperémica congestiva y folicular, no exudados-. Conjuntivitis bilateralññ.  Oídos; derecho normal, izquierdo; normal.  Respiratorio: BVB,  no signos de dificultad respiratoria escasos sibilantes en regiones basales anteriores , leve alargamiento espiratorio . ACV; corazón rítmico, no soplos. ABD: blando, depresible, no masas ni visceromegalias. NRL: Ausencia de signos meníngeos. No focalidad Pruebas clinicas: -Rapidas: Frecuencia cardiaca: 136.0 Temperatura: 36.7 Saturación de oxígeno: 97.0 -Complementarias: Sistemático TEC Densidad 1,010 pH 8,0 Leucocitos 100/µl Nitritos Negativo Proteinas Negativo Glucosa Normal  Urobilinógeno Normal Cuerpos cetónicos Negativo Bilirrubina Negativo Eritrocitos 10/µl Estudio de sedimento; No se observa nada anormal.  Pendente urocultivo.

**Diagnóstico de referencia:** Persistent bronchiolitis; Acute gastroenteritis; Acute conjunctivitis

**Opciones diagnósticas**

1. Adenoviral pharyngoconjunctival infection
2. Viral upper respiratory tract infection with mild viral-induced wheezing
3. Acute conjunctivitis, likely viral
4. Possible urinary tract infection
5. Acute viral gastroenteritis

**Revisión clínica**

- Diagnóstico de referencia: `[ ] válido` `[ ] ambiguo` `[ ] incorrecto`
- Opción equivalente: `P__ / 0 / consulta`
- Justificación:

---

### 10. T34

**Complejidad:** C6

**Historia clínica**

> Motivo de consulta: Paciente acude a consulta para ser diagnosticado Anamnesis: Paciente Hombre de 48 años. Varón de 47 años que acude a Urgencias por cuadro de  3 semanas de evolución consistente en persistencia de dolor costal derecho y en hipocondrio derecho que no controla con analgesicos vía oral y que no le permite estar tumbado ni apoyarse en dicha zona. Valorado por otro lado por Traumatología por dolor a nivel de escapula derecha con TAC que aporta (y dejo descrito en exploraciones complementarias). Asocia pérdida de peso (no cuantificada) desde hace 1-2 meses. No traumatismos previos. No disnea ni dolor torácico. No dolor abdominal, no nauseas ni vomitos. No alteraciones del habito intestinal. No otra sintomatología a la anamnesis por organos y aparatos. Vacunación por COVID-19 Antecedentes: No hay antecedentes Exploracion: Buen estado general. Normohidratado, normoperfundido, normocoloreado. AC: rítmico, no ausculto soplos AP: MVC, sin ruidos sobreañadidos´ Dolor a nivel escapular derecho. Dolor intenso a la palpación a nivel costal inferior derecho. Abdomen blando y depresible. Dolor a la palpació superficial y profunda a nivel de hipocondrio derecho. No signos de irritación peritoneal. No se palpan masas ni visceromegalias. RHA presentes. PPRB negativa. Pruebas clinicas: -Rapidas: Tensión arterial: 151.0 / 95.0 Frecuencia cardiaca: 75.0 Temperatura: 36.6 Saturación de oxígeno: 97.0 -Complementarias: TAC hombro derecho (Noviembre 2022). :Apreciamos una alteración en la densidad ósea que sugiere un patrón moteado, con pequeñosfocos líticos, que afectan a la espina de la escápula y también parcialmente al cuerpo de laescápula, con discreta insuflación y pequeños focos líticos de la cortical, así como mínimareacción perióstica. Dado el grupo de edad del paciente y las características de la lesión, nosobligan a descartar como primera posibilidad la de una lesión neoproliferativa hematológica (mieloma, linfoma?). No podemos descartar otras posibilidades. A correlacionar con la clínica yanalítica. A valorar clínicamente ampliar estudio mediante filiación histológica.Se ha incluido parcialmente la cúpula del lóbulo hepático derecho, donde parece identificarse unahipodensidad, que sugiere la presencia una lesión focal hepática de aproximadamente 15 mm dediámetro, indeterminada. A valorar mediante ecografía.Sin otros hallazgos reseñables

**Diagnóstico de referencia:** Shoulder lesion; Lymphoproliferative process

**Opciones diagnósticas**

1. Multiple myeloma
2. Primary bone lymphoma or secondary osseous lymphoma
3. Bone metastasis from an occult solid-organ malignancy
4. Hepatocellular carcinoma with bone metastasis
5. Primary malignant bone tumor of the scapula (such as chondrosarcoma or osteosarcoma)

**Revisión clínica**

- Diagnóstico de referencia: `[ ] válido` `[ ] ambiguo` `[ ] incorrecto`
- Opción equivalente: `P__ / 0 / consulta`
- Justificación:

---

### 11. T385

**Complejidad:** C7

**Historia clínica**

> Motivo de consulta: Paciente acude a consulta para ser diagnosticado Anamnesis: Paciente Mujer de 58 años. Según refiere la paciente presenta en horas de la noche del día de la fecha, mientras se encontraba en su domicilio, episodio de cefalea bifrontal acompañado de mareos, nauseas y vómitos. Se controla la TA en domicilio presentando cifras entorno a 220/110. Acude al centro de salud donde le administran tto SL (captopril?) indicándose que acuda al hospital para valoración.- Antecedentes: No hay antecedentes Exploracion: Lúcida, reactiva, buen estado general. Adecuada coloración e hidratación de piel y mucosas. Deambula por sus medios sin alteración de la marcha, disnea ni taquipnea. R1R2 en 4 focos, normofonéticos. Silencios libres. No signos de insuficiencia cardíaca. Adecuada perfusión periférica. Eupneica. Habla fluida. Buena mecánica ventilatoria. Buena entrada de aire bilateral sin ruidos agregados. Tolera decúbito a 0º. No nistagmus ni dismetrías. No déficit motor en extremidades. Contractura muscular paravertebral cervical bilateral, dolorosa a la palpación; no apofisalgias. Pruebas clinicas: -Rapidas: Tensión arterial: 202.0 / 110.0 Frecuencia cardiaca: 103.0 Temperatura: 36.6 Saturación de oxígeno: 95.0 -Complementarias: Hto: 40.6%; Hb: 14.1 gr; GB: 8500 (N: 53%; L: 41%); Plaq: 219000; Creat: 0,74; Glu: 100; Na: 140; K: 3,3. G. Venosa: 7.45 / 39 / 32 / 27.4 / 3.5 / 66%. Lactato: 2,1.- EKG: Ritmo sinusal, 97x', PR 222 mseg. HBAI. TCIV. No alt St-T. QTc. 483 mseg.-

**Diagnóstico de referencia:** Cervicogenic headache; Hypertensive crisis

**Opciones diagnósticas**

1. Crisis hipertensiva sin daño agudo de órgano diana (urgencia hipertensiva)
2. Cefalea tensional asociada a contractura cervical
3. Encefalopatía hipertensiva
4. Evento cerebrovascular de circulación posterior o accidente isquémico transitorio

**Revisión clínica**

- Diagnóstico de referencia: `[ ] válido` `[ ] ambiguo` `[ ] incorrecto`
- Opción equivalente: `P__ / 0 / consulta`
- Justificación:

---

### 12. T5

**Complejidad:** C6

**Historia clínica**

> Motivo de consulta: Paciente acude a consulta para ser diagnosticado Anamnesis: Paciente Mujer de 8 años. Niña diagnosticada de Fariingoamigdalitis hace tres días en tratamiento con Benoral, acude con dolor en región pre-esternal inteermitente desde hace 12 horas, dolor abdominal en región periumbilical-epigástrica que desapareció, tos escasa, afebril en los últimos dos días. Antecedentes: No hay antecedentes Exploracion: BEG, coloración normal de piel y mucosas, no exantema. ACP: Buena ventilación pulmonar sin ruidos sobreañadidos. Abdomen blando y depresible sin visceromegalias ni masas. ORL: Orofaringe hiperémica, tímpanos normales.  SN: Normal. Pruebas clinicas: -Rapidas: Frecuencia cardiaca: 145.0 Temperatura: 37.0 Saturación de oxígeno: 99.0 -Complementarias: Rx tórax PA normal. ECG normal.

**Diagnóstico de referencia:** Acute tonsillitis; Mild osteochondritis

**Opciones diagnósticas**

1. Viral pharyngotonsillitis
2. Musculoskeletal chest pain (precordial catch syndrome or chest wall pain)
3. Gastroesophageal reflux disease or acute gastritis
4. Anxiety-related tachycardia with functional chest pain

**Revisión clínica**

- Diagnóstico de referencia: `[ ] válido` `[ ] ambiguo` `[ ] incorrecto`
- Opción equivalente: `P__ / 0 / consulta`
- Justificación:

---

### 13. T795

**Complejidad:** C7

**Historia clínica**

> Motivo de consulta: Paciente acude a consulta para ser diagnosticado Anamnesis: Paciente Mujer de 95 años. Mujer de 94 años que acude a Urgencias por cuadro de 3 días de evolución consistente en congestión nasal asociado a afonia y tos seca. Su familiar refiere en el día de ayer mayor desorientación y alucinaciones nocturnas y refiere durante estos días algun atragantamiento a la hora de comer así como 2 epsiodios de apistaxis autolimitadas. Afebril en todo momento. No disnea ni dolor torácico. No dolor abdominal, no nauseas ni vómitos. No alteraciones del habito intestinal. No aumento de perimetro de MMII. No clínica miccional ni orina maloliente. No otra sintomatología a la anamnesis por organos y aparatos. Vacunación por COVID-19 (3 dosis) Antecedentes: No hay antecedentes Exploracion: Normohidratada, normoperfundida, normocoloreada.  AC: rítmica, no ausculto soplos AP: MVC, crepitantes en base izquierda ORL: orofaringe normal, no sangrado posterior, uvula normal Abdomen blando y depresible. No doloroso a la palpación. No signos de irritación peritoneal. No se palpan masas ni visceromegalias. RHA presentes.  EEII: No edemas. No signos de TVP. NEURO: Glasgow 15/15. Consciente y orientada en espacio y persona. Desorientada en tiempo. Lenguaje coherente y articulado. Pupilas isocóricas y normorreactivas. No observo nistagmo. DPAR conservado. MOEs sin restrcciones. Resto de pares craneales normales. Fuerza y sensibilidad conservadas a todos los niveles. No dismetrías ni disdiadocinesias. Romberg y Barany negativos. Marcha cautelosa. Signos meníngeos negativos. Pruebas clinicas: -Rapidas: Tensión arterial: 111.0 / 66.0 Frecuencia cardiaca: 72.0 Temperatura: 36.3 Saturación de oxígeno: 96.0 -Complementarias: Test de antigeno: negativo ANALÍTICA HEMOGRAMA Hemograma TEC Hematíes 4,59 x10e6/µL (4.10 - 5.90) Hemoglobina 11,90 g/dL (12.30 - 15.30) Hematocrito 39,20 % (35.00 - 47.00) Volumen Corpuscular Medio 85,40 fL (80.00 - 99.00) Hemoglobina Corpuscular Media 25,90 pg (28.00 - 33.00) Conc. Hemoglobina Corpuscular Media 30,40 g/dL (33.00 - 36.00) Coeficiente de anisocitosis 12,10 % (11.50 - 14.50) Leucocitos 7,21 x10e3/µL (4.40 - 11.30) Neutrófilos 5,15 x10e3/µL (1.50 - 7.50) Neutrófilos % 71,30 % (40.00 - 75.00) Linfocitos 0,79 x10e3/µL (1.20 - 3.40) Linfocitos % 11,00 % (20.00 - 50.00) Monocitos 1,23 x10e3/µL (0.10 - 0.80) Monocitos % 17,10 % (2.00 - 8.00) Eosinófilos 0,02 x10e3/µL (0.10 - 0.60) Eosinófilos % 0,30 % (2.00 - 7.00) Basófilos 0,02 x10e3/µL (0.00 - 0.30) Basófilos % 0,30 % (0.00 - 3.00) Recuento de plaquetas 186,00 x10e3/µL (150.00 - 450.00) Volumen plaquetar medio 10,60 fL (7.40 - 10.40) COAGULACION BASICA Actividad de Protrombina 59.00 % (70.00 - 120.00) TEC Tiempo de Protrombina 16.40 s (9.90 - 14.20) TEC INR 1.30 (0.80 - 1.20) TEC Tiempo de Cefalina (APTT) 31.30 s (25.10 - 38.00) GGM BIOQUIMICA GENERAL Glucosa 95.5 mg/dL (70.0 - 105.0) TEC Creatinina 0.75 mg/dL (0.50 - 0.90) GGM Urea 48.4 mg/dL (5.0 - 71.0) TEC Sodio 136.3 mmol/L (135.0 - 145.0) TEC Potasio 4.19 mmol/L (3.50 - 5.10) TEC GOT (AST) 15.0 U/L <33 GGM GPT (ALT) 9.7 U/L <33 GGM Proteina C Reactiva 65.81 mg/L <5 TEC

**Diagnóstico de referencia:** Lower respiratory infection; Hypoactive confusional syndrome

**Opciones diagnósticas**

1. Community-acquired pneumonia
2. Aspiration pneumonia
3. Acute viral upper respiratory tract infection (viral rhinitis/laryngitis)
4. Delirium secondary to acute infection
5. COVID-19

**Revisión clínica**

- Diagnóstico de referencia: `[ ] válido` `[ ] ambiguo` `[ ] incorrecto`
- Opción equivalente: `P__ / 0 / consulta`
- Justificación:

---
