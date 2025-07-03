📋 Proceso por Capítulo

  1. Organización Inicial:
  - Cada caso se asigna a UN SOLO capítulo (el primero alfabéticamente de sus diagnósticos)
  - Se cuentan casos disponibles por dataset en ese capítulo
  - Se ordenan datasets de minoritario a abundante

  2. Sistema de Deudas (se reinicia por capítulo):
  - Base target: Cada dataset intenta contribuir 10 casos
  - Deuda inicial: 0 (se reinicia en cada capítulo)

  3. Procesamiento Minoritario → Abundante:
  Para cada dataset en orden:
  - Necesita: 10 (base) + deuda_recibida
  - Toma: min(necesita, disponibles)
  - Si toma < necesita → transmite deuda = (necesita - toma)
  - Si toma >= necesita → deuda saldada (0)

  4. Selección Equidistante ICD-10:
  - Ordenar casos del dataset alfabéticamente por código ICD-10
  - Dividir en segmentos equidistantes según cantidad a tomar
  - Seleccionar casos en puntos medios de cada segmento

  🔄 Ejemplo Práctico:

  Capítulo X: 5 datasets necesitan 10 cada uno = 50 total
  - procheck: 0 disponibles → toma 0, transmite deuda 10
  - ramedis: 3 disponibles → necesita 10+10=20, toma 3, transmite 17
  - bulltes5: 8 disponibles → necesita 10+17=27, toma 8, transmite 19
  - urgtorre: 25 disponibles → necesita 10+19=29, toma 25, transmite 4
  - ausmle4: 200 disponibles → necesita 10+4=14, toma 14, deuda saldada
  Total: 0+3+8+25+14 = 50 casos exactos ✅

  ✅ Garantías:

  - Nunca excede 50 casos por capítulo
  - Puede quedar por debajo si no hay suficientes casos totales
  - Selección diversa usando equidistancia ICD-10
  - Balance entre datasets respetando disponibilidad