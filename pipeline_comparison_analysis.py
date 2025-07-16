#!/usr/bin/env python3
"""
Pipeline Performance Comparison Analysis
Compares GPT-4o vs GPT-4o (juanjoclassic) performance on matched cases only
"""

import json
import re
from pathlib import Path
from datetime import datetime

# File paths
BASE_DIR = Path("bench/pipelines/pipeline_v4 - fork/02. Pipeline/output")
DIAGNOSES_4O_DIR = BASE_DIR / "diagnoses_4o/20250715202717"
DIAGNOSES_4O_CLASSIC_DIR = BASE_DIR / "diagnoses_4o_juanjoclassic/20250716145333"

def load_json_file(file_path):
    """Load JSON file with error handling"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

def parse_evaluation_log(log_file):
    """Parse evaluation log to extract case results"""
    results = {}
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Extract matches
        match_pattern = r'Processing case \d+/\d+ \(Case ID: ([^)]+)\).*?▶️ Match found: ([^.]+)\. Position: ([^.]+)\.'
        matches = re.findall(match_pattern, content, re.DOTALL)
        
        for case_id, method, position in matches:
            results[case_id] = {
                'status': 'MATCH',
                'method': method,
                'position': position
            }
            
        # Extract no matches
        no_match_pattern = r'Processing case \d+/\d+ \(Case ID: ([^)]+)\).*?❌ No match found\.'
        no_matches = re.findall(no_match_pattern, content, re.DOTALL)
        
        for case_id in no_matches:
            results[case_id] = {
                'status': 'NO_MATCH',
                'method': None,
                'position': None
            }
            
    except Exception as e:
        print(f"Error parsing log file {log_file}: {e}")
        
    return results

def analyze_position_scoring(position):
    """Convert position to numeric score for comparison"""
    if position is None:
        return 0
    
    # Extract numeric part from position (e.g., "P1" -> 1)
    match = re.match(r'P(\d+)', position)
    if match:
        pos_num = int(match.group(1))
        # Higher positions get lower scores for ranking
        return 6 - pos_num if pos_num <= 5 else 0
    return 0

def calculate_success_rate(results):
    """Calculate success rate from results"""
    total = len(results)
    successful = sum(1 for r in results.values() if r['status'] == 'MATCH')
    return (successful / total * 100) if total > 0 else 0

def calculate_average_position(results):
    """Calculate average position from results"""
    matched_results = [r for r in results.values() if r['status'] == 'MATCH']
    if not matched_results:
        return 0
    
    total_score = 0
    for result in matched_results:
        pos_match = re.match(r'P(\d+)', result['position'])
        if pos_match:
            total_score += int(pos_match.group(1))
    
    return total_score / len(matched_results) if matched_results else 0

def generate_comparison_report():
    """Generate comprehensive comparison report"""
    
    # Load JSON summary files
    summary_4o = load_json_file(DIAGNOSES_4O_DIR / "evaluation_summary_4o.json")
    summary_classic = load_json_file(DIAGNOSES_4O_CLASSIC_DIR / "summary.json")
    
    # Parse evaluation logs
    log_4o = parse_evaluation_log(DIAGNOSES_4O_DIR / "evaluation.log")
    log_classic = parse_evaluation_log(DIAGNOSES_4O_CLASSIC_DIR / "evaluation.log")
    
    # Find common cases that matched in both runs
    common_matched_cases = set()
    for case_id in log_4o.keys():
        if (case_id in log_classic and 
            log_4o[case_id]['status'] == 'MATCH' and 
            log_classic[case_id]['status'] == 'MATCH'):
            common_matched_cases.add(case_id)
    
    # Filter results to only include common matched cases
    filtered_4o = {case_id: log_4o[case_id] for case_id in common_matched_cases}
    filtered_classic = {case_id: log_classic[case_id] for case_id in common_matched_cases}
    
    # Calculate metrics for filtered results
    avg_pos_4o = calculate_average_position(filtered_4o)
    avg_pos_classic = calculate_average_position(filtered_classic)
    
    # Count position distributions
    pos_dist_4o = {}
    pos_dist_classic = {}
    
    for case_id in common_matched_cases:
        pos_4o = log_4o[case_id]['position']
        pos_classic = log_classic[case_id]['position']
        
        pos_dist_4o[pos_4o] = pos_dist_4o.get(pos_4o, 0) + 1
        pos_dist_classic[pos_classic] = pos_dist_classic.get(pos_classic, 0) + 1
    
    # Generate report
    report = f"""
