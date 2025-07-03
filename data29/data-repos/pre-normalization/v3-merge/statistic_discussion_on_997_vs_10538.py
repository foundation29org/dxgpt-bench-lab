#!/usr/bin/env python3
"""
Análisis comparativo de datasets JSON usando taxonomía ICD10
"""

import json
import sys
import os
from collections import defaultdict, Counter
from typing import Dict, List, Set, Tuple, Any
import re

# Add utils directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from utils.icd10 import ICD10Taxonomy


def load_json_data(file_path: str) -> List[Dict]:
    """Cargar datos JSON"""
    print(f"Cargando datos de: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"  ✓ Cargados {len(data)} casos")
    return data


def extract_icd10_codes(cases: List[Dict]) -> Set[str]:
    """Extraer todos los códigos ICD10 únicos de los casos"""
    codes = set()
    for case in cases:
        if 'diagnoses' in case:
            for diagnosis in case['diagnoses']:
                if 'icd10' in diagnosis:
                    codes.add(diagnosis['icd10'])
    return codes


def analyze_icd10_hierarchy_coverage(codes_full: Set[str], codes_reduced: Set[str], taxonomy: ICD10Taxonomy) -> Dict:
    """Analizar cobertura por jerarquía ICD10"""
    
    def get_hierarchy_stats(codes: Set[str]) -> Dict[str, Set[str]]:
        """Obtener estadísticas por nivel de jerarquía"""
        hierarchy_codes = {
            'chapters': set(),
            'ranges': set(), 
            'categories': set(),
            'blocks': set(),
            'subblocks': set(),
            'groups': set(),
            'subgroups': set()
        }
        
        for code in codes:
            # Obtener información del código
            info = taxonomy.get(code)
            if info:
                code_type = taxonomy.type(code)
                if code_type in hierarchy_codes:
                    hierarchy_codes[code_type].add(code)
                
                # También obtener padres en la jerarquía
                parents = taxonomy.parents(code)
                for parent in parents:
                    parent_type = taxonomy.type(parent)
                    if parent_type in hierarchy_codes:
                        hierarchy_codes[parent_type].add(parent)
        
        return hierarchy_codes
    
    # Obtener estadísticas para ambos conjuntos
    full_hierarchy = get_hierarchy_stats(codes_full)
    reduced_hierarchy = get_hierarchy_stats(codes_reduced)
    
    # Calcular porcentajes de cobertura
    coverage = {}
    for level in full_hierarchy.keys():
        total_in_full = len(full_hierarchy[level])
        covered_in_reduced = len(reduced_hierarchy[level] & full_hierarchy[level])
        
        if total_in_full > 0:
            percentage = (covered_in_reduced / total_in_full) * 100
        else:
            percentage = 0
            
        coverage[level] = {
            'total_full': total_in_full,
            'covered_reduced': covered_in_reduced,
            'percentage': percentage
        }
    
    return coverage


def analyze_complexity_severity(cases: List[Dict]) -> Dict:
    """Analizar distribución por complejidad y severidad"""
    complexity_counts = Counter()
    severity_counts = Counter()
    complexity_severity_matrix = defaultdict(lambda: defaultdict(int))
    
    for case in cases:
        complexity = case.get('complexity', 'Unknown')
        complexity_counts[complexity] += 1
        
        if 'diagnoses' in case:
            for diagnosis in case['diagnoses']:
                severity = diagnosis.get('severity', 'Unknown')
                severity_counts[severity] += 1
                complexity_severity_matrix[complexity][severity] += 1
    
    return {
        'complexity_distribution': dict(complexity_counts),
        'severity_distribution': dict(severity_counts), 
        'complexity_severity_matrix': dict(complexity_severity_matrix),
        'min_cases_per_complexity': dict(complexity_counts),
        'min_cases_per_severity': dict(severity_counts)
    }


def extract_symptoms_from_case(case_text: str) -> List[str]:
    """Extraer síntomas mencionados en el texto del caso"""
    # Patrones comunes de síntomas en español e inglés
    symptom_patterns = [
        r'presenta? (?:los? siguientes? síntomas?|síntomas?):?\s*([^.]+)',
        r'síntomas?:?\s*([^.]+)',
        r'(?:fever|fiebre)',
        r'(?:pain|dolor)',
        r'(?:nausea|náusea)',
        r'(?:vomiting|vómito)',
        r'(?:headache|cefalea)',
        r'(?:cough|tos)',
        r'(?:diarrhea|diarrea)',
        r'(?:shortness of breath|disnea)',
        r'(?:fatigue|fatiga)',
        r'(?:dizziness|mareo)',
    ]
    
    symptoms = []
    case_lower = case_text.lower()
    
    # Extraer síntomas usando patrones
    for pattern in symptom_patterns:
        matches = re.findall(pattern, case_lower, re.IGNORECASE)
        symptoms.extend([match.strip() for match in matches if match.strip()])
    
    # Limpiar y normalizar síntomas
    cleaned_symptoms = []
    for symptom in symptoms:
        # Dividir por comas, guiones, etc.
        parts = re.split(r'[,;-]', symptom)
        for part in parts:
            clean_part = part.strip().lower()
            if len(clean_part) > 2:  # Filtrar palabras muy cortas
                cleaned_symptoms.append(clean_part)
    
    return list(set(cleaned_symptoms))  # Eliminar duplicados


def analyze_symptom_cooccurrence(cases: List[Dict]) -> Dict:
    """Analizar co-ocurrencia de síntomas"""
    all_symptoms = set()
    case_symptoms = []
    
    # Extraer síntomas de todos los casos
    for case in cases:
        case_text = case.get('case', '')
        symptoms = extract_symptoms_from_case(case_text)
        case_symptoms.append(symptoms)
        all_symptoms.update(symptoms)
    
    # Crear matriz de co-ocurrencia
    cooccurrence_matrix = defaultdict(lambda: defaultdict(int))
    symptom_counts = Counter()
    
    for symptoms in case_symptoms:
        # Contar síntomas individuales
        for symptom in symptoms:
            symptom_counts[symptom] += 1
        
        # Contar co-ocurrencias
        for i, symptom1 in enumerate(symptoms):
            for j, symptom2 in enumerate(symptoms):
                if i != j:  # No auto-correlación
                    cooccurrence_matrix[symptom1][symptom2] += 1
    
    # Encontrar las co-ocurrencias más frecuentes
    frequent_pairs = []
    for symptom1, pairs in cooccurrence_matrix.items():
        for symptom2, count in pairs.items():
            if count > 1:  # Solo pares que ocurren más de una vez
                # Evitar duplicados (A,B) y (B,A)
                pair = tuple(sorted([symptom1, symptom2]))
                frequent_pairs.append((pair, count))
    
    # Ordenar por frecuencia
    frequent_pairs.sort(key=lambda x: x[1], reverse=True)
    
    return {
        'total_unique_symptoms': len(all_symptoms),
        'symptom_frequency': dict(symptom_counts.most_common(20)),
        'top_cooccurrences': frequent_pairs[:15],
        'symptom_count_distribution': dict(Counter([len(symptoms) for symptoms in case_symptoms]))
    }


def analyze_case_length_distribution(cases: List[Dict]) -> Dict:
    """Analizar distribución de longitud de casos"""
    lengths = []
    word_counts = []
    char_counts = []
    
    for case in cases:
        case_text = case.get('case', '')
        
        # Contar caracteres
        char_count = len(case_text)
        char_counts.append(char_count)
        
        # Contar palabras
        words = case_text.split()
        word_count = len(words)
        word_counts.append(word_count)
        
        # Contar líneas
        lines = case_text.split('\n')
        line_count = len(lines)
        lengths.append(line_count)
    
    def get_stats(values: List[int]) -> Dict:
        if not values:
            return {'min': 0, 'max': 0, 'mean': 0, 'median': 0}
        
        values_sorted = sorted(values)
        n = len(values)
        
        return {
            'min': min(values),
            'max': max(values), 
            'mean': sum(values) / n,
            'median': values_sorted[n // 2],
            'q25': values_sorted[n // 4],
            'q75': values_sorted[3 * n // 4]
        }
    
    return {
        'character_stats': get_stats(char_counts),
        'word_stats': get_stats(word_counts),
        'line_stats': get_stats(lengths),
        'length_distribution': dict(Counter([len(case.get('case', '')) // 100 * 100 for case in cases]))
    }


def main():
    """Función principal de análisis"""
    
    # Configurar rutas
    base_dir = os.path.dirname(__file__)
    all_json_path = os.path.join(base_dir, "all.json")
    all_997_json_path = os.path.join(base_dir, "all_997.json")
    
    print("=" * 80)
    print("ANÁLISIS COMPARATIVO DE DATASETS MÉDICOS")
    print("=" * 80)
    
    # Verificar archivos
    if not os.path.exists(all_json_path):
        print(f"❌ Error: No se encuentra {all_json_path}")
        return
    
    if not os.path.exists(all_997_json_path):
        print(f"❌ Error: No se encuentra {all_997_json_path}")
        return
    
    # Cargar datos
    print("\n📂 CARGA DE DATOS")
    print("-" * 40)
    all_cases = load_json_data(all_json_path)
    reduced_cases = load_json_data(all_997_json_path)
    
    # Inicializar taxonomía ICD10
    print("\n🏥 INICIALIZANDO TAXONOMÍA ICD10")
    print("-" * 40)
    try:
        taxonomy = ICD10Taxonomy()
    except Exception as e:
        print(f"❌ Error inicializando taxonomía: {e}")
        return
    
    # 1. ANÁLISIS DE COBERTURA ICD10
    print("\n🎯 1. COBERTURA DE CATEGORÍAS ICD10")
    print("-" * 40)
    
    all_codes = extract_icd10_codes(all_cases)
    reduced_codes = extract_icd10_codes(reduced_cases)
    
    print(f"Códigos ICD10 únicos en all.json: {len(all_codes)}")
    print(f"Códigos ICD10 únicos en all_997.json: {len(reduced_codes)}")
    print(f"Códigos compartidos: {len(all_codes & reduced_codes)}")
    print(f"Cobertura básica: {len(reduced_codes & all_codes) / len(all_codes) * 100:.1f}%")
    
    # Análisis por jerarquía
    hierarchy_coverage = analyze_icd10_hierarchy_coverage(all_codes, reduced_codes, taxonomy)
    
    print("\nCOBERTURA POR NIVEL DE JERARQUÍA:")
    for level, stats in hierarchy_coverage.items():
        print(f"  {level.capitalize():12} | {stats['covered_reduced']:3d}/{stats['total_full']:3d} | {stats['percentage']:5.1f}%")
    
    # 2. ANÁLISIS DE COMPLEJIDAD Y SEVERIDAD  
    print("\n📊 2. ANÁLISIS DE COMPLEJIDAD Y SEVERIDAD")
    print("-" * 40)
    
    all_complexity = analyze_complexity_severity(all_cases)
    reduced_complexity = analyze_complexity_severity(reduced_cases)
    
    print("DISTRIBUCIÓN POR COMPLEJIDAD:")
    print(f"{'Nivel':8} | {'All.json':8} | {'All_997':8} | {'Min casos':10}")
    print("-" * 45)
    
    all_complex_sorted = sorted(all_complexity['complexity_distribution'].items())
    for complexity, count_all in all_complex_sorted:
        count_reduced = reduced_complexity['complexity_distribution'].get(complexity, 0)
        min_cases = min(count_all, count_reduced) if count_reduced > 0 else 0
        print(f"{complexity:8} | {count_all:8d} | {count_reduced:8d} | {min_cases:10d}")
    
    print("\nDISTRIBUCIÓN POR SEVERIDAD:")
    print(f"{'Nivel':8} | {'All.json':8} | {'All_997':8} | {'Min casos':10}")
    print("-" * 45)
    
    all_severity_sorted = sorted(all_complexity['severity_distribution'].items())
    for severity, count_all in all_severity_sorted:
        count_reduced = reduced_complexity['severity_distribution'].get(severity, 0)
        min_cases = min(count_all, count_reduced) if count_reduced > 0 else 0
        print(f"{severity:8} | {count_all:8d} | {count_reduced:8d} | {min_cases:10d}")
    
    # 3. ANÁLISIS DE CO-OCURRENCIA DE SÍNTOMAS
    print("\n🔗 3. ANÁLISIS DE CO-OCURRENCIA DE SÍNTOMAS")
    print("-" * 40)
    
    print("Analizando síntomas en all.json...")
    all_symptoms = analyze_symptom_cooccurrence(all_cases)
    
    print("Analizando síntomas en all_997.json...")
    reduced_symptoms = analyze_symptom_cooccurrence(reduced_cases)
    
    print(f"\nSíntomas únicos detectados:")
    print(f"  All.json: {all_symptoms['total_unique_symptoms']}")
    print(f"  All_997.json: {reduced_symptoms['total_unique_symptoms']}")
    
    print(f"\nSíntomas más frecuentes en all.json:")
    for symptom, count in list(all_symptoms['symptom_frequency'].items())[:10]:
        print(f"  {symptom:30} | {count:4d} casos")
    
    print(f"\nCo-ocurrencias más frecuentes en all.json:")
    for (symptom1, symptom2), count in all_symptoms['top_cooccurrences'][:10]:
        print(f"  {symptom1:20} + {symptom2:20} | {count:3d} veces")
    
    # 4. ANÁLISIS DE LONGITUD DE CASOS
    print("\n📏 4. DISTRIBUCIÓN DE LONGITUD DE CASOS")
    print("-" * 40)
    
    all_lengths = analyze_case_length_distribution(all_cases)
    reduced_lengths = analyze_case_length_distribution(reduced_cases)
    
    print("ESTADÍSTICAS DE LONGITUD (caracteres):")
    print(f"{'Dataset':12} | {'Min':6} | {'Q25':6} | {'Med':6} | {'Q75':6} | {'Max':6} | {'Prom':6}")
    print("-" * 70)
    
    all_char = all_lengths['character_stats']
    red_char = reduced_lengths['character_stats']
    
    print(f"{'All.json':12} | {all_char['min']:6.0f} | {all_char['q25']:6.0f} | {all_char['median']:6.0f} | {all_char['q75']:6.0f} | {all_char['max']:6.0f} | {all_char['mean']:6.0f}")
    print(f"{'All_997.json':12} | {red_char['min']:6.0f} | {red_char['q25']:6.0f} | {red_char['median']:6.0f} | {red_char['q75']:6.0f} | {red_char['max']:6.0f} | {red_char['mean']:6.0f}")
    
    print("\nESTADÍSTICAS DE LONGITUD (palabras):")
    print(f"{'Dataset':12} | {'Min':6} | {'Q25':6} | {'Med':6} | {'Q75':6} | {'Max':6} | {'Prom':6}")
    print("-" * 70)
    
    all_word = all_lengths['word_stats']
    red_word = reduced_lengths['word_stats']
    
    print(f"{'All.json':12} | {all_word['min']:6.0f} | {all_word['q25']:6.0f} | {all_word['median']:6.0f} | {all_word['q75']:6.0f} | {all_word['max']:6.0f} | {all_word['mean']:6.0f}")
    print(f"{'All_997.json':12} | {red_word['min']:6.0f} | {red_word['q25']:6.0f} | {red_word['median']:6.0f} | {red_word['q75']:6.0f} | {red_word['max']:6.0f} | {red_word['mean']:6.0f}")
    
    # RESUMEN FINAL
    print("\n" + "=" * 80)
    print("🎯 RESUMEN EJECUTIVO")
    print("=" * 80)
    
    print(f"📈 Cobertura ICD10 general: {len(reduced_codes & all_codes) / len(all_codes) * 100:.1f}%")
    print(f"📊 Casos totales: {len(all_cases)} → {len(reduced_cases)} ({len(reduced_cases)/len(all_cases)*100:.1f}%)")
    print(f"🏥 Códigos ICD10: {len(all_codes)} → {len(reduced_codes)} ({len(reduced_codes)/len(all_codes)*100:.1f}%)")
    print(f"🔬 Síntomas únicos: {all_symptoms['total_unique_symptoms']} → {reduced_symptoms['total_unique_symptoms']}")
    
    min_complexity = min([count for count in reduced_complexity['complexity_distribution'].values() if count > 0])
    min_severity = min([count for count in reduced_complexity['severity_distribution'].values() if count > 0])
    
    print(f"⚡ Mínimo casos por complejidad: {min_complexity}")
    print(f"🎭 Mínimo casos por severidad: {min_severity}")
    
    print("\n✅ Análisis completado exitosamente!")


if __name__ == "__main__":
    main()
