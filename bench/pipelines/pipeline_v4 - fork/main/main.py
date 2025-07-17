#!/usr/bin/env python3
"""
Main Pipeline Orchestrator
=========================

This is the main orchestrator that manages the entire pipeline execution:
1. Emulator: DDX generation using LLM
2. Labeler: Medical code attribution using Azure Text Analytics
3. Evaluator: Evaluation of DDX quality against GDX

Features:
- State management and resumption
- Configurable pipeline steps
- Proper file naming and organization
- User interaction for conflict resolution
- Validation and error handling
"""

import json
import os
import sys
import yaml
import shutil
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# Import pipeline modules
from emulator import DXGPTEmulator
from medlabeler import MedicalLabeler
from evaluator import evaluate_dataset

def clean_name_for_filename(name: str) -> str:
    """
    Clean a name for use in filenames by replacing invalid characters
    
    Args:
        name: Original name
        
    Returns:
        Cleaned name suitable for filenames
    """
    # Replace common invalid characters
    replacements = {
        '-': '_',
        ' ': '_',
        '.': '_',
        '/': '_',
        '\\': '_',
        ':': '_',
        '*': '_',
        '?': '_',
        '"': '_',
        '<': '_',
        '>': '_',
        '|': '_'
    }
    
    cleaned = name
    for old, new in replacements.items():
        cleaned = cleaned.replace(old, new)
    
    # Remove consecutive underscores
    while '__' in cleaned:
        cleaned = cleaned.replace('__', '_')
    
    # Remove leading/trailing underscores
    cleaned = cleaned.strip('_')
    
    return cleaned

def get_file_names(config: Dict[str, Any]) -> Dict[str, str]:
    """
    Generate file names based on configuration
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Dictionary with file name components
    """
    # Get dataset, model and prompt names
    dataset_path = config['DATASET_PATH']
    dataset_name = os.path.splitext(os.path.basename(dataset_path))[0]
    model_name = config['DXGPT_EMULATOR']['MODEL']
    prompt_path = config['DXGPT_EMULATOR']['CANDIDATE_PROMPT_PATH']
    prompt_name = os.path.splitext(os.path.basename(prompt_path))[0]
    
    # Clean names for filenames
    clean_dataset = clean_name_for_filename(dataset_name)
    clean_prompt = clean_name_for_filename(prompt_name)
    clean_model = clean_name_for_filename(model_name)
    
    # Create file name components
    prefix = f"{clean_prompt}___{clean_model}"
    
    return {
        'dataset_name': clean_dataset,
        'prompt_name': clean_prompt,
        'model_name': clean_model,
        'prefix': prefix,
        'emulator_file': f"{prefix}___ddxs_from_emulator.json",
        'labeler_file': f"{prefix}___ddxs_from_labeler.json",
        'config_file': f"{prefix}___config.yaml"
    }

def create_output_directory(config: Dict[str, Any]) -> str:
    """
    Create output directory structure
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Path to output directory
    """
    # Get file names
    file_names = get_file_names(config)
    
    # Create output directory path with dataset nesting
    output_dir = os.path.join(
        os.path.dirname(__file__), 'output',
        file_names['dataset_name'],
        file_names['prompt_name'],
        file_names['model_name']
    )
    
    os.makedirs(output_dir, exist_ok=True)
    
    return output_dir

def save_config_with_timestamp(config: Dict[str, Any], output_path: str) -> None:
    """
    Save configuration with timestamp
    
    Args:
        config: Configuration dictionary
        output_path: Path to save configuration
    """
    # Add timestamp
    config_with_timestamp = config.copy()
    config_with_timestamp['TIMESTAMP'] = datetime.now().isoformat()
    
    # Save configuration
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(config_with_timestamp, f, default_flow_style=False, allow_unicode=True)

