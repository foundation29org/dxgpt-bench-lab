#!/usr/bin/env python3
"""
Demo version of the summarization script that simulates LLM behavior
This creates the expected output structure without requiring actual LLM dependencies
"""
import json
import sys
import os
from pathlib import Path
from typing import List, Dict
import re

class DescriptionSummarizerDemo:
    """Demo summarizer that simulates LLM summarization"""
    
    def summarize_description(self, extended_description: str) -> str:
        """
        Simulate summarization by extracting key clinical information
        Real version would use LLM with temperature=0
        """
        
        # Extract key clinical patterns (simulation of what LLM would do)
        lines = extended_description.split('. ')
        summary_parts = []
        
        # Look for key clinical information patterns
        for line in lines:
            # Keep lines with clinical keywords
            clinical_keywords = [
                'síntomas', 'symptoms', 'años', 'years', 'age',
                'presenta', 'presents', 'dolor', 'pain', 
                'fiebre', 'fever', 'días', 'days',
                'exploración', 'examination', 'pruebas', 'tests',
                'antecedentes', 'history', 'diagnóstico', 'diagnosis',
                'tratamiento', 'treatment', 'evolución', 'evolution',
                'medicación', 'medication', 'alergia', 'allergy'
            ]
            
            if any(keyword in line.lower() for keyword in clinical_keywords):
                # Clean redundant phrases
                line = re.sub(r'Es importante señalar que|Cabe mencionar nuevamente que|'
                            r'Es fundamental considerar|Continuando con la descripción|'
                            r'Es necesario destacar', '', line)
                line = line.strip()
                if line and len(line) > 10:
                    summary_parts.append(line)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_parts = []
        for part in summary_parts:
            normalized = part.lower().strip()
            if normalized not in seen and len(part) > 20:
                seen.add(normalized)
                unique_parts.append(part)
        
        # Join and clean
        summary = '. '.join(unique_parts[:15])  # Keep most relevant parts
        summary = re.sub(r'\s+', ' ', summary).strip()
        
        # Ensure it ends with period
        if summary and not summary.endswith('.'):
            summary += '.'
        
        # Target approximately 30-40% of original length
        target_length = int(len(extended_description) * 0.35)
        if len(summary) > target_length:
            summary = summary[:target_length].rsplit('. ', 1)[0] + '.'
        
        return summary

def main():
    print("DEMO VERSION - Simulating LLM summarization")
    print("=" * 60)
    
    # Find the most recent served_largest directory
    served_dirs = sorted(Path("served_largest").glob("*_c*"), reverse=True)
    if not served_dirs:
        print("No served_largest directories found. Please run _serve_largest_N.py first.")
        return
    
    latest_dir = served_dirs[0]
    print(f"Using latest directory: {latest_dir}")
    
    # Load the largest_extended.json file
    input_file = latest_dir / "largest_extended.json"
    if not input_file.exists():
        print(f"File {input_file} not found. Please run _extend_descriptions.py first.")
        return
    
    with open(input_file, 'r', encoding='utf-8') as f:
        cases = json.load(f)
    
    print(f"Loaded {len(cases)} extended cases")
    
    # Initialize the demo summarizer
    summarizer = DescriptionSummarizerDemo()
    
    # Process each case
    summarized_cases = []
    for i, case in enumerate(cases):
        print(f"\nProcessing case {i+1}/{len(cases)} (ID: {case.get('id', 'unknown')})")
        extended_desc = case.get('case', '')
        print(f"Extended length: {len(extended_desc)} characters")
        
        # Summarize the description
        summarized_desc = summarizer.summarize_description(extended_desc)
        print(f"Summarized length: {len(summarized_desc)} characters")
        print(f"Compression ratio: {len(extended_desc) / len(summarized_desc) if len(summarized_desc) > 0 else 0:.1f}x")
        
        # Create summarized case
        summarized_case = case.copy()
        summarized_case['case'] = summarized_desc
        summarized_case['summarized_length'] = len(summarized_desc)
        
        # Keep track of all lengths
        if 'original_length' in case:
            summarized_case['original_length'] = case['original_length']
        if 'extended_length' in case:
            summarized_case['extended_length'] = case['extended_length']
        
        summarized_cases.append(summarized_case)
        
        # Save progress every 10 cases
        if (i + 1) % 10 == 0:
            output_file = latest_dir / "largest_summarized_demo.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(summarized_cases, f, ensure_ascii=False, indent=2)
            print(f"Progress saved ({i+1} cases)")
    
    # Save final results
    output_file = latest_dir / "largest_summarized_demo.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summarized_cases, f, ensure_ascii=False, indent=2)
    
    print(f"\nAll {len(summarized_cases)} summarized cases saved to: {output_file}")
    
    # Generate summary statistics
    total_original = sum(case.get('original_length', 0) for case in summarized_cases)
    total_extended = sum(case.get('extended_length', 0) for case in summarized_cases)
    total_summarized = sum(case['summarized_length'] for case in summarized_cases)
    
    summary = {
        "note": "DEMO VERSION - Real version would use gpt-4o-summary with temperature=0",
        "total_cases": len(summarized_cases),
        "total_original_chars": total_original,
        "total_extended_chars": total_extended,
        "total_summarized_chars": total_summarized,
        "average_compression_from_extended": total_extended / total_summarized if total_summarized > 0 else 0,
        "average_compression_from_original": total_original / total_summarized if total_summarized > 0 else 0,
        "individual_stats": [
            {
                "id": case.get('id', 'unknown'),
                "original": case.get('original_length', 0),
                "extended": case.get('extended_length', 0),
                "summarized": case['summarized_length'],
                "compression_from_extended": case.get('extended_length', 1) / case['summarized_length'] if case['summarized_length'] > 0 else 0,
                "compression_from_original": case.get('original_length', 1) / case['summarized_length'] if case['summarized_length'] > 0 else 0
            }
            for case in summarized_cases
        ]
    }
    
    summary_file = latest_dir / "summarization_summary_demo.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nSummary saved to: {summary_file}")
    print(f"Average compression from extended: {summary['average_compression_from_extended']:.1f}x")
    print(f"Average compression from original: {summary['average_compression_from_original']:.1f}x")
    
    print("\n" + "=" * 60)
    print("DEMO COMPLETE - This is a simulation of the summarization process")
    print("The real version would use gpt-4o-summary with temperature=0")
    print("and the exact prompt specified in the requirements")

if __name__ == "__main__":
    main()