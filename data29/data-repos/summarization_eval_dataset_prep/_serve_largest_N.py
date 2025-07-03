#!/usr/bin/env python3
import json
import os
from datetime import datetime
from pathlib import Path

# Parameter N - number of cases to select
N = 100

def load_all_cases():
    """Load all cases from all JSON files in the directory"""
    all_cases = []
    json_files = [
        'medbulltes5op.json',
        'medqausmle4op.json', 
        'new_england_med_journal.json',
        'ramedis.json',
        'rare_synthetic.json',
        'ukranian.json',
        'urgtorre.json'
    ]
    
    for json_file in json_files:
        if os.path.exists(json_file):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for case in data:
                        case['source_file'] = json_file
                        all_cases.append(case)
            except Exception as e:
                print(f"Error loading {json_file}: {e}")
    
    return all_cases

def main():
    # Load all cases
    print(f"Loading all cases...")
    all_cases = load_all_cases()
    print(f"Total cases loaded: {len(all_cases)}")
    
    # Sort cases by description length (longest first)
    all_cases.sort(key=lambda x: len(x.get('case', '')), reverse=True)
    
    # Select top N cases
    selected_cases = all_cases[:N]
    print(f"Selected {len(selected_cases)} cases with longest descriptions")
    
    # Show statistics
    lengths = [len(case['case']) for case in selected_cases]
    print(f"Description length range: {min(lengths)} - {max(lengths)} characters")
    print(f"Average description length: {sum(lengths) / len(lengths):.0f} characters")
    
    # Create output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(f"served_largest/{timestamp}_c{N}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save the selected cases
    output_file = output_dir / "largest.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(selected_cases, f, ensure_ascii=False, indent=2)
    
    print(f"\nSaved {len(selected_cases)} cases to: {output_file}")
    
    # Save a summary report
    report = {
        "timestamp": timestamp,
        "n_cases": N,
        "total_cases_available": len(all_cases),
        "selected_cases": len(selected_cases),
        "description_lengths": {
            "min": min(lengths),
            "max": max(lengths),
            "average": sum(lengths) / len(lengths)
        },
        "sources": {}
    }
    
    # Count cases by source
    for case in selected_cases:
        source = case.get('source_file', 'unknown')
        report['sources'][source] = report['sources'].get(source, 0) + 1
    
    report_file = output_dir / "selection_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    print(f"Saved report to: {report_file}")
    print(f"\nCases by source:")
    for source, count in report['sources'].items():
        print(f"  {source}: {count}")

if __name__ == "__main__":
    main()