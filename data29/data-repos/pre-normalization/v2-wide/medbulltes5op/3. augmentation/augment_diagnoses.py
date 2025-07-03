"""
Diagnosis Augmentation Script
Augments condition_diagnostic cases with severity and ICD10 codes using LLM batching
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


class DiagnosisAugmenter:
    """Augments medical diagnoses with severity and ICD10 codes."""
    
    def __init__(self, batch_size: int = 5):
        self.batch_size = batch_size
        self.llm = AzureLLM("gpt-4o", temperature=0.1)
        self.output_file = Path(__file__).parent / "medbulltes5op_augmented.json"
        self.metadata_file = Path(__file__).parent / "augmentation_metadata.json"
        self.progress_file = Path(__file__).parent / "augmentation_progress.json"
        self.augmentation_results = []
        self.processed_ids = set()
    
    def load_data(self) -> List[Dict[str, Any]]:
        """Load the classified medical cases."""
        data_path = Path(__file__).parent.parent / "2. crive-diagnosis" / "medbulltes5op_classified.json"
        with open(data_path, 'r', encoding='utf-8') as f:
            all_cases = json.load(f)
        
        # Filter only condition_diagnostic cases
        condition_cases = [case for case in all_cases if case.get("classification") == "condition_diagnostic"]
        return condition_cases
    
    def create_augmentation_prompt(self) -> str:
        """Create the prompt for diagnosis augmentation."""
        return """Analyze each medical case and provide:
1. Name: The specific diagnosis name
2. Severity: Rate from S0 (mildest) to S10 (most severe)
3. ICD10: The most specific ICD-10 code for this diagnosis
4. Complexity: Rate from C0 (simplest) to C10 (most complex) — return this at the same level as the case ID (do NOT nest it under diagnosis)

