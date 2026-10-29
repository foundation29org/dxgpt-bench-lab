
R@1 estricta

| Run | live | urg | live+urg | exam | synth | total |
|---|---:|---:|---:|---:|---:|---:|
| gpt-5.6-terra (base) | 52.0 % | 51.7 % | 51.9 % | 83.3 % | 83.3 % | 61.3 % |
| gpt-6.1-sol | 60.0 % | 53.3 % | 58.1 % | 86.7 % | 90.0 % | 67.0 % |
| claude-opus-5 | 53.3 % | 56.7 % | 54.3 % | 88.3 % | 90.0 % | 64.7 % |
| arm_a_self_critique | 56.0 % | 60.0 % | 57.1 % | 85.0 % | 83.3 % | 65.3 % |
| arm_b_panel | 60.7 % | 61.7 % | 61.0 % | 86.7 % | 80.0 % | 68.0 % |
| arm_b_panel_terra_sol | 61.3 % | 58.3 % | 60.5 % | 85.0 % | 86.7 % | 68.0 % |
| arm_c_sources | 57.3 % | 60.0 % | 58.1 % | 76.7 % | 83.3 % | 64.3 % |
| arm_a_self_critique_on_sol | 59.3 % | 56.7 % | 58.6 % | 85.0 % | 86.7 % | 66.7 % |
| arm_b_panel_terra_sol_on_sol | 60.0 % | 61.7 % | 60.5 % | 85.0 % | 86.7 % | 68.0 % |
| arm_c_sources_on_sol | 58.7 % | 53.3 % | 57.1 % | 85.0 % | 83.3 % | 65.3 % |

R@5 estricta

| Run | live | urg | live+urg | exam | synth | total |
|---|---:|---:|---:|---:|---:|---:|
| gpt-5.6-terra (base) | 71.3 % | 76.7 % | 72.9 % | 88.3 % | 96.7 % | 78.3 % |
| gpt-6.1-sol | 73.3 % | 78.3 % | 74.8 % | 96.7 % | 96.7 % | 81.3 % |
| claude-opus-5 | 71.3 % | 73.3 % | 71.9 % | 95.0 % | 93.3 % | 78.7 % |
| arm_a_self_critique | 72.7 % | 85.0 % | 76.2 % | 91.7 % | 96.7 % | 81.3 % |
| arm_b_panel | 76.0 % | 85.0 % | 78.6 % | 96.7 % | 93.3 % | 83.7 % |
| arm_b_panel_terra_sol | 74.0 % | 81.7 % | 76.2 % | 95.0 % | 96.7 % | 82.0 % |
| arm_c_sources | 72.7 % | 83.3 % | 75.7 % | 86.7 % | 96.7 % | 80.0 % |
| arm_a_self_critique_on_sol | 76.7 % | 83.3 % | 78.6 % | 93.3 % | 96.7 % | 83.3 % |
| arm_b_panel_terra_sol_on_sol | 73.3 % | 85.0 % | 76.7 % | 93.3 % | 96.7 % | 82.0 % |
| arm_c_sources_on_sol | 72.7 % | 81.7 % | 75.2 % | 93.3 % | 93.3 % | 80.7 % |

Casos reales (live+urg, 210) frente a gpt-5.6-terra (base)

| Run | R@1 gana / pierde | p | R@5 gana / pierde | p |
|---|---:|---:|---:|---:|
| gpt-6.1-sol | 22 / 9 (+6.2 pp) | 0.029 | 14 / 10 (+1.9 pp) | 0.541 |
| claude-opus-5 | 26 / 21 (+2.4 pp) | 0.560 | 15 / 17 (-1.0 pp) | 0.860 |
| arm_a_self_critique | 20 / 9 (+5.2 pp) | 0.061 | 13 / 6 (+3.3 pp) | 0.167 |
| arm_b_panel | 27 / 8 (+9.0 pp) | 0.002 | 19 / 7 (+5.7 pp) | 0.029 |
| arm_b_panel_terra_sol | 23 / 5 (+8.6 pp) | 0.001 | 12 / 5 (+3.3 pp) | 0.143 |
| arm_c_sources | 17 / 4 (+6.2 pp) | 0.007 | 10 / 4 (+2.9 pp) | 0.180 |
| arm_a_self_critique_on_sol | 24 / 10 (+6.7 pp) | 0.024 | 21 / 9 (+5.7 pp) | 0.043 |
| arm_b_panel_terra_sol_on_sol | 23 / 5 (+8.6 pp) | 0.001 | 15 / 7 (+3.8 pp) | 0.134 |
| arm_c_sources_on_sol | 23 / 12 (+5.2 pp) | 0.090 | 17 / 12 (+2.4 pp) | 0.458 |

Casos reales (live+urg, 210) frente a gpt-6.1-sol

