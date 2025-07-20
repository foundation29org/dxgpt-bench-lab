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
import logging
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
    
    def __init__(self, logger=None):
        """Initialize the Medical Labeler with Azure Text Analytics client
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger
        
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
                        
                        # Skip MTHU codes - these are not valid medical codes
                        if entity_id.startswith('MTHU'):
                            continue
                        
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
            # Log request details
            if self.logger:
                self.logger.info(f"Making Azure Text Analytics request for {len(texts)} texts")
                self.logger.info(f"Texts to process: {[text[:50] + ('...' if len(text) > 50 else '') for text in texts]}")
                self.logger.info(f"Azure endpoint: {self.endpoint}")
            
            # Call Azure Text Analytics for health entities (Long Running Operation)
            poller = self.client.begin_analyze_healthcare_entities(
                documents=texts,
                language="en",
                model_version="latest"
            )
            
            if self.logger:
                self.logger.info(f"Azure Text Analytics LRO started, waiting for completion...")
            
            # Wait for the operation to complete and get results
            response = poller.result()
            
            if self.logger:
                self.logger.info(f"Azure Text Analytics LRO completed successfully")
            
            results = {}
            
            for idx, result in enumerate(response):
                text = texts[idx]
                
                if not result.is_error:
                    # Log successful processing
                    if self.logger:
                        self.logger.info(f"Azure processing successful for text '{text[:30]}...' - Found {len(result.entities)} entities")
                    
                    # 🔧 DEBUG: Show what entities we got
                    print(f"🔍 DEBUG: Processing '{text}' - Found {len(result.entities)} entities")
                    
                    for entity_idx, entity in enumerate(result.entities):
                        print(f"   📋 Entity: '{entity.text}' | Category: {entity.category} | Confidence: {entity.confidence_score:.2f}")
                        
                        # Log detailed entity information
                        if self.logger:
                            self.logger.info(f"  Entity[{entity_idx+1}]: '{entity.text}' | Category: {entity.category} | Confidence: {entity.confidence_score:.2f}")
                            if hasattr(entity, 'offset'):
                                self.logger.info(f"    Offset: {entity.offset}, Length: {entity.length}")
                        
                        if hasattr(entity, 'data_sources') and entity.data_sources:
                            for ds_idx, ds in enumerate(entity.data_sources):
                                print(f"      🔗 Data Source: {ds.name} | ID: {ds.entity_id}")
                                if self.logger:
                                    self.logger.info(f"    DataSource[{ds_idx+1}]: {ds.name} | ID: {ds.entity_id}")
                        else:
                            print(f"      ⚠️  No data sources found for this entity")
                            if self.logger:
                                self.logger.warning(f"    No data sources found for entity '{entity.text}'")
                    
                    medical_codes = self._extract_medical_codes(result.entities)
                    results[text] = medical_codes
                    
                    # Log extracted codes in detail
                    total_codes = sum(len(codes) for codes in medical_codes.values())
                    print(f"   ✅ Extracted {total_codes} total medical codes: {medical_codes}")
                    print()
                    
                    if self.logger:
                        self.logger.info(f"Medical codes extracted for '{text[:30]}...': Total={total_codes}")
                        for code_type, codes in medical_codes.items():
                            if codes:
                                self.logger.info(f"  {code_type.upper()}: {codes}")
                            else:
                                self.logger.info(f"  {code_type.upper()}: []")
                
                else:
                    # Handle Azure Text Analytics errors
                    error_msg = f"Azure Text Analytics error for text: {text[:50]}..."
                    print(f"⚠️  {error_msg}")
                    
                    if self.logger:
                        self.logger.error(f"AZURE_ERROR: {error_msg}")
                        if hasattr(result, 'error'):
                            self.logger.error(f"Error details: {result.error}")
                        self.logger.error(f"Full text that failed: {text}")
                    
                    results[text] = {
                        "icd10": [],
                        "snomed": [],
                        "omim": [],
                        "orpha": []
                    }
            
            return results
        
        except Exception as e:
            error_msg = f"❌ Error calling Azure Text Analytics: {str(e)}"
            print(error_msg)
            
            if self.logger:
                self.logger.error(f"AZURE_API_FAILURE: {error_msg}")
                self.logger.error(f"Exception type: {type(e).__name__}")
                self.logger.error(f"Full exception details: {repr(e)}")
                
                # Categorize different types of Azure errors
                error_str = str(e).lower()
                if "timeout" in error_str or "connection" in error_str:
                    self.logger.error(f"NETWORK_ERROR: Connection timeout or network issue with Azure API")
                elif "authentication" in error_str or "credential" in error_str:
                    self.logger.error(f"AUTH_ERROR: Authentication failure with Azure Text Analytics")
                elif "quota" in error_str or "limit" in error_str:
                    self.logger.error(f"QUOTA_ERROR: Azure Text Analytics quota or rate limit exceeded")
                elif "unauthorized" in error_str or "403" in error_str:
                    self.logger.error(f"PERMISSION_ERROR: Insufficient permissions for Azure Text Analytics")
                elif "not found" in error_str or "404" in error_str:
                    self.logger.error(f"ENDPOINT_ERROR: Azure Text Analytics endpoint not found")
                else:
                    self.logger.error(f"UNKNOWN_AZURE_ERROR: Unclassified Azure API error")
                
                self.logger.error(f"Failed texts: {[text[:30] + '...' for text in texts]}")
            
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
        start_msg = f"🔬 Starting medical code attribution for {len(dataset)} cases..."
        azure_msg = f"🔗 Using Azure Text Analytics for entity recognition"
        
        print(start_msg)
        print(azure_msg)
        print("-" * 60)
        
        if self.logger:
            self.logger.info(start_msg)
            self.logger.info(azure_msg)
        
        # Collect all unique DDX texts for batch processing
        unique_ddx_texts = set()
        cases_with_empty_ddx = 0
        
        for i, case in enumerate(dataset):
            case_id = case.get('id', f'case_{i+1}')
            ddx_details = case.get('ddx_details', {})
            
            if not ddx_details:
                cases_with_empty_ddx += 1
                if self.logger:
                    self.logger.warning(f"Case {case_id} has empty DDX details - no medical codes will be attributed")
            else:
                for ddx_name in ddx_details.keys():
                    unique_ddx_texts.add(ddx_name)
                    if self.logger and len(ddx_details) == 1:  # Log only for the first DDX per case
                        self.logger.info(f"Case {case_id} has {len(ddx_details)} DDX entries")
        
        unique_msg = f"📝 Found {len(unique_ddx_texts)} unique DDX terms to process"
        print(unique_msg)
        if self.logger:
            self.logger.info(unique_msg)
            if cases_with_empty_ddx > 0:
                self.logger.warning(f"Found {cases_with_empty_ddx} cases with empty DDX details")
            
            # Log sample of unique DDX texts
            sample_ddx = list(unique_ddx_texts)[:10]
            self.logger.info(f"Sample DDX terms: {sample_ddx}")
            if len(unique_ddx_texts) > 10:
                self.logger.info(f"... and {len(unique_ddx_texts) - 10} more unique terms")
        
        # Process unique DDX texts in batches
        ddx_codes_cache = {}
        unique_ddx_list = list(unique_ddx_texts)
        
        batch_size = 5  # Azure Text Analytics batch size limit (max 5 records)
        
        for i in range(0, len(unique_ddx_list), batch_size):
            batch = unique_ddx_list[i:i+batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(unique_ddx_list) + batch_size - 1) // batch_size
            
            batch_msg = f"[{batch_num}/{total_batches}] Processing batch of {len(batch)} DDX terms..."
            print(f"{batch_msg} ", end="", flush=True)
            if self.logger:
                self.logger.info(batch_msg)
            
            batch_results = self._get_medical_codes_for_texts(batch)
            ddx_codes_cache.update(batch_results)
            
            print("✅ Done")
        
        print("-" * 60)
        
        # Apply medical codes to all cases
        results = []
        
        for i, case in enumerate(dataset, 1):
            case_id = case.get('id', f'case_{i}')
            case_msg = f"[{i}/{len(dataset)}] Processing case {case_id}..."
            print(f"{case_msg} ", end="", flush=True)
            if self.logger:
                self.logger.info(case_msg)
            
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
                    
                    # Log when no codes are found for a DDX
                    codes = ddx_codes_cache[ddx_name]
                    total_codes = sum(len(code_list) for code_list in codes.values())
                    if total_codes == 0 and self.logger:
                        self.logger.warning(f"No medical codes found for DDX '{ddx_name}' in case {case_id}")
                else:
                    # Fallback to empty codes if not in cache
                    updated_ddx_info['medical_codes'] = {
                        "icd10": [],
                        "snomed": [],
                        "omim": [],
                        "orpha": []
                    }
                    if self.logger:
                        self.logger.error(f"DDX '{ddx_name}' not found in cache for case {case_id} - this should not happen")
                
                updated_ddx_details[ddx_name] = updated_ddx_info
            
            case_with_codes['ddx_details'] = updated_ddx_details
            results.append(case_with_codes)
            
            ddx_count = len(ddx_details)
            success_msg = f"✅ Added codes to {ddx_count} DDX"
            print(success_msg)
            if self.logger:
                self.logger.info(f"[{i}/{len(dataset)}] Added codes to {ddx_count} DDX for case {case_id}")
        
        print("-" * 60)
        completion_msg = f"✅ Medical code attribution completed!"
        stats_msg = f"📊 Processed {len(results)} cases with medical codes"
        
        print(completion_msg)
        print(stats_msg)
        
        if self.logger:
            self.logger.info(completion_msg)
            self.logger.info(stats_msg)
        
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
            
            save_msg = f"💾 Labeled results saved to: {output_path}"
            print(save_msg)
            if self.logger:
                self.logger.info(save_msg)
            
        except Exception as e:
            error_msg = f"❌ Error saving results: {str(e)}"
            print(error_msg)
            if self.logger:
                self.logger.error(error_msg)
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
                remove_msg = f"🗑️  Removed emulator output: {emulator_output_path}"
                print(remove_msg)
                if self.logger:
                    self.logger.info(remove_msg)
            
            primary_msg = f"✅ Labeled output is now the primary dataset file"
            print(primary_msg)
            if self.logger:
                self.logger.info(primary_msg)
            
        except Exception as e:
            warning_msg = f"⚠️  Warning: Could not remove emulator output: {str(e)}"
            print(warning_msg)
            if self.logger:
                self.logger.warning(warning_msg)

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