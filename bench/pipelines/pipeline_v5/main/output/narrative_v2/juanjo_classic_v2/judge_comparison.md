# Comparación de jueces sobre `narrative_v2`

Mismas listas de diagnósticos; solo cambia el juez. Referencia: `gemini-2.5-pro`. Modelos: 6.

## R@1 estricta · Casos reales (`live`+`urg`, 210)

| Modelo | `gemini-2.5-pro` | `gemini-3.8-flash` | `gemini-2.5-flash` | `claude-opus-5-5` |
|---|---:|---:|---:|---:|
| gpt-6.1-sol | 58,1 % | 60,5 % | 56,7 % | 59,0 % |
| claude-opus-5 | 54,3 % | 55,2 % | 56,2 % | 53,3 % |
| gpt-5.6-terra | 51,9 % | 55,2 % | 52,9 % | 51,4 % |
| gpt-6.1-terra | 50,0 % | 53,8 % | 50,0 % | 51,0 % |
| gemini-3.1-pro | 45,7 % | 46,2 % | 44,8 % | 46,2 % |
| gpt-5.4-mini | 41,9 % | 43,8 % | 42,9 % | 42,9 % |
| **Orden** | gpt-6.1-sol > claude-opus-5 > gpt-5.6-terra > gpt-6.1-terra > gemini-3.1-pro > gpt-5.4-mini | gpt-6.1-sol > claude-opus-5 > gpt-5.6-terra > gpt-6.1-terra > gemini-3.1-pro > gpt-5.4-mini | gpt-6.1-sol > claude-opus-5 > gpt-5.6-terra > gpt-6.1-terra > gemini-3.1-pro > gpt-5.4-mini | gpt-6.1-sol > claude-opus-5 > gpt-5.6-terra > gpt-6.1-terra > gemini-3.1-pro > gpt-5.4-mini |
| Kendall tau con la referencia | 1 | 1,00 | 1,00 | 1,00 |

## R@5 estricta · Casos reales (`live`+`urg`, 210)

| Modelo | `gemini-2.5-pro` | `gemini-3.8-flash` | `gemini-2.5-flash` | `claude-opus-5-5` |
|---|---:|---:|---:|---:|
| gpt-6.1-sol | 74,8 % | 76,7 % | 73,8 % | 75,2 % |
| claude-opus-5 | 71,9 % | 71,4 % | 73,3 % | 69,0 % |
| gpt-5.6-terra | 72,9 % | 73,8 % | 71,9 % | 70,5 % |
| gpt-6.1-terra | 66,2 % | 67,6 % | 64,8 % | 65,2 % |
| gemini-3.1-pro | 60,5 % | 59,5 % | 57,6 % | 59,5 % |
| gpt-5.4-mini | 61,4 % | 65,7 % | 62,9 % | 63,3 % |
| **Orden** | gpt-6.1-sol > gpt-5.6-terra > claude-opus-5 > gpt-6.1-terra > gpt-5.4-mini > gemini-3.1-pro | gpt-6.1-sol > gpt-5.6-terra > claude-opus-5 > gpt-6.1-terra > gpt-5.4-mini > gemini-3.1-pro | gpt-6.1-sol > claude-opus-5 > gpt-5.6-terra > gpt-6.1-terra > gpt-5.4-mini > gemini-3.1-pro | gpt-6.1-sol > gpt-5.6-terra > claude-opus-5 > gpt-6.1-terra > gpt-5.4-mini > gemini-3.1-pro |
| Kendall tau con la referencia | 1 | 1,00 | 0,87 | 1,00 |

## R@1 estricta · Total (300)

