#!/usr/bin/env python3
import json
import sys
import os
from pathlib import Path
from typing import List, Dict

# Add parent directories to path to import utils
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

try:
    from utils.llm import get_llm
except ImportError as e:
    print(f"Warning: Could not import LLM module: {e}")
    print("Trying alternative approach...")
    # If we can't import, we'll use a simple text extension approach
    get_llm = None

class DescriptionExtender:
    def __init__(self):
        if get_llm:
            try:
                self.llm = get_llm(model_name="gpt-4o-summary")
                self.use_llm = True
            except Exception as e:
                print(f"Could not initialize LLM: {e}")
                self.llm = None
                self.use_llm = False
        else:
            self.llm = None
            self.use_llm = False
    
    def extend_description(self, original_description: str) -> str:
        """Extend a description by making it more verbose while preserving all original information"""
        
        if self.use_llm and self.llm:
            prompt = f"""You are a medical case description extender. Your task is to take a medical case description and make it much longer and more verbose while preserving ALL original information.

Rules:
1. Keep ALL original lines and information intact
2. Between original sentences, add redundant information, paraphrases, and internal monologue
3. Make it sound like someone is thinking out loud, repeating the same information in different ways
4. Add connecting phrases, elaborations, and restatements
5. The extended version should be at least 3x longer than the original
6. Maintain the medical/clinical tone
7. Do NOT change any facts or add new medical information

Original description:
{original_description}

Extended verbose description:"""

            try:
                response = self.llm.generate(prompt)
                return response.strip()
            except Exception as e:
                print(f"Error extending description with LLM: {e}")
                # Fall back to simple extension
                return self.simple_extend(original_description)
        else:
            # Use simple text extension if LLM not available
            return self.simple_extend(original_description)
    
    def simple_extend(self, original_description: str) -> str:
        """Simple text extension without LLM"""
        lines = original_description.split('. ')
        extended = []
        
        for i, line in enumerate(lines):
            # Add original line
            extended.append(line)
            
            # Add redundant elaborations
            if 'Paciente' in line:
                extended.append("Es importante señalar que el paciente se presenta con estos síntomas")
                extended.append("Cabe mencionar nuevamente que estamos ante un caso que requiere atención")
            
            if 'síntomas' in line:
                extended.append("Los síntomas mencionados son de particular relevancia clínica")
                extended.append("Es fundamental considerar cada uno de estos síntomas en su contexto")
            
            if 'años' in line:
                extended.append("La edad del paciente es un factor crucial a considerar")
                extended.append("Debemos tener en cuenta la edad al momento de evaluar el caso")
            
            # Add general elaborations
            if i < len(lines) - 1:
                extended.append("Continuando con la descripción del caso clínico")
                extended.append("Es necesario destacar los siguientes aspectos adicionales")
        
        return '. '.join(extended)

def main():
    # Find the most recent served_largest directory
    served_dirs = sorted(Path("served_largest").glob("*_c*"), reverse=True)
    if not served_dirs:
        print("No served_largest directories found. Please run _serve_largest_N.py first.")
        return
    
    latest_dir = served_dirs[0]
    print(f"Using latest directory: {latest_dir}")
    
    # Load the largest.json file
    input_file = latest_dir / "largest.json"
    if not input_file.exists():
        print(f"File {input_file} not found")
        return
    
    with open(input_file, 'r', encoding='utf-8') as f:
        cases = json.load(f)
    
    print(f"Loaded {len(cases)} cases")
    
    # Initialize the extender
    extender = DescriptionExtender()
    
    # Process each case
    extended_cases = []
    for i, case in enumerate(cases):
        print(f"\nProcessing case {i+1}/{len(cases)} (ID: {case.get('id', 'unknown')})")
        original_desc = case.get('case', '')
        print(f"Original length: {len(original_desc)} characters")
        
        # Extend the description
        extended_desc = extender.extend_description(original_desc)
        print(f"Extended length: {len(extended_desc)} characters")
        print(f"Expansion ratio: {len(extended_desc) / len(original_desc):.1f}x")
        
        # Create extended case
        extended_case = case.copy()
        extended_case['case'] = extended_desc
        extended_case['original_length'] = len(original_desc)
        extended_case['extended_length'] = len(extended_desc)
        extended_cases.append(extended_case)
        
        # Save progress every 10 cases
        if (i + 1) % 10 == 0:
            output_file = latest_dir / "largest_extended.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(extended_cases, f, ensure_ascii=False, indent=2)
            print(f"Progress saved ({i+1} cases)")
    
    # Save final results
    output_file = latest_dir / "largest_extended.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(extended_cases, f, ensure_ascii=False, indent=2)
    
    print(f"\nAll {len(extended_cases)} extended cases saved to: {output_file}")
    
    # Generate summary statistics
    total_original = sum(case['original_length'] for case in extended_cases)
    total_extended = sum(case['extended_length'] for case in extended_cases)
    
    summary = {
        "total_cases": len(extended_cases),
        "total_original_chars": total_original,
        "total_extended_chars": total_extended,
        "average_expansion_ratio": total_extended / total_original,
        "individual_ratios": [
            {
                "id": case.get('id', 'unknown'),
                "original": case['original_length'],
                "extended": case['extended_length'],
                "ratio": case['extended_length'] / case['original_length']
            }
            for case in extended_cases
        ]
    }
    
    summary_file = latest_dir / "extension_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nSummary saved to: {summary_file}")
    print(f"Average expansion ratio: {summary['average_expansion_ratio']:.1f}x")

if __name__ == "__main__":
    main()