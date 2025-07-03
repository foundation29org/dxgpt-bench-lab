#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para comparar resultados de evaluación semántica entre modelos.
Extrae 60 casos aleatorios (los mismos) de los últimos runs de o3_images, o1 y gpt_4o.
"""

import json
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

def find_latest_run(model_name: str, results_dir: Path) -> Path:
    """Encuentra el run más reciente para un modelo dado."""
    model_dir = results_dir / model_name
    if not model_dir.exists():
        raise FileNotFoundError(f"No se encontró el directorio del modelo: {model_dir}")
    
    # Buscar todos los runs (directorios que empiezan con "run_")
    runs = [d for d in model_dir.iterdir() if d.is_dir() and d.name.startswith("run_")]
    
    if not runs:
        raise FileNotFoundError(f"No se encontraron runs para el modelo {model_name}")
    
    # Ordenar por timestamp (asumiendo formato run_YYYYMMDD_HHMMSS)
    runs.sort(key=lambda x: x.name, reverse=True)
    
    return runs[0]

def load_semantic_evaluation(run_dir: Path) -> Dict:
    """Carga el archivo semantic_evaluation.json de un run."""
    semantic_file = run_dir / "semantic_evaluation.json"
    
    if not semantic_file.exists():
        raise FileNotFoundError(f"No se encontró semantic_evaluation.json en {run_dir}")
    
    with open(semantic_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_all_cases(semantic_data: Dict) -> List[Dict]:
    """Extrae todos los casos de todas las letras del dataset."""
    all_cases = []
    
    for letter, cases in semantic_data.items():
        if isinstance(cases, list):
            all_cases.extend(cases)
    
    return all_cases

def select_common_cases(model_data: Dict[str, List[Dict]], sample_size: int = 60) -> List[str]:
    """Selecciona casos que están presentes en todos los modelos."""
    # Obtener IDs de casos para cada modelo
    model_case_ids = {}
    for model, cases in model_data.items():
        model_case_ids[model] = {case['case_id'] for case in cases}
    
    # Encontrar intersección de todos los casos
    common_case_ids = set.intersection(*model_case_ids.values())
    
    if len(common_case_ids) < sample_size:
        print(f"⚠️  Solo se encontraron {len(common_case_ids)} casos comunes entre todos los modelos")
        sample_size = len(common_case_ids)
    
    # Seleccionar muestra aleatoria
    random.seed(42)  # Para reproducibilidad
    selected_ids = random.sample(list(common_case_ids), sample_size)
    
    return sorted(selected_ids)  # Ordenar para consistencia

def format_case_details(case: Dict, model_name: str) -> str:
    """Formatea los detalles de un caso para el archivo de salida."""
    output = []
    output.append(f"Case ID: {case['case_id']}")
    output.append(f"Final Best Score: {case['final_best_score']}")
    output.append(f"Associated DDX: {case['associated_ddx']}")
    output.append(f"Associated GDX: {case['associated_gdx']}")
    output.append("")
    
    # Detalles de evaluación
    output.append("Evaluation Breakdown:")
    for i, ddx_eval in enumerate(case.get('evaluation_breakdown', []), 1):
        output.append(f"  DDX {i}: {ddx_eval['ddx_name']}")
        output.append(f"    Best Score: {ddx_eval['best_score']}")
        output.append(f"    Best Matching GDX: {ddx_eval['best_matching_gdx']}")
        
        # Scores vs cada GDX
        if ddx_eval.get('scores_vs_each_gdx'):
            output.append("    Scores vs Each GDX:")
            for gdx_name, score_info in ddx_eval['scores_vs_each_gdx'].items():
                output.append(f"      - {gdx_name}: {score_info['score']} ({score_info['code_type']})")
        output.append("")
    
    return "\n".join(output)

def main():
    """Función principal."""
    # Configuración
    base_dir = Path(__file__).parent
    results_dir = base_dir / "results"
    
    models = {
        "o3_images": "o3_images",
        "o1": "o1",
        "gpt_4o": "gpt_4o_summary"
    }
    
    print("🔍 Buscando últimos runs de cada modelo...")
    
    # Cargar datos de cada modelo
    model_data = {}
    model_runs = {}
    
    for model_key, model_name in models.items():
        try:
            # Encontrar último run
            latest_run = find_latest_run(model_name, results_dir)
            model_runs[model_key] = latest_run
            print(f"✅ {model_name}: {latest_run.name}")
            
            # Cargar semantic_evaluation.json
            semantic_data = load_semantic_evaluation(latest_run)
            
            # Extraer todos los casos
            all_cases = extract_all_cases(semantic_data)
            model_data[model_key] = all_cases
            print(f"   → {len(all_cases)} casos encontrados")
            
        except Exception as e:
            print(f"❌ Error con {model_name}: {e}")
            return
    
    print("")
    
    # Seleccionar casos comunes
    print("📊 Seleccionando 60 casos aleatorios comunes...")
    selected_case_ids = select_common_cases(model_data, sample_size=60)
    print(f"✅ {len(selected_case_ids)} casos seleccionados")
    
    # Crear archivo de salida
    output_file = base_dir / f"model_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        # Header
        f.write("="*80 + "\n")
        f.write("COMPARACIÓN DE MODELOS - EVALUACIÓN SEMÁNTICA\n")
        f.write("="*80 + "\n")
        f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Casos seleccionados: {len(selected_case_ids)}\n")
        f.write("\nModelos comparados:\n")
        for model_key, run_dir in model_runs.items():
            f.write(f"  - {models[model_key]}: {run_dir.name}\n")
        f.write("\n" + "="*80 + "\n\n")
        
        # Procesar cada caso
        for case_num, case_id in enumerate(selected_case_ids, 1):
            f.write(f"\n{'='*80}\n")
            f.write(f"CASO {case_num}/60: {case_id}\n")
            f.write(f"{'='*80}\n\n")
            
            # Para cada modelo
            for model_key in ["o1", "gpt_4o", "o3_images"]:  # Orden específico
                model_name = models[model_key]
                f.write(f"### Modelo: {model_name}\n")
                f.write("-"*40 + "\n")
                
                # Buscar el caso en los datos del modelo
                case_data = None
                for case in model_data[model_key]:
                    if case['case_id'] == case_id:
                        case_data = case
                        break
                
                if case_data:
                    f.write(format_case_details(case_data, model_name))
                else:
                    f.write(f"⚠️  Caso no encontrado en los resultados de {model_name}\n")
                
                f.write("\n")
        
        # Resumen final
        f.write("\n" + "="*80 + "\n")
        f.write("RESUMEN ESTADÍSTICO\n")
        f.write("="*80 + "\n")
        
        # Calcular estadísticas por modelo
        for model_key, model_name in models.items():
            scores = []
            for case_id in selected_case_ids:
                for case in model_data[model_key]:
                    if case['case_id'] == case_id:
                        scores.append(case['final_best_score'])
                        break
            
            if scores:
                avg_score = sum(scores) / len(scores)
                min_score = min(scores)
                max_score = max(scores)
                f.write(f"\n{model_name}:\n")
                f.write(f"  - Score promedio: {avg_score:.4f}\n")
                f.write(f"  - Score mínimo: {min_score:.4f}\n")
                f.write(f"  - Score máximo: {max_score:.4f}\n")
                f.write(f"  - Casos con score >= 0.8: {sum(1 for s in scores if s >= 0.8)}/{len(scores)}\n")
    
    print(f"\n✅ Archivo generado: {output_file}")
    print(f"📄 Total: 180 evaluaciones (60 casos × 3 modelos)")

if __name__ == "__main__":
    main()