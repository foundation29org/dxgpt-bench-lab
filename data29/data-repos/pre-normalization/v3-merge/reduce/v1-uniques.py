#!/usr/bin/env python3
"""
Unique Disease Filter

Filtra casos de all.json para crear un dataset único donde cada enfermedad
aparece solo una vez, priorizando casos de datasets minoritarios.

Algoritmo:
1. Contar frecuencia de cada disease name en diagnoses
2. Procesar por frecuencia ascendente (n=1, n=2, n=3...)
3. Para cada enfermedad, si no está ya aceptada, escoger caso de dataset más minoritario
4. Generar uniques.json con casos únicos
"""

import json
import os
from collections import Counter, defaultdict
from datetime import datetime


def load_all_json():
    """Carga el archivo all.json."""
    all_json_path = "all.json"
    
    if not os.path.exists(all_json_path):
        raise FileNotFoundError(f"No se encontró {all_json_path}")
    
    print(f"📂 Cargando {all_json_path}...")
    
    with open(all_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"✅ Cargados {len(data)} casos")
    return data


def analyze_datasets_and_diseases(cases):
    """
    Analiza datasets y enfermedades en los casos.
    
    Returns:
        tuple: (dataset_frequencies, disease_frequencies, case_diseases_map)
    """
    print("\n🔍 Analizando datasets y enfermedades...")
    
    # Contar frecuencias de datasets
    dataset_counter = Counter()
    
    # Contar frecuencias de disease names
    disease_counter = Counter()
    
    # Mapear cada caso con sus enfermedades
    case_diseases_map = {}
    
    for case in cases:
        case_id = case.get('id')
        dataset_name = case.get('dataset', 'unknown')
        
        # Contar dataset
        dataset_counter[dataset_name] += 1
        
        # Extraer enfermedades de este caso
        case_diseases = set()
        diagnoses = case.get('diagnoses', [])
        
        for diagnosis in diagnoses:
            if isinstance(diagnosis, dict) and 'name' in diagnosis:
                disease_name = diagnosis['name']
                if disease_name:
                    # Normalizar nombre
                    disease_name = disease_name.strip().lower()
                    disease_counter[disease_name] += 1
                    case_diseases.add(disease_name)
        
        case_diseases_map[case_id] = {
            'diseases': case_diseases,
            'dataset': dataset_name,
            'case_data': case
        }
    
    # Ordenar datasets por frecuencia (menos frecuente primero = tipo A)
    dataset_priority = [dataset for dataset, _ in dataset_counter.most_common()[::-1]]
    
    print(f"📊 Estadísticas:")
    print(f"   - {len(dataset_counter)} datasets encontrados")
    print(f"   - {len(disease_counter)} enfermedades únicas")
    print(f"   - {sum(disease_counter.values())} instancias de enfermedades")
    
    print(f"\n🏷️ Prioridad de datasets (A=más minoritario):")
    for i, (dataset, count) in enumerate(reversed(dataset_counter.most_common())):
        priority_letter = chr(65 + i)  # A, B, C, D...
        print(f"   Tipo {priority_letter}: {dataset} ({count} casos)")
    
    return dataset_counter, disease_counter, case_diseases_map, dataset_priority


