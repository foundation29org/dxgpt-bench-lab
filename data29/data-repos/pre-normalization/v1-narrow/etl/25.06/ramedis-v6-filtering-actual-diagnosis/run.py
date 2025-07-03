"""
Script to filter JSON cases based on diagnostic criteria using LLM batching.

Filters out cases where diagnosis is a direct repetition, literal translation,
or pathognomonic symptom/finding already explicit in the clinical case.
Keeps cases requiring minimal inference or data integration.
"""

import sys
import os
import json
from typing import List, Dict, Any

# Add parent directories to path to import utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../../..')))
from utils.llm import Azure

def create_evaluation_prompt() -> str:
    """Create the prompt template for evaluating each case."""
    return """Evaluate if this medical case should be KEPT or DISCARDED based on the following criteria:

DISCARD if the diagnosis is:
- A direct repetition or literal translation of symptoms (e.g., mareos→Dizziness)
- An obvious pathognomonic finding already explicit in the case (e.g., Rx:Fractura→Fracture)
- A direct symptom-to-diagnosis mapping requiring no inference (e.g., Hyperphenylalaninemia→Phenylketonuria)
- Simply restating what's already clearly stated (e.g., tímpano abombado→Otitis media)

KEEP if the diagnosis requires:
- Minimal inference or integration of multiple data points
- Clinical reasoning beyond immediate recognition
- Synthesis of symptoms/findings (e.g., disnea+hipoventilación→Bronchospasm)
- Pattern recognition (e.g., malestar general+Rx engrosamiento hiliar→Respiratory infection)

Analyze this case:
- Case description: {case}
- Diagnosis: {diagnosis}

Return ONLY "KEEP" or "DISCARD" as your answer."""

def create_batch_schema() -> Dict[str, Any]:
    """Create the JSON schema for batch processing responses."""
    return {
        "type": "object",
        "properties": {
            "results": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": ["KEEP", "DISCARD"]
                }
            }
        },
        "required": ["results"],
        "additionalProperties": False
    }

def process_batch(llm: Azure, batch_data: List[Dict[str, Any]], prompt_template: str) -> List[str]:
    """Process a batch of cases and return decisions."""
    # Format batch items for the LLM
    batch_items = []
    for item in batch_data:
        # Combine all diagnosis names for evaluation
        diagnosis_names = ', '.join([diag['name'] for diag in item['diagnoses']])
        batch_items.append({
            "case": item['case'],
            "diagnosis": diagnosis_names
        })
    
    # Create the batch prompt
    batch_prompt = prompt_template + "\n\nEvaluate each case and return 'KEEP' or 'DISCARD' for each one."
    
    # Process with LLM using batch_items parameter
    results = llm.generate(
        batch_prompt,
        batch_items=batch_items,
        temperature=0.1,  # Low temperature for consistent evaluation
        max_tokens=100    # Each response should be just KEEP or DISCARD
    )
    
    return results

def main():
    """Main function to filter the JSON data."""
    # File paths
    input_file = "before.json"
    output_file = "after.json"
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found in current directory")
        return
    
    # Load the JSON data
    print(f"Loading data from {input_file}...")
    
    # Read JSON file
    with open(input_file, 'r', encoding='utf-8') as f:
        cases = json.load(f)
    
    print(f"Loaded {len(cases)} cases")
    
    # Initialize the LLM
    print("Initializing Azure LLM...")
    llm = Azure("gpt-4o")
    
    # Create prompt template
    prompt_template = create_evaluation_prompt()
    
    # Prepare data for batch processing
    all_cases = []
    for idx, case in enumerate(cases):
        all_cases.append({
            'index': idx,
            'case': case['case'],
            'diagnoses': case['diagnoses'],
            'original_data': case  # Keep reference to original data
        })
    
    # Process in batches of 5
    batch_size = 5
    all_decisions = []
    filtered_cases = []  # Store filtered cases as we go
    
    print(f"\nProcessing {len(all_cases)} cases in batches of {batch_size}...")
    
    # Initialize the output file with empty array
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('[\n')
    
    first_kept_case = True  # Track if we need a comma before the next case
    
    for i in range(0, len(all_cases), batch_size):
        batch = all_cases[i:i+batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(all_cases) + batch_size - 1) // batch_size
        
        print(f"Processing batch {batch_num}/{total_batches}...")
        
        try:
            # Process the batch
            decisions = process_batch(llm, batch, prompt_template)
            
            # Process decisions and update file incrementally
            batch_kept_cases = []
            for j, decision in enumerate(decisions):
                case_idx = batch[j]['index']
                all_decisions.append({
                    'index': case_idx,
                    'decision': decision
                })
                
                # If case is kept, add to filtered cases and write to file
                if decision == 'KEEP':
                    kept_case = cases[case_idx]
                    filtered_cases.append(kept_case)
                    batch_kept_cases.append(kept_case)
            
            # Write kept cases from this batch to file
            if batch_kept_cases:
                with open(output_file, 'a', encoding='utf-8') as f:
                    for case in batch_kept_cases:
                        if not first_kept_case:
                            f.write(',\n')
                        else:
                            first_kept_case = False
                        # Write the case with proper indentation
                        case_json = json.dumps(case, ensure_ascii=False, indent=2)
                        # Indent each line by 2 spaces
                        indented_json = '\n'.join('  ' + line if line else line for line in case_json.split('\n'))
                        f.write(indented_json)
            
            print(f"  Batch {batch_num} completed: {len([d for d in decisions if d == 'KEEP'])} kept, {len([d for d in decisions if d == 'DISCARD'])} discarded")
            print(f"  Total kept so far: {len(filtered_cases)} cases")
            
        except Exception as e:
            print(f"  Error processing batch {batch_num}: {e}")
            # Mark all items in failed batch as KEEP (conservative approach)
            for item in batch:
                case_idx = item['index']
                all_decisions.append({
                    'index': case_idx,
                    'decision': 'KEEP'
                })
                
                # Add to filtered cases and write to file
                kept_case = cases[case_idx]
                filtered_cases.append(kept_case)
                
                with open(output_file, 'a', encoding='utf-8') as f:
                    if not first_kept_case:
                        f.write(',\n')
                    else:
                        first_kept_case = False
                    case_json = json.dumps(kept_case, ensure_ascii=False, indent=2)
                    indented_json = '\n'.join('  ' + line if line else line for line in case_json.split('\n'))
                    f.write(indented_json)
    
    # Close the JSON array in the file
    with open(output_file, 'a', encoding='utf-8') as f:
        f.write('\n]')
    
    # Create a decision map for the log
    decision_map = {d['index']: d['decision'] for d in all_decisions}
    
    # Print summary
    print(f"\n=== Summary ===")
    print(f"Original cases: {len(cases)}")
    print(f"Kept cases: {len(filtered_cases)}")
    print(f"Discarded cases: {len(cases) - len(filtered_cases)}")
    print(f"Retention rate: {len(filtered_cases)/len(cases)*100:.1f}%")
    print(f"\nFiltered data saved to {output_file}")
    
    # Save a detailed log
    log_data = []
    for idx, case in enumerate(cases):
        diagnosis_names = ', '.join([diag['name'] for diag in case['diagnoses']])
        log_data.append({
            'id': case['id'],
            'diagnoses': diagnosis_names,
            'decision': decision_map.get(idx, 'ERROR'),
            'case_preview': case['case'][:100] + '...' if len(case['case']) > 100 else case['case']
        })
    
    with open('filtering_log.json', 'w', encoding='utf-8') as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)
    
    print("Detailed log saved to filtering_log.json")

if __name__ == "__main__":
    main()