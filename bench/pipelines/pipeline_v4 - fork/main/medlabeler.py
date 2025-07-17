#!/usr/bin/env python3
"""
Medical Labeler - Medical Code Attribution Module
================================================

This module handles the attribution of medical codes (ICD-10, SNOMED, OMIM, ORPHA)
to differential diagnoses using Azure Text Analytics.

Features:
- Azure Text Analytics integration for medical entity recognition
- Batch processing for efficiency
- Deduplication to avoid redundant API calls
- Progress tracking and error handling
- Clean terminal output for monitoring
"""

import json
import os
import sys
from typing import Dict, List, Any, Set, Optional
from datetime import datetime
import yaml

# Azure Text Analytics
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class MedicalLabeler:
    """Medical code attribution using Azure Text Analytics"""
    
    def __init__(self):
        """Initialize the Medical Labeler with Azure Text Analytics client"""
        # Get Azure credentials from environment
        self.endpoint = os.getenv('AZURE_LANGUAGE_ENDPOINT')
        self.key = os.getenv('AZURE_LANGUAGE_KEY')
        
        if not self.endpoint or not self.key:
            raise ValueError("Azure Language service credentials not found in environment variables")
        
        # Initialize Azure Text Analytics client
        self.client = TextAnalyticsClient(
            endpoint=self.endpoint,
            credential=AzureKeyCredential(self.key)
        )
    
    def _extract_medical_codes(self, entities: List[Any]) -> Dict[str, List[str]]:
        """
        Extract medical codes from Azure Text Analytics entities
        
        Args:
            entities: List of entities from Azure Text Analytics
            
        Returns:
            Dictionary with medical codes by type
        """
        medical_codes = {
            "icd10": [],
            "snomed": [],
            "omim": [],
            "orpha": []
        }
        
        for entity in entities:
            # Extract different types of medical codes
            if hasattr(entity, 'data_sources'):
                for data_source in entity.data_sources:
                    if hasattr(data_source, 'name') and hasattr(data_source, 'entity_id'):
                        source_name = data_source.name.lower()
                        entity_id = data_source.entity_id
                        
                        if 'icd10' in source_name or 'icd-10' in source_name:
                            if entity_id not in medical_codes["icd10"]:
                                medical_codes["icd10"].append(entity_id)
                        elif 'snomed' in source_name or 'sct' in source_name:
                            if entity_id not in medical_codes["snomed"]:
                                medical_codes["snomed"].append(entity_id)
                        elif 'omim' in source_name:
                            if entity_id not in medical_codes["omim"]:
                                medical_codes["omim"].append(entity_id)
                        elif 'orpha' in source_name or 'orphanet' in source_name:
                            if entity_id not in medical_codes["orpha"]:
                                medical_codes["orpha"].append(entity_id)
        
        return medical_codes
    
    def _get_medical_codes_for_texts(self, texts: List[str]) -> Dict[str, Dict[str, List[str]]]:
        """
        Get medical codes for a list of texts using Azure Text Analytics
        
        Args:
            texts: List of medical text strings
            
        Returns:
            Dictionary mapping text to medical codes
        """
        try:
            # Call Azure Text Analytics for health entities (Long Running Operation)
            poller = self.client.begin_analyze_healthcare_entities(
                documents=texts,
                language="en",
                model_version="latest"
            )
            
            # Wait for the operation to complete and get results
            response = poller.result()
            
            results = {}
            
            for idx, result in enumerate(response):
                if not result.is_error:
                    # 🔧 DEBUG: Show what entities we got
                    print(f"🔍 DEBUG: Processing '{texts[idx]}' - Found {len(result.entities)} entities")
                    for entity in result.entities:
                        print(f"   📋 Entity: '{entity.text}' | Category: {entity.category} | Confidence: {entity.confidence_score:.2f}")
                        if hasattr(entity, 'data_sources') and entity.data_sources:
                            for ds in entity.data_sources:
                                print(f"      🔗 Data Source: {ds.name} | ID: {ds.entity_id}")
                        else:
                            print(f"      ⚠️  No data sources found for this entity")
                    
                    medical_codes = self._extract_medical_codes(result.entities)
                    results[texts[idx]] = medical_codes
                    
                    # 🔧 DEBUG: Show extracted codes
                    total_codes = sum(len(codes) for codes in medical_codes.values())
                    print(f"   ✅ Extracted {total_codes} total medical codes: {medical_codes}")
                    print()
                else:
                    print(f"⚠️  Azure Text Analytics error for text: {texts[idx][:50]}...")
                    results[texts[idx]] = {
                        "icd10": [],
                        "snomed": [],
                        "omim": [],
                        "orpha": []
                    }
            
            return results
        
        except Exception as e:
            print(f"❌ Error calling Azure Text Analytics: {str(e)}")
            # Return empty results for all texts
            return {text: {"icd10": [], "snomed": [], "omim": [], "orpha": []} for text in texts}
    
    def process_dataset(self, dataset: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process dataset to add medical codes to DDX
        
        Args:
            dataset: List of cases with DDX details
            
        Returns:
            List of cases with medical codes added to DDX
        """
        print(f"🔬 Starting medical code attribution for {len(dataset)} cases...")
        print(f"🔗 Using Azure Text Analytics for entity recognition")
        print("-" * 60)
        
        # Collect all unique DDX texts for batch processing
        unique_ddx_texts = set()
        for case in dataset:
            ddx_details = case.get('ddx_details', {})
            for ddx_name in ddx_details.keys():
                unique_ddx_texts.add(ddx_name)
        
        print(f"📝 Found {len(unique_ddx_texts)} unique DDX terms to process")
        
        # Process unique DDX texts in batches
        ddx_codes_cache = {}
        unique_ddx_list = list(unique_ddx_texts)
        
        batch_size = 5  # Azure Text Analytics batch size limit (max 5 records)
        
        for i in range(0, len(unique_ddx_list), batch_size):
            batch = unique_ddx_list[i:i+batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(unique_ddx_list) + batch_size - 1) // batch_size
            
            print(f"[{batch_num}/{total_batches}] Processing batch of {len(batch)} DDX terms... ", end="", flush=True)
            
            batch_results = self._get_medical_codes_for_texts(batch)
            ddx_codes_cache.update(batch_results)
            
            print("✅ Done")
        
        print("-" * 60)
        
        # Apply medical codes to all cases
        results = []
        
        for i, case in enumerate(dataset, 1):
            case_id = case.get('id', f'case_{i}')
            print(f"[{i}/{len(dataset)}] Processing case {case_id}... ", end="", flush=True)
            
            # Create a copy of the case
            case_with_codes = case.copy()
            ddx_details = case_with_codes.get('ddx_details', {})
            
            # Add medical codes to each DDX
            updated_ddx_details = {}
            for ddx_name, ddx_info in ddx_details.items():
                updated_ddx_info = ddx_info.copy()
                
                # Get medical codes from cache
                if ddx_name in ddx_codes_cache:
                    updated_ddx_info['medical_codes'] = ddx_codes_cache[ddx_name]
                else:
                    # Fallback to empty codes if not in cache
                    updated_ddx_info['medical_codes'] = {
                        "icd10": [],
                        "snomed": [],
                        "omim": [],
                        "orpha": []
                    }
                
                updated_ddx_details[ddx_name] = updated_ddx_info
            
            case_with_codes['ddx_details'] = updated_ddx_details
            results.append(case_with_codes)
            
            ddx_count = len(ddx_details)
            print(f"✅ Added codes to {ddx_count} DDX")
        
        print("-" * 60)
        print(f"✅ Medical code attribution completed!")
        print(f"📊 Processed {len(results)} cases with medical codes")
        
        return results
    
    def save_results(self, results: List[Dict[str, Any]], output_path: str) -> None:
        """
        Save labeled results to JSON file
        
        Args:
            results: List of cases with medical codes
            output_path: Path to save the results
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save results
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Labeled results saved to: {output_path}")
            
        except Exception as e:
            print(f"❌ Error saving results: {str(e)}")
            raise
    
    def replace_emulator_output(self, emulator_output_path: str, labeled_output_path: str) -> None:
        """
        Replace emulator output with labeled output
        
        Args:
            emulator_output_path: Path to emulator output file
            labeled_output_path: Path to labeled output file
        """
        try:
            # Delete emulator output if it exists
            if os.path.exists(emulator_output_path):
                os.remove(emulator_output_path)
                print(f"🗑️  Removed emulator output: {emulator_output_path}")
            
            print(f"✅ Labeled output is now the primary dataset file")
            
        except Exception as e:
            print(f"⚠️  Warning: Could not remove emulator output: {str(e)}")

def main():
    """Main function for standalone execution"""
    # Load configuration with preference for saved copy
    # Import here to avoid circular imports
    from main import load_config_with_fallback
    config = load_config_with_fallback()
    
    # Assume input is from emulator output
    # In practice, this would be called from main.py with proper paths
    input_path = os.path.join(os.path.dirname(__file__), 'output', 'emulator_output.json')
    
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
    except FileNotFoundError:
        print(f"❌ Input file not found: {input_path}")
        sys.exit(1)
    
    # Initialize labeler
    labeler = MedicalLabeler()
    
    # Process dataset
    results = labeler.process_dataset(dataset)
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    output_path = os.path.join(
        os.path.dirname(__file__), 'output',
        f"labeled_results_{timestamp}.json"
    )
    
    labeler.save_results(results, output_path)

if __name__ == "__main__":
    main()