# Línea «The patient is in <país>» — resultados (2026-10-08)

Modelo `gpt56terra`, endpoint real `/api/diagnose` (servidor local con el código
nuevo, `response_mode: direct`). Un brazo = país enviado; `none` = sin país
(prompt idéntico al de producción actual). Ver `../README.md` para reproducir.

## 1. Sonda de enfermedades endémicas (`endemic`)

**Qué es:** 33 viñetas escritas por nosotros (14 clásicas, 14 vagas, 5 controles),
2 repeticiones por caso y brazo. **No es un benchmark validado**: sirve para
comprobar que el mecanismo funciona, no para estimar un porcentaje de mejora en
producción. Ninguna viñeta menciona país ni viajes. «Acierto» = el diagnóstico
esperado (regex) aparece en esa posición.

Brazos: `none`, `ES` (control negativo: país donde estas enfermedades no son típicas, con la
salvedad de la leishmaniasis visceral, que sí existe en España) y el/los
países donde la enfermedad es frecuente («endémico»; 34 ejecuciones por grupo
porque algunas enfermedades tienen dos países).

| Grupo | Brazo | Ejecuciones | Esperado en #1 | Esperado en top 5 |
|---|---|---|---|---|
| clásicas | none | 28 | 24 (86 %) | 28 (100 %) |
| clásicas | ES | 28 | 24 (86 %) | 25 (89 %) |
| clásicas | país endémico | 34 | 34 (100 %) | 34 (100 %) |
| **vagas** | none | 28 | 13 (46 %) | 18 (64 %) |
| **vagas** | ES | 28 | 12 (43 %) | 18 (64 %) |
| **vagas** | país endémico | 34 | 28 (82 %) | 34 (100 %) |
| controles | none | 10 | 10 (100 %) | 10 (100 %) |
| controles | ES | 10 | 10 (100 %) | 10 (100 %) |
| controles | IN / NG | 20 | 20 (100 %) | 20 (100 %) |

Lectura:

- Con la descripción **vaga** (síntomas sin los rasgos que delatan la
  enfermedad) el país endémico pasa el diagnóstico esperado de #1 en 46 % a 82 %
  y de top 5 en 64 % a 100 %. Sin país, la leptospirosis, el Chagas, la
  esquistosomiasis y el tifus de los matorrales no aparecen ni en el top 5
  (salen gripe, insuficiencia cardiaca, nefropatía IgA, dengue); con el país
  correcto salen en #1 (Chagas, esquistosomiasis, cólera, leishmaniasis) o en
  top 5.
- Con la descripción **clásica** casi no hay margen: el modelo ya acierta sin
  país (86 % en #1). El efecto sólo se ve en esquistosomiasis (none: 4.º y 5.º;
  NG: 1.º y 1.º), Chagas y tifus de los matorrales.
- `ES` ≈ `none`: añadir un país que no es endémico no mueve nada, es decir, no
  es la mera presencia de la frase lo que produce el cambio.
- Controles (5 enfermedades comunes × IN/NG/ES): el país no las desplaza (todas
  en #1 en todos los brazos). Muestra pequeña.
- Hay varianza entre repeticiones (p. ej. `malaria-vague`/ES: #1 y #3; Chagas
  clásico/none: #2 y #1). Por eso 2 repeticiones y no una.

Límites: el brazo endémico es el escenario favorable (país correcto y enfermedad
típica). No mide el caso desfavorable en que el país no tiene relación con el
paciente (viajero, país mal detectado); eso lo cubre sólo parcialmente la
sección 2.

## 2. Regresión sobre casos clínicos reales (`regression`)

100 casos de texto de MedReaMM `pilot100`, enviados con `none`, `IN` e `NG`
(ninguno es de India ni de Nigeria, así que el país es un dato irrelevante o
engañoso para ellos). Puntuación: juez `strict_equivalence`
(`evaluate_v4.py`, `gemini-2.5-pro`). Comparación emparejada con
`analyze_regression.py`.

| Brazo | R@1 | R@3 | R@5 | Sin acierto |
|---|---|---|---|---|
| none | 51 | 63 | 67 | 33 |
| IN | 51 | 66 | 69 | 31 |
| NG | 51 | 62 | 68 | 32 |

Diferencias emparejadas frente a `none` (casos que ganan / casos que pierden;
McNemar exacto):

| Brazo | R@1 | R@3 | R@5 |
|---|---|---|---|
| IN | +5 / −5 (p = 1,00) | +5 / −2 (p = 0,45) | +4 / −2 (p = 0,69) |
| NG | +5 / −5 (p = 1,00) | +4 / −5 (p = 1,00) | +3 / −2 (p = 1,00) |

Lectura: **no hay degradación detectable** en casos no relacionados con el país.
El R@1 es idéntico (51/100) en los tres brazos. El rango juzgado cambia en
18–19 de 100 casos, pero en ambos sentidos y en cantidad equilibrada.

Límite importante: no repetimos `none` dos veces, así que no medimos el ruido
propio del modelo y del juez. Ese 18–19 % de casos que se mueven es, en buena
parte, ruido de ejecución y no efecto del país; con n = 100 sólo se descartan
degradaciones grandes (varios puntos de R@1), no pequeñas.

## Conclusión

La línea hace lo que se pretende (empuja hacia enfermedades endémicas cuando la
descripción es inespecífica) sin que se vea coste en casos no relacionados ni en
enfermedades comunes. Lo que no se ha comprobado: pacientes que no están en su
país de residencia o con el país mal detectado, y distintos modelos. Si el país
es incorrecto, el modelo recibe un dato falso; de ahí la ventana de
confirmación en la web cuando la detección es incierta.
