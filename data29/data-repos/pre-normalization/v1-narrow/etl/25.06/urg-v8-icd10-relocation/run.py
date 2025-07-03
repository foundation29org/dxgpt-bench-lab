"""
Script to add ICD10 codes to individual diagnoses in the diagnoses array.
Takes afterafter.json and creates before.json with ICD10 codes added to each diagnosis.
"""

import sys
import os
import json
from typing import List, Dict, Any

# Add parent directories to path to import utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../..')))
from utils.llm import Azure

def create_icd10_prompt() -> str:
    """Create the prompt template for getting ICD10 codes."""
    return """Given the following medical diagnosis, provide the most appropriate ICD10 code.

Diagnosis: {diagnosis}

Return ONLY the ICD10 code (e.g., "J98.01", "J22", "H66.91", etc.) without any explanation or additional text."""

def create_batch_schema() -> Dict[str, Any]:
    """Create the JSON schema for batch processing ICD10 codes."""
    return {
        "type": "object",
        "properties": {
            "results": {
                "type": "array",
                "items": {
                    "type": "string",
                    "pattern": "^[A-Z][0-9]{2}(\\.[0-9]{1,2})?$"
                }
            }
        },
        "required": ["results"],
        "additionalProperties": False
    }

def process_icd10_batch(llm: Azure, diagnoses: List[str]) -> List[str]:
    """Process a batch of diagnoses to get ICD10 codes."""
    # Format batch items for the LLM
    batch_items = []
    for diagnosis in diagnoses:
        batch_items.append({
            "diagnosis": diagnosis
        })
    
    # Create the batch prompt
    batch_prompt = create_icd10_prompt() + "\n\nProvide the ICD10 code for each diagnosis."
    
    # Process with LLM using batch_items parameter
    try:
        results = llm.generate(
            batch_prompt,
            batch_items=batch_items,
            temperature=0.1,  # Low temperature for consistent codes
            max_tokens=50
        )
        return results
    except Exception as e:
        print(f"Error getting ICD10 codes: {e}")
        # Return placeholder codes if LLM fails
        return ["R69" for _ in diagnoses]  # R69 = Unknown and unspecified causes of morbidity

def main():
    """Main function to add ICD10 codes to diagnoses."""
    # File paths
    input_file = "afterafter.json"
    output_file = "before.json"
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found in current directory")
        return
    
    # Load the JSON data
    print(f"Loading data from {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        cases = json.load(f)
    
    print(f"Loaded {len(cases)} cases")
    
    # Initialize the LLM
    print("Initializing Azure LLM...")
    llm = Azure("gpt-4o")
    
    # Process cases
    batch_size = 5  # Process diagnoses in batches
    
    # Initialize the output file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('[\n')
    
    first_case = True
    total_diagnoses_processed = 0
    
    for case_idx, case in enumerate(cases):
        print(f"\nProcessing case {case_idx + 1}/{len(cases)} (ID: {case.get('id', 'unknown')})...")
        
        # Create a copy of the case
        new_case = case.copy()
        
        # Get all diagnosis names for ICD10 lookup
        diagnosis_names = [diag['name'] for diag in case.get('diagnoses', [])]
        
        if diagnosis_names:
            # Process diagnoses in batches to get ICD10 codes
            all_icd10_codes = []
            for i in range(0, len(diagnosis_names), batch_size):
                batch = diagnosis_names[i:i+batch_size]
                print(f"  Getting ICD10 codes for {len(batch)} diagnoses...")
                icd10_codes = process_icd10_batch(llm, batch)
                all_icd10_codes.extend(icd10_codes)
            
            # Update diagnoses with ICD10 codes
            new_diagnoses = []
            for i, diagnosis in enumerate(case.get('diagnoses', [])):
                new_diagnosis = diagnosis.copy()
                
                # Add ICD10 code
                if i < len(all_icd10_codes):
                    new_diagnosis['icd10'] = all_icd10_codes[i]
                else:
                    new_diagnosis['icd10'] = "R69"  # Unknown cause
                
                new_diagnoses.append(new_diagnosis)
            
            # Update the case with new diagnoses
            new_case['diagnoses'] = new_diagnoses
            total_diagnoses_processed += len(new_diagnoses)
        
        # Write the processed case to file
        with open(output_file, 'a', encoding='utf-8') as f:
            if not first_case:
                f.write(',\n')
            else:
                first_case = False
            
            # Write the case with proper indentation
            case_json = json.dumps(new_case, ensure_ascii=False, indent=2)
            # Indent each line by 2 spaces
            indented_json = '\n'.join('  ' + line if line else line for line in case_json.split('\n'))
            f.write(indented_json)
        
        print(f"  Case {case['id']} processed successfully ({len(diagnosis_names)} diagnoses)")
    
    # Close the JSON array
    with open(output_file, 'a', encoding='utf-8') as f:
        f.write('\n]')
    
    # Print summary
    print(f"\n=== Summary ===")
    print(f"Total cases processed: {len(cases)}")
    print(f"Total diagnoses with ICD10 codes added: {total_diagnoses_processed}")
    print(f"Output saved to: {output_file}")
    
    # Save a transformation log
    log_data = {
        "source_file": input_file,
        "output_file": output_file,
        "total_cases": len(cases),
        "total_diagnoses_processed": total_diagnoses_processed,
        "transformation": "Added ICD10 code to each individual diagnosis in diagnoses array"
    }
    
    with open('transformation_log.json', 'w', encoding='utf-8') as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)
    
    print("Transformation log saved to transformation_log.json")

if __name__ == "__main__":
    main()