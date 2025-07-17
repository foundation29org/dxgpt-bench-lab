#!/usr/bin/env python3
"""
Validation Script for Pipeline V4
=================================

This script validates the pipeline configuration and tests basic functionality.
"""

import json
import os
import sys
import yaml
from typing import Dict, Any

def validate_config(config_path: str) -> Dict[str, Any]:
    """
    Validate configuration file
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Loaded configuration dictionary
    """
    print("VALIDATION: Validating configuration...")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"ERROR: Configuration file not found: {config_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"ERROR: Error parsing configuration file: {str(e)}")
        sys.exit(1)
    
    # Check required top-level keys
    required_keys = ['DATASET_PATH', 'DXGPT_EMULATOR', 'EVALUATOR', 'MAIN']
    for key in required_keys:
        if key not in config:
            print(f"ERROR: Missing required configuration key: {key}")
            sys.exit(1)
    
    # Check DXGPT_EMULATOR configuration
    emulator_config = config['DXGPT_EMULATOR']
    required_emulator_keys = ['MODEL', 'CANDIDATE_PROMPT_PATH', 'PARAMS']
    for key in required_emulator_keys:
        if key not in emulator_config:
            print(f"ERROR: Missing required DXGPT_EMULATOR key: {key}")
            sys.exit(1)
    
    # Check EVALUATOR configuration
    evaluator_config = config['EVALUATOR']
    required_evaluator_keys = ['BERT_ACCEPTANCE_THRESHOLD', 'BERT_AUTOCONFIRM_THRESHOLD']
    for key in required_evaluator_keys:
        if key not in evaluator_config:
            print(f"ERROR: Missing required EVALUATOR key: {key}")
            sys.exit(1)
    
    # Check MAIN configuration
    main_config = config['MAIN']
    required_main_keys = ['SHOULD_EMULATE', 'SHOULD_LABEL', 'SHOULD_EVALUATE']
    for key in required_main_keys:
        if key not in main_config:
            print(f"ERROR: Missing required MAIN key: {key}")
            sys.exit(1)
    
    print("SUCCESS: Configuration validation passed")
    return config

def validate_loaded_config(config: Dict[str, Any]) -> None:
    """
    Validate an already-loaded configuration object
    
    Args:
        config: Configuration dictionary
    """
    print("VALIDATION: Validating loaded configuration...")
    
    # Check required top-level keys
    required_keys = ['DATASET_PATH', 'DXGPT_EMULATOR', 'EVALUATOR', 'MAIN']
    for key in required_keys:
        if key not in config:
            print(f"ERROR: Missing required configuration key: {key}")
            sys.exit(1)
    
    # Check DXGPT_EMULATOR configuration
    emulator_config = config['DXGPT_EMULATOR']
    required_emulator_keys = ['MODEL', 'CANDIDATE_PROMPT_PATH', 'PARAMS']
    for key in required_emulator_keys:
        if key not in emulator_config:
            print(f"ERROR: Missing required DXGPT_EMULATOR key: {key}")
            sys.exit(1)
    
    # Check EVALUATOR configuration
    evaluator_config = config['EVALUATOR']
    required_evaluator_keys = ['BERT_ACCEPTANCE_THRESHOLD', 'BERT_AUTOCONFIRM_THRESHOLD']
    for key in required_evaluator_keys:
        if key not in evaluator_config:
            print(f"ERROR: Missing required EVALUATOR key: {key}")
            sys.exit(1)
    
    # Check MAIN configuration
    main_config = config['MAIN']
    required_main_keys = ['SHOULD_EMULATE', 'SHOULD_LABEL', 'SHOULD_EVALUATE']
    for key in required_main_keys:
        if key not in main_config:
            print(f"ERROR: Missing required MAIN key: {key}")
            sys.exit(1)
    
    print("SUCCESS: Configuration validation passed")

