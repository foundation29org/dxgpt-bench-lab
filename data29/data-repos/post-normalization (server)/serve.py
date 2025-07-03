#!/usr/bin/env python3
"""
Script para crear un dataset de evaluación de alta calidad a partir de múltiples archivos JSON.
Implementa un algoritmo de selección inteligente para maximizar la diversidad.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Union
from datetime import datetime
from collections import defaultdict, Counter
import random
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import numpy as np
import seaborn as sns
from matplotlib.patches import Rectangle
import matplotlib.patches as patches
from matplotlib.collections import PatchCollection
import warnings
warnings.filterwarnings('ignore', category=UserWarning)

# ==============================================================================
# CONFIGURACIÓN DEL SCRIPT
# ==============================================================================

# Tamaño total del dataset de salida deseado
TARGET_DATASET_SIZE = 450

# Mapeo de prefijos de ID a nombres de archivos
SOURCE_FILES = {
    'B': 'medbulltes5op.json',
    'Q': 'medqausmle4op.json',
    'R': 'ramedis.json',
    'S': 'rare_synthetic.json',
    'U': 'ukranian.json',
    'J': 'new_england_med_journal.json',
    'T': 'urgtorre.json'
}

# Reglas de muestreo por fuente de datos
# Usa números enteros para un conteo exacto.
# Usa 'None' para dejar que el algoritmo decida libremente
# Formato: 'prefijo': {'min': valor, 'max': valor}
SAMPLING_RULES = {
    'B': {'min': None, 'max': None},  # Deja que el algoritmo llene el resto
    'Q': {'min': None, 'max': None},  # Deja que el algoritmo llene el resto
    'R': {'min': 50, 'max': 100},
    'U': {'min': 'all', 'max': 'all'},  # 'all' es una palabra clave para incluir todos los casos
    'S': {'min': 0, 'max': 25},
    'J': {'min': 'all', 'max': 'all'},
    'T': {'min': 0, 'max': 50},
}

# Clave para identificar un diagnóstico único ('icd10' o 'normalized_text')
UNIQUENESS_KEY = 'icd10'  # Usar el primer código ICD10 de cada diagnóstico

# Carpeta de salida
OUTPUT_FOLDER = 'served'

# ==============================================================================
# FUNCIONES AUXILIARES
# ==============================================================================

def extract_icd10_chapter(icd10_code: str) -> str:
    """Extrae el capítulo ICD-10 del código (primera letra)."""
    if icd10_code and isinstance(icd10_code, str) and len(icd10_code) > 0:
        return icd10_code[0].upper()
    return 'Unknown'


def extract_complexity_value(complexity: str) -> int:
    """Convierte complejidad (ej. 'C5') a valor numérico."""
    if complexity and isinstance(complexity, str) and complexity.startswith('C'):
        try:
            return int(complexity[1:])
        except:
            pass
    return 0


def extract_severity_value(severity: str) -> int:
    """Convierte severidad (ej. 'S5') a valor numérico."""
    if severity and isinstance(severity, str) and severity.startswith('S'):
        try:
            return int(severity[1:])
        except:
            pass
    return 0


def get_case_diagnoses_info(case: dict) -> List[Tuple[str, str]]:
    """
    Extrae información de diagnósticos de un caso.
    Retorna lista de tuplas (primer_codigo_icd10, capitulo_icd10)
    """
    diagnoses_info = []
    
    if 'diagnoses' in case and isinstance(case['diagnoses'], list):
        for diagnosis in case['diagnoses']:
            if 'medical_codes' in diagnosis and 'icd10' in diagnosis['medical_codes']:
                icd10_codes = diagnosis['medical_codes']['icd10']
                if icd10_codes and isinstance(icd10_codes, list) and len(icd10_codes) > 0:
                    first_code = icd10_codes[0]
                    if first_code:
                        chapter = extract_icd10_chapter(first_code)
                        diagnoses_info.append((first_code, chapter))
    
    return diagnoses_info


def calculate_case_score(case: dict, case_info: dict, current_dataset: List[dict],
                        diagnoses_included: Set[str], chapters_included: Set[str],
                        source_counts: Dict[str, int]) -> float:
    """
    Calcula la puntuación de un caso candidato para promover diversidad.
    """
    score = 0.0
    
    # Bonus por introducir nuevo capítulo ICD-10
    case_chapters = set(chapter for _, chapter in case_info['diagnoses_info'])
    new_chapters = case_chapters - chapters_included
    if new_chapters:
        score += 5.0 * len(new_chapters)
    
    # Bonus por fuente subrepresentada
    source = case_info['source']
    total_cases = len(current_dataset)
    if total_cases > 0:
        source_representation = source_counts.get(source, 0) / total_cases
        underrepresentation_bonus = 1.0 - source_representation
        score += 3.0 * underrepresentation_bonus
    else:
        score += 3.0  # Máximo bonus si es el primer caso
    
    # Bonus por complejidad
    complexity_value = case_info['complexity_value']
    score += 2.0 * (complexity_value / 10.0)  # Normalizado a 0-1
    
    # Bonus por ser multi-diagnóstico
    if len(case_info['diagnoses_info']) > 1:
        score += 1.0
    
    # Bonus adicional por severidad alta
    severity_value = case_info['severity_value']
    score += 0.5 * (severity_value / 10.0)  # Normalizado a 0-1
    
    return score


# ==============================================================================
# FASE 0: CARGA Y PREPARACIÓN
# ==============================================================================

def load_and_prepare_data() -> Tuple[List[dict], Dict[str, List[dict]]]:
    """
    Carga todos los datasets y prepara la información necesaria.
    Retorna: (todos_los_casos, casos_por_fuente)
    """
    all_cases = []
    cases_by_source = defaultdict(list)
    
    current_dir = Path(__file__).parent
    
    for prefix, filename in SOURCE_FILES.items():
        filepath = current_dir / filename
        
        if not filepath.exists():
            print(f"⚠️  Archivo no encontrado: {filename}")
            continue
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                dataset = json.load(f)
            
            if not isinstance(dataset, list):
                print(f"⚠️  El archivo {filename} no contiene una lista de casos")
                continue
            
            # Procesar cada caso
            for case in dataset:
                if not isinstance(case, dict) or 'id' not in case:
                    continue
                
                # Extraer información del caso
                case_info = {
                    'case': case,
                    'id': case['id'],
                    'source': prefix,
                    'complexity': case.get('complexity', 'C0'),
                    'complexity_value': extract_complexity_value(case.get('complexity', 'C0')),
                    'severity_value': extract_severity_value(case.get('severity', 'S0')),
                    'diagnoses_info': get_case_diagnoses_info(case)
                }
                
                all_cases.append(case_info)
                cases_by_source[prefix].append(case_info)
            
            print(f"✓ Cargados {len(dataset)} casos de {filename}")
            
        except Exception as e:
            print(f"⚠️  Error al cargar {filename}: {e}")
    
    return all_cases, dict(cases_by_source)


# ==============================================================================
# FASE 1: SELECCIÓN PRIORITARIA
# ==============================================================================

def phase1_priority_selection(cases_by_source: Dict[str, List[dict]], 
                             sampling_rules: Dict[str, dict]) -> Tuple[List[dict], Set[str], Set[str]]:
    """
    Implementa la Fase 1: Selección prioritaria según reglas 'min' y 'all'.
    """
    final_dataset = []
    diagnoses_included = set()
    chapters_included = set()
    
    for source, rules in sampling_rules.items():
        if source not in cases_by_source:
            continue
        
        source_cases = cases_by_source[source]
        min_rule = rules.get('min')
        
        if min_rule == 'all':
            # Incluir todos los casos de esta fuente
            for case_info in source_cases:
                final_dataset.append(case_info['case'])
                
                # Actualizar diagnósticos incluidos
                for icd10_code, chapter in case_info['diagnoses_info']:
                    diagnoses_included.add(icd10_code)
                    chapters_included.add(chapter)
            
            print(f"  → Incluidos todos los {len(source_cases)} casos de fuente '{source}'")
            
        elif isinstance(min_rule, int) and min_rule > 0:
            # Seleccionar los mejores 'min' casos
            # Ordenar por: 1) nuevos capítulos, 2) complejidad, 3) multi-diagnóstico
            
            selected_cases = []
            remaining_cases = source_cases.copy()
            
            for _ in range(min(min_rule, len(source_cases))):
                if not remaining_cases:
                    break
                
                # Calcular puntuación para cada caso restante
                best_score = -1
                best_case = None
                best_idx = -1
                
                for idx, case_info in enumerate(remaining_cases):
                    # Contar nuevos capítulos que aportaría
                    case_chapters = set(ch for _, ch in case_info['diagnoses_info'])
                    new_chapters = case_chapters - chapters_included
                    
                    # Calcular puntuación simple
                    score = (len(new_chapters) * 1000 +  # Prioridad máxima a nuevos capítulos
                            case_info['complexity_value'] * 10 +
                            len(case_info['diagnoses_info']))  # Bonus por multi-diagnóstico
                    
                    if score > best_score:
                        best_score = score
                        best_case = case_info
                        best_idx = idx
                
                if best_case:
                    selected_cases.append(best_case)
                    remaining_cases.pop(best_idx)
                    
                    # Actualizar sets
                    for icd10_code, chapter in best_case['diagnoses_info']:
                        diagnoses_included.add(icd10_code)
                        chapters_included.add(chapter)
            
            # Añadir casos seleccionados al dataset final
            for case_info in selected_cases:
                final_dataset.append(case_info['case'])
            
            print(f"  → Seleccionados {len(selected_cases)} casos de fuente '{source}' (min: {min_rule})")
    
    return final_dataset, diagnoses_included, chapters_included


# ==============================================================================
# FASE 2: LLENADO ITERATIVO INTELIGENTE
# ==============================================================================

def phase2_iterative_filling(all_cases: List[dict], final_dataset: List[dict],
                           diagnoses_included: Set[str], chapters_included: Set[str],
                           sampling_rules: Dict[str, dict], target_size: int) -> List[dict]:
    """
    Implementa la Fase 2: Llenado iterativo hasta alcanzar el tamaño objetivo.
    """
    # Crear conjunto de IDs ya incluidos
    included_ids = {case['id'] for case in final_dataset}
    
    # Crear pool de candidatos (casos no incluidos)
    candidate_pool = [case_info for case_info in all_cases 
                     if case_info['id'] not in included_ids]
    
    # Contador de casos por fuente
    source_counts = Counter(case_info['id'][0] for case_info in all_cases 
                           if case_info['id'] in included_ids)
    
    print(f"\n📊 Estado inicial: {len(final_dataset)} casos seleccionados")
    print(f"   Candidatos disponibles: {len(candidate_pool)}")
    
    iteration = 0
    while len(final_dataset) < target_size and candidate_pool:
        iteration += 1
        
        # Filtrar candidatos válidos
        valid_candidates = []
        
        for case_info in candidate_pool:
            source = case_info['source']
            
            # Verificar límite máximo
            max_rule = sampling_rules.get(source, {}).get('max')
            current_count = source_counts.get(source, 0)
            
            if max_rule == 'all':
                # Ya se procesó en fase 1
                continue
            elif isinstance(max_rule, int) and current_count >= max_rule:
                # Límite alcanzado
                continue
            
            # Verificar que tenga al menos un diagnóstico nuevo
            has_new_diagnosis = any(icd10_code not in diagnoses_included 
                                  for icd10_code, _ in case_info['diagnoses_info'])
            
            if has_new_diagnosis:
                valid_candidates.append(case_info)
        
        if not valid_candidates:
            print(f"\n⚠️  No quedan candidatos válidos. Deteniendo en {len(final_dataset)} casos.")
            break
        
        # Calcular puntuaciones
        candidate_scores = []
        for case_info in valid_candidates:
            score = calculate_case_score(
                case_info['case'], case_info, final_dataset,
                diagnoses_included, chapters_included, source_counts
            )
            candidate_scores.append((score, case_info))
        
        # Seleccionar el mejor candidato
        candidate_scores.sort(key=lambda x: x[0], reverse=True)
        best_score, best_candidate = candidate_scores[0]
        
        # Añadir al dataset final
        final_dataset.append(best_candidate['case'])
        source_counts[best_candidate['source']] += 1
        
        # Actualizar conjuntos
        for icd10_code, chapter in best_candidate['diagnoses_info']:
            diagnoses_included.add(icd10_code)
            chapters_included.add(chapter)
        
        # Eliminar del pool
        candidate_pool.remove(best_candidate)
        
        # Mostrar progreso cada 10 iteraciones
        if iteration % 10 == 0:
            print(f"   Iteración {iteration}: {len(final_dataset)}/{target_size} casos")
    
    return final_dataset


# ==============================================================================
# FASE 3: FINALIZACIÓN Y REPORTE
# ==============================================================================

def generate_report(final_dataset: List[dict], all_cases: List[dict], 
                   cases_by_source: Dict[str, List[dict]]) -> dict:
    """
    Genera estadísticas detalladas del dataset final.
    """
    report = {
        'total_cases': len(final_dataset),
        'source_composition': {},
        'icd10_chapters': defaultdict(int),
        'complexity_distribution': defaultdict(int),
        'severity_distribution': defaultdict(int),
        'unique_diagnoses': set(),
        'multi_diagnosis_cases': 0,
        'average_diagnoses_per_case': 0
    }
    
    # Analizar cada caso
    total_diagnoses = 0
    
    for case in final_dataset:
        # Fuente
        source = case['id'][0] if case.get('id') else 'Unknown'
        report['source_composition'][source] = report['source_composition'].get(source, 0) + 1
        
        # Complejidad
        complexity = case.get('complexity', 'Unknown')
        report['complexity_distribution'][complexity] += 1
        
        # Severidad (del primer diagnóstico)
        if 'diagnoses' in case and case['diagnoses']:
            first_diagnosis = case['diagnoses'][0]
            severity = first_diagnosis.get('severity', 'Unknown')
            report['severity_distribution'][severity] += 1
        
        # Diagnósticos
        if 'diagnoses' in case:
            num_diagnoses = len(case['diagnoses'])
            total_diagnoses += num_diagnoses
            
            if num_diagnoses > 1:
                report['multi_diagnosis_cases'] += 1
            
            for diagnosis in case['diagnoses']:
                if 'medical_codes' in diagnosis and 'icd10' in diagnosis['medical_codes']:
                    icd10_codes = diagnosis['medical_codes']['icd10']
                    if icd10_codes and icd10_codes[0]:
                        code = icd10_codes[0]
                        report['unique_diagnoses'].add(code)
                        chapter = extract_icd10_chapter(code)
                        report['icd10_chapters'][chapter] += 1
    
    # Calcular promedio
    if report['total_cases'] > 0:
        report['average_diagnoses_per_case'] = total_diagnoses / report['total_cases']
    
    # Calcular porcentajes por fuente
    report['source_percentages'] = {}
    for source, count in report['source_composition'].items():
        total_in_source = len(cases_by_source.get(source, []))
        if total_in_source > 0:
            percentage = (count / total_in_source) * 100
            report['source_percentages'][source] = {
                'selected': count,
                'total': total_in_source,
                'percentage': percentage
            }
    
    # Convertir defaultdicts a dicts ordenados alfabéticamente
    report['icd10_chapters'] = dict(sorted(report['icd10_chapters'].items()))
    report['complexity_distribution'] = dict(sorted(report['complexity_distribution'].items()))
    report['severity_distribution'] = dict(sorted(report['severity_distribution'].items()))
    
    return report


# ==============================================================================
# FUNCIONES DE VISUALIZACIÓN
# ==============================================================================

def create_sophisticated_visualizations(report: dict, output_dir: Path, final_dataset: List[dict]) -> None:
    """
    Crea visualizaciones individuales sofisticadas de todos los datos del reporte.
    """
    # Crear carpeta plots
    plots_dir = output_dir / 'plots'
    plots_dir.mkdir(exist_ok=True)
    
    # Configurar estilo
    plt.style.use('seaborn-v0_8-darkgrid')
    sns.set_palette("husl")
    
    # Colores personalizados para fuentes
    source_colors = {
        'B': '#FF6B6B',  # Rojo coral
        'Q': '#4ECDC4',  # Turquesa
        'R': '#45B7D1',  # Azul cielo
        'S': '#96CEB4',  # Verde menta
        'U': '#FECA57',  # Amarillo dorado
        'T': '#DDA0DD',  # Púrpura
        'J': '#98D8C8'   # Verde agua
    }
    
    # 1. COMPOSICIÓN POR FUENTE DE DATOS (PIE CHART) - Más importante
    plt.figure(figsize=(10, 8))
    source_data = report['source_composition']
    colors = [source_colors.get(s, '#888888') for s in source_data.keys()]
    
    wedges, texts, autotexts = plt.pie(source_data.values(), 
                                       labels=source_data.keys(),
                                       autopct='%1.1f%%',
                                       startangle=90,
                                       colors=colors,
                                       explode=[0.05] * len(source_data),
                                       shadow=False,
                                       textprops={'fontsize': 12, 'fontweight': 'bold'})
    
    # Añadir leyenda con números absolutos
    legend_labels = [f'{k}: {v} casos' for k, v in source_data.items()]
    plt.legend(wedges, legend_labels, title="Fuentes", loc="best", fontsize=10)
    
    plt.title('Composición por Fuente de Datos', fontsize=16, fontweight='bold', pad=20)
    plt.tight_layout()
    plt.savefig(plots_dir / '01_composicion_fuentes.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 2. HISTOGRAMA DE CAPÍTULOS ICD-10 CUBIERTOS
    plt.figure(figsize=(14, 8))
    chapters = sorted(report['icd10_chapters'].keys())
    chapter_counts = [report['icd10_chapters'][ch] for ch in chapters]
    
    bars = plt.bar(chapters, chapter_counts, 
                    color=plt.cm.viridis(np.linspace(0, 1, len(chapters))),
                    edgecolor='black', linewidth=1)
    
    # Añadir valores en las barras
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}', ha='center', va='bottom', fontsize=10)
    
    plt.xlabel('Capítulo ICD-10', fontsize=12, fontweight='bold')
    plt.ylabel('Número de casos', fontsize=12, fontweight='bold')
    plt.title(f'Distribución de Capítulos ICD-10 ({len(chapters)}/22 capítulos representados)', 
              fontsize=16, fontweight='bold')
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(plots_dir / '02_histograma_capitulos_icd10.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 3. HISTOGRAMA DE CASOS POR FUENTE
    plt.figure(figsize=(10, 8))
    sources = sorted(report['source_percentages'].keys())
    selected = [report['source_percentages'][s]['selected'] for s in sources]
    totals = [report['source_percentages'][s]['total'] for s in sources]
    
    x = np.arange(len(sources))
    width = 0.35
    
    bars1 = plt.bar(x - width/2, selected, width, label='Seleccionados', 
                     color=[source_colors.get(s, '#888888') for s in sources],
                     edgecolor='black', linewidth=1)
    bars2 = plt.bar(x + width/2, totals, width, label='Total disponible', alpha=0.5,
                     color=[source_colors.get(s, '#888888') for s in sources],
                     edgecolor='black', linewidth=1)
    
    # Añadir porcentajes en las barras seleccionadas
    for i, (bar, s) in enumerate(zip(bars1, sources)):
        height = bar.get_height()
        pct = report['source_percentages'][s]['percentage']
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{pct:.1f}%', ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    plt.xlabel('Fuente', fontsize=12, fontweight='bold')
    plt.ylabel('Número de casos', fontsize=12, fontweight='bold')
    plt.title('Casos Seleccionados vs Disponibles por Fuente', fontsize=16, fontweight='bold')
    plt.xticks(x, sources)
    plt.legend(fontsize=12)
    plt.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    plt.savefig(plots_dir / '03_histograma_casos_fuente.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 4. HISTOGRAMAS DE DISTRIBUCIÓN DE CAPÍTULOS POR DATASET
    # Analizar distribución de capítulos por fuente
    source_chapter_dist = defaultdict(lambda: defaultdict(int))
    
    for case in final_dataset:
        source = case['id'][0] if case.get('id') else 'Unknown'
        if 'diagnoses' in case:
            for diag in case['diagnoses']:
                if 'medical_codes' in diag and 'icd10' in diag['medical_codes']:
                    codes = diag['medical_codes']['icd10']
                    if codes and codes[0]:
                        chapter = extract_icd10_chapter(codes[0])
                        source_chapter_dist[source][chapter] += 1
    
    # Crear subplots para cada fuente con datos
    sources_with_data = sorted([s for s in source_chapter_dist.keys() if source_chapter_dist[s]])
    n_sources = len(sources_with_data)
    
    if n_sources > 0:
        # Determinar layout de subplots
        n_cols = min(3, n_sources)
        n_rows = (n_sources + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(6*n_cols, 5*n_rows))
        if n_sources == 1:
            axes = [axes]
        elif n_rows == 1:
            axes = axes.reshape(1, -1)
        elif n_cols == 1:
            axes = axes.reshape(-1, 1)
        
        # Graficar cada fuente
        for idx, source in enumerate(sources_with_data):
            row = idx // n_cols
            col = idx % n_cols
            ax = axes[row, col] if n_rows > 1 else axes[col]
            
            chapters = sorted(source_chapter_dist[source].keys())
            counts = [source_chapter_dist[source][ch] for ch in chapters]
            
            # Crear histograma
            bars = ax.bar(chapters, counts, 
                          color=source_colors.get(source, '#888888'),
                          edgecolor='black', linewidth=1, alpha=0.8)
            
            # Añadir valores en las barras
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{int(height)}', ha='center', va='bottom', fontsize=9)
            
            ax.set_xlabel('Capítulo ICD-10', fontsize=10)
            ax.set_ylabel('Número de casos', fontsize=10)
            ax.set_title(f'Dataset {source} ({sum(counts)} casos)', fontsize=12, fontweight='bold')
            ax.grid(axis='y', alpha=0.3)
            
            # Limitar etiquetas del eje x si hay muchos capítulos
            if len(chapters) > 10:
                ax.set_xticks(ax.get_xticks()[::2])
        
        # Ocultar subplots vacíos
        for idx in range(n_sources, n_rows * n_cols):
            row = idx // n_cols
            col = idx % n_cols
            ax = axes[row, col] if n_rows > 1 else axes[col]
            ax.axis('off')
        
        plt.suptitle('Distribución de Capítulos ICD-10 por Dataset', fontsize=16, fontweight='bold')
        plt.tight_layout()
        plt.savefig(plots_dir / '04_histograma_capitulos_por_dataset.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    # 5. DISTRIBUCIÓN DE COMPLEJIDAD POR CASOS
    plt.figure(figsize=(12, 8))
    complexities = sorted(report['complexity_distribution'].keys(), 
                         key=lambda x: int(x[1:]) if x.startswith('C') else 0)
    complexity_counts = [report['complexity_distribution'][c] for c in complexities]
    
    # Crear gráfico de barras con gradiente de color
    bars = plt.bar(complexities, complexity_counts, 
                    color=plt.cm.plasma(np.linspace(0, 1, len(complexities))),
                    edgecolor='black', linewidth=1.5)
    
    # Añadir valores en las barras
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}', ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    plt.xlabel('Nivel de Complejidad', fontsize=12, fontweight='bold')
    plt.ylabel('Número de casos', fontsize=12, fontweight='bold')
    plt.title('Distribución de Complejidad de Casos', fontsize=16, fontweight='bold')
    plt.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(plots_dir / '05_distribucion_complejidad.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 6. DISTRIBUCIÓN DE SEVERIDAD (ORDENADA)
    plt.figure(figsize=(12, 8))
    severities = sorted(report['severity_distribution'].keys(),
                       key=lambda x: int(x[1:]) if x.startswith('S') else 0)
    severity_counts = [report['severity_distribution'][s] for s in severities]
    
    # Gráfico combinado: barras + línea
    x_pos = np.arange(len(severities))
    
    # Barras con gradiente
    bars = plt.bar(x_pos, severity_counts, 
                    color=plt.cm.Reds(np.linspace(0.3, 0.9, len(severities))),
                    edgecolor='darkred', linewidth=1.5, alpha=0.7)
    
    # Línea de tendencia
    plt.plot(x_pos, severity_counts, marker='o', markersize=10, 
             linewidth=3, color='darkred', label='Tendencia')
    
    # Añadir valores
    for i, (bar, count) in enumerate(zip(bars, severity_counts)):
        plt.text(i, count + max(severity_counts)*0.02, str(count), 
                ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    plt.xticks(x_pos, severities)
    plt.xlabel('Nivel de Severidad', fontsize=12, fontweight='bold')
    plt.ylabel('Número de casos', fontsize=12, fontweight='bold')
    plt.title('Distribución de Severidad (Ordenada)', fontsize=16, fontweight='bold')
    plt.grid(axis='y', alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(plots_dir / '06_distribucion_severidad.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 7. HISTOGRAMA DE DISTRIBUCIÓN DE DIAGNÓSTICOS POR CASO
    plt.figure(figsize=(10, 8))
    
    # Contar diagnósticos por caso
    diagnoses_per_case = []
    for case in final_dataset:
        if 'diagnoses' in case:
            diagnoses_per_case.append(len(case['diagnoses']))
        else:
            diagnoses_per_case.append(0)
    
    unique_counts = sorted(set(diagnoses_per_case))
    count_freq = [diagnoses_per_case.count(x) for x in unique_counts]
    
    # Crear histograma estilizado
    bars = plt.bar(unique_counts, count_freq, 
                    color='skyblue', edgecolor='navy', linewidth=2,
                    width=0.8)
    
    # Añadir valores en las barras
    for bar, freq in zip(bars, count_freq):
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{freq}\n({freq/len(final_dataset)*100:.1f}%)', 
                ha='center', va='bottom', fontsize=10)
    
    plt.xlabel('Número de diagnósticos por caso', fontsize=12, fontweight='bold')
    plt.ylabel('Frecuencia', fontsize=12, fontweight='bold')
    plt.title(f'Distribución de Diagnósticos por Caso (Promedio: {report["average_diagnoses_per_case"]:.2f})', 
              fontsize=16, fontweight='bold')
    plt.xticks(unique_counts)
    plt.grid(axis='y', alpha=0.3)
    
    # Añadir estadísticas
    plt.axvline(x=report["average_diagnoses_per_case"], color='red', linestyle='--', 
                linewidth=2, label=f'Promedio: {report["average_diagnoses_per_case"]:.2f}')
    plt.legend()
    
    plt.tight_layout()
    plt.savefig(plots_dir / '07_histograma_diagnosticos_caso.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 8. FLUJO DE FUENTES A CAPÍTULOS ICD-10
    plt.figure(figsize=(14, 10))
    ax = plt.gca()
    
    # Calcular flujos
    source_to_chapter = defaultdict(lambda: defaultdict(int))
    for case in final_dataset:
        source = case['id'][0] if case.get('id') else 'Unknown'
        if 'diagnoses' in case:
            for diag in case['diagnoses']:
                if 'medical_codes' in diag and 'icd10' in diag['medical_codes']:
                    codes = diag['medical_codes']['icd10']
                    if codes and codes[0]:
                        chapter = codes[0][0]
                        source_to_chapter[source][chapter] += 1
    
    # Obtener fuentes y capítulos únicos
    sources_unique = sorted(source_to_chapter.keys())
    chapters_unique = sorted(set(ch for s in source_to_chapter.values() for ch in s.keys()))
    
    # Posiciones verticales
    y_sources = np.linspace(0.9, 0.1, len(sources_unique))
    y_chapters = np.linspace(0.9, 0.1, len(chapters_unique))
    
    # Dibujar nodos de fuentes
    for i, source in enumerate(sources_unique):
        total = sum(source_to_chapter[source].values())
        circle = plt.Circle((0.15, y_sources[i]), 0.03, 
                           color=source_colors.get(source, '#888888'),
                           edgecolor='black', linewidth=2)
        ax.add_patch(circle)
        ax.text(0.05, y_sources[i], f'{source}\n({total})', 
                ha='center', va='center', fontsize=11, fontweight='bold')
    
    # Dibujar nodos de capítulos
    for i, chapter in enumerate(chapters_unique):
        total = sum(source_to_chapter[s][chapter] for s in sources_unique if chapter in source_to_chapter[s])
        circle = plt.Circle((0.85, y_chapters[i]), 0.025, 
                           color='lightgray', edgecolor='black', linewidth=2)
        ax.add_patch(circle)
        ax.text(0.95, y_chapters[i], f'{chapter}\n({total})', 
                ha='center', va='center', fontsize=10)
    
    # Dibujar conexiones con grosor proporcional al flujo
    max_weight = max(source_to_chapter[s][ch] 
                    for s in source_to_chapter 
                    for ch in source_to_chapter[s])
    
    for i, source in enumerate(sources_unique):
        for j, chapter in enumerate(chapters_unique):
            if chapter in source_to_chapter[source]:
                weight = source_to_chapter[source][chapter]
                if weight > 0:
                    # Crear curva bezier
                    x_points = [0.18, 0.5, 0.82]
                    y_start = y_sources[i]
                    y_end = y_chapters[j]
                    y_points = [y_start, (y_start + y_end) / 2, y_end]
                    
                    # Grosor proporcional
                    linewidth = max(1, (weight / max_weight) * 10)
                    
                    # Dibujar curva
                    ax.plot(x_points, y_points, 
                           color=source_colors.get(source, '#888888'), 
                           alpha=min(0.8, 0.3 + (weight / max_weight) * 0.5),
                           linewidth=linewidth)
    
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    
    # Títulos
    ax.text(0.15, 0.98, 'FUENTES', ha='center', fontsize=14, fontweight='bold')
    ax.text(0.85, 0.98, 'CAPÍTULOS ICD-10', ha='center', fontsize=14, fontweight='bold')
    plt.title('Flujo de Fuentes de Datos a Capítulos ICD-10', 
              fontsize=18, fontweight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig(plots_dir / '08_flujo_fuentes_capitulos.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 9. HISTOGRAMA APILADO DE CAPÍTULOS POR DATASET
    plt.figure(figsize=(16, 10))
    
    # Preparar datos para el histograma apilado
    # Obtener todos los capítulos únicos (ordenados)
    all_chapters = sorted(set(ch for source_dict in source_chapter_dist.values() 
                            for ch in source_dict.keys()))
    
    # Crear matriz de datos: filas = fuentes, columnas = capítulos
    sources_ordered = sorted(source_chapter_dist.keys())
    data_matrix = []
    
    for source in sources_ordered:
        source_data = []
        for chapter in all_chapters:
            count = source_chapter_dist[source].get(chapter, 0)
            source_data.append(count)
        data_matrix.append(source_data)
    
    # Posiciones de las barras
    x_pos = np.arange(len(all_chapters))
    bar_width = 0.8
    
    # Crear el histograma apilado
    bottom = np.zeros(len(all_chapters))
    
    for i, (source, data) in enumerate(zip(sources_ordered, data_matrix)):
        plt.bar(x_pos, data, bar_width, 
                bottom=bottom,
                label=f'Dataset {source}',
                color=source_colors.get(source, '#888888'),
                edgecolor='black',
                linewidth=0.5)
        
        # Añadir valores dentro de las barras (solo si el valor > 0)
        for j, (pos, height) in enumerate(zip(x_pos, data)):
            if height > 0:
                # Calcular posición vertical del texto
                y_position = bottom[j] + height/2
                plt.text(pos, y_position, str(int(height)), 
                        ha='center', va='center', 
                        fontsize=9, fontweight='bold',
                        color='white' if height > 3 else 'black')
        
        bottom += data
    
    # Añadir totales encima de cada barra
    for i, (pos, total) in enumerate(zip(x_pos, bottom)):
        if total > 0:
            plt.text(pos, total + 0.5, str(int(total)), 
                    ha='center', va='bottom', 
                    fontsize=10, fontweight='bold')
    
    # Configurar ejes y etiquetas
    plt.xticks(x_pos, all_chapters, fontsize=12)
    plt.xlabel('Capítulo ICD-10', fontsize=14, fontweight='bold')
    plt.ylabel('Número de casos', fontsize=14, fontweight='bold')
    plt.title('Distribución de Capítulos ICD-10 por Dataset (Histograma Apilado)', 
              fontsize=16, fontweight='bold')
    
    # Añadir leyenda
    plt.legend(title='Datasets', bbox_to_anchor=(1.05, 1), loc='upper left', 
               fontsize=11, title_fontsize=12)
    
    # Añadir grilla
    plt.grid(axis='y', alpha=0.3)
    
    # Ajustar márgenes
    plt.tight_layout()
    plt.savefig(plots_dir / '09_histograma_apilado_capitulos.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("   ✓ Visualizaciones generadas exitosamente en la carpeta 'plots'")


def save_results(final_dataset: List[dict], report: dict) -> str:
    """
    Guarda el dataset y el reporte en la carpeta especificada.
    """
    # Crear timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Obtener número de casos
    num_cases = len(final_dataset)
    
    # Crear carpeta de salida con número de casos
    folder_name = f"{timestamp}_c{num_cases}"
    current_dir = Path(__file__).parent
    output_dir = current_dir / OUTPUT_FOLDER / folder_name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Guardar dataset
    dataset_path = output_dir / f'aggregated_{timestamp}.json'
    with open(dataset_path, 'w', encoding='utf-8') as f:
        json.dump(final_dataset, f, ensure_ascii=False, indent=2)
    
    # Guardar reporte detallado
    report_path = output_dir / f'report_{timestamp}.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)
    
    # Crear reporte en texto
    text_report_path = output_dir / f'report_{timestamp}.txt'
    with open(text_report_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write(f"REPORTE DE DATASET GENERADO - {timestamp}\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"Tamaño total del dataset: {report['total_cases']} casos\n\n")
        
        f.write("COMPOSICIÓN POR FUENTE:\n")
        f.write("-" * 50 + "\n")
        for source, info in sorted(report['source_percentages'].items()):
            f.write(f"Fuente '{source}': {info['selected']} casos "
                   f"({info['percentage']:.1f}% del total de la fuente)\n")
            f.write(f"  → Total en fuente original: {info['total']} casos\n")
        
        f.write("\n")
        f.write("DISTRIBUCIÓN DE DIAGNÓSTICOS POR CAPÍTULO ICD-10:\n")
        f.write("-" * 50 + "\n")
        for chapter, count in sorted(report['icd10_chapters'].items()):
            f.write(f"Capítulo {chapter}: {count} casos\n")
        
        f.write("\n")
        f.write("DISTRIBUCIÓN DE COMPLEJIDAD:\n")
        f.write("-" * 50 + "\n")
        for complexity, count in sorted(report['complexity_distribution'].items()):
            f.write(f"{complexity}: {count} casos\n")
        
        f.write("\n")
        f.write("MÉTRICAS DE DIVERSIDAD:\n")
        f.write("-" * 50 + "\n")
        f.write(f"Diagnósticos únicos incluidos: {len(report['unique_diagnoses'])}\n")
        f.write(f"Casos multi-diagnóstico: {report['multi_diagnosis_cases']} "
               f"({report['multi_diagnosis_cases']/report['total_cases']*100:.1f}%)\n")
        f.write(f"Promedio de diagnósticos por caso: {report['average_diagnoses_per_case']:.2f}\n")
        f.write(f"Capítulos ICD-10 representados: {len(report['icd10_chapters'])}\n")
    
    # Generar visualizaciones sofisticadas
    print("\n📈 Generando visualizaciones...")
    create_sophisticated_visualizations(report, output_dir, final_dataset)
    
    return str(output_dir)


# ==============================================================================
# FUNCIÓN PRINCIPAL
# ==============================================================================

def main():
    """
    Función principal que ejecuta todo el proceso.
    """
    print("🚀 Iniciando generación de dataset de evaluación...")
    print(f"   Objetivo: {TARGET_DATASET_SIZE} casos\n")
    
    # FASE 0: Carga y preparación
    print("📂 FASE 0: Cargando datasets...")
    all_cases, cases_by_source = load_and_prepare_data()
    
    total_available = len(all_cases)
    print(f"\n✓ Total de casos disponibles: {total_available}")
    
    if total_available == 0:
        print("❌ No se encontraron casos para procesar.")
        return
    
    # FASE 1: Selección prioritaria
    print("\n🎯 FASE 1: Selección prioritaria...")
    final_dataset, diagnoses_included, chapters_included = phase1_priority_selection(
        cases_by_source, SAMPLING_RULES
    )
    
    print(f"\n✓ Casos seleccionados en Fase 1: {len(final_dataset)}")
    print(f"   Diagnósticos únicos: {len(diagnoses_included)}")
    print(f"   Capítulos ICD-10: {len(chapters_included)}")
    
    # FASE 2: Llenado iterativo
    if len(final_dataset) < TARGET_DATASET_SIZE:
        print(f"\n🔄 FASE 2: Llenado iterativo ({TARGET_DATASET_SIZE - len(final_dataset)} casos restantes)...")
        final_dataset = phase2_iterative_filling(
            all_cases, final_dataset, diagnoses_included, chapters_included,
            SAMPLING_RULES, TARGET_DATASET_SIZE
        )
    
    # FASE 3: Finalización y reporte
    print("\n📊 FASE 3: Generando reporte y guardando resultados...")
    report = generate_report(final_dataset, all_cases, cases_by_source)
    output_path = save_results(final_dataset, report)
    
    # Mostrar resumen en consola
    print("\n" + "=" * 80)
    print("RESUMEN DEL DATASET GENERADO")
    print("=" * 80)
    print(f"\n✓ Tamaño total: {report['total_cases']} casos")
    
    print("\n📊 Composición por fuente:")
    for source, info in sorted(report['source_percentages'].items()):
        print(f"   Fuente '{source}': {info['selected']} casos ({info['percentage']:.1f}% del total)")
    
    print(f"\n🏥 Capítulos ICD-10 representados: {len(report['icd10_chapters'])}")
    print(f"📈 Diagnósticos únicos: {len(report['unique_diagnoses'])}")
    print(f"🔢 Promedio de diagnósticos por caso: {report['average_diagnoses_per_case']:.2f}")
    
    print(f"\n✅ Resultados guardados en: {output_path}")


if __name__ == "__main__":
    main()