=============================================================================
PIPELINE PERFORMANCE COMPARISON REPORT
=============================================================================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

COMPARISON METHODOLOGY:
- Analysis restricted to cases where BOTH pipelines found matches
- Excluding all "No Match Found" cases from both datasets
- Common matched cases: {len(common_matched_cases)}

=============================================================================
OVERALL PERFORMANCE COMPARISON
=============================================================================

ORIGINAL PIPELINE (diagnoses_4o):
- Total cases processed: {summary_4o['global']['total_cases'] if summary_4o else 'N/A'}
- Total matched cases: {summary_4o['global']['matched_cases'] if summary_4o else 'N/A'}
- Success rate: {summary_4o['global']['final_score_percentage'] if summary_4o else 'N/A'}%
- Average position: {summary_4o['global']['average_position'] if summary_4o else 'N/A'}

CLASSIC PIPELINE (diagnoses_4o_juanjoclassic):
- Total cases processed: {summary_classic['global_statistics']['total_cases'] if summary_classic else 'N/A'}
- Total matched cases: {summary_classic['global_statistics']['matched_cases'] if summary_classic else 'N/A'}
- Success rate: {summary_classic['global_statistics']['final_score_percentage'] if summary_classic else 'N/A'}%
- Average position: {summary_classic['global_statistics']['average_position'] if summary_classic else 'N/A'}

=============================================================================
FILTERED ANALYSIS (Common Matched Cases Only)
=============================================================================

CASES ANALYZED: {len(common_matched_cases)}

PERFORMANCE ON COMMON MATCHED CASES:

Original Pipeline (diagnoses_4o):
- Average position: {avg_pos_4o:.3f}
- Position distribution: {dict(sorted(pos_dist_4o.items()))}

Classic Pipeline (diagnoses_4o_juanjoclassic):
- Average position: {avg_pos_classic:.3f}
- Position distribution: {dict(sorted(pos_dist_classic.items()))}

=============================================================================
COMPARISON VERDICT
=============================================================================
"""

    if avg_pos_4o < avg_pos_classic:
        winner = "ORIGINAL PIPELINE (diagnoses_4o)"
        improvement = ((avg_pos_classic - avg_pos_4o) / avg_pos_classic) * 100
        report += f"""
WINNER: {winner}
IMPROVEMENT: {improvement:.2f}% better average position
DIFFERENCE: {avg_pos_classic - avg_pos_4o:.3f} positions better on average
"""
    elif avg_pos_classic < avg_pos_4o:
        winner = "CLASSIC PIPELINE (diagnoses_4o_juanjoclassic)"
        improvement = ((avg_pos_4o - avg_pos_classic) / avg_pos_4o) * 100
        report += f"""
WINNER: {winner}
IMPROVEMENT: {improvement:.2f}% better average position
DIFFERENCE: {avg_pos_4o - avg_pos_classic:.3f} positions better on average
"""
    else:
        report += f"""
RESULT: TIE
Both pipelines performed equally on common matched cases
"""

    # Method comparison
    method_dist_4o = {}
    method_dist_classic = {}
    
    for case_id in common_matched_cases:
        method_4o = log_4o[case_id]['method']
        method_classic = log_classic[case_id]['method']
        
        method_dist_4o[method_4o] = method_dist_4o.get(method_4o, 0) + 1
        method_dist_classic[method_classic] = method_dist_classic.get(method_classic, 0) + 1
    
    report += f"""

