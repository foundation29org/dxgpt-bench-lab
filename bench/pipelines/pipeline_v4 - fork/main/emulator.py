#!/usr/bin/env python3
"""
DXGPT Emulator - DDX Generation Module
=====================================

This module handles the generation of differential diagnoses (DDX) using LLM models.
It takes a dataset of medical cases and generates DDX lists for each case using
the specified prompt and model configuration.

Features:
- Configurable LLM models and parameters
- Structured JSON output with schema validation
- Progress tracking and error handling
- Clean terminal output for monitoring
"""

import json
import os
import sys
import ast
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import yaml

# Add project root to path (so we can import utils)
project_root = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')
project_root = os.path.abspath(project_root)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from utils.llm import get_llm
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

class DXGPTEmulator:
    """DXGPT Emulator for generating differential diagnoses"""
    
    def __init__(self, config: Dict[str, Any], logger=None):
        """
        Initialize the DXGPT Emulator
        
        Args:
            config: Configuration dictionary with emulator settings
            logger: Optional logger instance
        """
        self.config = config
        self.emulator_config = config['DXGPT_EMULATOR']
        self.logger = logger
        
        # Initialize LLM with logger
        self.llm = get_llm(self.emulator_config['MODEL'], logger=self.logger)
        
        # Load prompt template
        self.prompt_template = self._load_prompt_template()
        
        # Load output schema if enabled
        self.output_schema = None
        if self.emulator_config.get('OUTPUT_SCHEMA', False):
            self.output_schema = self._load_output_schema()
        
        # Initialize translation client if enabled
        self.translator_client = None
        self.translate_enabled = self.emulator_config.get('TRANSLATE_CASE', {}).get('ENABLED', False)
        self.target_language = self.emulator_config.get('TRANSLATE_CASE', {}).get('TARGET_LANGUAGE', 'en')
        
        if self.translate_enabled:
            if not AZURE_TRANSLATOR_AVAILABLE:
                if self.logger:
                    self.logger.warning("⚠️  Translation enabled but azure-ai-translation-text not installed.")
                    self.logger.warning("   Install it with: pip install azure-ai-translation-text")
                    self.logger.warning("   Translation disabled. Cases will be sent to LLM in original language.")
                self.translate_enabled = False
            else:
                self.translator_client = self._init_translator_client()
    
    def _load_prompt_template(self) -> str:
        """Load the prompt template from file"""
        prompt_path = os.path.join(
            os.path.dirname(__file__), '..', '..', '..', '..',
            self.emulator_config['CANDIDATE_PROMPT_PATH']
        )
        
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Prompt template not found at: {prompt_path}")
    
    def _load_output_schema(self) -> Dict[str, Any]:
        """Load the output schema from file"""
        schema_path = os.path.join(
            os.path.dirname(__file__), '..', '..', '..', '..',
            self.emulator_config['OUTPUT_SCHEMA_PATH']
        )
        
        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Output schema not found at: {schema_path}")
    
    def _init_translator_client(self):
        """Initialize Azure Translator client"""
        translator_key = os.getenv('AZURE_TRANSLATOR_KEY')
        translator_endpoint = os.getenv('AZURE_TRANSLATOR_ENDPOINT')
        translator_region = os.getenv('AZURE_TRANSLATOR_REGION', 'global')
        
        if not translator_key or not translator_endpoint:
            if self.logger:
                self.logger.warning("Translation enabled but AZURE_TRANSLATOR_KEY or AZURE_TRANSLATOR_ENDPOINT not set. Translation disabled.")
            self.translate_enabled = False
            return None
        
        try:
            credential = TranslatorCredential(translator_key, translator_region)
            client = TextTranslationClient(endpoint=translator_endpoint, credential=credential)
            if self.logger:
                self.logger.info(f"Azure Translator client initialized. Target language: {self.target_language}")
            return client
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to initialize Azure Translator client: {e}")
            self.translate_enabled = False
            return None
    
    def _translate_case_description(self, case_description: str) -> str:
        """
        Translate case description to target language using Azure Translator
        Only translates if the detected language is different from target language
        
        Args:
            case_description: Original case description
            
        Returns:
            Translated case description, or original if translation fails or not needed
        """
        if not self.translate_enabled or not self.translator_client:
            return case_description
        
        if not case_description or not case_description.strip():
            return case_description
        
        try:
            # First, detect the source language
            detect_response = self.translator_client.detect_language(
                body=[{"text": case_description}]
            )
            
            if not detect_response or len(detect_response) == 0:
                if self.logger:
                    self.logger.warning("Could not detect language, skipping translation")
                return case_description
            
            detected_language = detect_response[0].language
            confidence = getattr(detect_response[0], 'confidence_score', None)
            
            # Only translate if detected language is different from target
            if detected_language.lower() == self.target_language.lower():
                if self.logger:
                    self.logger.info(f"Case already in target language ({detected_language}), skipping translation")
                return case_description
            
            # Translate to target language
            response = self.translator_client.translate(
                content=[case_description],
                to=[self.target_language]
            )
            
            if response and len(response) > 0 and len(response[0].translations) > 0:
                translated_text = response[0].translations[0].text
                if self.logger:
                    conf_str = f" (confidence: {confidence:.2f})" if confidence else ""
                    self.logger.info(f"Case translated from {detected_language}{conf_str} to {self.target_language}")
                return translated_text
            else:
                if self.logger:
                    self.logger.warning("Translation returned empty result, using original text")
                return case_description
                
        except HttpResponseError as e:
            if self.logger:
                self.logger.error(f"Azure Translator error: {e}. Using original text.")
            return case_description
        except Exception as e:
            if self.logger:
                self.logger.error(f"Unexpected error during translation: {e}. Using original text.")
            return case_description
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """
        Determine if an error is retryable (transient error that might succeed on retry)
        
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
    
    def _generate_ddx_for_case(self, case: Dict[str, Any], max_retries: int = 5, base_delay: float = 5.0) -> Tuple[List[str], str]:
        """
        Generate DDX for a single case with automatic retry for transient errors
        
        Args:
            case: Case dictionary containing case description
            max_retries: Maximum number of retry attempts (default: 5, increased for high-demand models)
            base_delay: Base delay in seconds for exponential backoff (default: 5.0, increased for high-demand models)
            
        Returns:
            Tuple of (List of differential diagnoses, raw response)
        """
        # Format the prompt with case description
        case_description = case.get('case', '')
        
        # Check for alternative description fields if primary field is empty
        if not case_description:
            alt_description = case.get('description', '') or case.get('case_description', '') or case.get('patient_description', '')
            if alt_description:
                case_description = alt_description
        
        # Translate case description if enabled
        if self.translate_enabled and case_description:
            original_description = case_description
            case_description = self._translate_case_description(case_description)
            if self.logger and original_description != case_description:
                self.logger.info(f"Case {case.get('id', 'unknown')}: Translated case description ({len(original_description)} -> {len(case_description)} chars)")
        
        prompt = self.prompt_template.format(case_description=case_description)
        
        # Get LLM parameters
        params = self.emulator_config.get('PARAMS', {})
        
        # Check if this is a reasoning model (O3, GPT-5, or Gemini 3 Pro)
        model_name = self.emulator_config['MODEL'].lower()
        is_o3_model = 'o3' in model_name
        is_gpt5_model = 'gpt-5' in model_name or 'gpt5' in model_name
        is_gemini_model = 'gemini' in model_name
        is_reasoning_model = is_o3_model or is_gpt5_model
        
        case_id = case.get('id', 'unknown')
        last_error = None
        
        # Retry loop
        for attempt in range(max_retries + 1):
            try:
                # Log request details
                if self.logger:
                    self.logger.info(f"Generating DDX for case {case.get('id', 'unknown')} using model {model_name}")
                    self.logger.info(f"Prompt length: {len(prompt)} characters")
                    if is_gemini_model:
                        self.logger.info(f"Gemini Model parameters: thinking_level={params.get('thinking_level', 'low')}, max_tokens={params.get('max_tokens', 12000)}, temperature={params.get('temperature', 0.1)}")
                    elif is_reasoning_model:
                        model_type = "O3" if is_o3_model else "GPT-5"
                        self.logger.info(f"{model_type} Model parameters: reasoning_effort={params.get('reasoning_effort', 'low')}, max_tokens={params.get('max_tokens', 12000)}")
                    else:
                        self.logger.info(f"Standard model parameters: max_tokens={params.get('max_tokens', 4000)}, temperature={params.get('temperature', 0.1)}")
                    self.logger.info(f"Output schema enabled: {self.output_schema is not None}")
                
                # Generate response with model-appropriate parameters
                if is_gemini_model:
                    # Gemini 3 Pro uses thinking_level instead of reasoning_effort
                    if self.output_schema:
                        response = self.llm.generate(
                            prompt,
                            thinking_level=params.get('thinking_level', 'low'),
                            max_tokens=params.get('max_tokens', 12000),
                            temperature=params.get('temperature', 0.1),
                            schema=self.output_schema
                        )
                    else:
                        response = self.llm.generate(
                            prompt,
                            thinking_level=params.get('thinking_level', 'low'),
                            max_tokens=params.get('max_tokens', 12000),
                            temperature=params.get('temperature', 0.1)
                        )
                elif is_reasoning_model:
                    # Reasoning models (O3 and GPT-5) use reasoning_effort
                    # GPT-5 models can also use max_tokens (as max_completion_tokens)
                    if self.output_schema:
                        response = self.llm.generate(
                            prompt,
                            reasoning_effort=params.get('reasoning_effort', 'low'),
                            max_tokens=params.get('max_tokens', 12000),
                            schema=self.output_schema
                        )
                    else:
                        response = self.llm.generate(
                            prompt,
                            reasoning_effort=params.get('reasoning_effort', 'low'),
                            max_tokens=params.get('max_tokens', 12000)
                        )
                else:
                    # Standard models use temperature and max_tokens
                    if self.output_schema:
                        response = self.llm.generate(
                            prompt,
                            max_tokens=params.get('max_tokens', 4000),
                            temperature=params.get('temperature', 0.1),
                            schema=self.output_schema
                        )
                    else:
                        response = self.llm.generate(
                            prompt,
                            max_tokens=params.get('max_tokens', 4000),
                            temperature=params.get('temperature', 0.1)
                        )
                
                # Log successful API response
                if self.logger:
                    if attempt > 0:
                        self.logger.info(f"✅ Retry {attempt} succeeded for case {case_id}")
                    self.logger.info(f"LLM API call successful for case {case_id}")
                    self.logger.info(f"Response length: {len(str(response))} characters")
                
                # Extract DDX using unified parsing logic
                ddx_list = self._extract_ddx_from_response(response, case_id)
                return ddx_list, str(response)
            
            except Exception as e:
                last_error = e
                error_msg = f"ERROR: Error generating DDX for case {case_id} (attempt {attempt + 1}/{max_retries + 1}): {str(e)}"
                
                if self.logger:
                    self.logger.error(error_msg)
                    # Log detailed error information
                    self.logger.error(f"Exception type: {type(e).__name__}")
                    self.logger.error(f"Full exception details: {repr(e)}")
                    
                    # Categorize different types of errors
                    error_str = str(e).lower()
                    if "timeout" in error_str or "connection" in error_str:
                        self.logger.error(f"NETWORK_ERROR: Likely network/connection issue with LLM API")
                    elif "rate" in error_str or "limit" in error_str:
                        self.logger.error(f"RATE_LIMIT_ERROR: API rate limit exceeded")
                    elif "authentication" in error_str or "api" in error_str:
                        self.logger.error(f"API_ERROR: Authentication or API configuration issue")
                    elif "token" in error_str:
                        self.logger.error(f"TOKEN_ERROR: Token limit or token-related issue")
                    else:
                        self.logger.error(f"UNKNOWN_ERROR: Unclassified error during LLM generation")
                
                # Check if error is retryable
                is_retryable = self._is_retryable_error(e)
                
                if not is_retryable:
                    # Non-retryable error (authentication, invalid request, etc.)
                    if self.logger:
                        self.logger.error(f"❌ Non-retryable error for case {case_id}, giving up")
                    break
                
                # If this was the last attempt, don't retry
                if attempt >= max_retries:
                    if self.logger:
                        self.logger.error(f"❌ Max retries ({max_retries}) reached for case {case_id}, giving up")
                    break
                
                # Calculate exponential backoff delay
                # For NoCapacity errors, use longer delays and more informative logging
                error_str = str(e).lower()
                if "nocapacity" in error_str or "429" in error_str:
                    # Use longer delays for capacity issues (5s, 10s, 20s, 40s, 80s)
                    delay = base_delay * (2 ** attempt)
                    if self.logger:
                        self.logger.warning(f"⏳ NoCapacity error detected for case {case_id}, waiting {delay:.1f} seconds before retry... (attempt {attempt + 1}/{max_retries})")
                        self.logger.warning(f"   💡 Tip: Model may be experiencing high demand. Consider waiting or using Provisioned Throughput.")
                else:
                    # Standard exponential backoff for other retryable errors
                    delay = base_delay * (2 ** attempt)
                    if self.logger:
                        self.logger.warning(f"⏳ Retryable error detected for case {case_id}, retrying in {delay:.1f} seconds... (attempt {attempt + 1}/{max_retries})")
                
                time.sleep(delay)
        
        # All retries exhausted or non-retryable error
        if self.logger:
            self.logger.error(f"❌ Failed to generate DDX for case {case_id} after {max_retries + 1} attempts")
        
        # Helpful tip for common configuration issues
        if last_error and ("diagnosis" in str(last_error) or "format" in str(last_error).lower()):
            tip_msg = f"TIP: Check if OUTPUT_SCHEMA setting conflicts with your prompt's expected format"
            print(tip_msg)
            if self.logger:
                self.logger.warning(tip_msg)
        
        return [], ""
    
    def _extract_ddx_from_response(self, response, case_id: str) -> List[str]:
        """
        Universal DDX extractor - handles multiple response formats
        regardless of whether output schema is used or not
        
        Supported formats:
        - FORMAT_A: Raw list ["Disease A", "Disease B", ...]
        - FORMAT_B: Dictionary {"diagnoses": ["Disease A", "Disease B", ...]}
        - FORMAT_C: List of objects [{"diagnosis": "Disease A", "description": "...", ...}, ...]
        - FORMAT_D: FORMAT_C wrapped in tags <diagnosis_output>[{"diagnosis": "...", ...}]</diagnosis_output>
        
        Args:
            response: Raw LLM response
            case_id: Case identifier for error reporting
            
        Returns:
            List of differential diagnoses
        """
        try:
            # Log parsing attempt
            if self.logger:
                self.logger.info(f"Starting DDX parsing for case {case_id}")
                self.logger.info(f"Original response length: {len(str(response))} characters")
            
            # Clean response text (handle markdown code blocks)
            response_text = str(response).strip()
            original_text = response_text
            
            if response_text.startswith('```json'):
                response_text = response_text.split('```json')[1].split('```')[0].strip()
                if self.logger:
                    self.logger.info(f"Detected JSON markdown format, extracted content")
            elif response_text.startswith('```'):
                response_text = response_text.split('```')[1].split('```')[0].strip()
                if self.logger:
                    self.logger.info(f"Detected generic markdown format, extracted content")
            
            # FORMAT_D: Extract content from XML-like tags
            if '<diagnosis_output>' in response_text and '</diagnosis_output>' in response_text:
                start_tag = '<diagnosis_output>'
                end_tag = '</diagnosis_output>'
                start_idx = response_text.find(start_tag) + len(start_tag)
                end_idx = response_text.find(end_tag)
                if start_idx < end_idx:
                    response_text = response_text[start_idx:end_idx].strip()
                    if self.logger:
                        self.logger.info(f"Detected XML-like tags, extracted content from <diagnosis_output>")
            
            if self.logger:
                self.logger.info(f"Cleaned response length: {len(response_text)} characters")
                if len(response_text) <= 1000:
                    self.logger.info(f"Cleaned response text: {response_text}")
                else:
                    self.logger.info(f"Cleaned response text (truncated): {response_text[:500]}... [TRUNCATED]")
            
            # Try to parse as JSON first
            parsed = None
            try:
                parsed = json.loads(response_text)
                if self.logger:
                    self.logger.info(f"Successfully parsed as JSON for case {case_id}")
            except json.JSONDecodeError as json_error:
                if self.logger:
                    self.logger.warning(f"JSON parsing failed for case {case_id}: {json_error}")
                # If JSON fails, try Python literal evaluation (handles single quotes)
                try:
                    parsed = ast.literal_eval(response_text)
                    if self.logger:
                        self.logger.info(f"Successfully parsed using ast.literal_eval for case {case_id}")
                except (ValueError, SyntaxError) as literal_error:
                    error_msg = f"Failed to parse response for case {case_id}"
                    print(f"WARNING: {error_msg} - Response: {str(response)[:50]}...")
                    
                    if self.logger:
                        self.logger.error(f"PARSING_FAILURE: {error_msg}")
                        self.logger.error(f"JSON error: {json_error}")
                        self.logger.error(f"Literal eval error: {literal_error}")
                        self.logger.error(f"Response preview: {str(response)[:500]}...")
                        self.logger.error(f"Cleaned text preview: {response_text[:500]}...")
                    
                    return []
            
            # Check if it's a list first
            if isinstance(parsed, list) and len(parsed) > 0:
                if self.logger:
                    self.logger.info(f"Detected list format with {len(parsed)} items for case {case_id}")
                
                # Check if it's a list of objects with diagnosis fields
                if isinstance(parsed[0], dict):
                    if self.logger:
                        self.logger.info(f"List contains dictionaries, checking for diagnosis fields")
                        self.logger.info(f"First object keys: {list(parsed[0].keys())}")
                    
                    # FORMAT_C: List of diagnosis objects with "diagnosis" field (juanjo_classic.txt format)
                    # Example: [{"diagnosis": "Disease A", "description": "...", "symptoms_in_common": [...], "symptoms_not_in_common": [...]}, ...]
                    if 'diagnosis' in parsed[0]:
                        if self.logger:
                            self.logger.info(f"Detected FORMAT_C: List of objects with 'diagnosis' field")
                        
                        diagnoses = []
                        for i, item in enumerate(parsed):
                            if isinstance(item, dict) and 'diagnosis' in item:
                                diagnosis_name = item['diagnosis']
                                if diagnosis_name:  # Only add non-empty diagnoses
                                    diagnoses.append(str(diagnosis_name))
                                    if self.logger:
                                        self.logger.info(f"FORMAT_C[{i+1}]: {diagnosis_name}")
                                        # Log additional fields if present
                                        if 'rationale' in item:
                                            self.logger.info(f"  Rationale: {item['rationale']}")
                                        if 'matching_symptoms' in item:
                                            self.logger.info(f"  Matching symptoms: {item['matching_symptoms']}")
                                        if 'unmatched_symptoms' in item:
                                            self.logger.info(f"  Unmatched symptoms: {item['unmatched_symptoms']}")
                        
                        if diagnoses:
                            if self.logger:
                                self.logger.info(f"FORMAT_C parsing successful: extracted {len(diagnoses)} diagnoses")
                            return diagnoses
                        else:
                            error_msg = f"FORMAT_C malformed: No valid diagnosis objects found for case {case_id}"
                            print(f"WARNING: {error_msg}")
                            if self.logger:
                                self.logger.error(error_msg)
                            return []
                    
                    # FORMAT_D: List of diagnosis objects with "dx" field (claude_sonnet_4.txt format)
                    # Example: [{"dx": "Disease A", "rationale": "Brief reason", "confidence": "High/Medium/Low"}, ...]
                    elif 'dx' in parsed[0]:
                        if self.logger:
                            self.logger.info(f"Detected FORMAT_D: List of objects with 'dx' field")
                        
                        diagnoses = []
                        for i, item in enumerate(parsed):
                            if isinstance(item, dict) and 'dx' in item:
                                diagnosis_name = item['dx']
                                if diagnosis_name:  # Only add non-empty diagnoses
                                    diagnoses.append(str(diagnosis_name))
                                    if self.logger:
                                        self.logger.info(f"FORMAT_D[{i+1}]: {diagnosis_name}")
                                        # Log additional fields if present
                                        if 'rationale' in item:
                                            self.logger.info(f"  Rationale: {item['rationale']}")
                                        if 'confidence' in item:
                                            self.logger.info(f"  Confidence: {item['confidence']}")
                        
                        if diagnoses:
                            if self.logger:
                                self.logger.info(f"FORMAT_D parsing successful: extracted {len(diagnoses)} diagnoses")
                            return diagnoses
                        else:
                            error_msg = f"FORMAT_D malformed: No valid dx objects found for case {case_id}"
                            print(f"WARNING: {error_msg}")
                            if self.logger:
                                self.logger.error(error_msg)
                            return []
                    
                    else:
                        # Unknown object format in list
                        error_msg = f"Unknown object format in list for case {case_id}"
                        print(f"WARNING: {error_msg}")
                        print(f"WARNING: First object keys: {list(parsed[0].keys())}")
                        if self.logger:
                            self.logger.error(f"UNKNOWN_OBJECT_FORMAT: {error_msg}")
                            self.logger.error(f"First object keys: {list(parsed[0].keys())}")
                            self.logger.error(f"First object content: {parsed[0]}")
                        return []
                else:
                    # FORMAT_A: Simple list of strings
                    # Example: ["Disease A", "Disease B", "Disease C", ...]
                    if self.logger:
                        self.logger.info(f"Detected FORMAT_A: Simple list of strings")
                        for i, item in enumerate(parsed):
                            self.logger.info(f"FORMAT_A[{i+1}]: {item}")
                    
                    result = [str(item) for item in parsed if item]  # Convert to strings, filter empty
                    if self.logger:
                        self.logger.info(f"FORMAT_A parsing successful: extracted {len(result)} diagnoses")
                    return result
            
            # FORMAT_B: Dictionary with "diagnoses" key
            # Example: {"diagnoses": ["Disease A", "Disease B", ...]} OR {"diagnoses": [{"dx": "Disease", ...}, ...]}
            elif isinstance(parsed, dict) and 'diagnoses' in parsed:
                if self.logger:
                    self.logger.info(f"Detected FORMAT_B: Dictionary with 'diagnoses' key")
                    self.logger.info(f"Dictionary keys: {list(parsed.keys())}")
                
                diagnoses = parsed['diagnoses']
                if isinstance(diagnoses, list):
                    if self.logger:
                        self.logger.info(f"FORMAT_B diagnoses list has {len(diagnoses)} items")
                        for i, item in enumerate(diagnoses):
                            self.logger.info(f"FORMAT_B[{i+1}]: {item}")
                    
                    # Check if diagnoses list contains dictionary objects or simple strings
                    if len(diagnoses) > 0 and isinstance(diagnoses[0], dict):
                        # Handle dictionary objects in diagnoses list
                        result = []
                        for i, item in enumerate(diagnoses):
                            if isinstance(item, dict):
                                # Try to extract diagnosis name from 'dx' field first, then 'diagnosis'
                                diagnosis_name = item.get('dx') or item.get('diagnosis')
                                if diagnosis_name:
                                    result.append(str(diagnosis_name))
                                    if self.logger:
                                        self.logger.info(f"FORMAT_B extracted diagnosis[{i+1}]: {diagnosis_name}")
                                        if 'rationale' in item:
                                            self.logger.info(f"  Rationale: {item['rationale']}")
                                        if 'confidence' in item:
                                            self.logger.info(f"  Confidence: {item['confidence']}")
                        
                        if self.logger:
                            self.logger.info(f"FORMAT_B parsing successful: extracted {len(result)} diagnoses from dictionary objects")
                        return result
                    else:
                        # Handle simple string list
                        result = [str(item) for item in diagnoses if item]  # Convert to strings, filter empty
                        if self.logger:
                            self.logger.info(f"FORMAT_B parsing successful: extracted {len(result)} diagnoses from string list")
                        return result
                else:
                    error_msg = f"FORMAT_B malformed: 'diagnoses' key exists but value is not a list for case {case_id}"
                    print(f"WARNING: {error_msg}")
                    if self.logger:
                        self.logger.error(error_msg)
                        self.logger.error(f"'diagnoses' value type: {type(diagnoses)}")
                        self.logger.error(f"'diagnoses' value: {diagnoses}")
                    return []
            
            else:
                error_msg = f"UNKNOWN_FORMAT: Unexpected response structure for case {case_id}"
                print(f"WARNING: {error_msg}")
                print(f"WARNING: Response type: {type(parsed)}")
                if isinstance(parsed, dict):
                    print(f"WARNING: Response keys: {list(parsed.keys())}")
                print(f"TIP: Check if OUTPUT_SCHEMA enforces a format different from your prompt")
                
                if self.logger:
                    self.logger.error(error_msg)
                    self.logger.error(f"Parsed response type: {type(parsed)}")
                    if isinstance(parsed, dict):
                        self.logger.error(f"Dictionary keys: {list(parsed.keys())}")
                        self.logger.error(f"Dictionary content: {parsed}")
                    else:
                        self.logger.error(f"Parsed content: {parsed}")
                
                return []
                
        except Exception as e:
            error_msg = f"PARSING_ERROR for case {case_id}: {str(e)}"
            print(f"WARNING: {error_msg}")
            print(f"TIP: Check if OUTPUT_SCHEMA conflicts with prompt instructions")
            
            if self.logger:
                self.logger.error(f"CRITICAL_PARSING_ERROR: {error_msg}")
                self.logger.error(f"Exception type: {type(e).__name__}")
                self.logger.error(f"Full exception details: {repr(e)}")
                self.logger.error(f"Raw response for debugging: {str(response)[:1000]}...")
            
            return []
    
    def generate_ddx_for_dataset(self, dataset: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate DDX for entire dataset
        
        Args:
            dataset: List of case dictionaries
            
        Returns:
            List of cases with DDX added
        """
        start_msg = f"STARTING: DDX generation for {len(dataset)} cases..."
        model_msg = f"MODEL: {self.emulator_config['MODEL']}"
        prompt_msg = f"PROMPT: {self.emulator_config['CANDIDATE_PROMPT_PATH']}"
        schema_msg = f"SCHEMA: {'Enabled' if self.output_schema else 'Disabled'}"
        
        print(start_msg)
        print(model_msg)
        print(prompt_msg)
        print(schema_msg)
        print("-" * 60)
        
        if self.logger:
            self.logger.info(start_msg)
            self.logger.info(model_msg)
            self.logger.info(prompt_msg)
            self.logger.info(schema_msg)
        
        results = []
        
        for i, case in enumerate(dataset, 1):
            case_id = case.get('id', f'case_{i}')
            processing_msg = f"[{i}/{len(dataset)}] Processing case {case_id}..."
            print(processing_msg)
            if self.logger:
                self.logger.info(processing_msg)
            
            # Generate DDX
            ddx_list, raw_response = self._generate_ddx_for_case(case)
            
            # Add delay between requests for Gemini models to respect rate limits
            # Rate limits vary by tier (source: https://ai.google.dev/gemini-api/docs/rate-limits)
            # 
            # FREE TIER (sin facturación):
            #   - gemini-2.5-pro: 2 RPM, 125K TPM, 50 RPD
            #   - gemini-2.5-flash: 10 RPM, 250K TPM, 250 RPD
            #   - gemini-2.0-flash: 15 RPM, 1M TPM, 200 RPD
            # 
            # TIER 1 (con facturación asociada):
            #   - gemini-3-pro-preview: 50 RPM, 1M TPM, 1,000 RPD
            #   - gemini-2.5-pro: 150 RPM, 2M TPM, 10,000 RPD
            #   - gemini-2.5-flash: 1,000 RPM, 1M TPM, 10,000 RPD
            #   - gemini-2.0-flash: 2,000 RPM, 4M TPM, unlimited RPD
            # 
            # Delays calculated to stay safely under tier 1 limits (using ~80% of max RPM)
            model_name = self.emulator_config['MODEL'].lower()
            is_gemini = 'gemini' in model_name
            if is_gemini:
                # Determine delay based on model type and tier 1 limits
                if '2.0-flash' in model_name or ('2.0' in model_name and 'flash' in model_name):
                    # Tier 1: 2,000 RPM = 0.03s per request, using 0.05s for safety
                    delay_seconds = 0.05
                elif '2.5-flash' in model_name or ('2.5' in model_name and 'flash' in model_name):
                    # Tier 1: 1,000 RPM = 0.06s per request, using 0.1s for safety
                    delay_seconds = 0.1
                elif 'flash-lite' in model_name:
                    # Tier 1: 4,000 RPM = 0.015s per request, using 0.05s for safety
                    delay_seconds = 0.05
                elif '2.5-pro' in model_name or ('2.5' in model_name and 'pro' in model_name):
                    # Tier 1: 150 RPM = 0.4s per request, using 0.5s for safety
                    delay_seconds = 0.5
                elif '3' in model_name and 'pro' in model_name:
                    # Tier 1: 50 RPM = 1.2s per request, using 1.5s for safety
                    delay_seconds = 1.5
                else:
                    # Default: conservative delay for unknown models
                    delay_seconds = 0.3
                
                if self.logger:
                    self.logger.info(f"Waiting {delay_seconds}s before next Gemini API call (rate limit protection for {model_name})...")
                import time
                time.sleep(delay_seconds)
            
            # Display minimal response info
            response_preview = str(raw_response)[:100] + "..." if len(str(raw_response)) > 100 else str(raw_response)
            print(f"RESPONSE: {response_preview} | DDX_COUNT: {len(ddx_list)}")
            
            # Log detailed raw response
            if self.logger:
                self.logger.info(f"[{i}/{len(dataset)}] RAW_LLM_RESPONSE for case {case_id}:")
                # Log the full raw response with proper formatting
                if len(str(raw_response)) > 2000:  # Truncate very long responses
                    self.logger.info(f"RAW_RESPONSE (truncated): {str(raw_response)[:2000]}... [TRUNCATED - Total length: {len(str(raw_response))} chars]")
                else:
                    self.logger.info(f"RAW_RESPONSE: {raw_response}")
                
                # Log parsed DDX list
                self.logger.info(f"[{i}/{len(dataset)}] PARSED_DDX for case {case_id}: {ddx_list}")
            
            if ddx_list:
                success_msg = f"✅ SUCCESS: Generated {len(ddx_list)} DDX"
                print(success_msg)
                if self.logger:
                    self.logger.info(f"[{i}/{len(dataset)}] SUCCESS: Generated {len(ddx_list)} DDX for case {case_id}")
                    # Log each individual DDX with position
                    for j, ddx in enumerate(ddx_list, 1):
                        self.logger.info(f"[{i}/{len(dataset)}] DDX[{j}]: {ddx}")
                
                # Create DDX details dictionary
                ddx_details = {}
                for j, ddx in enumerate(ddx_list, 1):
                    ddx_details[ddx] = {
                        "normalized_text": ddx,
                        "position": j
                    }
                
                # Add DDX to case
                case_with_ddx = case.copy()
                case_with_ddx['ddx_details'] = ddx_details
                results.append(case_with_ddx)
            else:
                fail_msg = "FAILED: No DDX generated"
                print(fail_msg)
                if self.logger:
                    self.logger.warning(f"[{i}/{len(dataset)}] FAILED: No DDX generated for case {case_id}")
                    self.logger.warning(f"[{i}/{len(dataset)}] Empty DDX might be due to: parsing failure, LLM error, or unexpected response format")
                # Add empty DDX to maintain structure
                case_with_ddx = case.copy()
                case_with_ddx['ddx_details'] = {}
                results.append(case_with_ddx)
            
            print("-" * 40)
        
        print("-" * 60)
        successful_cases = sum(1 for r in results if r.get('ddx_details'))
        completion_msg = f"COMPLETED: DDX generation finished!"
        stats_msg = f"STATS: Success rate: {successful_cases}/{len(dataset)} ({successful_cases/len(dataset)*100:.1f}%)"
        
        print(completion_msg)
        print(stats_msg)
        
        if self.logger:
            self.logger.info(completion_msg)
            self.logger.info(stats_msg)
        
        return results
    
    def save_results(self, results: List[Dict[str, Any]], output_path: str) -> None:
        """
        Save DDX results to JSON file
        
        Args:
            results: List of cases with DDX
            output_path: Path to save the results
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save results
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            save_msg = f"SAVED: DDX results saved to: {output_path}"
            print(save_msg)
            if self.logger:
                self.logger.info(save_msg)
            
        except Exception as e:
            error_msg = f"ERROR: Error saving results: {str(e)}"
            print(error_msg)
            if self.logger:
                self.logger.error(error_msg)
            raise

def main():
    """Main function for standalone execution"""
    # Load configuration with preference for saved copy
    # Import here to avoid circular imports
    from main import load_config_with_fallback
    config = load_config_with_fallback()
    
    # Load dataset
    dataset_path = os.path.join(
        os.path.dirname(__file__), '..', '..', '..', '..',
        config['DATASET_PATH']
    )
    
    try:
        with open(dataset_path, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: Dataset file not found: {dataset_path}")
        sys.exit(1)
    
    # Initialize emulator
    emulator = DXGPTEmulator(config)
    
    # Generate DDX
    results = emulator.generate_ddx_for_dataset(dataset)
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    output_path = os.path.join(
        os.path.dirname(__file__), 'output',
        f"ddx_results_{timestamp}.json"
    )
    
    emulator.save_results(results, output_path)

if __name__ == "__main__":
    main()