| Run | R@1 gana / pierde | p | R@5 gana / pierde | p |
|---|---:|---:|---:|---:|
| gpt-5.6-terra (base) | 9 / 22 (-6.2 pp) | 0.029 | 10 / 14 (-1.9 pp) | 0.541 |
| claude-opus-5 | 20 / 28 (-3.8 pp) | 0.312 | 16 / 22 (-2.9 pp) | 0.418 |
| arm_a_self_critique | 20 / 22 (-1.0 pp) | 0.878 | 16 / 13 (+1.4 pp) | 0.711 |
| arm_b_panel | 19 / 13 (+2.9 pp) | 0.377 | 12 / 4 (+3.8 pp) | 0.077 |
| arm_b_panel_terra_sol | 14 / 9 (+2.4 pp) | 0.405 | 7 / 4 (+1.4 pp) | 0.549 |
| arm_c_sources | 15 / 15 (+0.0 pp) | 1.000 | 13 / 11 (+1.0 pp) | 0.839 |
| arm_a_self_critique_on_sol | 9 / 8 (+0.5 pp) | 1.000 | 11 / 3 (+3.8 pp) | 0.057 |
| arm_b_panel_terra_sol_on_sol | 11 / 6 (+2.4 pp) | 0.332 | 6 / 2 (+1.9 pp) | 0.289 |
| arm_c_sources_on_sol | 7 / 9 (-1.0 pp) | 0.804 | 6 / 5 (+0.5 pp) | 1.000 |

R@1 en casos reales de raras (116) frente a gpt-5.6-terra (base)

| Run | R@1 | Gana / pierde | p |
|---|---:|---:|---:|
| gpt-5.6-terra (base) | 53.4 % | 0 / 0 | 1.000 |
| arm_a_self_critique | 55.2 % | 8 / 6 | 0.791 |
| arm_b_panel | 62.1 % | 15 / 5 | 0.041 |
| arm_b_panel_terra_sol | 63.8 % | 15 / 3 | 0.008 |
| arm_c_sources | 56.9 % | 7 / 3 | 0.344 |

R@1 en casos reales no raras (94) frente a gpt-5.6-terra (base)

| Run | R@1 | Gana / pierde | p |
|---|---:|---:|---:|
| gpt-5.6-terra (base) | 50.0 % | 0 / 0 | 1.000 |
| arm_a_self_critique | 59.6 % | 12 / 3 | 0.035 |
| arm_b_panel | 59.6 % | 12 / 3 | 0.035 |
| arm_b_panel_terra_sol | 56.4 % | 8 / 2 | 0.109 |
| arm_c_sources | 59.6 % | 10 / 1 | 0.012 |

Control de longitud: acierto dentro de las opciones que dio gpt-5.6-terra (base) en cada caso (live+urg, mediana 5.0)

| Run | Acierto | Gana / pierde frente a la base | p |
|---|---:|---:|---:|
| gpt-5.6-terra (base) | 72.9 % | 0 / 0 | 1.000 |
| arm_a_self_critique | 75.2 % | 13 / 8 | 0.383 |
| arm_b_panel | 77.1 % | 17 / 8 | 0.108 |
| arm_b_panel_terra_sol | 75.2 % | 11 / 6 | 0.332 |
| arm_c_sources | 75.2 % | 10 / 5 | 0.302 |

R@1 en casos reales de raras (116) frente a gpt-6.1-sol

| Run | R@1 | Gana / pierde | p |
|---|---:|---:|---:|
| gpt-6.1-sol | 64.7 % | 0 / 0 | 1.000 |
| arm_a_self_critique_on_sol | 61.2 % | 2 / 6 | 0.289 |
| arm_b_panel_terra_sol_on_sol | 62.9 % | 4 / 6 | 0.754 |
| arm_c_sources_on_sol | 61.2 % | 2 / 6 | 0.289 |

R@1 en casos reales no raras (94) frente a gpt-6.1-sol

| Run | R@1 | Gana / pierde | p |
|---|---:|---:|---:|
| gpt-6.1-sol | 50.0 % | 0 / 0 | 1.000 |
| arm_a_self_critique_on_sol | 55.3 % | 7 / 2 | 0.180 |
| arm_b_panel_terra_sol_on_sol | 57.4 % | 7 / 0 | 0.016 |
| arm_c_sources_on_sol | 52.1 % | 5 / 3 | 0.727 |

Control de longitud: acierto dentro de las opciones que dio gpt-6.1-sol en cada caso (live+urg, mediana 5.0)

| Run | Acierto | Gana / pierde frente a la base | p |
|---|---:|---:|---:|
| gpt-6.1-sol | 74.8 % | 0 / 0 | 1.000 |
| arm_a_self_critique_on_sol | 78.6 % | 11 / 3 | 0.057 |
| arm_b_panel_terra_sol_on_sol | 76.7 % | 6 / 2 | 0.289 |
| arm_c_sources_on_sol | 75.2 % | 6 / 5 | 1.000 |

Coste y latencia de la segunda etapa (solo las llamadas del brazo)

| Brazo | Llamadas | Coste | Coste por caso | Mediana por llamada | Opciones (mediana) |
|---|---:|---:|---:|---:|---:|
| arm_a_self_critique | 300 | 2.31 $ | 7.7 m$ | 5.7 s | 5.0 |
| arm_b_panel | 300 | 1.23 $ | 4.1 m$ | 2.5 s | 5.0 |
| arm_b_panel_terra_sol | 300 | 1.02 $ | 3.4 m$ | 2.0 s | 5.0 |
| arm_c_sources | 600 | 3.77 $ | 12.6 m$ | 3.2 s | 5.0 |
| arm_a_self_critique_on_sol | 300 | 0.92 $ | 3.1 m$ | 6.8 s | 5.0 |
| arm_b_panel_terra_sol_on_sol | 300 | 0.71 $ | 2.4 m$ | 4.2 s | 5.0 |
| arm_c_sources_on_sol | 600 | 2.38 $ | 7.9 m$ | 5.1 s | 5.0 |
