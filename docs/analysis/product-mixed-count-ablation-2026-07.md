# Mini-set mixto: ablacion del numero de diagnosticos

## Alcance

Prueba cualitativa sobre `product_mixed_24` con `gpt-5.4-mini low`. El prompt de produccion `juanjo_classic_v2` no se modifica. Se ejecutaron tres copias independientes:

| Variante | Regla | Casos validos | Tiempo medio |
|---|---|---:|---:|
| Baseline | `N` sin fijar | 24/24 | 4.3 s |
| Exact 4 | exactamente 4 diagnosticos | 24/24 | 3.8 s |
| Exact 5 | exactamente 5 diagnosticos | 24/24 | 4.6 s |

## Resultado

Fijar un numero exacto controla correctamente el tamaño de la lista, pero no resuelve el problema de texto mixto. En los cuatro casos de solo antecedentes, fuerza diagnósticos y síntomas que no estaban presentes:

- `P013` (`diabetes and hypertension`): las tres variantes repiten las condiciones declaradas; las variantes de cuatro y cinco añaden diagnósticos no solicitados.
- `P014` (`ME/CFS and fibromyalgia`): la variante de cuatro añade hipotiroidismo y depresión; la de cinco también amplía el diferencial.
- `P015` (`I have asthma and use an inhaler`): la variante de cuatro añade COPD, rinitis y broncoconstricción; la de cinco añade además asma alérgica y disfunción de cuerdas vocales.
- `P016` (`high blood pressure on amlodipine`): las variantes exactas tratan la condición y el tratamiento como síntomas y rellenan con diagnósticos de hipertensión.

El comportamiento se produce porque todas las variantes siguen obligando a devolver un diferencial aunque no exista una queja activa.

## Decision

No adoptar ni `exactly 4` ni `exactly 5` como cambio aislado de producción.

La siguiente prueba es la Variante A de clasificación interna:

- separar silenciosamente hallazgos actuales de antecedentes, tratamientos y contexto;
- usar antecedentes y fármacos para modular la probabilidad;
- prohibir antecedentes y datos ausentes en arrays de síntomas;
- permitir una respuesta vacía cuando no hay síntoma, signo o hallazgo activo.

La cantidad de diagnósticos se reevaluará después como un límite máximo, no como una obligación fija.

## Variante mínima de contexto

Se probó una versión corta del prompt que presenta el texto como datos del paciente y añade solo dos reglas: antecedentes y medicación son contexto, no síntomas; los arrays de síntomas solo pueden incluir datos presentes.

| Resultado | Observación |
|---|---|
| JSON válido | 24/24 |
| Tiempo medio | 2.9 s |
| `P005` — dolor perineal + ME/CFS/policitemia | Corrige los arrays: solo incluye dolor perineal |
| `P006` — dolor torácico + diabetes/hipertensión | Corrige los arrays: solo incluye dolor torácico |
| `P009` — estatinas + mialgia | Corrige los arrays: solo incluye mialgia |
| `P010` — enalapril + tos | Sigue incluyendo enalapril como síntoma en el primer candidato |
| `P013`–`P016` — solo antecedentes | Sigue repitiendo las condiciones conocidas como diagnósticos |

La versión mínima es una mejora prometedora en entradas mixtas con un síntoma activo y no impone abstención. No resuelve las entradas sin queja activa: decidir si el producto debe pedir más información, devolver una respuesta sin diferencial o seguir ofreciendo hipótesis a partir de antecedentes es una decisión de UX y seguridad, no una métrica de ranking.

## Regresión completa: Terra low

La frase mínima se evaluó también con `gpt-5.6-terra low` en `all_256_clean` (`n=256`), manteniendo juez, parámetros y dataset constantes frente a Terra histórico.

| Prompt | Avg pos | R@1 | R@3 | R@5 / coverage | Latencia |
|---|---:|---:|---:|---:|---:|
| Histórico | **1.382** | **74.6%** | **94.9%** | 98.1% (251/256) | 6.9 s |
| Contexto mínimo | 1.482 | 71.1% | 93.0% | 98.1% (251/256) | 7.3 s |

La adición conserva cobertura, pero empeora `avg_pos` en `+0.100`, R@1 en `-3.5pp`, R@3 en `-1.9pp` y latencia en `+6%`.

**Decisión:** no adoptar el encuadre mínimo en producción. Mantener `juanjo_classic_v2.txt` como prompt histórico y usar el mini-set para descubrir problemas de producto, no para aceptar cambios de prompt sin una regresión completa favorable.

## Regresión completa: hasta cuatro diagnósticos

Se probó otra modificación aislada con Terra: conservar el prompt histórico, pero pedir hasta cuatro diagnósticos ordenados por probabilidad. La intención era limitar diferenciales extensos sin forzar cuatro cuando el caso justificara menos.

| Prompt | Avg pos | R@1 | R@3 | R@5 / coverage | Latencia |
|---|---:|---:|---:|---:|---:|
| Histórico | **1.382** | **74.6%** | **94.9%** | 98.1% (251/256) | 6.9 s |
| Hasta 4 | 1.462 | 69.9% | 94.1% | 98.1% (251/256) | 8.4 s |

La modificación empeora `avg_pos` en `+0.080`, R@1 en `-4.7pp`, R@3 en `-0.8pp` y latencia en `+22%`, sin ganar cobertura.

**Decisión:** no adoptar un límite de cuatro diagnósticos. La configuración histórica de Terra sigue siendo la mejor para priorización diagnóstica.