=============================================================================
RESOLUTION METHOD COMPARISON (Common Matched Cases)
=============================================================================

Original Pipeline Methods:
{chr(10).join(f"- {method}: {count} cases" for method, count in sorted(method_dist_4o.items()))}

Classic Pipeline Methods:
{chr(10).join(f"- {method}: {count} cases" for method, count in sorted(method_dist_classic.items()))}

=============================================================================
DETAILED CASE-BY-CASE ANALYSIS
=============================================================================
"""

    # Case-by-case comparison
    better_4o = 0
    better_classic = 0
    same_performance = 0
    
    case_comparisons = []
    
    for case_id in sorted(common_matched_cases):
        pos_4o = log_4o[case_id]['position']
        pos_classic = log_classic[case_id]['position']
        method_4o = log_4o[case_id]['method']
        method_classic = log_classic[case_id]['method']
        
        # Extract position numbers for comparison
        pos_num_4o = int(re.match(r'P(\d+)', pos_4o).group(1))
        pos_num_classic = int(re.match(r'P(\d+)', pos_classic).group(1))
        
        if pos_num_4o < pos_num_classic:
            better_4o += 1
            status = "4O BETTER"
        elif pos_num_classic < pos_num_4o:
            better_classic += 1
            status = "CLASSIC BETTER"
        else:
            same_performance += 1
            status = "SAME"
        
        case_comparisons.append({
            'case_id': case_id,
            'pos_4o': pos_4o,
            'pos_classic': pos_classic,
            'method_4o': method_4o,
            'method_classic': method_classic,
            'status': status
        })
    
    report += f"""
PERFORMANCE SUMMARY:
- Cases where Original performed better: {better_4o}
- Cases where Classic performed better: {better_classic}
- Cases with same performance: {same_performance}

FIRST 20 CASE COMPARISONS:
Case ID | Original | Classic | Method 4O | Method Classic | Winner
--------|----------|---------|-----------|----------------|--------
"""
    
    for comp in case_comparisons[:20]:
        report += f"{comp['case_id']:<7} | {comp['pos_4o']:<8} | {comp['pos_classic']:<7} | {comp['method_4o']:<9} | {comp['method_classic']:<14} | {comp['status']}\n"
    
    if len(case_comparisons) > 20:
        report += f"... and {len(case_comparisons) - 20} more cases\n"
    
    report += f"""
=============================================================================
CONCLUSIONS
=============================================================================

1. DATASET SCOPE:
   - Analysis based on {len(common_matched_cases)} cases where both pipelines found matches
   - Excluded all "No Match Found" cases for fair comparison
   
2. PERFORMANCE WINNER:
   - {"Original Pipeline" if avg_pos_4o < avg_pos_classic else "Classic Pipeline" if avg_pos_classic < avg_pos_4o else "Tie"}
   
3. STATISTICAL SIGNIFICANCE:
   - Position difference: {abs(avg_pos_4o - avg_pos_classic):.3f}
   - Individual case wins: 4O={better_4o}, Classic={better_classic}, Same={same_performance}
   
4. RECOMMENDATION:
   - {"Use Original Pipeline" if avg_pos_4o < avg_pos_classic else "Use Classic Pipeline" if avg_pos_classic < avg_pos_4o else "Both pipelines equivalent"}

=============================================================================
"""
    
    return report

def main():
    """Main execution function"""
    print("Starting pipeline comparison analysis...")
    
    # Generate the comparison report
    report = generate_comparison_report()
    
    # Save report to file
    output_file = "pipeline_comparison_report.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"Analysis complete! Report saved to: {output_file}")
    print("\nKey findings preview:")
    print("=" * 50)
    
    # Print a summary
    lines = report.split('\n')
    in_verdict = False
    for line in lines:
        if "COMPARISON VERDICT" in line:
            in_verdict = True
        elif in_verdict and "DETAILED CASE-BY-CASE" in line:
            break
        elif in_verdict and line.strip():
            print(line)

if __name__ == "__main__":
    main()