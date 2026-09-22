# Resultados del benchmark de imagen documental

Ejecuciones: 21 y 22 de septiembre de 2026.

Modelo de clasificación: `gpt-5.6-terra`, imagen con detalle bajo.
Producto: endpoint local completo de DxGPT, modelo `gpt56terra`.

## Clasificación y ruta

La ejecución inicial evaluó 45 imágenes con el manifest legacy:

- 32 imágenes documentales;
- 10 imágenes médicas reales revisadas de MedReaMM;
- 3 composiciones mixtas sintéticas.

Al adaptar el gold a V1 se detectó que las nueve variantes escaneo/foto/
manuscrito de los tres casos mixtos también contenían el panel médico. El gold
corregido usado por V1 es 23 documentales, 10 médicas y 12 mixtas. El generador
ya marca esa verdad upstream para todos los formatos.

Resultado:

- cobertura: 45/45, 100%;
- ruta correcta: 45/45, 100%;
- imágenes médicas enviadas a OCR: 0/10;
- imágenes documentales enviadas a OCR + imagen: 32/32;
- imágenes mixtas enviadas a OCR + imagen: 3/3;
- latencia media: 1,62 s; p95: 2,28 s.

Con las etiquetas legacy, la clasificación nominal tuvo 88,9% de exactitud.
Terra no reconoció ninguna
de las tres composiciones `mixed` como clase mixta, pero sí las trató como
documentales. Como ambas clases comparten la ruta `OCR + imagen original`, el
enrutado fue correcto. Esto indica que producción no necesita distinguir
`document_image` de `mixed`; necesita separar con seguridad:

```text
contiene documento legible → OCR + imagen original
imagen médica / desconocida → imagen original directa
```

Dos controles MedReaMM que inicialmente parecían falsos positivos eran tablas
de laboratorio, no imágenes clínicas. Se corrigió el gold tras inspeccionar
los archivos. Las etiquetas revisadas están en `medreamm_labels.yaml`.

### Comparación V1 con GPT-5.4-mini

El 22 de septiembre de 2026 se repitió solo la fase de clasificación sobre
las mismas 45 imágenes con el prompt y la política exactos de V1. En esta
política una imagen mixta debe ir a visión y nunca a OCR aislado.

- Terra: clase y ruta correctas 45/45; 0 rutas inseguras;
- GPT-5.4-mini: clase correcta 43/45 y ruta correcta 44/45;
- GPT-5.4-mini envió una composición mixta de embolia pulmonar a OCR aislado,
  por lo que no superó la puerta de seguridad;
- latencia media: 1,98 s con Terra frente a 2,33 s con GPT-5.4-mini;
- p95: 2,65 s con Terra frente a 3,10 s con GPT-5.4-mini;
- coste estimado de las 45 llamadas: 0,088 USD con Terra frente a 0,039 USD
  con GPT-5.4-mini, usando los precios configurados en el servidor.

GPT-5.4-mini fue aproximadamente un 56% más barato, pero fue más lento y tuvo
una ruta clínicamente insegura. V1 mantiene Terra.

## Baseline anterior a V1

Se ejecutaron 50 entradas: diez casos por cinco formatos. Las 50 peticiones
terminaron técnicamente, pero una respuesta HTTP correcta no implica que el
producto haya recuperado los datos o generado un diagnóstico.

| Formato | Hechos conservados | Cobertura diagnóstica |
|---|---:|---:|
| PDF nativo | 100% | 100% |
| PDF escaneado | 97,5% | 100% |
| Fotografía JPEG directa | 37,5% | 50% |
| Escaneo PNG directo | 10% | 10% |
| Manuscrito simulado directo | 10% | 10% |

El resultado confirma el problema: el flujo actual trata fotos y escaneos de
informes como imágenes médicas. En muchos casos devuelve `missing_patient_data`
sin recuperar valores, fechas ni negaciones. Document Intelligence conserva
casi todos los hechos cuando el mismo contenido llega como PDF.

El evaluador `strict_equivalence` encontró el gold en 27/50 casos:

- R@1: 22/50, 44%;
- cobertura: 27/50, 54%;
- posición media entre matches: 1,185;
- PDF nativo: cobertura 10/10, R@1 8/10;
- PDF escaneado: cobertura 10/10, R@1 8/10;
- fotografía directa: cobertura 5/10, R@1 4/10;
- escaneo PNG directo: cobertura y R@1 1/10;
- manuscrito simulado directo: cobertura y R@1 1/10.

El strict confirma la misma brecha que el recall de hechos. La coincidencia
literal del nombre top-1 no se usa como exactitud clínica: nombres equivalentes
como `Acute pulmonary embolism` frente a `Pulmonary embolism` no son cadenas
idénticas.

Durante esta ejecución se detectó que el juez LLM recibía casos sin ninguna
opción diagnóstica y reintentaba una respuesta imposible. El evaluador ahora
omite el juez cuando `ddx_details` está vacío.

## Validación end-to-end de V1

El 22 de septiembre se repitieron las mismas 50 entradas contra el servidor
local con V1 activa:

- 50/50 peticiones completadas;
- 30/30 imágenes siguieron la ruta esperada;
- 21/21 imágenes exclusivamente documentales usaron OCR con éxito;
- 9/9 imágenes mixtas conservaron la imagen y fueron a Terra vision;
- no hubo ninguna imagen mixta enviada a OCR aislado.

