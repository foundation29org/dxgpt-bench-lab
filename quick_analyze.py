#!/usr/bin/env python3
"""
Analyze challenging cases with score 0.0 from semantic evaluation
"""

import json
import os
import re
from datetime import datetime
from typing import List, Dict, Any, Tuple
from utils.llm import get_llm
from utils.bert import calculate_semantic_similarity

def load_semantic_evaluation(run_path: str) -> Dict:
    """Load semantic evaluation results."""
    sem_eval_path = os.path.join(run_path, "semantic_evaluation.json")
    with open(sem_eval_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_diagnoses(run_path: str) -> Dict:
    """Load diagnoses data."""
    diag_path = os.path.join(run_path, "diagnoses.json")
    with open(diag_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_zero_score_cases(semantic_data: Dict, diagnoses_data: Dict, limit: int = 10) -> List[Dict]:
    """Extract cases with DDX that have 0.0 score against GDX."""
    challenging_cases = []
    
    # Iterate through all case categories
    for category, cases in semantic_data.items():
        if not isinstance(cases, list):
            continue
            
        for case in cases:
            case_id = case.get("case_id")
            
            # Find case details in diagnoses data
            case_details = None
            # Look through all categories in diagnoses_data
            for diag_category, diag_cases in diagnoses_data.items():
                if not isinstance(diag_cases, list):
                    continue
                for diag_case in diag_cases:
                    if diag_case.get("case_id") == case_id:
                        case_details = diag_case
                        break
                if case_details:
                    break
            
            if not case_details:
                continue
            
            # Check each DDX evaluation
            for ddx_eval in case.get("evaluation_breakdown", []):
                if ddx_eval.get("best_score", 1.0) == 0.0:
                    # Found a 0.0 score
                    challenging_cases.append({
                        "case_id": case_id,
                        "case_description": case_details.get("case_description", ""),
                        "ddx_name": ddx_eval.get("ddx_name", ""),
                        "gdx_list": list(case_details.get("gdx_details", {}).keys()),
                        "all_ddx": list(case_details.get("ddx_details", {}).keys()),
                        "zero_score_gdx": list(ddx_eval.get("scores_vs_each_gdx", {}).keys())
                    })
                    
                    if len(challenging_cases) >= limit:
                        return challenging_cases
    
    return challenging_cases

def evaluate_similarity_batch(pairs: List[Tuple[str, str]], model: str = "gpt-4o-summary") -> Dict:
    """Evaluate similarity using two different prompts in batch."""
    llm = get_llm(model)
    
    # Prepare batch for prompt 1: Semantic similarity (1-10)
    batch_items_p1 = []
    for ddx, gdx in pairs:
        batch_items_p1.append({
            "ddx": ddx,
            "gdx": gdx
        })
    
    prompt1 = """Evalúa la similitud semántica entre estos dos diagnósticos médicos en una escala del 1 al 10:
- 1 = Completamente diferentes (no relacionados, conceptos médicos distintos)
- 2 = Muy diferentes (mínima relación conceptual)
- 3 = Bastante diferentes (alguna relación distante)
- 4 = Diferentes pero con elementos comunes
- 5 = Moderadamente relacionados (comparten algunos aspectos)
- 6 = Bastante relacionados (similares pero distinguibles)
- 7 = Muy relacionados (alta similitud conceptual)
- 8 = Extremadamente similares (casi idénticos)
- 9 = Prácticamente idénticos (diferencias mínimas)
- 10 = Idénticos (mismo concepto, posiblemente diferente redacción)

Diagnóstico DDX: {ddx}
Diagnóstico GDX: {gdx}

Responde ÚNICAMENTE con un número del 1 al 10."""

    schema1 = {
        "type": "integer",
        "minimum": 1,
        "maximum": 10
    }
    
    print(f"📊 Evaluating semantic similarity for {len(pairs)} pairs...")
    results_p1 = llm.generate(prompt1, batch_items=batch_items_p1, schema=schema1, temperature=0.1)
    
    # Prepare batch for prompt 2: Clinical interchangeability (1-10)
    prompt2 = """¿Cuán confiado te sentirías usando estos dos términos diagnósticos intercambiablemente en un entorno clínico?
Escala del 1 al 10:
- 1 = Nada confiado (términos completamente diferentes, usar uno por otro sería un error grave)
- 2 = Muy poco confiado (términos mayormente diferentes con mínima relación)
- 3 = Poco confiado (términos relacionados pero con diferencias significativas)
- 4 = Algo inseguro (términos con cierta relación pero diferencias importantes)
- 5 = Moderadamente confiado (términos relacionados pero con matices distintos)
- 6 = Bastante confiado (términos similares con algunas diferencias menores)
- 7 = Confiado (términos muy similares, intercambiables en muchos contextos)
- 8 = Muy confiado (términos casi idénticos con diferencias sutiles)
- 9 = Extremadamente confiado (términos prácticamente idénticos)
- 10 = Totalmente confiado (términos completamente intercambiables)

Diagnóstico DDX: {ddx}
Diagnóstico GDX: {gdx}

Responde ÚNICAMENTE con un número del 1 al 10."""

    print(f"🏥 Evaluating clinical interchangeability for {len(pairs)} pairs...")
    results_p2 = llm.generate(prompt2, batch_items=batch_items_p1, schema=schema1, temperature=0.1)
    
    # Combine results
    combined_results = []
    for i, (ddx, gdx) in enumerate(pairs):
        combined_results.append({
            "ddx": ddx,
            "gdx": gdx,
            "semantic_similarity": results_p1[i] if i < len(results_p1) else None,
            "clinical_interchangeability": results_p2[i] if i < len(results_p2) else None
        })
    
    return combined_results

def calculate_bert_scores(pairs: List[Tuple[str, str]]) -> List[float]:
    """Calculate BERT scores for diagnosis pairs."""
    bert_scores = []
    
    print(f"🤖 Calculating BERT scores for {len(pairs)} pairs...")
    for ddx, gdx in pairs:
        try:
            # Calculate semantic similarity
            similarity_matrix = calculate_semantic_similarity(ddx, gdx)
            
            # Extract score from nested structure
            if ddx in similarity_matrix and gdx in similarity_matrix[ddx]:
                score = similarity_matrix[ddx][gdx]
                bert_scores.append(score)
            else:
                bert_scores.append(None)
        except Exception as e:
            print(f"   ❌ Error calculating BERT for '{ddx}' vs '{gdx}': {e}")
            bert_scores.append(None)
    
    return bert_scores

def main():
    # Path to the latest O1 run
    run_path = "bench/pipelines/pipeline_v2/results/o1/run_20250704_103221"
    
    print("📚 Loading evaluation data...")
    semantic_data = load_semantic_evaluation(run_path)
    diagnoses_data = load_diagnoses(run_path)
    
    print("🔍 Extracting challenging cases (score 0.0)...")
    challenging_cases = extract_zero_score_cases(semantic_data, diagnoses_data, limit=10)
    
    # Save challenging cases
    with open("challenging_cases.json", 'w', encoding='utf-8') as f:
        json.dump(challenging_cases, f, ensure_ascii=False, indent=2)
    print(f"💾 Saved {len(challenging_cases)} challenging cases to challenging_cases.json")
    
    # Prepare pairs for evaluation
    all_pairs = []
    case_mapping = {}  # Track which pair belongs to which case
    
    for case in challenging_cases:
        ddx = case["ddx_name"]
        for gdx in case["gdx_list"]:
            pair = (ddx, gdx)
            all_pairs.append(pair)
            case_mapping[pair] = case["case_id"]
    
    # Additional pairs for analysis (not linked to specific cases)
    additional_pairs = [
        ("C7 radiculopathy", "Cervical disc herniation at C6-C7"),
        # Add more pairs here as needed
    ]
    
    for pair in additional_pairs:
        all_pairs.append(pair)
        case_mapping[pair] = "ADDITIONAL"  # Special case ID for additional pairs
    
    print(f"\n📋 Total pairs to evaluate: {len(all_pairs)}")
    
    # Evaluate with LLM
    llm_results = evaluate_similarity_batch(all_pairs)
    
    # Calculate BERT scores
    bert_scores = calculate_bert_scores(all_pairs)
    
    # Generate summary report
    report_lines = [
        "CHALLENGING CASES ANALYSIS REPORT",
        "=" * 80,
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Total challenging cases analyzed: {len(challenging_cases)}",
        f"Total DDX-GDX pairs evaluated: {len(all_pairs)}",
        "",
        "=" * 80,
        ""
    ]
    
    # Process results by case
    current_case_id = None
    case_best_scores = {}  # Track best scores per case
    
    for i, (pair, llm_result, bert_score) in enumerate(zip(all_pairs, llm_results, bert_scores)):
        ddx, gdx = pair
        case_id = case_mapping[pair]
        
        # New case header
        if case_id != current_case_id:
            if current_case_id is not None and current_case_id != "ADDITIONAL":
                # Add best match for previous case
                if current_case_id in case_best_scores:
                    best = case_best_scores[current_case_id]
                    report_lines.extend([
                        "",
                        f"🏆 BEST MATCH FOR CASE {current_case_id}:",
                        f"   {best['ddx']} <-> {best['gdx']}",
                        f"   Combined Score: {best['combined']:.2f}",
                        "",
                        "-" * 80,
                        ""
                    ])
            
            current_case_id = case_id
            
            if case_id == "ADDITIONAL":
                # Handle additional pairs section
                report_lines.extend([
                    "ADDITIONAL PAIRS ANALYSIS",
                    "=" * 40,
                    "These pairs were added manually for comparison:",
                    ""
                ])
            else:
                # Handle regular cases
                case_info = next(c for c in challenging_cases if c["case_id"] == case_id)
                
                report_lines.extend([
                    f"CASE: {case_id}",
                    f"DDX with 0.0 score: {case_info['ddx_name']}",
                    f"Ground Truth: {', '.join(case_info['gdx_list'])}",
                    f"Case Description: {case_info['case_description'][:100]}..." if len(case_info['case_description']) > 100 else f"Case Description: {case_info['case_description']}",
                    ""
                ])
        
        # Pair results
        sem_score = llm_result.get("semantic_similarity", 0)
        clin_score = llm_result.get("clinical_interchangeability", 0)
        bert = bert_score if bert_score is not None else 0.0
        
        # Calculate combined score (average of all three normalized to 0-1)
        combined = (sem_score/10 + clin_score/10 + bert) / 3
        
        report_lines.extend([
            f"Pair: {ddx} <-> {gdx}",
            f"  Original ICD-10/Code Score: 0.0",
            f"  GPT-4o Semantic Similarity: {sem_score}/10",
            f"  GPT-4o Clinical Interchangeability: {clin_score}/10",
            f"  BERT Score: {bert:.4f}" if bert > 0 else f"  BERT Score: Failed",
            f"  Combined Score: {combined:.4f}",
            ""
        ])
        
        # Track best score for this case
        if case_id not in case_best_scores or combined > case_best_scores[case_id]['combined']:
            case_best_scores[case_id] = {
                'ddx': ddx,
                'gdx': gdx,
                'sem': sem_score,
                'clin': clin_score,
                'bert': bert,
                'combined': combined
            }
    
    # Add final case best match (only for regular cases, not additional pairs)
    if current_case_id in case_best_scores and current_case_id != "ADDITIONAL":
        best = case_best_scores[current_case_id]
        report_lines.extend([
            "",
            f"🏆 BEST MATCH FOR CASE {current_case_id}:",
            f"   {best['ddx']} <-> {best['gdx']}",
            f"   Combined Score: {best['combined']:.2f}",
            "",
            "=" * 80,
            ""
        ])
    
    # Summary statistics (excluding additional pairs)
    regular_case_scores = {k: v for k, v in case_best_scores.items() if k != "ADDITIONAL"}
    
    report_lines.extend([
        "SUMMARY STATISTICS",
        "-" * 40,
        f"Cases where all methods agree on 0.0: {sum(1 for c in regular_case_scores.values() if c['combined'] < 0.1)}",
        f"Cases with moderate improvement: {sum(1 for c in regular_case_scores.values() if 0.1 <= c['combined'] < 0.5)}",
        f"Cases with significant improvement: {sum(1 for c in regular_case_scores.values() if c['combined'] >= 0.5)}",
        "",
        "Average scores across all pairs:",
        f"  GPT-4o Semantic: {sum(r.get('semantic_similarity', 0) for r in llm_results) / len(llm_results):.1f}/10",
        f"  GPT-4o Clinical: {sum(r.get('clinical_interchangeability', 0) for r in llm_results) / len(llm_results):.1f}/10",
        f"  BERT: {sum(s for s in bert_scores if s is not None) / len([s for s in bert_scores if s is not None]):.4f}" if any(s is not None for s in bert_scores) else "  BERT: N/A"
    ])
    
    # Write report
    report_path = "challenging_cases_analysis.txt"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    
    print(f"\n✅ Analysis complete! Report saved to: {report_path}")
    print(f"📊 Evaluated {len(all_pairs)} DDX-GDX pairs from {len(challenging_cases)} challenging cases")

if __name__ == "__main__":
    main()