Consider clinical presentation, urgency, and potential outcomes for severity.
Consider diagnostic difficulty, multiple comorbidities, and case nuances for complexity."""
    
    def create_augmentation_schema(self) -> Dict[str, Any]:
        """Create the schema for augmentation results."""
        return {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "complexity": {
                    "type": "string",
                    "enum": ["C0", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9", "C10"]
                },
                "diagnosis": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "severity": {
                            "type": "string",
                            "enum": ["S0", "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9", "S10"]
                        },
                        "icd10": {"type": "string"}
                    },
                    "required": ["name", "severity", "icd10"],
                    "additionalProperties": False
                }
            },
            "required": ["id", "complexity", "diagnosis"],
            "additionalProperties": False
        }
    
    def load_progress(self):
        """Load existing progress if available."""
        if self.progress_file.exists():
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                progress_data = json.load(f)
                self.augmentation_results = progress_data.get("augmentation_results", [])
                # Backward-compatibility: migrate old records where complexity is nested inside diagnosis
                for res in self.augmentation_results:
                    if "complexity" not in res and isinstance(res.get("diagnosis"), dict) and "complexity" in res["diagnosis"]:
                        res["complexity"] = res["diagnosis"].pop("complexity")
                self.processed_ids = set(progress_data.get("processed_ids", []))
                print(f"Resuming from previous progress: {len(self.processed_ids)} cases already processed")
    
    def save_progress(self):
        """Save current progress."""
        progress_data = {
            "augmentation_results": self.augmentation_results,
            "processed_ids": list(self.processed_ids)
        }
        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, indent=2, ensure_ascii=False)
    
    def save_current_output(self, all_cases: List[Dict[str, Any]]):
        """Save current state of augmented cases."""
        # Create lookup for augmentations
        augmentation_lookup = {
            result["id"]: result
            for result in self.augmentation_results
        }
        
        # Build augmented cases with complexity at top level
        augmented_cases = []
        for case in all_cases:
            if case["id"] in augmentation_lookup:
                augmentation_data = augmentation_lookup[case["id"]]
                augmented_case = {
                    "id": case["id"],
                    "case": case["case"],
                    "complexity": augmentation_data["complexity"],
                    "diagnosis": {
                        "name": augmentation_data["diagnosis"]["name"],
                        "severity": augmentation_data["diagnosis"]["severity"],
                        "icd10": augmentation_data["diagnosis"]["icd10"]
                    },
                    "classification": case["classification"]
                }
            else:
                # Keep original structure if not augmented yet
                augmented_case = case.copy()
            
            augmented_cases.append(augmented_case)
        
        # Save to file
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(augmented_cases, f, indent=2, ensure_ascii=False)
    
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
        
        # Get augmentations from LLM
        prompt = self.create_augmentation_prompt()
        schema = self.create_augmentation_schema()
        
        try:
            results = self.llm.generate(
                prompt=prompt,
                batch_items=batch_items,
                schema=schema,
                temperature=0.1,
                max_tokens=2000
            )
            
            return results
        except Exception as e:
            print(f"Error processing batch: {e}")
            # Return default augmentations for this batch
            return [{
                "id": item["id"],
                "complexity": "C5",
                "diagnosis": {
                    "name": item["diagnosis"],
                    "severity": "S5",
                    "icd10": "R69"  # Unspecified illness
                }
            } for item in batch_items]
    
    def augment_all_diagnoses(self):
        """Augment all condition_diagnostic cases."""
        print("Loading condition_diagnostic cases...")
        cases = self.load_data()
        total_cases = len(cases)
        print(f"Total condition_diagnostic cases to augment: {total_cases}")
        
        # Load any existing progress
        self.load_progress()
        
        # Filter out already processed cases
        remaining_cases = [case for case in cases if case["id"] not in self.processed_ids]
        
        if not remaining_cases:
            print("All cases have been processed!")
        else:
            print(f"Processing {len(remaining_cases)} remaining cases...")
            
            # Process in batches
            for i in range(0, len(remaining_cases), self.batch_size):
                batch = remaining_cases[i:i + self.batch_size]
                batch_num = (i // self.batch_size) + 1
                total_batches = (len(remaining_cases) + self.batch_size - 1) // self.batch_size
                
                print(f"\nProcessing batch {batch_num}/{total_batches} (cases {i+1}-{min(i+self.batch_size, len(remaining_cases))})...")
                
                # Process batch
                batch_results = self.process_batch(batch)
                
                # Update results
                self.augmentation_results.extend(batch_results)
                self.processed_ids.update(result["id"] for result in batch_results)
                
                # Save progress
                self.save_progress()
                self.save_current_output(cases)
                
                print(f"Saved {len(self.augmentation_results)} augmentations so far...")
        
        # Create final output and metadata
        print("\nCreating final augmented dataset...")
        self.create_final_output(cases)
        
        # Clean up progress file
        if self.progress_file.exists():
            self.progress_file.unlink()
        
        print(f"\nAugmentation complete! Results saved to {self.output_file}")
        print(f"Metadata saved to {self.metadata_file}")
    
    def create_final_output(self, cases: List[Dict[str, Any]]):
        """Create final output with augmented diagnoses."""
        # Save final augmented data
        self.save_current_output(cases)
        
        # Calculate statistics
        severity_counts = {}
        complexity_counts = {}
        for result in self.augmentation_results:
            severity = result["diagnosis"]["severity"]
            complexity = result["complexity"]
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            complexity_counts[complexity] = complexity_counts.get(complexity, 0) + 1
        
        # Create metadata
        metadata = {
            "augmentation_date": datetime.now().isoformat(),
            "total_condition_diagnostic_cases": len(cases),
            "severity_distribution": severity_counts,
            "complexity_distribution": complexity_counts,
            "batch_size": self.batch_size,
            "model": "gpt-4o",
            "temperature": 0.1
        }
        
        # Save metadata
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        print(f"\nSeverity Distribution:")
        for severity in sorted(severity_counts.keys()):
            count = severity_counts[severity]
            percentage = (count / len(cases) * 100)
            print(f"{severity}: {count} cases ({percentage:.1f}%)")
        
        print(f"\nComplexity Distribution:")
        for complexity in sorted(complexity_counts.keys()):
            count = complexity_counts[complexity]
            percentage = (count / len(cases) * 100)
            print(f"{complexity}: {count} cases ({percentage:.1f}%)")


if __name__ == "__main__":
    augmenter = DiagnosisAugmenter(batch_size=5)
    augmenter.augment_all_diagnoses()