La ruta documental pura resolvió el problema:

- hechos conservados: 21/21, 100%;
- cobertura diagnóstica: 21/21, 100%;
- `strict_equivalence`: cobertura 21/21 y R@1 15/21.

Las imágenes mixtas siguieron siendo débiles con visión directa:

- hechos conservados: 2/9, 22,2%;
- cobertura diagnóstica: 2/9, 22,2%;
- `strict_equivalence`: cobertura y R@1 2/9.

En el conjunto completo, V1 obtuvo:

- hechos conservados y cobertura diagnóstica: 86%;
- `strict_equivalence`: cobertura 43/50, 86%; R@1 34/50, 68%;
- posición media entre matches: 1,302;
- latencia end-to-end media: 21,45 s; p95: 29,04 s.

Frente al baseline, strict subió de 27/50 a 43/50 en cobertura y de 22/50 a
34/50 en R@1. Por formato, V1 obtuvo cobertura/R@1 de 10/10 y 9/10 en PDF
nativo; 10/10 y 8/10 en PDF escaneado; 7/10 y 5/10 en escaneo PNG; 9/10 y
8/10 en fotografía; y 7/10 y 4/10 en manuscrito.

El coste total registrado aumentó de 0,518 USD a 0,828 USD porque V1 sí llegó
al diagnóstico en los 21 documentos-imagen, mientras el baseline terminaba
antes por falta de datos en 16 de ellos. El coste por caso cubierto por strict
se mantuvo prácticamente igual: 0,0192 USD en ambos flujos. En documentos
imagen, clasificación + OCR añadió unos 0,0035 USD por caso diagnosticado. La
latencia media de esos casos pasó de 15,38 s a 25,34 s.

## Experimento OCR + imagen en contenido mixto

Se compararon las nueve imágenes mixtas de V1 con una segunda ejecución que
añadió el OCR obtenido de cada imagen original y conservó esa misma imagen en
la llamada diagnóstica. Ningún texto superó 1.000 caracteres, por lo que no
intervino el resumen.

Visión directa:

- hechos y cobertura diagnóstica: 2/9, 22,2%;
- strict: cobertura 2/9 y R@1 2/9.

OCR de la imagen original + imagen original:

- hechos y cobertura diagnóstica: 9/9, 100%;
- strict: cobertura 9/9 y R@1 9/9;
- no se observó interferencia diagnóstica en esta muestra.

El flujo híbrido costó 0,237 USD en total, 0,0263 USD por caso, frente a 0,072
USD y 0,0080 USD con visión directa. La comparación bruta favorece a la ruta
que falla pronto; por caso cubierto, el híbrido fue más eficiente: 0,0263 USD
frente a 0,0361 USD. Incluyendo los 4,52 s medios de OCR, la latencia híbrida
fue 27,84 s de media y 35,00 s p95. Los dos únicos casos que visión directa sí
diagnosticó tardaron 26,81 s de media.

Una primera comprobación usando el PDF escaneado equivalente como fuente OCR
también obtuvo 9/9 de cobertura, pero solo R@1 7/9. La ejecución definitiva
anterior usa OCR de cada fotografía, escaneo o manuscrito original.

## Regresión del flujo híbrido implementado

El 22 de septiembre se ejecutaron de nuevo las nueve imágenes mixtas, esta vez
contra el flujo real del servidor y sin adjuntar el PDF usado como proxy:

- 9/9 peticiones completadas;
- 9/9 conservaron la imagen original para Terra;
- 9/9 ejecutaron OCR sobre la propia imagen y usaron el texto resultante;
- 36/36 hechos conservados y cobertura diagnóstica 9/9;
- latencia end-to-end media 28,18 s y p95 43,59 s;
- coste registrado 0,24081 USD, 0,02676 USD por caso: 0,01982 de
  clasificación, 0,01350 de OCR y 0,20749 de diagnóstico.

El primer strict obtuvo 8/9 por una decisión inestable del juez: rechazó
`Community-acquired bacterial pneumonia (right lower lobe)` frente al gold
`Community-acquired pneumonia`, pese a que el prompt acepta una forma más
específica que preserve el diagnóstico. Al repetir el mismo juez sobre el mismo
input etiquetado aceptó esa opción y obtuvo cobertura 9/9, R@1 8/9 y R@2 9/9.
Esta variación pertenece al evaluador, no a la salida de Terra, y debe
conservarse como advertencia.

La media de latencia queda 0,34 s por encima del experimento aislado anterior y
el coste por caso sube aproximadamente un 1,6%; ambos resultados son
consistentes con aquel experimento. Ningún texto superó 1.000 caracteres, por
lo que el resumen sigue cubierto por pruebas de integración, no por estas nueve
entradas.

## Decisión

La ruta V1 para imágenes exclusivamente documentales queda validada: OCR sin
imagen recupera los hechos y mejora de forma sustancial el diagnóstico.

La ruta mixta de visión directa es segura, pero insuficiente. La evidencia
favorece cambiarla a `OCR + imagen original`: recupera todos los hechos y
mejora strict sin perder el visual. La implementación y su regresión
end-to-end quedan completadas. Si el OCR falla o devuelve texto insuficiente,
se mantiene visión directa como fallback. El texto combinado sigue pasando por
el resumen actual cuando supera 1.000 caracteres.

Antes del rollout siguen haciendo falta la segunda revisión de etiquetas
MedReaMM y más controles médicos difíciles.
