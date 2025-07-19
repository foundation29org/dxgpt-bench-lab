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
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import yaml

# Add utils to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'utils'))

from utils.llm import get_llm
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class DXGPTEmulator:
    """DXGPT Emulator for generating differential diagnoses"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the DXGPT Emulator
        
        Args:
            config: Configuration dictionary with emulator settings
        """
        self.config = config
        self.emulator_config = config['DXGPT_EMULATOR']
        
        # Initialize LLM
        self.llm = get_llm(self.emulator_config['MODEL'])
        
        # Load prompt template
        self.prompt_template = self._load_prompt_template()
        
        # Load output schema if enabled
        self.output_schema = None
        if self.emulator_config.get('OUTPUT_SCHEMA', False):
            self.output_schema = self._load_output_schema()
    
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
    
    def _generate_ddx_for_case(self, case: Dict[str, Any]) -> Tuple[List[str], str]:
        """
        Generate DDX for a single case
        
        Args:
            case: Case dictionary containing case description
            
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
        
        prompt = self.prompt_template.format(case_description=case_description)
        
        # Get LLM parameters
        params = self.emulator_config.get('PARAMS', {})
        
        # Check if this is an O3 model
        model_name = self.emulator_config['MODEL'].lower()
        is_o3_model = 'o3' in model_name
        
        try:
            # Generate response with model-appropriate parameters
            if is_o3_model:
                # O3 models use reasoning_effort instead of temperature/max_tokens
                if self.output_schema:
                    response = self.llm.generate(
                        prompt,
                        reasoning_effort=params.get('reasoning_effort', 'low'),
                        schema=self.output_schema
                    )
                else:
                    response = self.llm.generate(
                        prompt,
                        reasoning_effort=params.get('reasoning_effort', 'low')
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
            
            # Extract DDX using unified parsing logic
            ddx_list = self._extract_ddx_from_response(response, case.get('id', 'unknown'))
            return ddx_list, str(response)
        
        except Exception as e:
            case_id = case.get('id', 'unknown')
            print(f"ERROR: Error generating DDX for case {case_id}: {str(e)}")
            
            # Helpful tip for common configuration issues
            if "diagnosis" in str(e) or "format" in str(e).lower():
                print(f"TIP: Check if OUTPUT_SCHEMA setting conflicts with your prompt's expected format")
            
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
            # Clean response text (handle markdown code blocks)
            response_text = str(response).strip()
            if response_text.startswith('```json'):
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif response_text.startswith('```'):
                response_text = response_text.split('```')[1].split('```')[0].strip()
            
            # FORMAT_D: Extract content from XML-like tags
            if '<diagnosis_output>' in response_text and '</diagnosis_output>' in response_text:
                start_tag = '<diagnosis_output>'
                end_tag = '</diagnosis_output>'
                start_idx = response_text.find(start_tag) + len(start_tag)
                end_idx = response_text.find(end_tag)
                if start_idx < end_idx:
                    response_text = response_text[start_idx:end_idx].strip()
            
            # Try to parse as JSON first
            parsed = None
            try:
                parsed = json.loads(response_text)
            except json.JSONDecodeError as json_error:
                # If JSON fails, try Python literal evaluation (handles single quotes)
                try:
                    parsed = ast.literal_eval(response_text)
                except (ValueError, SyntaxError) as literal_error:
                    print(f"WARNING: Failed to parse response for case {case_id}")
                    print(f"WARNING: Response preview: {str(response)[:200]}...")
                    print(f"TIP: If LLM returns unexpected format, check if OUTPUT_SCHEMA conflicts with prompt instructions")
                    return []
            
            # Check if it's a list first
            if isinstance(parsed, list) and len(parsed) > 0:
                # Check if it's a list of objects with diagnosis fields
                if isinstance(parsed[0], dict):
                    # FORMAT_C: List of diagnosis objects with "diagnosis" field (juanjo_classic.txt format)
                    # Example: [{"diagnosis": "Disease A", "description": "...", "symptoms_in_common": [...], "symptoms_not_in_common": [...]}, ...]
                    if 'diagnosis' in parsed[0]:
                        diagnoses = []
                        for item in parsed:
                            if isinstance(item, dict) and 'diagnosis' in item:
                                diagnosis_name = item['diagnosis']
                                if diagnosis_name:  # Only add non-empty diagnoses
                                    diagnoses.append(str(diagnosis_name))
                        
                        if diagnoses:
                            return diagnoses
                        else:
                            print(f"WARNING: FORMAT_C malformed: No valid diagnosis objects found for case {case_id}")
                            return []
                    
                    # FORMAT_D: List of diagnosis objects with "dx" field (claude_sonnet_4.txt format)
                    # Example: [{"dx": "Disease A", "rationale": "Brief reason", "confidence": "High/Medium/Low"}, ...]
                    elif 'dx' in parsed[0]:
                        diagnoses = []
                        for item in parsed:
                            if isinstance(item, dict) and 'dx' in item:
                                diagnosis_name = item['dx']
                                if diagnosis_name:  # Only add non-empty diagnoses
                                    diagnoses.append(str(diagnosis_name))
                        
                        if diagnoses:
                            return diagnoses
                        else:
                            print(f"WARNING: FORMAT_D malformed: No valid dx objects found for case {case_id}")
                            return []
                    
                    else:
                        # Unknown object format in list
                        print(f"WARNING: Unknown object format in list for case {case_id}")
                        print(f"WARNING: First object keys: {list(parsed[0].keys())}")
                        return []
                else:
                    # FORMAT_A: Simple list of strings
                    # Example: ["Disease A", "Disease B", "Disease C", ...]
                    return [str(item) for item in parsed if item]  # Convert to strings, filter empty
            
            # FORMAT_B: Dictionary with "diagnoses" key
            # Example: {"diagnoses": ["Disease A", "Disease B", ...]}
            elif isinstance(parsed, dict) and 'diagnoses' in parsed:
                diagnoses = parsed['diagnoses']
                if isinstance(diagnoses, list):
                    return [str(item) for item in diagnoses if item]  # Convert to strings, filter empty
                else:
                    print(f"WARNING: FORMAT_B malformed: 'diagnoses' key exists but value is not a list for case {case_id}")
                    return []
            
            else:
                print(f"WARNING: UNKNOWN_FORMAT: Unexpected response structure for case {case_id}")
                print(f"WARNING: Response type: {type(parsed)}")
                if isinstance(parsed, dict):
                    print(f"WARNING: Response keys: {list(parsed.keys())}")
                print(f"TIP: Check if OUTPUT_SCHEMA enforces a format different from your prompt")
                return []
                
        except Exception as e:
            print(f"WARNING: PARSING_ERROR for case {case_id}: {str(e)}")
            print(f"TIP: Check if OUTPUT_SCHEMA conflicts with prompt instructions")
            return []
    
    def generate_ddx_for_dataset(self, dataset: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate DDX for entire dataset
        
        Args:
            dataset: List of case dictionaries
            
        Returns:
            List of cases with DDX added
        """
        print(f"STARTING: DDX generation for {len(dataset)} cases...")
        print(f"MODEL: {self.emulator_config['MODEL']}")
        print(f"PROMPT: {self.emulator_config['CANDIDATE_PROMPT_PATH']}")
        print(f"SCHEMA: {'Enabled' if self.output_schema else 'Disabled'}")
        print("-" * 60)
        
        results = []
        
        for i, case in enumerate(dataset, 1):
            case_id = case.get('id', f'case_{i}')
            print(f"[{i}/{len(dataset)}] Processing case {case_id}...")
            
            # Generate DDX
            ddx_list, raw_response = self._generate_ddx_for_case(case)
            
            # Display the raw response object
            print(f"RAW_RESPONSE: {raw_response}")
            print(f"PARSED_DDX: {ddx_list}")
            
            if ddx_list:
                print(f"✅ SUCCESS: Generated {len(ddx_list)} DDX")
                
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
                print("FAILED: No DDX generated")
                # Add empty DDX to maintain structure
                case_with_ddx = case.copy()
                case_with_ddx['ddx_details'] = {}
                results.append(case_with_ddx)
            
            print("-" * 40)
        
        print("-" * 60)
        successful_cases = sum(1 for r in results if r.get('ddx_details'))
        print(f"COMPLETED: DDX generation finished!")
        print(f"STATS: Success rate: {successful_cases}/{len(dataset)} ({successful_cases/len(dataset)*100:.1f}%)")
        
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
            
            print(f"SAVED: DDX results saved to: {output_path}")
            
        except Exception as e:
            print(f"ERROR: Error saving results: {str(e)}")
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