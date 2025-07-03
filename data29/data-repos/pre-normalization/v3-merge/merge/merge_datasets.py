"""
Script to merge multiple JSON datasets into a single file with specific transformations:
- Adds a 'dataset' field based on the source file
- Keeps only specific fields: case, complexity, diagnoses
- Within diagnoses, keeps only: name, severity, icd10
- Reassigns new sequential IDs
"""

import json
import os

# Define dataset mappings
DATASET_MAPPINGS = {
    'ukranian_augmented.json': 'procheck',
    'urgtorre.json': 'urgtorre',
    'ramedis.json': 'ramedis',
    'medqausmle4op_augmented.json': 'ausmle4',
    'medbulltes5op_augmented.json': 'bulltes5'
}

def process_case(case, dataset_name, case_id):
    """Process a single case to keep only required fields."""
    # Start with ID as the first field
    processed_case = {'id': case_id}
    
    # Keep basic fields
    if 'case' in case:
        processed_case['case'] = case['case']
    
    if 'complexity' in case:
        processed_case['complexity'] = case['complexity']
    
    # Process diagnoses
    if 'diagnoses' in case:
        processed_diagnoses = []
        for diagnosis in case['diagnoses']:
            processed_diagnosis = {}
            
            # Keep only name, severity, and icd10
            if 'name' in diagnosis:
                processed_diagnosis['name'] = diagnosis['name']
            if 'severity' in diagnosis:
                processed_diagnosis['severity'] = diagnosis['severity']
            if 'icd10' in diagnosis:
                processed_diagnosis['icd10'] = diagnosis['icd10']
            
            # Only add diagnosis if it has at least the name
            if 'name' in processed_diagnosis:
                processed_diagnoses.append(processed_diagnosis)
        
        processed_case['diagnoses'] = processed_diagnoses
    
    # Add dataset field
    processed_case['dataset'] = dataset_name
    
    return processed_case

def main():
    """Main function to merge all datasets."""
    all_cases = []
    
    # Process each file
    current_id = 1
    for filename, dataset_name in DATASET_MAPPINGS.items():
        if os.path.exists(filename):
            print(f"Processing {filename} as '{dataset_name}'...")
            
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Handle both single object and array formats
                if isinstance(data, list):
                    cases = data
                else:
                    cases = [data]
                
                # Process each case
                processed_count = 0
                for case in cases:
                    processed_case = process_case(case, dataset_name, current_id)
                    
                    # Only add if we have at least case or diagnoses
                    if 'case' in processed_case or 'diagnoses' in processed_case:
                        all_cases.append(processed_case)
                        processed_count += 1
                        current_id += 1
                
                print(f"  Processed {processed_count} cases from {filename}")
                
            except Exception as e:
                print(f"  Error processing {filename}: {e}")
        else:
            print(f"Warning: {filename} not found, skipping...")
    
    # Save merged data
    output_file = 'all.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_cases, f, ensure_ascii=False, indent=2)
    
    # Print summary
    print(f"\n=== Summary ===")
    print(f"Total cases merged: {len(all_cases)}")
    
    # Count cases per dataset
    dataset_counts = {}
    for case in all_cases:
        dataset = case.get('dataset', 'unknown')
        dataset_counts[dataset] = dataset_counts.get(dataset, 0) + 1
    
    print("\nCases per dataset:")
    for dataset, count in sorted(dataset_counts.items()):
        print(f"  {dataset}: {count}")
    
    print(f"\nMerged data saved to {output_file}")
    
    # Save summary statistics
    summary = {
        "total_cases": len(all_cases),
        "datasets_processed": len(DATASET_MAPPINGS),
        "cases_per_dataset": dataset_counts,
        "fields_kept": ["id", "case", "complexity", "diagnoses", "dataset"],
        "diagnosis_fields_kept": ["name", "severity", "icd10"]
    }
    
    with open('merge_summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print("Merge summary saved to merge_summary.json")

if __name__ == "__main__":
    main()