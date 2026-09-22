# Resultados del benchmark de imagen documental

Ejecución: 21 de septiembre de 2026.

Modelo de clasificación: `gpt-5.6-terra`, imagen con detalle bajo.
Producto: endpoint local completo de DxGPT, modelo `gpt56terra`.

## Clasificación y ruta

Se evaluaron 45 imágenes:

- 32 imágenes documentales;
- 10 imágenes médicas reales revisadas de MedReaMM;
- 3 composiciones mixtas sintéticas.

Resultado:

- cobertura: 45/45, 100%;
- ruta correcta: 45/45, 100%;
- imágenes médicas enviadas a OCR: 0/10;
- imágenes documentales enviadas a OCR + imagen: 32/32;
- imágenes mixtas enviadas a OCR + imagen: 3/3;
- latencia media: 1,62 s; p95: 2,28 s.

La clasificación nominal tuvo 88,9% de exactitud. Terra no reconoció ninguna
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

## Flujo de producto actual

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

## Decisión

La evidencia justifica implementar, detrás de feature flag:

1. clasificador visual conservador;
2. `document_image` o `mixed` con confianza >= 0,90: extraer texto y conservar
   la imagen original para Terra;
3. `medical_image`, `unknown` o error: Terra directo;
4. nunca sustituir la imagen por OCR.

No justifica todavía activar la función en producción. El piloto médico solo
incluye diez imágenes y sus etiquetas tienen una única revisión. Antes del
rollout hacen falta una segunda revisión, más controles médicos difíciles y
una comparación end-to-end de `OCR + imagen` frente a imagen directa.
