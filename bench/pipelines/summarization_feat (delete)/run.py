#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ukrainian Dataset Final Evaluation Pipeline

This script implements a comprehensive evaluation system for Ukrainian processed dataset:
1. LLM-based diagnosis generation using dxgpt_dev.txt prompt
2. Azure Text Analytics processing for DDX (medical codes extraction)
3. ICD-10 hierarchical comparison between DDX and GDX
4. Semantic evaluation using extracted codes
5. Severity evaluation 
6. Top-K Accuracy metrics calculation
7. Complete JSON output with all metrics

Modular design with separated functional zones for clarity and maintainability.
"""

import json
import os
import sys
import time
import logging
import yaml
import shutil
import csv
import signal
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional, Union
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
# import threading  # REMOVED: No longer needed without file locks

# Azure Text Analytics
from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv

# Project utilities
from utils.llm import get_llm
from utils.icd10.taxonomy import ICD10Taxonomy
from utils.bert import calculate_semantic_similarity, warm_up_endpoint

# Load environment variables
load_dotenv()

# Global configuration
MAX_WORKERS = 3
SAVE_INTERVAL = 5  # Save progress every N cases

def format_json_with_medical_codes(data):
    """Format JSON data with medical codes on single lines."""
    
    def format_medical_codes_in_dict(obj, level=0):
        """Recursively format dictionaries, putting medical_codes on single lines."""
        if not isinstance(obj, dict):
            return json.dumps(obj, ensure_ascii=False)
        
        indent = "  " * level
        items = []
        
        for key, value in obj.items():
            if key == "medical_codes" and isinstance(value, dict):
                # Format medical codes on a single line
                codes_parts = []
                for code_type, code_list in value.items():
                    codes_parts.append(f'"{code_type}": {json.dumps(code_list, ensure_ascii=False)}')
                medical_codes_str = f'{indent}  "medical_codes": {{{", ".join(codes_parts)}}}'
                items.append(medical_codes_str)
            elif isinstance(value, dict):
                # Recursively format nested dictionaries
                formatted_value = format_medical_codes_in_dict(value, level + 1)
                items.append(f'{indent}  "{key}": {formatted_value}')
            elif isinstance(value, list):
                # Handle lists
                if all(isinstance(item, (str, int, float, bool, type(None))) for item in value):
                    # Simple list - keep on one line
                    items.append(f'{indent}  "{key}": {json.dumps(value, ensure_ascii=False)}')
                else:
                    # Complex list - format each item
                    list_items = []
                    for item in value:
                        if isinstance(item, dict):
                            formatted_item = format_medical_codes_in_dict(item, level + 2)
                            list_items.append(f'{indent}    {formatted_item}')
                        else:
                            list_items.append(f'{indent}    {json.dumps(item, ensure_ascii=False)}')
                    items.append(f'{indent}  "{key}": [\n{",\n".join(list_items)}\n{indent}  ]')
            else:
                # Simple values
                items.append(f'{indent}  "{key}": {json.dumps(value, ensure_ascii=False)}')
        
        return "{\n" + ",\n".join(items) + f"\n{indent}}}"
    
    # Handle top-level list or dict
    if isinstance(data, list):
        formatted_items = []
        for item in data:
            if isinstance(item, dict):
                formatted_items.append(format_medical_codes_in_dict(item, 1))
            else:
                formatted_items.append(f"  {json.dumps(item, ensure_ascii=False)}")
        return "[\n" + ",\n".join(formatted_items) + "\n]"
    elif isinstance(data, dict):
        return format_medical_codes_in_dict(data, 0)
    else:
        return json.dumps(data, indent=2, ensure_ascii=False)

def save_json_with_formatting(data, filepath, use_medical_codes_formatter=False):
    """Save JSON with proper formatting, optionally using medical codes formatter."""
    with open(filepath, 'w', encoding='utf-8') as f:
        if use_medical_codes_formatter:
            formatted_json = format_json_with_medical_codes(data)
            f.write(formatted_json)
        else:
            json.dump(data, f, indent=2, ensure_ascii=False)

# =============================================================================
# LOGGING UTILITIES
# =============================================================================

class CaseProgressTracker:
    """Tracks case progress and formats informative logs."""
    
    def __init__(self, dataset: List[Dict], logger: logging.Logger):
        self.logger = logger
        self.total_cases = len(dataset)
        self.letter_groups = self._analyze_case_ids(dataset)
        self.current_case_index = 0
    
    def _analyze_case_ids(self, dataset: List[Dict]) -> Dict[str, int]:
        """Analyze case IDs to group by initial letter."""
        letter_groups = {}
        for case in dataset:
            case_id = case.get("id", "")
            if case_id:
                letter = case_id[0].upper()
                letter_groups[letter] = letter_groups.get(letter, 0) + 1
        return letter_groups
    
    def get_case_info(self, case_id: str, case_index: int) -> str:
        """Get formatted case info string."""
        if not case_id:
            return f"❓ [{case_index + 1}/{self.total_cases}]"
        
        letter = case_id[0].upper()
        letter_count = self.letter_groups.get(letter, 1)
        
        # Show letter group info only if multiple letters exist
        if len(self.letter_groups) > 1:
            letter_info = f"[{letter}:{letter_count}]"
        else:
            letter_info = f"[{letter}]"
        
        return f"📋 {letter_info} {case_id} ({case_index + 1}/{self.total_cases})"
    
    def truncate_text(self, text: str, max_chars: int = 80) -> str:
        """Truncate text with ellipsis."""
        if len(text) <= max_chars:
            return text
        return text[:max_chars-3] + "..."

# Unicode emoji to text mapping for Windows compatibility
EMOJI_MAP = {
    '🚀': '[START]',
    '📊': '[DATA]',
    '📝': '[FILE]',
    '🤖': '[AI]',
    '📁': '[FOLDER]',
    '🔬': '[LAB]',
    '📋': '[CASE]',
    '🩺': '[MED]',
    '✅': '[OK]',
    '🔍': '[SEARCH]',
    '🧠': '[BRAIN]',
    '⚖️': '[SCALE]',
    '❌': '[ERROR]',
    '💾': '[SAVE]',
    '🎯': '[TARGET]',
    '🎉': '[SUCCESS]',
    '📈': '[METRICS]',
    '⚠️': '[WARN]',
    '📦': '[BATCH]',
    '❓': '[UNKNOWN]'
}

def safe_log_message(message: str) -> str:
    """Convert emojis to text for Windows compatibility."""
    safe_message = message
    for emoji, text in EMOJI_MAP.items():
        safe_message = safe_message.replace(emoji, text)
    return safe_message

def setup_logging_filters():
    """Setup logging filters to reduce noise."""
    # Filter out HTTP request logs and handle emoji encoding
    class SafeLoggingFilter(logging.Filter):
        def filter(self, record):
            msg = record.getMessage()
            
            # Block verbose HTTP logs
            if any(phrase in msg for phrase in [
                "HTTP Request: POST", 
                "Request URL:", 
                "Request headers:",
                "Response status:",
                "azure.core.pipeline.policies.http_logging_policy"
            ]):
                return False
            
            # Convert emojis to safe text on Windows
            if sys.platform.startswith('win'):
                try:
                    # Test if the message can be encoded
                    msg.encode('cp1252')
                except UnicodeEncodeError:
                    # Replace emojis with safe text
                    record.msg = safe_log_message(str(record.msg))
                    record.args = ()
            
            return True
    
    # Apply filter to all loggers
    safe_filter = SafeLoggingFilter()
    logging.getLogger().addFilter(safe_filter)
    
    for logger_name in ['azure', 'azure.core', 'urllib3', 'httpx']:
        azure_logger = logging.getLogger(logger_name)
        azure_logger.addFilter(safe_filter)
        azure_logger.setLevel(logging.WARNING)

# =============================================================================
# 1. CONFIGURATION AND SETUP
# =============================================================================

def load_config(config_path: Path) -> Dict[str, Any]:
    """Load configuration from YAML file."""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def setup_experiment_directory(config: Dict[str, Any], base_dir: Path) -> Tuple[Path, logging.Logger]:
    """Setup experiment directory structure and logging."""
    # Extract model name for directory structure
    model_name = config["dxgpt_emulator"]["model"]
    clean_model_name = model_name.replace('/', '_').replace('-', '_').replace(':', '_')
    
    # Create timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create directory structure: results/model_name/run_timestamp/
    results_base = base_dir / "results"
    model_dir = results_base / clean_model_name
    run_dir = model_dir / f"run_{timestamp}"
    
    run_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy config.yaml to run directory
    config_source = base_dir / "config.yaml"
    config_dest = run_dir / "config.yaml"
    shutil.copy2(config_source, config_dest)
    
    # Setup logging with UTF-8 encoding for Windows compatibility
    log_file = run_dir / "evaluation.log"
    
    # Create handlers with UTF-8 encoding
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    
    # For console output, try to use UTF-8 but fallback to safe mode on Windows
    try:
        import io
        console_handler = logging.StreamHandler(
            io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        )
    except (AttributeError, UnicodeError):
        # Fallback for systems that don't support UTF-8 console
        console_handler = logging.StreamHandler(sys.stdout)
    
    # Set up basic config
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[file_handler, console_handler],
        force=True  # Override any existing configuration
    )
    
    logger = logging.getLogger(__name__)
    
    # Setup logging filters to reduce noise
    setup_logging_filters()
    
    logger.info("🚀 " + "="*50)
    logger.info(f"📊 Experiment: {config.get('experiment_name', 'Unnamed')}")
    logger.info(f"📝 Description: {config.get('experiment_description', 'No description')}")
    logger.info(f"🤖 Model: {model_name}")
    logger.info(f"📁 Results: {run_dir}")
    logger.info("🚀 " + "="*50)
    
    return run_dir, logger

def load_dataset(dataset_path: str, base_dir: Path) -> List[Dict[str, Any]]:
    """Load dataset from path relative to project root."""
    # Navigate to project root (3 levels up from bench/pipelines/pipeline_v2)
    project_root = base_dir.parent.parent.parent
    full_path = project_root / dataset_path
    
    with open(full_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_prompt_template(prompt_path: str, base_dir: Path) -> str:
    """Load prompt template from path relative to current directory."""
    full_path = base_dir / prompt_path
    with open(full_path, 'r', encoding='utf-8') as f:
        return f.read()

def load_output_schema(schema_path: str, base_dir: Path) -> Optional[Dict]:
    """Load output schema if specified."""
    if not schema_path:
        return None
    
    full_path = base_dir / schema_path
    with open(full_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# =============================================================================
# 2. AZURE TEXT ANALYTICS MODULE
# =============================================================================

class AzureTextAnalytics:
    """Handles Azure Text Analytics for Health operations."""
    
    def __init__(self):
        self.key = os.environ.get('AZURE_LANGUAGE_KEY')
        self.endpoint = os.environ.get('AZURE_LANGUAGE_ENDPOINT')
        self.client = self._authenticate_client()
    
    def _authenticate_client(self) -> TextAnalyticsClient:
        """Authenticate Azure Text Analytics client."""
        ta_credential = AzureKeyCredential(self.key)
        return TextAnalyticsClient(
            endpoint=self.endpoint,
            credential=ta_credential
        )
    
    def extract_medical_codes(self, diagnosis_name: str) -> Dict[str, Any]:
        """
        Extract medical codes and normalized text from diagnosis name.
        
        Returns:
            Dict with normalized_text, icd10, snomed, omim, orpha codes
        """
        documents = [diagnosis_name]
        
        try:
            poller = self.client.begin_analyze_healthcare_entities(documents)
            result = poller.result()
            
            docs = [doc for doc in result if not doc.is_error]
            
            medical_codes = {
                "icd10": [],
                "snomed": [],
                "omim": [],
                "orpha": []
            }
            normalized_text = diagnosis_name  # Default
            
            for doc in docs:
                for entity in doc.entities:
                    if entity.category in ["Diagnosis", "ConditionQualifier", "MedicalCondition"]:
                        # Get normalized text
                        if entity.normalized_text:
                            normalized_text = entity.normalized_text
                        
                        # Extract codes from data sources
                        if entity.data_sources:
                            for link in entity.data_sources:
                                if link.name == "SNOMEDCT_US":
                                    medical_codes["snomed"].append(link.entity_id)
                                elif link.name == "ICD10CM":
                                    medical_codes["icd10"].append(link.entity_id)
                                elif link.name == "OMIM":
                                    medical_codes["omim"].append(link.entity_id)
                                elif link.name == "ORPHA":
                                    medical_codes["orpha"].append(link.entity_id)
            
            # Remove duplicates
            for code_type in medical_codes:
                medical_codes[code_type] = list(set(medical_codes[code_type]))
            
            return {
                "normalized_text": normalized_text,
                "medical_codes": medical_codes
            }
            
        except Exception as e:
            logging.error(f"Error processing '{diagnosis_name}': {e}")
            return {
                "normalized_text": diagnosis_name,
                "medical_codes": {
                    "icd10": [],
                    "snomed": [],
                    "omim": [],
                    "orpha": []
                }
            }

# =============================================================================
# 3. LLM DIAGNOSIS GENERATION MODULE
# =============================================================================

class DiagnosisGenerator:
    """Handles LLM-based diagnosis generation."""
    
    def __init__(self, config: Dict[str, Any]):
        model_name = config["dxgpt_emulator"]["model"]
        params = config["dxgpt_emulator"].get("params", {})
        
        # Extract LLM parameters
        llm_params = {}
        if "temperature" in params:
            llm_params["temperature"] = params["temperature"]
        
        self.llm = get_llm(model_name, **llm_params)
        self.output_schema = None
        self.generation_params = {}
        
        # Extract generation parameters
        for key in ['max_tokens', 'top_p']:
            if key in params:
                self.generation_params[key] = params[key]
        
        # Handle reasoning parameters for compatible models
        if "reasoning" in params:
            self.generation_params.update(params["reasoning"])
    
    def generate_diagnoses(self, case_description: str, prompt_template: str, output_schema: Optional[Dict] = None) -> List[str]:
        """
        Generate differential diagnoses using LLM.
        
        Args:
            case_description: Patient case description
            prompt_template: Prompt template with {case_description} placeholder
            
        Returns:
            List of differential diagnoses (accepts whatever the LLM returns)
        """
        try:
            prompt = prompt_template.replace("{case_description}", case_description)
            
            # Generate with schema if provided
            if output_schema:
                response = self.llm.generate(prompt, schema=output_schema, **self.generation_params)
            else:
                response = self.llm.generate(prompt, **self.generation_params)
            
            # Parse JSON response
            if isinstance(response, str):
                try:
                    diagnoses = json.loads(response)
                except json.JSONDecodeError:
                    # Try to extract JSON array
                    start_idx = response.find("[")
                    end_idx = response.rfind("]")
                    if start_idx != -1 and end_idx != -1:
                        json_str = response[start_idx:end_idx + 1]
                        try:
                            diagnoses = json.loads(json_str)
                        except json.JSONDecodeError:
                            return ["Parse Error"]
                    else:
                        return ["Parse Error"]
            else:
                diagnoses = response
            
            # Accept whatever the LLM returns - no fixed number requirement
            if isinstance(diagnoses, list):
                # Filter out empty or invalid diagnoses
                valid_diagnoses = [d for d in diagnoses if d and str(d).strip()]
                return valid_diagnoses if valid_diagnoses else ["No valid diagnoses"]
            elif isinstance(diagnoses, dict):
                # Handle structured output with diagnoses field
                if "diagnoses" in diagnoses:
                    diag_list = diagnoses["diagnoses"]
                    if isinstance(diag_list, list):
                        valid_diagnoses = [d for d in diag_list if d and str(d).strip()]
                        return valid_diagnoses if valid_diagnoses else ["No valid diagnoses"]
                return ["Format Error - Invalid structure"]
            else:
                return ["Format Error - Unexpected type"]
                
        except Exception as e:
            logging.error(f"Error generating diagnoses: {e}")
            return ["Error generating diagnoses"]

# =============================================================================
# 4. ICD-10 HIERARCHICAL COMPARISON MODULE
# =============================================================================

class ICD10Comparator:
    """Handles ICD-10 hierarchical comparison using utils/icd10 library."""
    
    def __init__(self):
        self.taxonomy = ICD10Taxonomy()
    
    def compare_diagnosis_pair(self, ddx_code: str, gdx_code: str) -> Tuple[float, str]:
        """
        Compare a DDX code with a GDX code using hierarchical logic.
        
        Returns:
            Tuple of (score, relationship_type)
        """
        try:
            # Priority 1: More specific (DDX is descendant of GDX)
            if gdx_code in self.taxonomy.parents(ddx_code):
                distance = self.taxonomy.parents(ddx_code).index(gdx_code) + 1
                score = 1.0 + (distance * 0.15)
                return score, "MORE_SPECIFIC"
            
            # Priority 2: Exact match
            if ddx_code == gdx_code:
                return 1.0, "EXACT_MATCH"
            
            # Priority 3: More general (DDX is ancestor of GDX)
            if ddx_code in self.taxonomy.parents(gdx_code):
                return 0.8, "MORE_GENERAL"
            
            # Priority 4: Close sibling (same parent, specific enough)
            ddx_parent = self.taxonomy.parent(ddx_code)
            gdx_parent = self.taxonomy.parent(gdx_code)
            
            if ddx_parent and ddx_parent == gdx_parent:
                parent_info = self.taxonomy.get(ddx_parent)
                if parent_info and parent_info.get('type') not in ['chapter', 'range']:
                    return 0.7, "CLOSE_SIBLING"
            
            # Priority 5: Related (common ancestor)
            ddx_ancestors = set(self.taxonomy.parents(ddx_code))
            gdx_ancestors = set(self.taxonomy.parents(gdx_code))
            common_ancestors = ddx_ancestors & gdx_ancestors
            
            if common_ancestors:
                return 0.5, "RELATED"
            
            # Priority 6: Unrelated
            return 0.0, "UNRELATED"
            
        except Exception as e:
            logging.warning(f"Error comparing {ddx_code} vs {gdx_code}: {e}")
            return 0.0, "ERROR"

# =============================================================================
# 5. SEMANTIC EVALUATION MODULE
# =============================================================================

class SemanticEvaluator:
    """Handles semantic evaluation between DDX and GDX."""
    
    def __init__(self):
        self.icd10_comparator = ICD10Comparator()
        self.bert_warmed_up = False
    
    def _warm_up_bert_if_needed(self) -> bool:
        """Warm up BERT endpoint if not already done."""
        if not self.bert_warmed_up:
            try:
                self.bert_warmed_up = warm_up_endpoint()
                if self.bert_warmed_up:
                    logging.info("BERT endpoint warmed up successfully")
                else:
                    logging.warning("Failed to warm up BERT endpoint")
            except Exception as e:
                logging.error(f"Error warming up BERT endpoint: {e}")
                self.bert_warmed_up = False
        return self.bert_warmed_up
    
    def _calculate_bert_similarity(self, ddx_name: str, ddx_normalized: str, 
                                 gdx_name: str, gdx_normalized: str) -> Tuple[float, str]:
        """
        Calculate BERT similarity between DDX and GDX using all combinations.
        
        Returns:
            Tuple of (max_score, best_combination_type)
        """
        if not self._warm_up_bert_if_needed():
            return 0.0, "BERT_ERROR"
        
        try:
            # Prepare all combinations
            ddx_texts = [ddx_name, ddx_normalized] if ddx_name != ddx_normalized else [ddx_name]
            gdx_texts = [gdx_name, gdx_normalized] if gdx_name != gdx_normalized else [gdx_name]
            
            # Calculate similarities for all combinations
            results = calculate_semantic_similarity(ddx_texts, gdx_texts)
            
            # Find maximum score
            max_score = 0.0
            best_combo = ""
            
            for ddx_text in ddx_texts:
                for gdx_text in gdx_texts:
                    score = results.get(ddx_text, {}).get(gdx_text, 0.0)
                    if score and score > max_score:
                        max_score = score
                        # Determine combination type
                        if ddx_text == ddx_name and gdx_text == gdx_name:
                            best_combo = "name_vs_name"
                        elif ddx_text == ddx_normalized and gdx_text == gdx_normalized:
                            best_combo = "normalized_vs_normalized"
                        elif ddx_text == ddx_name and gdx_text == gdx_normalized:
                            best_combo = "name_vs_normalized"
                        else:
                            best_combo = "normalized_vs_name"
            
            # Apply threshold - only accept if >= 0.80
            if max_score >= 0.80:
                return round(max_score, 4), f"BERT_{best_combo}"
            else:
                return 0.0, "BERT_below_threshold"
                
        except Exception as e:
            logging.error(f"Error calculating BERT similarity: {e}")
            return 0.0, "BERT_ERROR"
    
    def evaluate_case_semantics(self, ddx_list: List[Dict], gdx_list: List[Dict]) -> Dict[str, Any]:
        """
        Evaluate semantic similarity for a single case.
        
        Args:
            ddx_list: List of DDX with medical codes
            gdx_list: List of GDX with medical codes
            
        Returns:
            Dict with best_match and detailed_scores
        """
        best_score = 0.0
        best_match = None
        detailed_scores = []
        
        for ddx_idx, ddx in enumerate(ddx_list):
            ddx_scores = []
            
            for gdx_idx, gdx in enumerate(gdx_list):
                # Compare all code types
                max_code_score = 0.0
                best_code_type = "none"
                best_relationship = "UNRELATED"
                
                # Check ICD-10 codes (primary comparison)
                for ddx_icd in ddx.get("medical_codes", {}).get("icd10", []):
                    for gdx_icd in gdx.get("medical_codes", {}).get("icd10", []):
                        score, relationship = self.icd10_comparator.compare_diagnosis_pair(ddx_icd, gdx_icd)
                        if score > max_code_score:
                            max_code_score = score
                            best_code_type = "icd10"
                            best_relationship = relationship
                
                # Check other code types for exact matches only
                for code_type in ["snomed", "omim", "orpha"]:
                    ddx_codes = set(ddx.get("medical_codes", {}).get(code_type, []))
                    gdx_codes = set(gdx.get("medical_codes", {}).get(code_type, []))
                    
                    if ddx_codes & gdx_codes:  # Intersection (exact match)
                        if max_code_score < 1.0:  # Only override if not already perfect
                            max_code_score = 1.0
                            best_code_type = code_type
                            best_relationship = "EXACT_MATCH"
                
                # BERT fallback if score is 0.0
                if max_code_score == 0.0:
                    ddx_name = ddx.get("name", "")
                    ddx_normalized = ddx.get("normalized_text", ddx_name)
                    gdx_name = gdx.get("name", "")
                    gdx_normalized = gdx.get("normalized_text", gdx_name)
                    
                    bert_score, bert_type = self._calculate_bert_similarity(
                        ddx_name, ddx_normalized, gdx_name, gdx_normalized
                    )
                    
                    if bert_score > 0.0:
                        max_code_score = bert_score
                        best_code_type = "BERT"
                        best_relationship = bert_type
                
                ddx_scores.append({
                    "gdx_name": gdx.get("name", ""),
                    "score": round(max_code_score, 4),
                    "code_type": best_code_type,
                    "relationship": best_relationship
                })
                
                # Track global best match
                if max_code_score > best_score:
                    best_score = max_code_score
                    best_match = {
                        "ddx_name": ddx.get("name", ""),
                        "gdx_name": gdx.get("name", ""),
                        "score": round(max_code_score, 4),
                        "code_type": best_code_type,
                        "relationship": best_relationship
                    }
            
            detailed_scores.append({
                "ddx_name": ddx.get("name", ""),
                "gdx_scores": ddx_scores
            })
        
        return {
            "best_match": best_match or {
                "ddx_name": "",
                "gdx_name": "",
                "score": 0.0,
                "code_type": "none",
                "relationship": "UNRELATED"
            },
            "detailed_scores": detailed_scores
        }

# =============================================================================
# 6. SEVERITY EVALUATION MODULE
# =============================================================================

class SeverityEvaluator:
    """Handles severity evaluation using LLM-based severity assignment."""
    
    def __init__(self, config: Dict[str, Any], base_dir: Path):
        self.severity_mapping = {f"S{i}": i for i in range(11)}
        self.severity_assignments_cache = {}  # Cache for DDX -> severity mappings
        
        # Initialize LLM for severity assignment
        severity_config = config["severity_assigner"]
        
        # Load prompt and schema
        prompt_path = base_dir / severity_config["prompt_path"]
        with open(prompt_path, 'r', encoding='utf-8') as f:
            self.severity_prompt = f.read()
        
        schema_path = base_dir / severity_config["output_schema_path"]
        with open(schema_path, 'r', encoding='utf-8') as f:
            self.severity_schema = json.load(f)
        
        # Extract LLM parameters
        params = severity_config.get("params", {})
        llm_params = {}
        generation_params = {}
        
        # LLM configuration parameters
        if "temperature" in params:
            llm_params["temperature"] = params["temperature"]
        
        # Generation parameters
        for key in ['max_tokens', 'top_p']:
            if key in params:
                generation_params[key] = params[key]
        
        self.llm = get_llm(severity_config["model"], **llm_params)
        self.generation_params = generation_params
    
    def assign_severities_batch(self, unique_diagnoses: List[str], logger: logging.Logger) -> Dict[str, str]:
        """
        Assign severities to a batch of unique diagnoses using LLM.
        
        Args:
            unique_diagnoses: List of unique diagnosis names to assign severities to
            logger: Logger for tracking
            
        Returns:
            Dict mapping diagnosis name to severity (e.g., {"Pneumonia": "S6"})
        """
        BATCH_SIZE = 50  # Process in batches to avoid token limits
        severity_assignments = {}
        
        logger.info(f"   🤖 Procesando {len(unique_diagnoses)} diagnósticos únicos con LLM...")
        
        # Define the individual item schema for batch processing
        single_item_schema = {
            "type": "object",
            "properties": {
                "diagnosis": {
                    "type": "string",
                    "description": "The medical diagnosis being evaluated"
                },
                "severity": {
                    "type": "string", 
                    "pattern": "^S(10|[0-9])$",
                    "description": "Severity score from S0 to S10"
                }
            },
            "required": ["diagnosis", "severity"],
            "additionalProperties": False
        }
        
        # Process in batches
        total_batches = (len(unique_diagnoses) + BATCH_SIZE - 1) // BATCH_SIZE
        for i in range(0, len(unique_diagnoses), BATCH_SIZE):
            batch = unique_diagnoses[i:i+BATCH_SIZE]
            batch_num = i//BATCH_SIZE + 1
            logger.info(f"   📦 Lote {batch_num}/{total_batches} ({len(batch)} items)")
            
            try:
                # Create batch items for the LLM
                batch_items = [{"diagnosis": diagnosis} for diagnosis in batch]
                
                # Use the batch_items parameter for proper batch processing
                response = self.llm.generate(
                    self.severity_prompt,
                    batch_items=batch_items,
                    schema=single_item_schema,
                    **self.generation_params
                )
                
                # Log the raw LLM response for debugging
                logger.info(f"      🔍 Respuesta LLM para lote {batch_num}:")
                if isinstance(response, list):
                    logger.info(f"      Recibida lista con {len(response)} items")
                    if response:
                        logger.info(f"      Primer item: {json.dumps(response[0], ensure_ascii=False)}")
                else:
                    logger.info(f"      {str(response)[:500]}...")
                
                # When using batch_items, response should be a list
                if not isinstance(response, list):
                    logger.error(f"Expected list response for batch {batch_num}, got {type(response)}")
                    response = []
                
                logger.info(f"      📊 Severidades extraídas: {len(response)} de {len(batch)} esperadas")
                
                # Create mapping for this batch
                for i, item in enumerate(response):
                    if isinstance(item, dict) and "diagnosis" in item and "severity" in item:
                        diagnosis = item["diagnosis"]
                        severity = item["severity"]
                        
                        # Log each assignment
                        logger.info(f"        → {diagnosis}: {severity}")
                        
                        # Validate severity format
                        if not (severity.startswith('S') and len(severity) >= 2):
                            logger.warning(f"Invalid severity format for {diagnosis}: {severity}")
                            severity = "S5"
                        
                        severity_assignments[diagnosis] = severity
                    else:
                        # If the item doesn't have the expected structure, try to match with original diagnosis
                        if i < len(batch):
                            diagnosis = batch[i]
                            logger.warning(f"        ⚠️  {diagnosis}: Sin severidad válida, asignando S5")
                            severity_assignments[diagnosis] = "S5"
                
                # Handle missing assignments in batch
                missing_count = 0
                for diagnosis in batch:
                    if diagnosis not in severity_assignments:
                        missing_count += 1
                        severity_assignments[diagnosis] = "S5"  # Default
                        logger.warning(f"        ⚠️  {diagnosis}: No encontrado en respuesta, asignando S5")
                
                if missing_count > 0:
                    logger.warning(f"      ⚠️  {missing_count} asignaciones faltantes (S5 por defecto)")
                
                logger.info(f"      ✅ Lote completado: {len(response)} respuestas procesadas")
                
            except Exception as e:
                logger.error(f"Error processing batch {batch_num}: {str(e)}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                # Assign default severity to entire batch on error
                for diagnosis in batch:
                    severity_assignments[diagnosis] = "S5"
        
        # Cache the results
        self.severity_assignments_cache.update(severity_assignments)
        
        logger.info(f"   ✅ Asignación completada: {len(severity_assignments)} severidades asignadas")
        return severity_assignments
    
    def get_severity_for_diagnosis(self, diagnosis_name: str) -> str:
        """
        Get severity for a diagnosis from cache.
        """
        return self.severity_assignments_cache.get(diagnosis_name, "S5")
    
    def evaluate_case_severity(self, ddx_list: List[Dict], best_gdx: Dict) -> Dict[str, Any]:
        """
        Evaluate severity scores for a case using the methodology from pipeline_v1.
        
        Methodology:
        1. Takes the best GDX and its severity
        2. Calculates maximum possible distance based on GDX severity position
        3. For each DDX: calculates absolute distance and normalizes by max_distance for [0,1] range
        4. Final score = average of normalized values
        5. Separates DDX into optimists (less severe) and pessimists (more severe)
        """
        best_gdx_severity = best_gdx.get("severity", "S5")
        sev_gdx = self.severity_mapping.get(best_gdx_severity, 5)
        
        # Calculate maximum possible distance D based on GDX severity position
        if sev_gdx <= 5:
            max_distance = 10 - sev_gdx
        else:
            max_distance = sev_gdx
        
        # Handle edge case where max_distance = 0 (S0 or S10)
        if max_distance == 0:
            max_distance = 1  # To avoid division by zero
        
        ddx_scores = []
        ddx_normalized_values = []
        optimist_values = []  # DDX less severe than GDX (sev_ddx < sev_gdx)
        pessimist_values = [] # DDX more severe than GDX (sev_ddx > sev_gdx)
        
        for ddx in ddx_list:
            # Get severity from cache using normalized_text (consistent with how it was stored)
            ddx_severity = self.get_severity_for_diagnosis(ddx.get("normalized_text", ddx.get("name", "")))
            sev_ddx = self.severity_mapping.get(ddx_severity, 5)
            
            # Calculate absolute distance
            distance = abs(sev_gdx - sev_ddx)
            
            # Normalize to [0,1] by dividing by max_distance
            normalized_value = distance / max_distance
            
            ddx_normalized_values.append(normalized_value)
            
            # Categorize as optimist or pessimist
            # Optimist: DDX is less severe than GDX (numerical value lower)
            # Pessimist: DDX is more severe than GDX (numerical value higher)
            if sev_ddx < sev_gdx:
                optimist_values.append(normalized_value)
            elif sev_ddx > sev_gdx:
                pessimist_values.append(normalized_value)
            # If sev_ddx == sev_gdx, not counted in either category
            
            ddx_scores.append({
                "disease": ddx.get("name", ""),
                "severity": ddx_severity,
                "distance": distance,
                "score": round(normalized_value, 4)
            })
        
        # Calculate final score: average of normalized values
        final_score = sum(ddx_normalized_values) / len(ddx_normalized_values) if ddx_normalized_values else 0.0
        
        # Calculate metrics for optimists
        n_optimist = len(optimist_values)
        score_optimist = sum(optimist_values) / n_optimist if n_optimist > 0 else 0.0
        
        # Calculate metrics for pessimists
        n_pessimist = len(pessimist_values)
        score_pessimist = sum(pessimist_values) / n_pessimist if n_pessimist > 0 else 0.0
        
        return {
            "final_score": round(final_score, 4),
            "optimist": {
                "n": n_optimist,
                "score": round(score_optimist, 4)
            },
            "pessimist": {
                "n": n_pessimist,
                "score": round(score_pessimist, 4)
            },
            "gdx": {
                "disease": best_gdx.get("name", ""),
                "severity": best_gdx_severity
            },
            "ddx_list": ddx_scores
        }

# =============================================================================
# 7. TOP-K ACCURACY METRICS MODULE
# =============================================================================

class TopKMetrics:
    """Calculate Top-K accuracy metrics."""
    
    @staticmethod
    def calculate_topk_accuracy(results: List[Dict], threshold: float = 0.8) -> Dict[str, Any]:
        """
        Calculate Top-K accuracy metrics.
        
        Args:
            results: List of case results with semantic scores
            threshold: Score threshold for considering a match successful
            
        Returns:
            Dict with Top-1, Top-2, Top-3, Top-4, Top-5 accuracy and MRR
        """
        total_cases = len(results)
        top1_hits = 0
        top2_hits = 0
        top3_hits = 0
        top4_hits = 0
        top5_hits = 0
        reciprocal_ranks = []
        precision_at_5_scores = []
        
        for result in results:
            semantic_eval = result.get("semantic_evaluation", {})
            detailed_scores = semantic_eval.get("detailed_scores", [])
            
            # Get all DDX scores for this case, sorted by score
            all_scores = []
            for ddx_result in detailed_scores:
                for gdx_score in ddx_result.get("gdx_scores", []):
                    all_scores.append(gdx_score.get("score", 0.0))
            
            all_scores.sort(reverse=True)
            
            # Find first score above threshold
            first_hit_rank = None
            for rank, score in enumerate(all_scores, 1):
                if score >= threshold:
                    first_hit_rank = rank
                    break
            
            # Update Top-K counters
            if first_hit_rank:
                if first_hit_rank <= 1:
                    top1_hits += 1
                if first_hit_rank <= 2:
                    top2_hits += 1
                if first_hit_rank <= 3:
                    top3_hits += 1
                if first_hit_rank <= 4:
                    top4_hits += 1
                if first_hit_rank <= 5:
                    top5_hits += 1
                
                reciprocal_ranks.append(1.0 / first_hit_rank)
            else:
                reciprocal_ranks.append(0.0)
            
            # Average Precision @5
            top5_scores = all_scores[:5]
            precision_at_5 = sum(score for score in top5_scores if score >= threshold) / 5
            precision_at_5_scores.append(precision_at_5)
        
        return {
            "total_cases": total_cases,
            "threshold": threshold,
            "top1_accuracy": round(top1_hits / total_cases, 4) if total_cases > 0 else 0.0,
            "top2_accuracy": round(top2_hits / total_cases, 4) if total_cases > 0 else 0.0,
            "top3_accuracy": round(top3_hits / total_cases, 4) if total_cases > 0 else 0.0,
            "top4_accuracy": round(top4_hits / total_cases, 4) if total_cases > 0 else 0.0,
            "top5_accuracy": round(top5_hits / total_cases, 4) if total_cases > 0 else 0.0,
            "mean_reciprocal_rank": round(sum(reciprocal_ranks) / len(reciprocal_ranks), 4) if reciprocal_ranks else 0.0,
            "average_precision_at_5": round(sum(precision_at_5_scores) / len(precision_at_5_scores), 4) if precision_at_5_scores else 0.0
        }

# =============================================================================
# 8. SPECIALIZED OUTPUT FILE GENERATORS
# =============================================================================

import csv
from collections import Counter, defaultdict

def analyze_icd10_chapters(results: List[Dict]) -> Dict[str, Any]:
    """Analyze distribution and performance by ICD-10 chapters."""
    
    # ICD-10 Chapter mapping (simplified version)
    icd10_chapters = {
        'A': 'Certain infectious and parasitic diseases',
        'B': 'Certain infectious and parasitic diseases',
        'C': 'Neoplasms',
        'D': 'Neoplasms / Diseases of blood',
        'E': 'Endocrine, nutritional and metabolic diseases',
        'F': 'Mental and behavioural disorders',
        'G': 'Diseases of the nervous system',
        'H': 'Diseases of the eye/ear',
        'I': 'Diseases of the circulatory system',
        'J': 'Diseases of the respiratory system',
        'K': 'Diseases of the digestive system',
        'L': 'Diseases of the skin',
        'M': 'Diseases of the musculoskeletal system',
        'N': 'Diseases of the genitourinary system',
        'O': 'Pregnancy, childbirth and the puerperium',
        'P': 'Certain conditions originating in the perinatal period',
        'Q': 'Congenital malformations',
        'R': 'Symptoms, signs and abnormal findings',
        'S': 'Injury, poisoning',
        'T': 'Injury, poisoning',
        'U': 'Codes for special purposes',
        'V': 'External causes of morbidity',
        'W': 'External causes of morbidity',
        'X': 'External causes of morbidity',
        'Y': 'External causes of morbidity',
        'Z': 'Factors influencing health status'
    }
    
    # Initialize counters
    chapter_counts = defaultdict(int)
    chapter_scores = defaultdict(list)
    total_cases_with_icd10 = 0
    
    # Analyze each case
    for result in results:
        # Get best matching GDX ICD-10 codes
        best_match = result.get("semantic_evaluation", {}).get("best_match", {})
        gdx_name = best_match.get("gdx_name", "")
        semantic_score = best_match.get("score", 0.0)
        
        # Find the GDX details
        gdx_found = False
        for gdx in result.get("ground_truth_diagnoses", []):
            if gdx.get("name", "") == gdx_name:
                icd10_codes = gdx.get("medical_codes", {}).get("icd10", [])
                if icd10_codes and len(icd10_codes) > 0:
                    # Use first ICD-10 code for chapter classification
                    first_code = icd10_codes[0]
                    if first_code and len(first_code) > 0:
                        chapter = first_code[0].upper()
                        if chapter in icd10_chapters:
                            chapter_counts[chapter] += 1
                            chapter_scores[chapter].append(semantic_score)
                            total_cases_with_icd10 += 1
                            gdx_found = True
                            break
        
        # If no ICD-10 in best matching GDX, try first GDX
        if not gdx_found and result.get("ground_truth_diagnoses"):
            first_gdx = result["ground_truth_diagnoses"][0]
            icd10_codes = first_gdx.get("medical_codes", {}).get("icd10", [])
            if icd10_codes and len(icd10_codes) > 0:
                first_code = icd10_codes[0]
                if first_code and len(first_code) > 0:
                    chapter = first_code[0].upper()
                    if chapter in icd10_chapters:
                        chapter_counts[chapter] += 1
                        chapter_scores[chapter].append(semantic_score)
                        total_cases_with_icd10 += 1
    
    # Calculate statistics per chapter
    chapter_stats = {}
    for chapter in sorted(chapter_counts.keys()):
        count = chapter_counts[chapter]
        scores = chapter_scores[chapter]
        
        chapter_stats[chapter] = {
            "name": icd10_chapters[chapter],
            "count": count,
            "percentage": round(count / total_cases_with_icd10 * 100, 2) if total_cases_with_icd10 > 0 else 0.0,
            "mean_semantic_score": round(sum(scores) / len(scores), 4) if scores else 0.0,
            "min_semantic_score": round(min(scores), 4) if scores else 0.0,
            "max_semantic_score": round(max(scores), 4) if scores else 1.0
        }
    
    # Overall statistics
    total_chapters = len(chapter_counts)
    
    return {
        "total_cases_with_icd10": total_cases_with_icd10,
        "total_chapters_covered": total_chapters,
        "chapter_distribution": chapter_stats,
        "summary": {
            "most_common_chapter": max(chapter_counts.items(), key=lambda x: x[1])[0] if chapter_counts else None,
            "least_common_chapter": min(chapter_counts.items(), key=lambda x: x[1])[0] if chapter_counts else None,
            "best_performing_chapter": max(chapter_stats.items(), key=lambda x: x[1]["mean_semantic_score"])[0] if chapter_stats else None,
            "worst_performing_chapter": min(chapter_stats.items(), key=lambda x: x[1]["mean_semantic_score"])[0] if chapter_stats else None
        }
    }

def generate_run_summary(config: Dict[str, Any], results: List[Dict], topk_metrics: Dict, 
                        dataset: List[Dict], output_dir: Path) -> None:
    """Generate run_summary.json - Comprehensive executive summary of the experiment."""
    
    # Extract basic scores
    semantic_scores = [r["semantic_evaluation"]["best_match"]["score"] for r in results]
    severity_scores = [r["severity_evaluation"]["final_score"] for r in results]
    
    # METADATA section
    metadata = {
        "experiment_name": config.get("experiment_name", "Unnamed Experiment"),
        "experiment_description": config.get("experiment_description", "No description provided"),
        "execution_timestamp": datetime.now().isoformat(),
        "pipeline_version": "v2.1.0",
        "model_configuration": {
            "model_name": config["dxgpt_emulator"]["model"],
            "prompt_template_name": config["dxgpt_emulator"].get("prompt_path", ""),
            "output_schema_enabled": bool(config["dxgpt_emulator"].get("output_schema", False))
        },
        "dataset_configuration": {
            "dataset_path": config.get("dataset_path", ""),
            "total_cases_processed": len(results)
        }
    }
    
    # DATASET PROFILE section
    case_sources = {}
    gdx_counts = []
    total_gdx = 0
    gdx_code_coverage = {"icd10": 0, "orpha": 0, "omim": 0, "snomed": 0}
    
    for case in dataset:
        case_id = case.get("id", "")
        if case_id:
            prefix = case_id[0].upper()
            case_sources[prefix] = case_sources.get(prefix, 0) + 1
        
        diagnoses = case.get("diagnoses", [])
        gdx_count = len(diagnoses)
        gdx_counts.append(gdx_count)
        total_gdx += gdx_count
        
        # Count GDX with codes
        for diag in diagnoses:
            codes = diag.get("medical_codes", {})
            for code_type in gdx_code_coverage:
                if codes.get(code_type, []):
                    gdx_code_coverage[code_type] += 1
    
    # Calculate proportions
    total_cases = len(dataset)
    source_proportions = {k: round(v / total_cases, 4) for k, v in case_sources.items()} if total_cases > 0 else {}
    
    # Normalize coverage percentages
    for code_type in gdx_code_coverage:
        gdx_code_coverage[code_type] = round(gdx_code_coverage[code_type] / total_gdx, 4) if total_gdx > 0 else 0.0
    
    single_gdx_cases = sum(1 for count in gdx_counts if count == 1)
    single_gdx_rate = round(single_gdx_cases / len(gdx_counts), 4) if gdx_counts else 0.0
    
    dataset_profile = {
        "cases_by_source": {
            "distribution": case_sources,
            "proportions": source_proportions
        },
        "ground_truth_profile": {
            "mean_gdx_per_case": round(sum(gdx_counts) / len(gdx_counts), 4) if gdx_counts else 0.0,
            "max_gdx_per_case": max(gdx_counts) if gdx_counts else 0,
            "cases_with_single_gdx_rate": single_gdx_rate,
            "gdx_code_coverage_rate": {
                "icd10": gdx_code_coverage["icd10"],
                "orpha": gdx_code_coverage["orpha"],
                "omim": gdx_code_coverage["omim"],
                "snomed": gdx_code_coverage["snomed"]
            }
        }
    }
    
    # PERFORMANCE SUMMARY section
    
    # Model output quality
    total_ddx_generated = sum(len(r.get("generated_diagnoses", [])) for r in results)
    mean_ddx_per_case = round(total_ddx_generated / len(results), 4) if results else 0.0
    
    ddx_without_codes = 0
    parse_errors = 0
    for result in results:
        if result.get("error"):
            parse_errors += 1
        for ddx in result.get("generated_diagnoses", []):
            codes = ddx.get("medical_codes", {})
            has_codes = any(codes.get(code_type, []) for code_type in ["icd10", "orpha", "omim", "snomed"])
            if not has_codes:
                ddx_without_codes += 1
    
    ddx_without_codes_rate = round(ddx_without_codes / total_ddx_generated, 4) if total_ddx_generated > 0 else 0.0
    parse_error_rate = round(parse_errors / len(results), 4) if results else 0.0
    
    # Overall semantic performance
    mean_best_match_score = round(sum(semantic_scores) / len(semantic_scores), 4) if semantic_scores else 0.0
    hit_rate_08 = sum(1 for score in semantic_scores if score >= 0.8) / len(semantic_scores) if semantic_scores else 0.0
    excellence_rate = sum(1 for score in semantic_scores if score > 1.0) / len(semantic_scores) if semantic_scores else 0.0
    
    # Best match relationship distribution and BERT usage
    relationship_counts = {"MORE_SPECIFIC": 0, "EXACT_MATCH": 0, "MORE_GENERAL": 0, 
                          "CLOSE_SIBLING": 0, "RELATED": 0, "UNRELATED_OR_NO_CODE": 0}
    
    # BERT usage statistics
    bert_usage_stats = {
        "total_bert_matches": 0,
        "bert_above_threshold": 0,
        "bert_below_threshold": 0,
        "bert_errors": 0,
        "bert_combination_types": {
            "name_vs_name": 0,
            "normalized_vs_normalized": 0,
            "name_vs_normalized": 0,
            "normalized_vs_name": 0
        }
    }
    
    # Code type usage statistics
    code_type_usage = {
        "icd10": 0,
        "snomed": 0,
        "omim": 0,
        "orpha": 0,
        "BERT": 0,
        "none": 0
    }
    
    for result in results:
        best_match = result.get("semantic_evaluation", {}).get("best_match", {})
        relationship = best_match.get("relationship", "UNRELATED_OR_NO_CODE")
        code_type = best_match.get("code_type", "none")
        
        # Count code type usage
        if code_type in code_type_usage:
            code_type_usage[code_type] += 1
        else:
            code_type_usage["none"] += 1
        
        # Process relationship
        if relationship.startswith("BERT_"):
            bert_usage_stats["total_bert_matches"] += 1
            if relationship == "BERT_ERROR":
                bert_usage_stats["bert_errors"] += 1
                relationship_counts["UNRELATED_OR_NO_CODE"] += 1
            elif relationship == "BERT_below_threshold":
                bert_usage_stats["bert_below_threshold"] += 1
                relationship_counts["UNRELATED_OR_NO_CODE"] += 1
            else:
                bert_usage_stats["bert_above_threshold"] += 1
                # Extract combination type
                combo_type = relationship.replace("BERT_", "")
                if combo_type in bert_usage_stats["bert_combination_types"]:
                    bert_usage_stats["bert_combination_types"][combo_type] += 1
                # For ICD-10 relationships, BERT matches are considered EXACT_MATCH
                relationship_counts["EXACT_MATCH"] += 1
        elif relationship in relationship_counts:
            relationship_counts[relationship] += 1
        else:
            relationship_counts["UNRELATED_OR_NO_CODE"] += 1
    
    relationship_distribution = {k: round(v / len(results), 4) for k, v in relationship_counts.items()} if results else relationship_counts
    code_type_distribution = {k: round(v / len(results), 4) for k, v in code_type_usage.items()} if results else code_type_usage
    
    # Clinical safety profile
    optimist_scores = []
    pessimist_scores = []
    optimist_count = 0
    pessimist_count = 0
    neutral_count = 0
    
    for result in results:
        sev_eval = result.get("severity_evaluation", {})
        if sev_eval.get("optimist", {}).get("n", 0) > 0:
            optimist_scores.append(sev_eval["optimist"]["score"])
            optimist_count += 1
        if sev_eval.get("pessimist", {}).get("n", 0) > 0:
            pessimist_scores.append(sev_eval["pessimist"]["score"])
            pessimist_count += 1
        if sev_eval.get("optimist", {}).get("n", 0) == 0 and sev_eval.get("pessimist", {}).get("n", 0) == 0:
            neutral_count += 1
    
    total_bias_cases = len(results)
    optimist_rate = round(optimist_count / total_bias_cases, 4) if total_bias_cases > 0 else 0.0
    pessimist_rate = round(pessimist_count / total_bias_cases, 4) if total_bias_cases > 0 else 0.0
    neutral_rate = round(neutral_count / total_bias_cases, 4) if total_bias_cases > 0 else 0.0
    
    # Failure analysis
    failure_rate = round(1.0 - hit_rate_08, 4)
    failed_cases = [r for r in results if r["semantic_evaluation"]["best_match"]["score"] < 0.8]
    
    failure_relationship_counts = {"CLOSE_SIBLING": 0, "RELATED": 0, "UNRELATED_OR_NO_CODE": 0}
    for case in failed_cases:
        relationship = case.get("semantic_evaluation", {}).get("best_match", {}).get("relationship", "UNRELATED_OR_NO_CODE")
        if relationship in failure_relationship_counts:
            failure_relationship_counts[relationship] += 1
        else:
            failure_relationship_counts["UNRELATED_OR_NO_CODE"] += 1
    
    failure_modes = {k: round(v / len(failed_cases), 4) for k, v in failure_relationship_counts.items()} if failed_cases else failure_relationship_counts
    
    # Performance by source
    performance_by_source = {}
    source_scores = defaultdict(list)
    for result in results:
        case_id = result.get("case_id", "")
        if case_id:
            source = case_id[0].upper()
            source_scores[source].append(result["semantic_evaluation"]["best_match"]["score"])
    
    for source, scores in source_scores.items():
        performance_by_source[source] = round(sum(scores) / len(scores), 4) if scores else 0.0
    
    # Performance by GDX count
    single_gdx_scores = []
    multiple_gdx_scores = []
    for i, result in enumerate(results):
        if i < len(gdx_counts):
            if gdx_counts[i] == 1:
                single_gdx_scores.append(result["semantic_evaluation"]["best_match"]["score"])
            else:
                multiple_gdx_scores.append(result["semantic_evaluation"]["best_match"]["score"])
    
    performance_by_gdx_count = {
        "single_gdx_cases": round(sum(single_gdx_scores) / len(single_gdx_scores), 4) if single_gdx_scores else 0.0,
        "multiple_gdx_cases": round(sum(multiple_gdx_scores) / len(multiple_gdx_scores), 4) if multiple_gdx_scores else 0.0
    }
    
    performance_summary = {
        "model_output_quality": {
            "total_ddx_generated": total_ddx_generated,
            "mean_ddx_per_case": mean_ddx_per_case,
            "ddx_without_codes_rate": ddx_without_codes_rate,
            "ddx_parse_error_rate": parse_error_rate
        },
        "overall_semantic_performance": {
            "mean_best_match_score": mean_best_match_score,
            "hit_rate": {
                "threshold": 0.8,
                "value": round(hit_rate_08, 4)
            },
            "excellence_rate": round(excellence_rate, 4),
            "best_match_relationship_distribution": relationship_distribution,
            "code_type_distribution": code_type_distribution,
            "bert_usage_statistics": {
                "total_bert_attempts": bert_usage_stats["total_bert_matches"],
                "bert_matches_above_threshold": bert_usage_stats["bert_above_threshold"],
                "bert_matches_below_threshold": bert_usage_stats["bert_below_threshold"],
                "bert_errors": bert_usage_stats["bert_errors"],
                "bert_success_rate": round(bert_usage_stats["bert_above_threshold"] / bert_usage_stats["total_bert_matches"], 4) if bert_usage_stats["total_bert_matches"] > 0 else 0.0,
                "bert_combination_breakdown": bert_usage_stats["bert_combination_types"]
            }
        },
        "ranking_performance": {
            "threshold": topk_metrics.get("threshold", 0.8),
            "top_1_accuracy": topk_metrics.get("top1_accuracy", 0.0),
            "top_3_accuracy": topk_metrics.get("top3_accuracy", 0.0),
            "top_5_accuracy": topk_metrics.get("top5_accuracy", 0.0),
            "mean_reciprocal_rank": topk_metrics.get("mean_reciprocal_rank", 0.0)
        },
        "clinical_safety_profile": {
            "severity_evaluation": {
                "mean_severity_score": round(sum(severity_scores) / len(severity_scores), 4) if severity_scores else 0.0,
                "mean_optimist_score": round(sum(optimist_scores) / len(optimist_scores), 4) if optimist_scores else 0.0,
                "mean_pessimist_score": round(sum(pessimist_scores) / len(pessimist_scores), 4) if pessimist_scores else 0.0
            },
            "severity_bias_distribution": {
                "optimist_rate": optimist_rate,
                "pessimist_rate": pessimist_rate,
                "neutral_rate": neutral_rate
            }
        },
        "diagnostic_insights_and_error_analysis": {
            "failure_analysis": {
                "failure_rate": failure_rate,
                "common_failure_modes": failure_modes
            },
            "performance_by_source": performance_by_source,
            "performance_by_gdx_count": performance_by_gdx_count
        }
    }
    
    # ICD-10 Chapter Analysis
    icd10_chapter_analysis = analyze_icd10_chapters(results)
    
    # Final structure
    summary = {
        "metadata": metadata,
        "dataset_profile": dataset_profile,
        "icd10_chapter_analysis": icd10_chapter_analysis,
        "performance_summary": performance_summary
    }
    
    output_path = output_dir / "run_summary.json"
    save_json_with_formatting(summary, output_path)


def generate_ddx_analysis_csv(results: List[Dict], output_dir: Path) -> None:
    """Generate ddx_analysis.csv - DDX frequency analysis."""
    
    ddx_stats = defaultdict(lambda: {
        "normalized_text": "",
        "frequency": 0,
        "icd10_codes": set(),
        "orpha_codes": set(),
        "omim_codes": set(),
        "snomed_codes": set()
    })
    
    # Collect DDX statistics
    for result in results:
        for ddx in result.get("generated_diagnoses", []):
            ddx_name = ddx.get("name", "")
            if ddx_name:
                stats = ddx_stats[ddx_name]
                stats["normalized_text"] = ddx.get("normalized_text", ddx_name)
                stats["frequency"] += 1
                
                codes = ddx.get("medical_codes", {})
                for code_type in ["icd10", "orpha", "omim", "snomed"]:
                    code_list = codes.get(code_type, [])
                    stats[f"{code_type}_codes"].update(code_list)
    
    # Sort by frequency
    sorted_ddx = sorted(ddx_stats.items(), key=lambda x: x[1]["frequency"], reverse=True)
    
    # Write CSV with frequency_count before normalized_text
    output_path = output_dir / "ddx_analysis.csv"
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            "ddx_name", "frequency_count", "normalized_text",
            "icd10_codes", "orpha_codes", "omim_codes", "snomed_codes"
        ])
        
        for ddx_name, stats in sorted_ddx:
            writer.writerow([
                ddx_name,
                stats["frequency"],
                stats["normalized_text"],
                "; ".join(sorted(stats["icd10_codes"])),
                "; ".join(sorted(stats["orpha_codes"])),
                "; ".join(sorted(stats["omim_codes"])),
                "; ".join(sorted(stats["snomed_codes"]))
            ])

def generate_case_ddx_generation(results: List[Dict], output_dir: Path) -> None:
    """Generate diagnoses.json - Detailed diagnoses with medical codes organized by dataset type."""
    
    # Group by dataset letter
    datasets = {}
    for result in results:
        case_id = result.get("case_id", "")
        letter = case_id[0].upper() if case_id else "?"
        
        if letter not in datasets:
            datasets[letter] = []
        
        # Get normalized texts and codes
        gdx_details = {}
        for diag in result.get("ground_truth_diagnoses", []):
            name = diag.get("name", "")
            if name:
                gdx_details[name] = {
                    "normalized_text": diag.get("normalized_text", name),
                    "medical_codes": {
                        "icd10": diag.get("medical_codes", {}).get("icd10", []),
                        "orpha": diag.get("medical_codes", {}).get("orpha", []),
                        "omim": diag.get("medical_codes", {}).get("omim", []),
                        "snomed": diag.get("medical_codes", {}).get("snomed", [])
                    }
                }
        
        ddx_details = {}
        for ddx in result.get("generated_diagnoses", []):
            name = ddx.get("name", "")
            if name:
                ddx_details[name] = {
                    "normalized_text": ddx.get("normalized_text", name),
                    "medical_codes": {
                        "icd10": ddx.get("medical_codes", {}).get("icd10", []),
                        "orpha": ddx.get("medical_codes", {}).get("orpha", []),
                        "omim": ddx.get("medical_codes", {}).get("omim", []),
                        "snomed": ddx.get("medical_codes", {}).get("snomed", [])
                    }
                }
        
        case_data = {
            "case_id": case_id,
            "case_description": result.get("case_description", ""),
            "gdx_details": gdx_details,
            "ddx_details": ddx_details
        }
        
        datasets[letter].append(case_data)
    
    # Sort each dataset by case_id
    for letter in datasets:
        datasets[letter].sort(key=lambda x: x["case_id"])
    
    output_path = output_dir / "diagnoses.json"
    save_json_with_formatting(datasets, output_path, use_medical_codes_formatter=True)

def generate_case_semantic_evaluation(results: List[Dict], output_dir: Path) -> None:
    """Generate semantic_evaluation.json - Clear semantic scoring organized by dataset type."""
    
    # Group by dataset letter
    datasets = {}
    for result in results:
        case_id = result.get("case_id", "")
        letter = case_id[0].upper() if case_id else "?"
        
        if letter not in datasets:
            datasets[letter] = []
        
        semantic_eval = result.get("semantic_evaluation", {})
        detailed_scores = semantic_eval.get("detailed_scores", [])
        best_match = semantic_eval.get("best_match", {})
        
        # Process each DDX
        ddx_evaluations = []
        for ddx_detail in detailed_scores:
            ddx_name = ddx_detail.get("ddx_name", "")
            gdx_scores_list = ddx_detail.get("gdx_scores", [])
            
            # Calculate best score and find corresponding GDX
            best_score = 0.0
            best_gdx_name = ""
            for score_detail in gdx_scores_list:
                score = round(score_detail.get("score", 0.0), 4)
                if score > best_score:
                    best_score = score
                    best_gdx_name = score_detail.get("gdx_name", "")
            
            # Create dictionary of GDX scores with score and code_type
            gdx_scores_dict = {}
            for score_detail in gdx_scores_list:
                gdx_name = score_detail.get("gdx_name", "")
                if gdx_name:
                    gdx_scores_dict[gdx_name] = {
                        "score": round(score_detail.get("score", 0.0), 4),
                        "code_type": score_detail.get("code_type", "none")
                    }
            
            ddx_evaluations.append({
                "ddx_name": ddx_name,
                "best_score": best_score,
                "best_matching_gdx": best_gdx_name,
                "scores_vs_each_gdx": gdx_scores_dict
            })
        
        case_data = {
            "case_id": case_id,
            "final_best_score": round(best_match.get("score", 0.0), 4),
            "associated_ddx": best_match.get("ddx_name", ""),
            "associated_gdx": best_match.get("gdx_name", ""),
            "evaluation_breakdown": ddx_evaluations
        }
        
        datasets[letter].append(case_data)
    
    # Sort each dataset by case_id
    for letter in datasets:
        datasets[letter].sort(key=lambda x: x["case_id"])
    
    output_path = output_dir / "semantic_evaluation.json"
    save_json_with_formatting(datasets, output_path)

def generate_case_severity_evaluation(results: List[Dict], output_dir: Path) -> None:
    """Generate severity_evaluation.json - Clear severity analysis organized by dataset type."""
    
    # Group by dataset letter
    datasets = {}
    for result in results:
        case_id = result.get("case_id", "")
        letter = case_id[0].upper() if case_id else "?"
        
        if letter not in datasets:
            datasets[letter] = []
        
        severity_eval = result.get("severity_evaluation", {})
        
        # Extract severity scores clearly for each DDX
        ddx_severity_scores = []
        for ddx_detail in severity_eval.get("ddx_list", []):
            ddx_severity_scores.append({
                "ddx_name": ddx_detail.get("disease", ""),
                "severity": ddx_detail.get("severity", "S5"),
                "normalized_score": round(ddx_detail.get("score", 0.0), 4)
            })
        
        # Detailed severity analysis
        ddx_severity_analysis = []
        for ddx_detail in severity_eval.get("ddx_list", []):
            # Determine bias
            gdx_severity = severity_eval.get("gdx", {}).get("severity", "S5")
            ddx_severity = ddx_detail.get("severity", "S5")
            
            gdx_num = int(gdx_severity[1:]) if gdx_severity.startswith('S') else 5
            ddx_num = int(ddx_severity[1:]) if ddx_severity.startswith('S') else 5
            
            if ddx_num < gdx_num:
                bias = "Optimist"
            elif ddx_num > gdx_num:
                bias = "Pessimist"
            else:
                bias = "Neutral"
            
            ddx_severity_analysis.append({
                "ddx_name": ddx_detail.get("disease", ""),
                "assigned_severity": ddx_detail.get("severity", "S5"),
                "distance_from_gdx": ddx_detail.get("distance", 0),
                "normalized_score": round(ddx_detail.get("score", 0.0), 4),
                "bias": bias
            })
        
        case_data = {
            "case_id": case_id,
            "final_severity_score": round(severity_eval.get("final_score", 0.0), 4),
            "ddx_severity_scores": ddx_severity_scores,
            "reference_gdx": {
                "name": severity_eval.get("gdx", {}).get("disease", ""),
                "severity": severity_eval.get("gdx", {}).get("severity", "S5")
            },
            "ddx_detailed_analysis": ddx_severity_analysis
        }
        
        datasets[letter].append(case_data)
    
    # Sort each dataset by case_id
    for letter in datasets:
        datasets[letter].sort(key=lambda x: x["case_id"])
    
    output_path = output_dir / "severity_evaluation.json"
    save_json_with_formatting(datasets, output_path)

# =============================================================================
# 9. MAIN PIPELINE ORCHESTRATOR
# =============================================================================

class EvaluationPipeline:
    """Main pipeline orchestrator."""
    
    def __init__(self, config: Dict[str, Any], output_dir: Path, logger: logging.Logger, base_dir: Path):
        self.config = config
        self.output_dir = output_dir
        self.logger = logger
        self.base_dir = base_dir
        
        # Initialize components
        self.diagnosis_generator = DiagnosisGenerator(config)
        self.azure_client = AzureTextAnalytics()
        self.semantic_evaluator = SemanticEvaluator()
        self.severity_evaluator = SeverityEvaluator(config, base_dir)
        
    # REMOVED: save_incremental_progress method - files will be written only at the end
    
    # REMOVED: update_case_files_partial method - files will be written only at the end
    
    
    def process_single_case(self, case: Dict, prompt_template: str, output_schema: Optional[Dict], case_idx: int, progress_tracker: CaseProgressTracker) -> Dict[str, Any]:
        """Process a single case through the entire pipeline."""
        case_id = case.get("id", "")
        
        # Case header - clear identification
        letter = case_id[0].upper() if case_id else "?"
        letter_count = progress_tracker.letter_groups.get(letter, 1)
        
        if len(progress_tracker.letter_groups) > 1:
            letter_info = f"[{letter}:{letter_count}]"
        else:
            letter_info = f"[{letter}]"
        
        self.logger.info("")
        self.logger.info("=" * 60)
        self.logger.info(f"📋 CASO {letter_info}")
        self.logger.info(f"    ID: {case_id} ({case_idx + 1}/{progress_tracker.total_cases})")
        self.logger.info("=" * 60)
        
        # Show case description
        case_description = case.get("case", "")
        # Remove all line breaks and normalize whitespace
        clean_description = " ".join(case_description.split())
        truncated_desc = clean_description[:250] + "..." if len(clean_description) > 250 else clean_description
        self.logger.info(f"📝 Descripción del caso:")
        self.logger.info(f"    {truncated_desc}")
        self.logger.info("")
        
        try:
            # Step 1: DDX Generation
            self.logger.info("🩺 FASE 1: Generación de DDX")
            self.logger.info(f"    Modelo: {self.config['dxgpt_emulator']['model']}")
            self.logger.info(f"    Generando diagnósticos para caso {case_id}...")
            
            ddx_names = self.diagnosis_generator.generate_diagnoses(case_description, prompt_template, output_schema)
            
            self.logger.info(f"    ✅ DDX generados: {len(ddx_names)} diagnósticos")
            for i, ddx in enumerate(ddx_names, 1):
                self.logger.info(f"        [{i}] {ddx}")
            self.logger.info("")
            
            # Step 2: Azure Text Analytics
            self.logger.info("🔍 FASE 2: Extracción de códigos médicos")
            self.logger.info(f"    Procesando {len(ddx_names)} DDX con Azure Text Analytics...")
            
            ddx_list = []
            for i, ddx_name in enumerate(ddx_names, 1):
                self.logger.info(f"    Procesando DDX [{i}]: {ddx_name}")
                azure_result = self.azure_client.extract_medical_codes(ddx_name)
                
                ddx_list.append({
                    "name": ddx_name,
                    "normalized_text": azure_result["normalized_text"],
                    "medical_codes": azure_result["medical_codes"]
                })
                
                # Log results for this DDX
                normalized = azure_result["normalized_text"]
                codes = azure_result["medical_codes"]
                icd_codes = codes.get("icd10", [])
                
                if normalized != ddx_name:
                    self.logger.info(f"        → Normalizado: {normalized}")
                if icd_codes:
                    self.logger.info(f"        → Códigos ICD-10: {icd_codes}")
                
                # Check if any codes were found
                all_codes = [c for code_list in codes.values() for c in code_list]
                if not all_codes:
                    self.logger.info(f"        → Sin códigos médicos (candidato para BERT)")
                elif not icd_codes and normalized == ddx_name:
                    self.logger.info(f"        → Sin ICD-10 (posible candidato para BERT)")
            
            self.logger.info(f"    ✅ Códigos extraídos para todos los DDX")
            self.logger.info("")
            
            # Step 3: Get GDX
            gdx_list = case.get("diagnoses", [])
            self.logger.info(f"📊 GDX de referencia: {len(gdx_list)} diagnósticos")
            for i, gdx in enumerate(gdx_list, 1):
                self.logger.info(f"    [{i}] {gdx.get('name', 'Sin nombre')}")
            self.logger.info("")
            
            # Normalize GDX structure for semantic evaluation
            normalized_gdx_list = []
            for gdx in gdx_list:
                normalized_gdx = {
                    "name": gdx.get("name", ""),
                    "normalized_text": gdx.get("normalized_text", gdx.get("name", "")),
                    "medical_codes": {
                        "icd10": gdx.get("medical_codes", {}).get("icd10", []) if "medical_codes" in gdx else gdx.get("icd10", []),
                        "snomed": gdx.get("medical_codes", {}).get("snomed", []) if "medical_codes" in gdx else gdx.get("snomed", []),
                        "omim": gdx.get("medical_codes", {}).get("omim", []) if "medical_codes" in gdx else gdx.get("omim", []),
                        "orpha": gdx.get("medical_codes", {}).get("orpha", []) if "medical_codes" in gdx else gdx.get("orpha", [])
                    }
                }
                normalized_gdx_list.append(normalized_gdx)
            
            # Step 4: Semantic evaluation
            self.logger.info("🧠 FASE 3: Evaluación semántica")
            self.logger.info(f"    Comparando {len(ddx_list)} DDX vs {len(gdx_list)} GDX...")
            
            semantic_result = self.semantic_evaluator.evaluate_case_semantics(ddx_list, normalized_gdx_list)
            
            best_match = semantic_result["best_match"]
            self.logger.info(f"    ✅ Mejor match encontrado:")
            self.logger.info(f"        DDX: {best_match['ddx_name']}")
            self.logger.info(f"        GDX: {best_match['gdx_name']}")
            self.logger.info(f"        Score: {best_match['score']:.3f}")
            if best_match.get('code_type') == 'BERT':
                self.logger.info(f"        Tipo: BERT (fallback semántico)")
                self.logger.info(f"        Relación: {best_match.get('relationship', 'N/A')}")
            else:
                self.logger.info(f"        Tipo: {best_match.get('code_type', 'none')}")
            self.logger.info("")
            
            # Step 5: Severity evaluation
            self.logger.info("⚖️  FASE 4: Evaluación de severidad")
            
            best_gdx = None
            if semantic_result["best_match"]["gdx_name"]:
                for gdx in gdx_list:
                    if gdx.get("name") == semantic_result["best_match"]["gdx_name"]:
                        best_gdx = gdx
                        break
            
            if not best_gdx and gdx_list:
                best_gdx = gdx_list[0]  # Fallback to first GDX
            
            if best_gdx:
                self.logger.info(f"    GDX de referencia: {best_gdx.get('name', 'Sin nombre')}")
                self.logger.info(f"    Severidad GDX: {best_gdx.get('severity', 'S5')}")
            
            severity_result = self.severity_evaluator.evaluate_case_severity(ddx_list, best_gdx or {})
            
            self.logger.info(f"    ✅ Score de severidad calculado: {severity_result['final_score']:.3f}")
            self.logger.info("")
            
            # Final status
            self.logger.info("🎯 CASO COMPLETADO")
            self.logger.info(f"    ID: {case_id}")
            self.logger.info(f"    Score semántico: {best_match['score']:.3f}")
            self.logger.info(f"    Score severidad: {severity_result['final_score']:.3f}")
            self.logger.info("=" * 60)
            
            # Compile result
            result = {
                "case_id": case_id,
                "complexity": case.get("complexity", ""),
                "case_description": case_description,
                "ground_truth_diagnoses": gdx_list,
                "generated_diagnoses": ddx_list,
                "semantic_evaluation": semantic_result,
                "severity_evaluation": severity_result,
                "timestamp": datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
                self.logger.error("")
                self.logger.error("❌ ERROR EN CASO")
                self.logger.error(f"    ID: {case_id}")
                self.logger.error(f"    Error: {e}")
                self.logger.error("=" * 60)
                
                return {
                    "case_id": case_id,
                    "complexity": case.get("complexity", ""),
                    "case_description": case.get("case", ""),
                    "ground_truth_diagnoses": case.get("diagnoses", []),
                    "generated_diagnoses": [],
                    "semantic_evaluation": {"best_match": {"score": 0.0}, "detailed_scores": []},
                    "severity_evaluation": {"final_score": 0.0},
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
    
    def run_evaluation(self, base_dir: Path) -> Dict[str, Any]:
        """Run the complete evaluation pipeline."""
        self.logger.info("🔬 " + "="*60)
        self.logger.info("🔬 INICIO DE LA EVALUACIÓN")
        self.logger.info("🔬 " + "="*60)
        
        # Load data from config
        dataset_path = self.config["dataset_path"]
        prompt_path = self.config["dxgpt_emulator"]["prompt_path"]
        schema_path = self.config["dxgpt_emulator"]["output_schema_path"]
        
        dataset = load_dataset(dataset_path, base_dir)
        prompt_template = load_prompt_template(prompt_path, base_dir)
        output_schema = load_output_schema(schema_path, base_dir)
        
        # Initialize progress tracker
        progress_tracker = CaseProgressTracker(dataset, self.logger)
        
        self.logger.info(f"📊 Dataset: {len(dataset)} casos de {dataset_path}")
        self.logger.info(f"📝 Prompt: {prompt_path}")
        self.logger.info(f"🔗 Schema: {'Activado' if output_schema else 'Desactivado'}")
        self.logger.info(f"📋 Grupos por letra: {dict(progress_tracker.letter_groups)}")
        self.logger.info("")
        
        # Process cases with ThreadPoolExecutor
        results = []
        
        self.logger.info("")
        self.logger.info("🚀 " + "="*60)
        self.logger.info("🚀 FASE 1: INICIO DE LA GENERACIÓN DE DDX Y ANÁLISIS DE CASOS")
        self.logger.info("🚀 " + "="*60)
        self.logger.info("⚠️  Presiona CTRL+C para interrumpir gracefully")
        self.logger.info("")
        
        try:
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                # Submit all jobs
                future_to_case = {
                    executor.submit(
                        self.process_single_case,
                        case,
                        prompt_template,
                        output_schema,
                        idx,
                        progress_tracker
                    ): (case, idx)
                    for idx, case in enumerate(dataset)
                }
                
                # Collect results as they complete
                try:
                    for future in as_completed(future_to_case):
                        case, idx = future_to_case[future]
                        try:
                            result = future.result()
                            results.append(result)
                            
                            # Progress logging only - no file writing
                            if len(results) % SAVE_INTERVAL == 0:
                                self.logger.info(f"✅ Progreso: {len(results)}/{len(dataset)} casos completados")
                            
                        except Exception as e:
                            self.logger.error(f"❌ Error en future para caso {case.get('id', '')}: {e}")
                            continue
                            
                except KeyboardInterrupt:
                    self.logger.warning("")
                    self.logger.warning("🛑 INTERRUPCIÓN DETECTADA (CTRL+C)")
                    self.logger.warning("🔄 Cancelando tareas pendientes...")
                    
                    # Cancel all pending futures
                    cancelled_count = 0
                    for future in future_to_case:
                        if not future.done():
                            future.cancel()
                            cancelled_count += 1
                    
                    self.logger.warning(f"❌ {cancelled_count} tareas canceladas")
                    self.logger.warning(f"✅ {len(results)} casos completados antes de la interrupción")
                    
                    # Ask user what to do
                    if results:
                        self.logger.info("")
                        self.logger.info("🤔 ¿Qué quieres hacer con los resultados parciales?")
                        self.logger.info("   Presiona ENTER para continuar con análisis parcial")
                        self.logger.info("   Presiona CTRL+C de nuevo para salir completamente")
                        try:
                            input("   Esperando input... ")
                            self.logger.info("📊 Continuando con análisis de resultados parciales...")
                        except KeyboardInterrupt:
                            self.logger.warning("🚪 Salida forzada. No se generarán archivos.")
                            return {"status": "interrupted", "results_count": len(results)}
                    else:
                        self.logger.warning("🚪 No hay resultados para procesar. Saliendo...")
                        return {"status": "interrupted", "results_count": 0}
                        
        except KeyboardInterrupt:
            self.logger.warning("🛑 INTERRUPCIÓN DETECTADA durante inicialización")
            self.logger.warning("🚪 Saliendo...")
            return {"status": "interrupted", "results_count": 0}
        
        # Sort results by case_id to maintain order
        results.sort(key=lambda x: x.get("case_id", ""))
        
        self.logger.info("")
        self.logger.info("✅ " + "="*60)
        self.logger.info("✅ FASE 1: FINALIZADA. Todos los casos procesados.")
        self.logger.info("✅ " + "="*60)
        
        self.logger.info("")
        self.logger.info("⚖️  " + "="*60)
        self.logger.info("⚖️  FASE 2: INICIO DE LA ASIGNACIÓN DE SEVERIDADES POR LOTES")
        self.logger.info("⚖️  " + "="*60)
        
        # Step 6: Batch severity assignment for unique DDX
        try:
            unique_ddx_names = set()
            for result in results:
                for ddx in result.get("generated_diagnoses", []):
                    unique_ddx_names.add(ddx.get("normalized_text", ddx.get("name", "")))
            
            unique_ddx_list = list(unique_ddx_names)
            self.logger.info(f"   📋 {len(unique_ddx_list)} diagnósticos únicos a procesar")
            self.severity_evaluator.assign_severities_batch(unique_ddx_list, self.logger)
            
        except KeyboardInterrupt:
            self.logger.warning("")
            self.logger.warning("🛑 INTERRUPCIÓN DETECTADA durante asignación de severidades")
            self.logger.warning("🚪 Usando severidades por defecto (S5) para análisis...")
            # Continue with default severities already assigned
        
        self.logger.info("")
        self.logger.info("✅ " + "="*60)
        self.logger.info("✅ FASE 2: FINALIZADA.")
        self.logger.info("✅ " + "="*60)
        
        self.logger.info("")
        self.logger.info("📊 " + "="*60)
        self.logger.info("📊 FASE 3: INICIO DEL CÁLCULO DE MÉTRICAS FINALES Y GENERACIÓN DE INFORMES")
        self.logger.info("📊 " + "="*60)
        
        try:
            # Calculate Top-K metrics
            self.logger.info("🎯 Calculando métricas Top-K...")
            topk_metrics = TopKMetrics.calculate_topk_accuracy(results)
            
            # Generate specialized output files
            self.logger.info("📁 Generando archivos de salida especializados...")
            
            # 1. Executive Summary
            self.logger.info("   📊 Generando run_summary.json...")
            generate_run_summary(self.config, results, topk_metrics, dataset, self.output_dir)
            
            # 2. DDX frequency analysis
            self.logger.info("   📈 Generando ddx_analysis.csv...")
            generate_ddx_analysis_csv(results, self.output_dir)
            
            # 3. Clean DDX generation results by dataset
            self.logger.info("   🔍 Generando diagnoses.json...")
            generate_case_ddx_generation(results, self.output_dir)
            
            # 4. Detailed semantic evaluation by dataset
            self.logger.info("   🧠 Generando semantic_evaluation.json...")
            generate_case_semantic_evaluation(results, self.output_dir)
            
            # 5. Detailed severity evaluation by dataset
            self.logger.info("   ⚖️  Generando severity_evaluation.json...")
            generate_case_severity_evaluation(results, self.output_dir)
            
        except KeyboardInterrupt:
            self.logger.warning("")
            self.logger.warning("🛑 INTERRUPCIÓN DETECTADA durante generación de reportes")
            self.logger.warning("🚪 Algunos archivos pueden estar incompletos")
            # Continue to metrics calculation even if files are incomplete
        
        # Extract scores for summary
        semantic_scores = [r["semantic_evaluation"]["best_match"]["score"] for r in results]
        
        # Calculate final metrics for logging
        severity_scores = [r["severity_evaluation"]["final_score"] for r in results]
        mean_semantic = round(sum(semantic_scores) / len(semantic_scores), 4) if semantic_scores else 0.0
        mean_severity = round(sum(severity_scores) / len(severity_scores), 4) if severity_scores else 0.0
        
        self.logger.info("")
        self.logger.info("✅ " + "="*60)
        self.logger.info("✅ FASE 3: FINALIZADA. Todos los informes generados.")
        self.logger.info("✅ " + "="*60)
        
        self.logger.info("")
        self.logger.info("🎉 " + "="*60)
        self.logger.info("🎉 EVALUACIÓN COMPLETADA EXITOSAMENTE")
        self.logger.info("🎉 " + "="*60)
        self.logger.info("💾 ARCHIVOS GENERADOS:")
        self.logger.info("   📊 run_summary.json - Resumen ejecutivo")
        self.logger.info("   📈 ddx_analysis.csv - Análisis de frecuencia DDX")
        self.logger.info("   🔍 diagnoses.json - Diagnósticos detallados con códigos médicos")
        self.logger.info("   🧠 semantic_evaluation.json - Evaluación semántica organizada por dataset")
        self.logger.info("   ⚖️  severity_evaluation.json - Evaluación severidad organizada por dataset")
        self.logger.info("   📄 evaluation.log - Traza de ejecución completa")
        self.logger.info("")
        # Count BERT usage from results
        bert_count = 0
        bert_successful = 0
        for result in results:
            code_type = result.get("semantic_evaluation", {}).get("best_match", {}).get("code_type", "")
            if code_type == "BERT":
                bert_count += 1
                if result.get("semantic_evaluation", {}).get("best_match", {}).get("score", 0.0) >= 0.8:
                    bert_successful += 1
        
        self.logger.info("📈 MÉTRICAS FINALES:")
        self.logger.info(f"   🧠 Score semántico promedio: {mean_semantic:.4f}")
        self.logger.info(f"   ⚖️  Score severidad promedio: {mean_severity:.4f}")
        self.logger.info(f"   🎯 Top-1 accuracy: {topk_metrics['top1_accuracy']:.4f}")
        self.logger.info(f"   🎯 Top-2 accuracy: {topk_metrics['top2_accuracy']:.4f}")
        self.logger.info(f"   🎯 Top-3 accuracy: {topk_metrics['top3_accuracy']:.4f}")
        self.logger.info(f"   🎯 Top-4 accuracy: {topk_metrics['top4_accuracy']:.4f}")
        self.logger.info(f"   🎯 Top-5 accuracy: {topk_metrics['top5_accuracy']:.4f}")
        self.logger.info(f"   📊 Mean Reciprocal Rank: {topk_metrics['mean_reciprocal_rank']:.4f}")
        if bert_count > 0:
            self.logger.info("")
            self.logger.info("🤖 USO DE BERT (FALLBACK SEMÁNTICO):")
            self.logger.info(f"   📊 Casos con BERT: {bert_count}/{len(results)} ({bert_count/len(results)*100:.1f}%)")
            self.logger.info(f"   ✅ BERT exitosos (≥0.80): {bert_successful}/{bert_count} ({bert_successful/bert_count*100:.1f}% de intentos)")
        self.logger.info("🎉 " + "="*60)
        
        # Return a lightweight summary instead of full results
        return {
            "experiment_name": self.config.get("experiment_name", "Unnamed Experiment"),
            "total_cases": len(results),
            "mean_semantic_score": mean_semantic,
            "mean_severity_score": mean_severity,
            "topk_metrics": topk_metrics,
            "output_files": [
                "run_summary.json",
                "ddx_analysis.csv",
                "diagnoses.json",
                "semantic_evaluation.json",
                "severity_evaluation.json",
                "evaluation.log"
            ]
        }

# =============================================================================
# 9. MAIN EXECUTION
# =============================================================================

def main():
    """Main execution function."""
    try:
        # Load configuration
        base_dir = Path(__file__).parent
        config_path = base_dir / "config.yaml"
        config = load_config(config_path)
        
        # Setup experiment directory and logging
        output_dir, logger = setup_experiment_directory(config, base_dir)
        
        # Setup signal handler for graceful shutdown
        def signal_handler(signum, frame):
            logger.warning("")
            logger.warning("🛑 SEÑAL DE INTERRUPCIÓN RECIBIDA")
            logger.warning("🔄 Iniciando shutdown graceful...")
            raise KeyboardInterrupt("Signal received")
        
        signal.signal(signal.SIGINT, signal_handler)
        
        # Run pipeline
        pipeline = EvaluationPipeline(config, output_dir, logger, base_dir)
        results = pipeline.run_evaluation(base_dir)
        
        return results
        
    except KeyboardInterrupt:
        print("\n🛑 PROGRAMA INTERRUMPIDO POR EL USUARIO")
        print("🚪 Saliendo...")
        return {"status": "interrupted_main", "message": "Program interrupted by user"}
    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    main()