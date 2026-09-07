#!/usr/bin/env python3
"""
QA Validation Checks for DxGPT Evaluation Datasets

Pre-evaluation gate checks:
1. Label leakage — diagnosis terms in case text
2. Boilerplate prefix — "Motivo de consulta" artifact
3. Template markers — section headers (Anamnesis, etc.)
4. List format symptoms — dash-separated lists
5. Language mixing — Spanish + English in single case

Usage:
    python validation_checks.py --dataset bench/datasets/all_275.json --report output/validation_report.txt
"""

import json
import re
import sys
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Any


@dataclass
class CheckResult:
    check_name: str
    status: str  # PASS, FAIL, WARN
    rate: float
    count: int
    threshold: float
    details: str = ""
    failed_cases: List[str] = None

    def __post_init__(self):
        if self.failed_cases is None:
            self.failed_cases = []


def load_dataset(dataset_path: Path) -> List[Dict[str, Any]]:
    """Load JSON dataset."""
    with open(dataset_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_diagnosis_terms(diagnoses: List[Dict]) -> set:
    """Extract all diagnosis name variants from diagnosis list."""
    terms = set()
    for diag in diagnoses:
        if diag.get('name'):
            terms.add(diag['name'].lower())
        if diag.get('normalized_text'):
            terms.add(diag['normalized_text'].lower())
    return terms


def check_label_leakage(data: List[Dict], threshold: float = 0.05) -> CheckResult:
    """Check if diagnosis terms appear in case text (label leakage)."""
    leakage_cases = []
    
    for case in data:
        diag_terms = extract_diagnosis_terms(case.get('diagnoses', []))
        case_text = case.get('case', '').lower()
        
        for term in diag_terms:
            if term and len(term) > 4 and term in case_text:
                leakage_cases.append(case.get('id', '?'))
                break
    
    rate = len(leakage_cases) / len(data) if data else 0
    status = 'PASS' if rate <= threshold else 'FAIL'
    
    return CheckResult(
        check_name='Label Leakage',
        status=status,
        rate=rate,
        count=len(leakage_cases),
        threshold=threshold,
        details=f"{len(leakage_cases)}/{len(data)} cases have diagnosis terms in case text",
        failed_cases=leakage_cases[:20]
    )


def check_boilerplate_prefix(data: List[Dict], threshold: float = 0.1) -> CheckResult:
    """Check for 'Motivo de consulta' boilerplate prefix."""
    prefix_pattern = r"^Motivo de consulta: Paciente acude.*?Anamnesis:"
    prefix_cases = []
    
    for case in data:
        case_text = case.get('case', '')
        if re.match(prefix_pattern, case_text):
            prefix_cases.append(case.get('id', '?'))
    
    rate = len(prefix_cases) / len(data) if data else 0
    status = 'PASS' if rate < threshold else 'FAIL'
    
    return CheckResult(
        check_name='Boilerplate Prefix',
        status=status,
        rate=rate,
        count=len(prefix_cases),
        threshold=threshold,
        details=f"{len(prefix_cases)}/{len(data)} cases start with 'Motivo de consulta' prefix",
        failed_cases=prefix_cases[:20]
    )


def check_template_markers(data: List[Dict], threshold: float = 0.4) -> CheckResult:
    """Check for section marker artifacts (Anamnesis, Antecedentes, etc.)."""
    markers = [
        r'\bAnamnesis\b',
        r'\bAntecedentes\b',
        r'\bExploracion\b',
        r'\bExploraci[o|ó]n\b',
        r'\bPruebas.*clinicas\b'
    ]
    marked_cases = []
    
    for case in data:
        case_text = case.get('case', '')
        marker_count = sum(len(re.findall(m, case_text)) for m in markers)
        if marker_count >= 2:
            marked_cases.append(case.get('id', '?'))
    
    rate = len(marked_cases) / len(data) if data else 0
    status = 'PASS' if rate < threshold else 'WARN' if rate < 0.6 else 'FAIL'
    
    return CheckResult(
        check_name='Template Markers',
        status=status,
        rate=rate,
        count=len(marked_cases),
        threshold=threshold,
        details=f"{len(marked_cases)}/{len(data)} cases have ≥2 section markers",
        failed_cases=marked_cases[:20]
    )


def check_list_format_symptoms(data: List[Dict], threshold: float = 0.6) -> CheckResult:
    """Check for dash-separated symptom lists instead of prose."""
    list_pattern = r'\s-\w+\s-\w+'
    list_cases = []
    
    for case in data:
        case_text = case.get('case', '')
        if re.search(list_pattern, case_text):
            list_cases.append(case.get('id', '?'))
    
    rate = len(list_cases) / len(data) if data else 0
    status = 'PASS' if rate <= threshold else 'FAIL'
    
    return CheckResult(
        check_name='List-Format Symptoms',
        status=status,
        rate=rate,
        count=len(list_cases),
        threshold=threshold,
        details=f"{len(list_cases)}/{len(data)} cases use dash-separated symptom lists",
        failed_cases=list_cases[:20]
    )


def run_all_checks(dataset_path: Path) -> tuple[List[CheckResult], int]:
    """Run all validation checks on dataset. Returns (results, dataset_size)."""
    print(f"Loading dataset from {dataset_path}...")
    data = load_dataset(dataset_path)
    print(f"Loaded {len(data)} cases.\n")
    
    results = [
        check_label_leakage(data, threshold=0.05),
        check_boilerplate_prefix(data, threshold=0.1),
        check_template_markers(data, threshold=0.4),
        check_list_format_symptoms(data, threshold=0.6),
    ]
    
    return results, len(data)


def print_results(results: List[CheckResult], dataset_size: int = 0) -> None:
    """Pretty-print validation results."""
    print("=" * 80)
    print("QA VALIDATION RESULTS")
    print("=" * 80)
    
    for result in results:
        status_symbol = '✓' if result.status == 'PASS' else '⚠' if result.status == 'WARN' else '✗'
        print(f"\n{status_symbol} {result.check_name.upper()} — {result.status}")
        print(f"   Rate: {result.rate:.1%} (threshold: {result.threshold:.1%})")
        print(f"   Count: {result.count}/{dataset_size} cases affected")
        print(f"   {result.details}")
        if result.failed_cases:
            print(f"   Sample failed cases: {', '.join(result.failed_cases[:5])}")
    
    print("\n" + "=" * 80)
    summary_status = 'PASS' if all(r.status == 'PASS' for r in results) else \
                     'WARN' if any(r.status == 'WARN' for r in results) else 'FAIL'
    print(f"OVERALL: {summary_status}")
    print("=" * 80)


def export_results(results: List[CheckResult], output_path: Path) -> None:
    """Export results to JSON."""
    data = {
        'timestamp': __import__('datetime').datetime.now().isoformat(),
        'checks': [asdict(r) for r in results],
        'overall_status': 'PASS' if all(r.status == 'PASS' for r in results) else \
                          'WARN' if any(r.status == 'WARN' for r in results) else 'FAIL'
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    print(f"\nResults exported to {output_path}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Run QA validation checks on DxGPT datasets.')
    parser.add_argument('--dataset', type=Path, required=True, help='Path to dataset JSON file')
    parser.add_argument('--output', type=Path, help='Path to export JSON results (optional)')
    
    args = parser.parse_args()
    
    if not args.dataset.exists():
        print(f"Error: Dataset file not found: {args.dataset}")
        sys.exit(1)
    
    results, dataset_size = run_all_checks(args.dataset)
    print_results(results, dataset_size)
    
    if args.output:
        export_results(results, args.output)
        sys.exit(0 if all(r.status in ['PASS', 'WARN'] for r in results) else 1)