| Modelo | `gemini-2.5-pro` | `gemini-3.8-flash` | `gemini-2.5-flash` | `claude-opus-5-5` |
|---|---:|---:|---:|---:|
| gpt-6.1-sol | 67,0 % | 68,0 % | 66,0 % | 67,3 % |
| claude-opus-5 | 64,7 % | 65,3 % | 66,0 % | 63,7 % |
| gpt-5.6-terra | 61,3 % | 64,0 % | 61,7 % | 61,0 % |
| gpt-6.1-terra | 59,3 % | 62,0 % | 59,0 % | 59,7 % |
| gemini-3.1-pro | 57,0 % | 57,7 % | 56,3 % | 57,3 % |
| gpt-5.4-mini | 54,7 % | 56,3 % | 55,7 % | 55,3 % |
| **Orden** | gpt-6.1-sol > claude-opus-5 > gpt-5.6-terra > gpt-6.1-terra > gemini-3.1-pro > gpt-5.4-mini | gpt-6.1-sol > claude-opus-5 > gpt-5.6-terra > gpt-6.1-terra > gemini-3.1-pro > gpt-5.4-mini | gpt-6.1-sol > claude-opus-5 > gpt-5.6-terra > gpt-6.1-terra > gemini-3.1-pro > gpt-5.4-mini | gpt-6.1-sol > claude-opus-5 > gpt-5.6-terra > gpt-6.1-terra > gemini-3.1-pro > gpt-5.4-mini |
| Kendall tau con la referencia | 1 | 1,00 | 1,00 | 1,00 |

## R@5 estricta · Total (300)

| Modelo | `gemini-2.5-pro` | `gemini-3.8-flash` | `gemini-2.5-flash` | `claude-opus-5-5` |
|---|---:|---:|---:|---:|
| gpt-6.1-sol | 81,3 % | 82,3 % | 80,3 % | 81,0 % |
| claude-opus-5 | 78,7 % | 78,3 % | 79,7 % | 76,3 % |
| gpt-5.6-terra | 78,3 % | 79,7 % | 78,0 % | 76,7 % |
| gpt-6.1-terra | 73,7 % | 75,0 % | 72,3 % | 73,0 % |
| gemini-3.1-pro | 68,7 % | 68,0 % | 66,7 % | 67,7 % |
| gpt-5.4-mini | 70,0 % | 73,3 % | 71,3 % | 71,3 % |
| **Orden** | gpt-6.1-sol > claude-opus-5 > gpt-5.6-terra > gpt-6.1-terra > gpt-5.4-mini > gemini-3.1-pro | gpt-6.1-sol > gpt-5.6-terra > claude-opus-5 > gpt-6.1-terra > gpt-5.4-mini > gemini-3.1-pro | gpt-6.1-sol > claude-opus-5 > gpt-5.6-terra > gpt-6.1-terra > gpt-5.4-mini > gemini-3.1-pro | gpt-6.1-sol > gpt-5.6-terra > claude-opus-5 > gpt-6.1-terra > gpt-5.4-mini > gemini-3.1-pro |
| Kendall tau con la referencia | 1 | 0,87 | 1,00 | 0,87 |

## Coincidencia con la referencia

Por caso: ¿coinciden en si hay acierto estricto en P1 (o en el top 5)? Por opción: ¿ponen la misma nota 2/1/0, y coinciden en «es un 2 o no» (lo único que usa la nota estricta)? «Más nota» = el otro juez puntúa más alto.

| Juez | Sobre | Mismo veredicto P1 | Mismo veredicto top 5 | Misma nota 2/1/0 | Kappa 2/1/0 | Mismo «2 o no» | Kappa «2 o no» | Más nota | Menos nota | Opciones |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `gemini-3.8-flash` | 6 modelos | 97,0 % | 95,8 % | 87,7 % | 0,79 | 98,0 % | 0,93 | 3,8 % | 8,5 % | 10211 |
| `gemini-2.5-flash` | 6 modelos | 96,8 % | 96,1 % | 86,8 % | 0,77 | 97,8 % | 0,92 | 2,1 % | 11,1 % | 10211 |
| `claude-opus-5-5` | 6 modelos | 97,1 % | 95,9 % | 85,1 % | 0,74 | 97,8 % | 0,92 | 1,6 % | 13,3 % | 10211 |
| `gemini-2.5-pro (repetido)` | gpt-5.6-terra | 97,3 % | 96,7 % | 94,3 % | 0,91 | 98,5 % | 0,96 | 3,0 % | 2,7 % | 1423 |

## Coste y latencia del juez

| Juez | Llamadas | Coste estimado | Mediana por llamada | Casos con error del juez |
|---|---:|---:|---:|---:|
| `gemini-2.5-pro` | 1923 | 26,15 $ | 11,1 s | 0 |
| `gemini-3.8-flash` | 1925 | 0,83 $ | 2,0 s | 0 |
| `gemini-2.5-flash` | 1927 | 5,99 $ | 5,0 s | 0 |
| `claude-opus-5-5` | 1920 | 11,97 $ | 2,8 s | 0 |