def validate_dataset(dataset_path: str) -> None:
    """
    Validate dataset file
    
    Args:
        dataset_path: Path to dataset file
    """
    print(f"📊 Validating dataset: {dataset_path}")
    
    try:
        with open(dataset_path, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: Dataset file not found: {dataset_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Error parsing dataset JSON: {str(e)}")
        sys.exit(1)
    
    if not isinstance(dataset, list):
        print(f"ERROR: Dataset must be a list, got {type(dataset)}")
        sys.exit(1)
    
    if len(dataset) == 0:
        print("ERROR: Dataset is empty")
        sys.exit(1)
    
    # Validate first few cases
    for i, case in enumerate(dataset[:3]):
        if not isinstance(case, dict):
            print(f"ERROR: Case {i} is not a dictionary")
            sys.exit(1)
        
        # Check required fields
        if 'id' not in case:
            print(f"ERROR: Case {i} missing 'id' field")
            sys.exit(1)
        
        if 'case' not in case:
            print(f"ERROR: Case {i} missing 'case' field")
            sys.exit(1)
        
        if 'diagnoses' not in case:
            print(f"ERROR: Case {i} missing 'diagnoses' field")
            sys.exit(1)
        
        # Check diagnoses structure
        diagnoses = case['diagnoses']
        if not isinstance(diagnoses, list):
            print(f"ERROR: Case {i} diagnoses must be a list")
            sys.exit(1)
        
        for j, diag in enumerate(diagnoses):
            if not isinstance(diag, dict):
                print(f"ERROR: Case {i} diagnosis {j} is not a dictionary")
                sys.exit(1)
            
            if 'name' not in diag:
                print(f"ERROR: Case {i} diagnosis {j} missing 'name' field")
                sys.exit(1)
            
            if 'medical_codes' not in diag:
                print(f"ERROR: Case {i} diagnosis {j} missing 'medical_codes' field")
                sys.exit(1)
    
    print(f"SUCCESS: Dataset validation passed ({len(dataset)} cases)")

def validate_prompt(prompt_path: str) -> None:
    """
    Validate prompt file
    
    Args:
        prompt_path: Path to prompt file
    """
    print(f"📝 Validating prompt: {prompt_path}")
    
    try:
        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompt = f.read()
    except FileNotFoundError:
        print(f"ERROR: Prompt file not found: {prompt_path}")
        sys.exit(1)
    
    if not prompt.strip():
        print("ERROR: Prompt file is empty")
        sys.exit(1)
    
    if '{case_description}' not in prompt:
        print("ERROR: Prompt must contain '{case_description}' placeholder")
        sys.exit(1)
    
    print("SUCCESS: Prompt validation passed")

def validate_schema(schema_path: str) -> None:
    """
    Validate output schema file
    
    Args:
        schema_path: Path to schema file
    """
    print(f"🔧 Validating schema: {schema_path}")
    
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: Schema file not found: {schema_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Error parsing schema JSON: {str(e)}")
        sys.exit(1)
    
    # Basic schema validation
    if not isinstance(schema, dict):
        print("ERROR: Schema must be a dictionary")
        sys.exit(1)
    
    if 'type' not in schema:
        print("ERROR: Schema missing 'type' field")
        sys.exit(1)
    
    print("SUCCESS: Schema validation passed")

def clean_name_for_filename(name: str) -> str:
    """Clean a name for use in filenames by replacing invalid characters"""
    replacements = {
        '-': '_', ' ': '_', '.': '_', '/': '_', '\\': '_', ':': '_',
        '*': '_', '?': '_', '"': '_', '<': '_', '>': '_', '|': '_'
    }
    
    cleaned = name
    for old, new in replacements.items():
        cleaned = cleaned.replace(old, new)
    
    while '__' in cleaned:
        cleaned = cleaned.replace('__', '_')
    
    return cleaned.strip('_')

def validate_file_naming(config: Dict[str, Any]) -> None:
    """
    Validate file naming logic
    
    Args:
        config: Configuration dictionary
    """
    print("📁 Validating file naming...")
    
    # Test clean_name_for_filename
    test_cases = [
        ("gpt-4o-summary", "gpt_4o_summary"),
        ("dxgpt_dev.txt", "dxgpt_dev_txt"),
        ("test-name with spaces", "test_name_with_spaces"),
        ("file/with\\slashes", "file_with_slashes"),
        ("all_450.json", "all_450_json")
    ]
    
    for input_name, expected in test_cases:
        result = clean_name_for_filename(input_name)
        if result != expected:
            print(f"❌ Name cleaning failed: '{input_name}' -> '{result}' (expected '{expected}')")
            sys.exit(1)
    
    # Test basic file naming structure
    dataset_path = config['DATASET_PATH']
    dataset_name = os.path.splitext(os.path.basename(dataset_path))[0]
    model_name = config['DXGPT_EMULATOR']['MODEL']
    prompt_path = config['DXGPT_EMULATOR']['CANDIDATE_PROMPT_PATH']
    prompt_name = os.path.splitext(os.path.basename(prompt_path))[0]
    
    clean_dataset = clean_name_for_filename(dataset_name)
    clean_prompt = clean_name_for_filename(prompt_name)
    clean_model = clean_name_for_filename(model_name)
    
    if not clean_dataset or not clean_prompt or not clean_model:
        print("❌ File naming produced empty strings")
        sys.exit(1)
    
    print("✅ File naming validation passed")

def main():
    """Main validation function"""
    print("VALIDATION: Starting Pipeline V4 Validation")
    print("="*50)
    
    # Load configuration with preference for saved copy
    # Import here to avoid circular imports
    from main import load_config_with_fallback
    config = load_config_with_fallback()
    
    # Validate the loaded configuration
    validate_loaded_config(config)
    
    # Get script directory for relative paths
    script_dir = os.path.dirname(__file__)
    
    # Validate dataset
    dataset_path = os.path.join(script_dir, '..', '..', '..', '..', config['DATASET_PATH'])
    validate_dataset(dataset_path)
    
    # Validate prompt
    prompt_path = os.path.join(script_dir, '..', '..', '..', '..', config['DXGPT_EMULATOR']['CANDIDATE_PROMPT_PATH'])
    validate_prompt(prompt_path)
    
    # Validate schema if enabled
    if config['DXGPT_EMULATOR'].get('OUTPUT_SCHEMA', False):
        schema_path = os.path.join(script_dir, '..', '..', '..', '..', config['DXGPT_EMULATOR']['OUTPUT_SCHEMA_PATH'])
        validate_schema(schema_path)
    
    # Validate file naming
    validate_file_naming(config)
    
    print("\n" + "="*50)
    print("SUCCESS: All validation checks passed!")
    print("READY: Pipeline is ready to run")
    print("="*50)

if __name__ == "__main__":
    main()