def filter_unique_cases(cases, disease_counter, case_diseases_map, dataset_priority):
    """
    Filtra casos para obtener enfermedades únicas según el algoritmo especificado.
    
    Returns:
        list: Lista de casos únicos seleccionados
    """
    print(f"\n🎯 Iniciando filtrado de casos únicos...")
    
    accepted_cases = []
    accepted_diseases = set()
    
    # Agrupar enfermedades por frecuencia
    diseases_by_frequency = defaultdict(list)
    for disease, freq in disease_counter.items():
        diseases_by_frequency[freq].append(disease)
    
    # Procesar por frecuencia ascendente (n=1, n=2, n=3...)
    for frequency in sorted(diseases_by_frequency.keys()):
        diseases_at_frequency = diseases_by_frequency[frequency]
        
        print(f"\n📋 Procesando enfermedades con frecuencia n={frequency} ({len(diseases_at_frequency)} enfermedades)")
        
        for disease_name in diseases_at_frequency:
            # Verificar si esta enfermedad ya está aceptada
            if disease_name in accepted_diseases:
                continue
            
            # Buscar casos que contengan esta enfermedad
            candidate_cases = []
            for case_id, case_info in case_diseases_map.items():
                if disease_name in case_info['diseases']:
                    candidate_cases.append(case_info)
            
            if not candidate_cases:
                continue
            
            # Si solo hay un caso, lo aceptamos
            if len(candidate_cases) == 1:
                selected_case = candidate_cases[0]
            else:
                # Priorizar por tipo de dataset (A, B, C...)
                selected_case = None
                
                for priority_dataset in dataset_priority:
                    for case_info in candidate_cases:
                        if case_info['dataset'] == priority_dataset:
                            selected_case = case_info
                            break
                    if selected_case:
                        break
                
                # Fallback: tomar el primero si no encontramos match
                if not selected_case:
                    selected_case = candidate_cases[0]
            
            # Aceptar el caso seleccionado
            accepted_cases.append(selected_case['case_data'])
            
            # Marcar todas las enfermedades de este caso como aceptadas
            for disease in selected_case['diseases']:
                accepted_diseases.add(disease)
            
            # Log del progreso
            dataset_type = chr(65 + dataset_priority.index(selected_case['dataset'])) if selected_case['dataset'] in dataset_priority else '?'
            print(f"  ✅ {disease_name} -> Caso {selected_case['case_data']['id']} (dataset {selected_case['dataset']}, tipo {dataset_type})")
    
    print(f"\n🎉 Filtrado completado:")
    print(f"   - {len(accepted_cases)} casos únicos seleccionados")
    print(f"   - {len(accepted_diseases)} enfermedades únicas cubiertas")
    
    return accepted_cases


def save_unique_dataset(unique_cases, output_file="uniques.json"):
    """Guarda el dataset único en JSON."""
    print(f"\n💾 Guardando dataset único en {output_file}...")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(unique_cases, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Dataset único guardado: {len(unique_cases)} casos")


def generate_summary_report(unique_cases, dataset_priority):
    """Genera un reporte resumen del filtrado."""
    print(f"\n📊 REPORTE RESUMEN:")
    print(f"=" * 50)
    
    # Contar por dataset en casos únicos
    unique_dataset_counter = Counter()
    unique_diseases = set()
    
    for case in unique_cases:
        dataset_name = case.get('dataset', 'unknown')
        unique_dataset_counter[dataset_name] += 1
        
        # Contar enfermedades únicas
        for diagnosis in case.get('diagnoses', []):
            if isinstance(diagnosis, dict) and 'name' in diagnosis:
                disease_name = diagnosis['name']
                if disease_name:
                    unique_diseases.add(disease_name.strip().lower())
    
    print(f"📈 Distribución de casos únicos por dataset:")
    for dataset in dataset_priority:
        count = unique_dataset_counter.get(dataset, 0)
        percentage = (count / len(unique_cases)) * 100 if unique_cases else 0
        dataset_type = chr(65 + dataset_priority.index(dataset))
        print(f"   Tipo {dataset_type} ({dataset}): {count} casos ({percentage:.1f}%)")
    
    print(f"\n🎯 Resultados finales:")
    print(f"   - Casos únicos: {len(unique_cases)}")
    print(f"   - Enfermedades únicas: {len(unique_diseases)}")
    print(f"   - Datasets representados: {len(unique_dataset_counter)}")


def main():
    """Función principal."""
    print("🚀 FILTRO DE ENFERMEDADES ÚNICAS")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Paso 1: Cargar datos
        cases = load_all_json()
        
        # Paso 2: Analizar datasets y enfermedades
        dataset_counter, disease_counter, case_diseases_map, dataset_priority = analyze_datasets_and_diseases(cases)
        
        # Paso 3: Filtrar casos únicos
        unique_cases = filter_unique_cases(cases, disease_counter, case_diseases_map, dataset_priority)
        
        # Paso 4: Guardar resultado
        save_unique_dataset(unique_cases)
        
        # Paso 5: Generar reporte
        generate_summary_report(unique_cases, dataset_priority)
        
        print(f"\n🎉 Proceso completado exitosamente!")
        print(f"📄 Archivo generado: uniques.json")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())