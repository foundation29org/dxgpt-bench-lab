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
    print(f"Error: Could not import LLM module: {e}")
    print("This script requires the LLM module to work.")
    sys.exit(1)

class DescriptionSummarizer:
    def __init__(self, model_name="gpt-4o-summary"):
        try:
            self.llm = get_llm(model_name=model_name)
            print(f"Successfully initialized LLM with model: {model_name}")
        except Exception as e:
            print(f"Error initializing LLM: {e}")
            raise
    
    def summarize_description(self, extended_description: str) -> str:
        """Summarize an extended description using the specified prompt and parameters"""
        
        prompt = f"""Summarize the following patient's medical description, keeping only relevant clinical information such as symptoms, evolution time, important medical history, and physical signs. Do not include irrelevant details or repeat phrases. The result should be shorter, clearer, and maintain the medical essence:

"{extended_description}"

Return ONLY the summarized description, with no additional commentary or explanation."""

        try:
            # Generate with specific parameters
            response = self.llm.generate(
                prompt,
                temperature=0,  # Maximum precision
                max_tokens=1000,
                # Note: top_p, frequency_penalty, and presence_penalty might not be supported
                # by all providers, but we'll include them as kwargs
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
            return response.strip()
        except Exception as e:
            print(f"Error summarizing description: {e}")
            # Return a truncated version if summarization fails
            return extended_description[:1000] + "..." if len(extended_description) > 1000 else extended_description

def main():
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
    
    # Initialize the summarizer
    summarizer = DescriptionSummarizer()
    
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
            output_file = latest_dir / "largest_summarized.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(summarized_cases, f, ensure_ascii=False, indent=2)
            print(f"Progress saved ({i+1} cases)")
    
    # Save final results
    output_file = latest_dir / "largest_summarized.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summarized_cases, f, ensure_ascii=False, indent=2)
    
    print(f"\nAll {len(summarized_cases)} summarized cases saved to: {output_file}")
    
    # Generate summary statistics
    total_original = sum(case.get('original_length', 0) for case in summarized_cases)
    total_extended = sum(case.get('extended_length', 0) for case in summarized_cases)
    total_summarized = sum(case['summarized_length'] for case in summarized_cases)
    
    summary = {
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
    
    summary_file = latest_dir / "summarization_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nSummary saved to: {summary_file}")
    print(f"Average compression from extended: {summary['average_compression_from_extended']:.1f}x")
    print(f"Average compression from original: {summary['average_compression_from_original']:.1f}x")

if __name__ == "__main__":
    main()