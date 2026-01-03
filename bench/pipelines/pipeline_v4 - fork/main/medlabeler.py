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
import time
from typing import Dict, List, Any, Set, Optional, Tuple
from datetime import datetime
import yaml

# Azure Text Analytics
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv

# Azure Translator imports
try:
    from azure.ai.translation.text import TextTranslationClient, TranslatorCredential
    from azure.core.exceptions import HttpResponseError
    AZURE_TRANSLATOR_AVAILABLE = True
except ImportError:
    AZURE_TRANSLATOR_AVAILABLE = False

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
        
        # Initialize Azure Translator client for DDX translation
        self.translator_client = None
        if AZURE_TRANSLATOR_AVAILABLE:
            translator_key = os.getenv('AZURE_TRANSLATOR_KEY')
            translator_endpoint = os.getenv('AZURE_TRANSLATOR_ENDPOINT')
            translator_region = os.getenv('AZURE_TRANSLATOR_REGION', 'global')
            
            if translator_key and translator_endpoint:
                try:
                    self.translator_client = TextTranslationClient(
                        endpoint=translator_endpoint,
                        credential=TranslatorCredential(translator_key, translator_region)
                    )
                    if self.logger:
                        self.logger.info("✅ Azure Translator client initialized for DDX translation")
                        self.logger.info(f"   Translator endpoint: {translator_endpoint}")
                        self.logger.info(f"   Translator region: {translator_region}")
                except Exception as e:
                    if self.logger:
                        self.logger.warning(f"Could not initialize Azure Translator: {e}. DDX translation disabled.")
                    self.translator_client = None
            else:
                if self.logger:
                    self.logger.warning("⚠️  Azure Translator credentials not found in environment variables:")
                    self.logger.warning(f"   AZURE_TRANSLATOR_KEY: {'Set' if translator_key else 'NOT SET'}")
                    self.logger.warning(f"   AZURE_TRANSLATOR_ENDPOINT: {'Set' if translator_endpoint else 'NOT SET'}")
                    self.logger.warning("   DDX translation will be disabled. DDX texts will be sent to Azure Text Analytics as-is.")
        else:
            if self.logger:
                self.logger.warning("⚠️  Azure Translator library (azure-ai-translation-text) not available.")
                self.logger.warning("   Install it with: pip install azure-ai-translation-text")
                self.logger.warning("   DDX translation will be disabled. DDX texts will be sent to Azure Text Analytics as-is.")
    
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
            if hasattr(entity, 'data_sources') and entity.data_sources:
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
    
    def _is_retryable_translation_error(self, error: Exception) -> bool:
        """
        Determine if a translation error is retryable (transient error that might succeed on retry)
        
        Args:
            error: The exception that occurred
            
        Returns:
            True if the error is retryable, False otherwise
        """
        error_str = str(error).lower()
        error_type = type(error).__name__
        
        # Check for rate limit errors (429)
        if "429" in error_str or "rate" in error_str or "limit" in error_str or "nocapacity" in error_str:
            return True
        
        # Check for server errors (500, 502, 503, 504)
        if any(code in error_str for code in ["500", "502", "503", "504", "server error", "internal error"]):
            return True
        
        # Check for timeout/connection errors
        if "timeout" in error_str or "connection" in error_str or "timed out" in error_str:
            return True
        
        # Check for specific error types that are typically retryable
        retryable_types = ["RateLimitError", "TimeoutError", "ConnectionError", "HTTPError"]
        if any(rt in error_type for rt in retryable_types):
            return True
        
        # Non-retryable errors (authentication, invalid request, etc.)
        if "authentication" in error_str or "unauthorized" in error_str or "401" in error_str or "403" in error_str:
            return False
        
        if "invalid" in error_str and "request" in error_str:
            return False
        
        # Default: don't retry unknown errors
        return False
    
    def _translate_ddx_text(self, text: str, max_retries: int = 3, base_delay: float = 1.0) -> str:
        """
        Translate DDX text to English using Azure Translator with automatic retry for transient errors
        Only translates if the detected language is different from English
        
        Args:
            text: Original DDX text
            max_retries: Maximum number of retry attempts (default: 3)
            base_delay: Base delay in seconds for exponential backoff (default: 1.0)
            
        Returns:
            Translated DDX text, or original if translation fails or not needed
        """
        if not self.translator_client:
            return text
        
        if not text or not text.strip():
            return text
        
        last_error = None
        
        # Retry loop
        for attempt in range(max_retries + 1):
            try:
                # First, detect the source language
                detect_response = self.translator_client.detect_language(
                    body=[{"text": text}]
                )
                
                if not detect_response or len(detect_response) == 0:
                    if self.logger:
                        self.logger.warning(f"Could not detect language for DDX '{text[:30]}...', skipping translation")
                    return text
                
                detected_language = detect_response[0].language
                confidence = getattr(detect_response[0], 'confidence_score', None)
                
                # Only translate if detected language is different from English
                if detected_language.lower() == 'en':
                    if self.logger:
                        self.logger.debug(f"DDX already in English ({detected_language}), skipping translation")
                    return text
                
                # Translate to English
                response = self.translator_client.translate(
                    content=[text],
                    to=['en']
                )
                
                if response and len(response) > 0 and len(response[0].translations) > 0:
                    translated_text = response[0].translations[0].text
                    if self.logger:
                        if attempt > 0:
                            self.logger.info(f"   ✅ Translation retry {attempt} succeeded for DDX '{text[:30]}...'")
                        conf_str = f" (confidence: {confidence:.2f})" if confidence else ""
                        self.logger.info(f"   🔄 DDX translation: {detected_language}{conf_str} → English")
                        self.logger.info(f"      Original: '{text}'")
                        self.logger.info(f"      Translated: '{translated_text}'")
                    return translated_text
                else:
                    if self.logger:
                        self.logger.warning(f"Translation returned empty result for DDX '{text[:30]}...', using original text")
                    return text
                    
            except HttpResponseError as e:
                last_error = e
                is_retryable = self._is_retryable_translation_error(e)
                
                if not is_retryable:
                    # Non-retryable error (authentication, invalid request, etc.)
                    if self.logger:
                        self.logger.error(f"❌ Non-retryable Azure Translator error for DDX '{text[:30]}...': {e}. Using original text.")
                    return text
                
                # If this was the last attempt, don't retry
                if attempt >= max_retries:
                    if self.logger:
                        self.logger.error(f"❌ Max retries ({max_retries}) reached for DDX translation '{text[:30]}...': {e}. Using original text.")
                    return text
                
                # Calculate exponential backoff delay
                delay = base_delay * (2 ** attempt)
                if self.logger:
                    self.logger.warning(f"⏳ Retryable Azure Translator error for DDX '{text[:30]}...', retrying in {delay:.1f} seconds... (attempt {attempt + 1}/{max_retries})")
                
                time.sleep(delay)
                
            except Exception as e:
                last_error = e
                is_retryable = self._is_retryable_translation_error(e)
                
                if not is_retryable:
                    if self.logger:
                        self.logger.error(f"❌ Non-retryable error during DDX translation '{text[:30]}...': {e}. Using original text.")
                    return text
                
                # If this was the last attempt, don't retry
                if attempt >= max_retries:
                    if self.logger:
                        self.logger.error(f"❌ Max retries ({max_retries}) reached for DDX translation '{text[:30]}...': {e}. Using original text.")
                    return text
                
                # Calculate exponential backoff delay
                delay = base_delay * (2 ** attempt)
                if self.logger:
                    self.logger.warning(f"⏳ Retryable error during DDX translation '{text[:30]}...', retrying in {delay:.1f} seconds... (attempt {attempt + 1}/{max_retries})")
                
                time.sleep(delay)
        
        # All retries exhausted
        if self.logger:
            self.logger.error(f"❌ Failed to translate DDX '{text[:30]}...' after {max_retries + 1} attempts. Using original text.")
        
        return text
    
    def _get_medical_codes_for_texts(self, texts: List[str]) -> Tuple[Dict[str, Dict[str, List[str]]], Dict[str, str]]:
        """
        Get medical codes for a list of texts using Azure Text Analytics
        Translates texts to English if needed before sending to Azure
        
        Args:
            texts: List of medical text strings (original DDX texts)
            
        Returns:
            Tuple of:
            - Dictionary mapping original text to medical codes
            - Dictionary mapping original text to translated text
        """
        try:
            # Translate texts to English if translator is available
            translated_texts = []
            original_to_translated = {}
            
            if self.translator_client:
                if self.logger:
                    self.logger.info(f"🌐 DDX Translation: Translating {len(texts)} DDX texts to English before sending to Azure Text Analytics")
                    self.logger.info(f"   Original DDX texts: {[text[:50] + ('...' if len(text) > 50 else '') for text in texts]}")
                
                for original_text in texts:
                    translated_text = self._translate_ddx_text(original_text)
                    translated_texts.append(translated_text)
                    original_to_translated[original_text] = translated_text
                    if original_text != translated_text and self.logger:
                        self.logger.info(f"   ✅ Translated: '{original_text[:40]}...' → '{translated_text[:40]}...'")
                
                if self.logger:
                    translated_count = sum(1 for orig, trans in original_to_translated.items() if orig != trans)
                    self.logger.info(f"   📊 Translation summary: {translated_count}/{len(texts)} DDX texts translated to English")
            else:
                # No translator available, use original texts
                if self.logger:
                    self.logger.warning("⚠️  DDX Translation: Azure Translator not available. Using original DDX texts (may be in Spanish).")
                translated_texts = texts
                original_to_translated = {text: text for text in texts}
            
            # Log request details
            if self.logger:
                self.logger.info(f"Making Azure Text Analytics request for {len(translated_texts)} texts")
                self.logger.info(f"Texts to process: {[text[:50] + ('...' if len(text) > 50 else '') for text in translated_texts]}")
                self.logger.info(f"Azure endpoint: {self.endpoint}")
            
            # Call Azure Text Analytics for health entities (Long Running Operation)
            # Always use English since we translate if needed
            poller = self.client.begin_analyze_healthcare_entities(
                documents=translated_texts,
                language="en",
                model_version="latest"
            )
            
            if self.logger:
                self.logger.info(f"Azure Text Analytics LRO started, waiting for completion...")
            
            # Wait for the operation to complete and get results
            response = poller.result()
            
            if self.logger:
                self.logger.info(f"Azure Text Analytics LRO completed successfully")
            
            # Check if response is valid
            if response is None:
                if self.logger:
                    self.logger.error("Azure Text Analytics returned None response")
                return {text: {"icd10": [], "snomed": [], "omim": [], "orpha": []} for text in texts}
            
            results = {}
            
            for idx, result in enumerate(response):
                # Get the translated text that was sent to Azure
                translated_text = translated_texts[idx]
                # Get the original text to use as key in results
                original_text = texts[idx]
                
                if not result.is_error:
                    # Check if entities exist and is not None
                    entities = result.entities if hasattr(result, 'entities') and result.entities is not None else []
                    
                    # Log successful processing (use original text for logging)
                    if self.logger:
                        self.logger.info(f"Azure processing successful for text '{original_text[:30]}...' - Found {len(entities)} entities")
                        if original_text != translated_text:
                            self.logger.info(f"  (Processed translated version: '{translated_text[:30]}...')")
                    
                    # 🔧 DEBUG: Show what entities we got
                    print(f"🔍 DEBUG: Processing '{original_text}' - Found {len(entities)} entities")
                    
                    for entity_idx, entity in enumerate(entities):
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
                    
                    medical_codes = self._extract_medical_codes(entities)
                    # Use original text as key (not translated)
                    results[original_text] = medical_codes
                    
                    # Log extracted codes in detail
                    total_codes = sum(len(codes) for codes in medical_codes.values())
                    print(f"   ✅ Extracted {total_codes} total medical codes: {medical_codes}")
                    print()
                    
                    if self.logger:
                        self.logger.info(f"Medical codes extracted for '{original_text[:30]}...': Total={total_codes}")
                        for code_type, codes in medical_codes.items():
                            if codes:
                                self.logger.info(f"  {code_type.upper()}: {codes}")
                            else:
                                self.logger.info(f"  {code_type.upper()}: []")
                
                else:
                    # Handle Azure Text Analytics errors
                    error_msg = f"Azure Text Analytics error for text: {original_text[:50]}..."
                    print(f"⚠️  {error_msg}")
                    
                    if self.logger:
                        self.logger.error(f"AZURE_ERROR: {error_msg}")
                        if hasattr(result, 'error'):
                            self.logger.error(f"Error details: {result.error}")
                        self.logger.error(f"Full text that failed: {original_text}")
                    
                    results[original_text] = {
                        "icd10": [],
                        "snomed": [],
                        "omim": [],
                        "orpha": []
                    }
            
            return results, original_to_translated
        
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
            empty_results = {text: {"icd10": [], "snomed": [], "omim": [], "orpha": []} for text in texts}
            empty_translations = {text: text for text in texts}  # No translation if error
            return empty_results, empty_translations
    
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
        ddx_translation_cache = {}  # Cache translations: original -> translated
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
            
            batch_results, batch_translations = self._get_medical_codes_for_texts(batch)
            ddx_codes_cache.update(batch_results)
            ddx_translation_cache.update(batch_translations)
            
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
                
                # Get medical codes from cache (using original DDX name as key)
                if ddx_name in ddx_codes_cache:
                    updated_ddx_info['medical_codes'] = ddx_codes_cache[ddx_name]
                    
                    # Update normalized_text with English translation if available
                    if ddx_name in ddx_translation_cache:
                        translated_text = ddx_translation_cache[ddx_name]
                        if translated_text != ddx_name:
                            updated_ddx_info['normalized_text'] = translated_text
                            if self.logger:
                                self.logger.debug(f"Updated normalized_text for DDX '{ddx_name}' to English: '{translated_text}'")
                    
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