def load_config_with_fallback(base_dir: str = None) -> Dict[str, Any]:
    """
    Load configuration with preference for saved copy in output directory
    
    Args:
        base_dir: Base directory to search for config (defaults to script directory)
        
    Returns:
        Configuration dictionary
    """
    if base_dir is None:
        base_dir = os.path.dirname(__file__)
    
    # First try to find saved config copy in output structure
    saved_config_path = None
    output_base = os.path.join(base_dir, 'output')
    
    if os.path.exists(output_base):
        # Look for most recent config copy
        for root, dirs, files in os.walk(output_base):
            for file in files:
                if file.endswith('___config.yaml'):
                    potential_path = os.path.join(root, file)
                    if saved_config_path is None or os.path.getmtime(potential_path) > os.path.getmtime(saved_config_path):
                        saved_config_path = potential_path
    
    # Try saved config first
    if saved_config_path and os.path.exists(saved_config_path):
        try:
            with open(saved_config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            print(f"CONFIG: Using saved copy: {saved_config_path}")
            return config
        except Exception as e:
            print(f"WARNING: Failed to load saved config copy, falling back to original: {str(e)}")
    
    # Fallback to original config.yaml
    original_config_path = os.path.join(base_dir, 'config.yaml')
    try:
        with open(original_config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        print(f"CONFIG: Using original: {original_config_path}")
        return config
    except FileNotFoundError:
        print(f"ERROR: Configuration file not found: {original_config_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"ERROR: Error parsing configuration file: {str(e)}")
        sys.exit(1)

def check_file_exists(file_path: str) -> bool:
    """Check if file exists and is not empty"""
    return os.path.exists(file_path) and os.path.getsize(file_path) > 0

def get_user_choice(message: str, options: List[str]) -> str:
    """
    Get user choice from a list of options (always includes abort option)
    
    Args:
        message: Message to display
        options: List of available options
        
    Returns:
        Selected option or "ABORT" if user chooses to abort
    """
    print(f"\n{message}")
    
    # Add abort option to the list
    all_options = options + ["❌ Abort operation"]
    
    for i, option in enumerate(all_options, 1):
        print(f"{i}. {option}")
    
    while True:
        try:
            choice = int(input("Enter your choice (number): "))
            if 1 <= choice <= len(all_options):
                selected_option = all_options[choice - 1]
                
                # Check if user chose abort
                if selected_option == "❌ Abort operation":
                    print("\n🚫 Operation aborted by user")
                    return "ABORT"
                
                return selected_option
            else:
                print(f"Please enter a number between 1 and {len(all_options)}")
        except ValueError:
            print("Please enter a valid number")
        except KeyboardInterrupt:
            print("\n\n🚫 Operation aborted by user (Ctrl+C)")
            return "ABORT"

def validate_pipeline_state(config: Dict[str, Any], output_dir: str, file_names: Dict[str, str]) -> Tuple[str, str]:
    """
    Validate pipeline state and determine next steps
    
    Args:
        config: Configuration dictionary
        output_dir: Output directory path
        file_names: Dictionary with file names
        
    Returns:
        Tuple of (next_step, input_file_path)
    """
    main_config = config.get('MAIN', {})
    should_emulate = main_config.get('SHOULD_EMULATE', True)
    should_label = main_config.get('SHOULD_LABEL', True)
    should_evaluate = main_config.get('SHOULD_EVALUATE', True)
    
    # Check file existence
    emulator_file = os.path.join(output_dir, file_names['emulator_file'])
    labeler_file = os.path.join(output_dir, file_names['labeler_file'])
    
    emulator_exists = check_file_exists(emulator_file)
    labeler_exists = check_file_exists(labeler_file)
    
    # Determine next step based on state and configuration
    # 🔧 Check most advanced state first (labeler exists = both emulation & labeling done)
    if should_label and labeler_exists:
        # Labeler output exists, ask user about evaluation
        if should_evaluate:
            options = [
                "Re-run complete pipeline from DDX generation (will overwrite existing results)",
                "Skip to evaluation using existing labeled results"
            ]
            choice = get_user_choice(
                f"⚠️  Labeled results already exist at {labeler_file}\n"
                f"👌  Both EMULATION and LABELING have been completed.",
                options
            )
            if choice == "ABORT":
                return 'abort', None
            elif choice == options[0]:
                return 'emulate', None  # Re-run from emulation (not labeling)
            else:
                return 'evaluate', labeler_file  # Skip to evaluation
        else:
            # Evaluation disabled, pipeline complete
            print("✅ EMULATION and LABELING completed. EVALUATION disabled.")
            return 'done', None
    # 🔧 Check intermediate state (emulator exists but labeler doesn't)
    elif should_emulate and emulator_exists:
        # Emulator output exists, ask user
        options = [
            "Re-run DDX generation (will overwrite existing results)",
            "Continue with medical code labeling using existing DDX"
        ]
        choice = get_user_choice(
            f"⚠️  DDX results already exist at {emulator_file}",
            options
        )
        if choice == "ABORT":
            return 'abort', None
        elif choice == options[0]:
            return 'emulate', None
        else:
            return 'label', emulator_file
    # 🔧 Check if emulation is needed (starting from scratch)
    elif should_emulate and not emulator_exists:
        return 'emulate', None
    # 🔧 Check if labeling is needed but no emulator output exists
    elif should_label and not labeler_exists:
        if emulator_exists:
            return 'label', emulator_file
        else:
            print("❌ Error: Cannot label without emulator output")
            return 'error', None
    # 🔧 Check if only evaluation is needed
    elif should_evaluate:
        if labeler_exists:
            return 'evaluate', labeler_file
        elif emulator_exists:
            print("❌ Error: Cannot evaluate without medical codes (labeler output)")
            return 'error', None
        else:
            print("❌ Error: Cannot evaluate without DDX results")
            return 'error', None
    else:
        print("✅ All requested pipeline steps are disabled")
        return 'done', None

def run_emulator(config: Dict[str, Any], output_dir: str, file_names: Dict[str, str]) -> Optional[str]:
    """
    Run the emulator step
    
    Args:
        config: Configuration dictionary
        output_dir: Output directory path
        file_names: Dictionary with file names
        
    Returns:
        Path to emulator output file or None if failed
    """
    print("\n" + "="*60)
    print("STEP 1: DDX GENERATION (EMULATOR)")
    print("="*60)
    
    try:
        # Load dataset
        dataset_path = os.path.join(
            os.path.dirname(__file__), '..', '..', '..', '..',
            config['DATASET_PATH']
        )
        
        with open(dataset_path, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
        
        # Initialize emulator
        emulator = DXGPTEmulator(config)
        
        # Generate DDX
        results = emulator.generate_ddx_for_dataset(dataset)
        
        # Save results
        output_file = os.path.join(output_dir, file_names['emulator_file'])
        emulator.save_results(results, output_file)
        
        return output_file
        
    except Exception as e:
        print(f"❌ Error in emulator step: {str(e)}")
        return None

def run_labeler(config: Dict[str, Any], input_file: str, output_dir: str, file_names: Dict[str, str]) -> Optional[str]:
    """
    Run the labeler step
    
    Args:
        config: Configuration dictionary
        input_file: Path to input file from emulator
        output_dir: Output directory path
        file_names: Dictionary with file names
        
    Returns:
        Path to labeler output file or None if failed
    """
    print("\n" + "="*60)
    print("STEP 2: MEDICAL CODE ATTRIBUTION (LABELER)")
    print("="*60)
    
    try:
        # Load emulator results
        with open(input_file, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
        
        # Initialize labeler
        labeler = MedicalLabeler()
        
        # Process dataset
        results = labeler.process_dataset(dataset)
        
        # Save results
        output_file = os.path.join(output_dir, file_names['labeler_file'])
        labeler.save_results(results, output_file)
        
        # Remove emulator output as requested
        labeler.replace_emulator_output(input_file, output_file)
        
        return output_file
        
    except Exception as e:
        print(f"❌ Error in labeler step: {str(e)}")
        return None

def run_evaluator(config: Dict[str, Any], input_file: str, output_dir: str, file_names: Dict[str, str]) -> Optional[str]:
    """
    Run the evaluator step
    
    Args:
        config: Configuration dictionary
        input_file: Path to input file from labeler
        output_dir: Output directory path
        file_names: Dictionary with file names
        
    Returns:
        Path to evaluation output directory or None if failed
    """
    print("\n" + "="*60)
    print("STEP 3: EVALUATION")
    print("="*60)
    
    try:
        # Create timestamped evaluation directory
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        eval_output_dir = os.path.join(output_dir, timestamp)
        os.makedirs(eval_output_dir, exist_ok=True)
        
        # Run evaluation
        evaluate_dataset(input_file, eval_output_dir, config)
        
        # Save configuration copy to evaluation directory
        config_file = os.path.join(eval_output_dir, file_names['config_file'])
        save_config_with_timestamp(config, config_file)
        
        return eval_output_dir
        
    except Exception as e:
        print(f"❌ Error in evaluator step: {str(e)}")
        return None

def main():
    """Main pipeline orchestrator"""
    print("🚀 Starting Pipeline V4 - Medical Diagnosis Evaluation System")
    print("="*70)
    
    # Load configuration
    config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"❌ Configuration file not found: {config_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"❌ Error parsing configuration file: {str(e)}")
        sys.exit(1)
    
    # Validate configuration
    required_keys = ['DATASET_PATH', 'DXGPT_EMULATOR', 'MAIN']
    for key in required_keys:
        if key not in config:
            print(f"❌ Missing required configuration key: {key}")
            sys.exit(1)
    
    # Get file names and create output directory
    file_names = get_file_names(config)
    output_dir = create_output_directory(config)
    
    print(f"📁 Output directory: {output_dir}")
    print(f"📋 Experiment: {config.get('EXPERIMENT_NAME', 'no-name-provided')}")
    print(f"📝 Description: {config.get('EXPERIMENT_DESCRIPTION', 'no-description-provided')}")
    
    # Save configuration copy
    config_file = os.path.join(output_dir, file_names['config_file'])
    save_config_with_timestamp(config, config_file)
    
    # CRITICAL: Switch to using the saved config copy for all subsequent operations
    # This ensures perfect reproducibility and protects against config.yaml changes during execution
    print(f"IMPORTANT: Switching to saved config copy: {config_file}")
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        print("SUCCESS: Now using timestamped config copy for all pipeline operations")
    except Exception as e:
        print(f"ERROR: Failed to load saved config copy: {str(e)}")
        sys.exit(1)
    
    # Validate pipeline state and determine next steps
    next_step, input_file = validate_pipeline_state(config, output_dir, file_names)
    
    if next_step == 'error':
        sys.exit(1)
    elif next_step == 'abort':
        print("✅ Pipeline execution aborted")
        sys.exit(0)
    elif next_step == 'done':
        print("✅ Pipeline execution completed (all steps disabled)")
        sys.exit(0)
    
    # Execute pipeline steps
    current_input = input_file
    
    # Step 1: Emulator
    if next_step == 'emulate':
        current_input = run_emulator(config, output_dir, file_names)
        if not current_input:
            print("❌ Pipeline failed at emulator step")
            sys.exit(1)
        next_step = 'label'
    
    # Step 2: Labeler
    if next_step == 'label' and config.get('MAIN', {}).get('SHOULD_LABEL', True):
        current_input = run_labeler(config, current_input, output_dir, file_names)
        if not current_input:
            print("❌ Pipeline failed at labeler step")
            sys.exit(1)
        next_step = 'evaluate'
    
    # Step 3: Evaluator
    if next_step == 'evaluate' and config.get('MAIN', {}).get('SHOULD_EVALUATE', True):
        eval_output_dir = run_evaluator(config, current_input, output_dir, file_names)
        if not eval_output_dir:
            print("❌ Pipeline failed at evaluator step")
            sys.exit(1)
    
    print("\n" + "="*70)
    print("✅ Pipeline execution completed successfully!")
    print(f"📊 Results saved to: {output_dir}")
    print("="*70)

if __name__ == "__main__":
    main()