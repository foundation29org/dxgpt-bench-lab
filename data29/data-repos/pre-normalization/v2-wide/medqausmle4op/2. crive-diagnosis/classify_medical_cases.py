"""
Medical Case Classification Script
Classifies medical cases as 'condition_diagnostic' or 'clinical_action' using LLM batching
"""

import json
import os
import sys
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime

# Add utils to path
sys.path.append(str(Path(__file__).resolve().parents[5]))

from utils.llm.azure import AzureLLM


class MedicalCaseClassifier:
    """Classifies medical cases using LLM batching."""
    
    def __init__(self, batch_size: int = 20):
        self.batch_size = batch_size
        self.llm = AzureLLM("gpt-4o", temperature=0.1)
        self.output_file = Path(__file__).parent / "medqausmle4op_classified.json"
        self.metadata_file = Path(__file__).parent / "classification_metadata.json"
        self.progress_file = Path(__file__).parent / "classification_progress.json"
        self.results = []
        self.classification_results = []
        self.processed_ids = set()
    
    def load_data(self) -> List[Dict[str, Any]]:
        """Load the processed medical cases."""
        data_path = Path(__file__).parent.parent / "1. reduct" / "medqausmle4op_processed.json"
        with open(data_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_progress(self) -> bool:
        """Load existing progress if available. Returns True if progress exists."""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    progress_data = json.load(f)
                    self.classification_results = progress_data.get("classification_results", [])
                    self.processed_ids = set(progress_data.get("processed_ids", []))
                    print(f"Loaded existing progress: {len(self.processed_ids)} cases already processed")
                    return True
            except Exception as e:
                print(f"Error loading progress file: {e}")
                return False
        return False
    
    def save_progress(self):
        """Save current progress to file."""
        progress_data = {
            "classification_results": self.classification_results,
            "processed_ids": list(self.processed_ids),
            "last_updated": datetime.now().isoformat()
        }
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, indent=2, ensure_ascii=False)
    
    def save_current_output(self, original_cases: List[Dict[str, Any]]):
        """Save the current state of classified cases to the output file."""
        # Create lookup for classifications
        classification_lookup = {
            result["id"]: result["classification"]
            for result in self.classification_results
        }
        
        # Add classification field to each case
        classified_cases = []
        for case in original_cases:
            case_with_classification = case.copy()
            case_id = case["id"]
            
            if case_id in classification_lookup:
                case_with_classification["classification"] = classification_lookup[case_id]
            else:
                case_with_classification["classification"] = "unclassified"
            
            classified_cases.append(case_with_classification)
        
        # Save to output file
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(classified_cases, f, indent=2, ensure_ascii=False)
    
    def create_classification_prompt(self) -> str:
        """Create the prompt for case classification."""
        return """You are a medical expert. For each case, classify the diagnosis as either:
- 'condition_diagnostic': A medical condition, disease, syndrome, or diagnosis
- 'clinical_action': A treatment, medication, procedure, test, or clinical action

Only return the classification label for each case following the schema."""
    
    def create_classification_schema(self) -> Dict[str, Any]:
        """Create the schema for classification results."""
        return {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "classification": {
                    "type": "string",
                    "enum": ["condition_diagnostic", "clinical_action"]
                }
            },
            "required": ["id", "classification"],
            "additionalProperties": False
        }
    
    def process_batch(self, batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process a batch of cases through the LLM."""
        # Prepare batch items for LLM
        batch_items = []
        for case in batch:
            batch_items.append({
                "id": case["id"],
                "case": case["case"],
                "diagnosis": case["diagnosis"]
            })
        
        # Get classifications from LLM
        prompt = self.create_classification_prompt()
        schema = self.create_classification_schema()
        
        try:
            results = self.llm.generate(
                prompt=prompt,
                batch_items=batch_items,
                schema=schema,
                temperature=0.1,
                max_tokens=1000
            )
            
            return results
        except Exception as e:
            print(f"Error processing batch: {e}")
            # Return error classifications for this batch
            return [{"id": item["id"], "classification": "error"} 
                   for item in batch_items]
    
    def classify_all_cases(self):
        """Classify all medical cases in batches."""
        print("Loading medical cases...")
        cases = self.load_data()
        total_cases = len(cases)
        print(f"Total cases to classify: {total_cases}")
        
        # Load existing progress if available
        self.load_progress()
        
        # Filter out already processed cases
        cases_to_process = [case for case in cases if case["id"] not in self.processed_ids]
        
        if len(cases_to_process) == 0:
            print("All cases have already been processed!")
            self.create_final_output(cases, self.classification_results)
            return
        
        print(f"Cases to process: {len(cases_to_process)} (already processed: {len(self.processed_ids)})")
        
        # Process in batches
        for i in range(0, len(cases_to_process), self.batch_size):
            batch = cases_to_process[i:i + self.batch_size]
            batch_num = (i // self.batch_size) + 1
            total_batches = (len(cases_to_process) + self.batch_size - 1) // self.batch_size
            
            print(f"\nProcessing batch {batch_num}/{total_batches} (cases {i+1}-{min(i+self.batch_size, len(cases_to_process))})...")
            
            # Process batch
            batch_results = self.process_batch(batch)
            
            # Add results and update processed IDs
            for result in batch_results:
                self.classification_results.append(result)
                self.processed_ids.add(result["id"])
            
            # Save progress after each batch
            self.save_progress()
            self.save_current_output(cases)
            
            print(f"Processed {len(self.classification_results)} classifications total...")
            print(f"Progress saved to {self.output_file}")
        
        # Create final output with original data and classifications
        print("\nCreating final classified dataset...")
        self.create_final_output(cases, self.classification_results)
        
        # Clean up progress file after successful completion
        if self.progress_file.exists():
            self.progress_file.unlink()
            print("Removed progress file after successful completion")
        
        print(f"\nClassification complete! Results saved to {self.output_file}")
        print(f"Metadata saved to {self.metadata_file}")
    
    def create_final_output(self, original_cases: List[Dict[str, Any]], classification_results: List[Dict[str, Any]]):
        """Create final output combining original data with classifications."""
        # Create lookup for classifications (without reasoning)
        classification_lookup = {
            result["id"]: result["classification"]
            for result in classification_results
        }
        
        # Add classification field to each case
        classified_cases = []
        for case in original_cases:
            case_with_classification = case.copy()
            case_id = case["id"]
            
            if case_id in classification_lookup:
                case_with_classification["classification"] = classification_lookup[case_id]
            else:
                case_with_classification["classification"] = "unclassified"
            
            classified_cases.append(case_with_classification)
        
        # Save main output as a single JSON array
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(classified_cases, f, indent=2, ensure_ascii=False)
        
        # Calculate statistics
        condition_diagnostic_count = sum(1 for case in classified_cases if case["classification"] == "condition_diagnostic")
        clinical_action_count = sum(1 for case in classified_cases if case["classification"] == "clinical_action")
        unclassified_count = sum(1 for case in classified_cases if case["classification"] == "unclassified")
        error_count = sum(1 for case in classified_cases if case["classification"] == "error")
        
        # Create metadata with statistics
        metadata = {
            "classification_date": datetime.now().isoformat(),
            "total_cases": len(original_cases),
            "statistics": {
                "condition_diagnostic": condition_diagnostic_count,
                "clinical_action": clinical_action_count,
                "unclassified": unclassified_count,
                "error": error_count
            },
            "percentages": {
                "condition_diagnostic": f"{(condition_diagnostic_count / len(original_cases) * 100):.2f}%",
                "clinical_action": f"{(clinical_action_count / len(original_cases) * 100):.2f}%",
                "unclassified": f"{(unclassified_count / len(original_cases) * 100):.2f}%",
                "error": f"{(error_count / len(original_cases) * 100):.2f}%"
            },
            "batch_size": self.batch_size,
            "model": "gpt-4o",
            "temperature": 0.1
        }
        
        # Save metadata
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        print(f"\nClassification Statistics:")
        print(f"Condition diagnostics: {condition_diagnostic_count} ({(condition_diagnostic_count / len(original_cases) * 100):.2f}%)")
        print(f"Clinical actions: {clinical_action_count} ({(clinical_action_count / len(original_cases) * 100):.2f}%)")
        if unclassified_count > 0:
            print(f"Unclassified: {unclassified_count}")
        if error_count > 0:
            print(f"Errors: {error_count}")


if __name__ == "__main__":
    classifier = MedicalCaseClassifier(batch_size=20)
    classifier.classify_all_cases()