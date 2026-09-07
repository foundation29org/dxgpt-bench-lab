#!/usr/bin/env python3
"""
Multi-LLM timing test
Test multiple LLM models (GPT-5, GPT-4o, O3, O1) with clinical cases.
Usage: python llm_timing_test.py --gpt4o --none
       python llm_timing_test.py --o3 --high
       python llm_timing_test.py --o1 --none
       python llm_timing_test.py --gpt5mini --low
"""

import os
import time
import json
import requests
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Hardcoded prompt (juanjo classic)
PROMPT = """You are a diagnostic assistant. Given the patient case below, generate N possible diagnoses. For each:

- Give a brief description of the disease  
- List symptoms the patient has that match the disease  
- List patient symptoms that are not typical for the disease  

Output format:  
Return a JSON array of N objects, each with the following keys:  
- "diagnosis": disease name  
- "description": brief summary of the disease  
- "symptoms_in_common": list of matching symptoms  
- "symptoms_not_in_common": list of patient symptoms not typical of that disease  

Output only valid JSON (no extra text, no XML, no formatting wrappers).  

Example:  
```json
[
  {{
    "diagnosis": "Disease A",
    "description": "Short explanation.",
    "symptoms_in_common": ["sx1", "sx2"],
    "symptoms_not_in_common": ["sx3", "sx4"]
  }},
  ...
]

PATIENT DESCRIPTION:
{case_description}
"""

# Hardcoded clinical cases (4 different cases from dataset - indices 0, 10, 25, 50)
CLINICAL_CASES = [
    # Case 1: R443 (index 0) - Renal/Lupus complex case
    """Motivo de consulta: Paciente acude a consulta para ser diagnosticado Anamnesis: Paciente de sexo desconocido de desconocidos años. El paciente presenta los siguientes síntomas:  -Renal insufficiency  -Proteinuria  -Glomerulonephritis  -Renal cyst  -Uveitis  -Arthritis  -Lymphopenia  -Pulmonary embolism  -Deep venous thrombosis  -Microscopic hematuria  -Reduced coagulation factor V activity  -Antinuclear antibody positivity  -Renal cell carcinoma  -Knee pain  -Anti-beta 2 glycoprotein I antibody positivity Antecedentes: No hay antecedentes Exploracion: No se realiza Pruebas clinicas:""",
    
    # Case 2: R39 (index 10) - Metabolic acidemia case
    """Motivo de consulta: Paciente acude a consulta para ser diagnosticado Anamnesis: Paciente de sexo desconocido de desconocidos años. El paciente presenta los siguientes síntomas:  -Seizure  -Generalized hypotonia  -Death in infancy  -Thrombocytopenia  -Leukopenia  -Metabolic acidosis  -Hyperammonemia  -Vomiting  -Methylmalonic acidemia  -Neonatal death  -Methylmalonic aciduria Antecedentes: No hay antecedentes Exploracion: No se realiza Pruebas clinicas:""",
    
    # Case 3: R118 (index 25) - Simple neonatal case
    """Motivo de consulta: Paciente acude a consulta para ser diagnosticado Anamnesis: Paciente de sexo desconocido de desconocidos años. El paciente presenta los siguientes síntomas:  -Death in infancy  -Neonatal death  -Elevated urinary carboxylic acid Antecedentes: No hay antecedentes Exploracion: No se realiza Pruebas clinicas:""",
    
    # Case 4: U1 (index 50) - Rheumatology case
    """Record ID: 1
Patient Initials: M.K.S.
Gender: Female
DOB: 25.05.2000
Age: Not provided
Date of Admission: Not provided
Department: Rheumatology
Mode of Admission: Planned
Complaints: Pain in hip joints (predominantly left); Periodic pain in wrists, cervical, and thoracic spine
History of Present Illness: Patient has been ill since the age of 12. Disease began acutely after an episode of tonsillitis. Fever and swelling of the ankle joint were noted. Juvenile rheumatoid arthritis (JRA) was not diagnosed at that time. Over the years, the patient experienced periodic exacerbations of joint pain and swelling, particularly affecting the hips, wrists, and spine."""
]

# Model mappings with their configurations
MODEL_CONFIGS = {
    # GPT-5 models (reasoning models)
    'gpt5mini': {
        'deployment_name': 'gpt-5-mini',
        'api_version': '2024-12-01-preview',
        'is_reasoning_model': True,
        'supports_reasoning_effort': True
    },
    'gpt5nano': {
        'deployment_name': 'gpt-5-nano',
        'api_version': '2024-12-01-preview',
        'is_reasoning_model': True,
        'supports_reasoning_effort': True
    },
    'gpt5base': {
        'deployment_name': 'gpt-5',
        'api_version': '2024-12-01-preview',
        'is_reasoning_model': True,
        'supports_reasoning_effort': True
    },
    
    # Other models (non-reasoning)
    'gpt4o': {
        'deployment_name': 'gpt-4o-summary',
        'api_version': '2024-02-15-preview',
        'is_reasoning_model': False,
        'supports_reasoning_effort': False
    },
    'o3': {
        'deployment_name': 'o3-images',
        'api_version': '2024-12-01-preview',
        'is_reasoning_model': True,
        'supports_reasoning_effort': True
    },
    'o1': {
        'deployment_name': 'o1',
        'api_version': '2024-02-15-preview',
        'is_reasoning_model': True,
        'supports_reasoning_effort': False  # O1 doesn't support reasoning_effort parameter
    }
}

# Reasoning effort options
REASONING_EFFORTS = ['none', 'minimal', 'low', 'medium', 'high']

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Multi-LLM timing test')
    
    # Model selection
    parser.add_argument('--gpt5mini', action='store_true', help='Use gpt-5-mini')
    parser.add_argument('--gpt5nano', action='store_true', help='Use gpt-5-nano')
    parser.add_argument('--gpt5base', action='store_true', help='Use gpt-5')
    parser.add_argument('--gpt4o', action='store_true', help='Use gpt-4o-summary')
    parser.add_argument('--o3', action='store_true', help='Use o3-images')
    parser.add_argument('--o1', action='store_true', help='Use o1')
    
    # Reasoning effort selection
    parser.add_argument('--none', action='store_true', help='No reasoning effort (for non-reasoning models)')
    parser.add_argument('--minimal', action='store_true', help='Use minimal reasoning effort')
    parser.add_argument('--low', action='store_true', help='Use low reasoning effort')
    parser.add_argument('--medium', action='store_true', help='Use medium reasoning effort')
    parser.add_argument('--high', action='store_true', help='Use high reasoning effort')
    
    return parser.parse_args()

def get_model_and_effort(args):
    """Extract model variant and reasoning effort from args."""
    # Determine model variant
    model_variant = 'gpt5mini'  # default
    if args.gpt5nano:
        model_variant = 'gpt5nano'
    elif args.gpt5base:
        model_variant = 'gpt5base'
    elif args.gpt4o:
        model_variant = 'gpt4o'
    elif args.o3:
        model_variant = 'o3'
    elif args.o1:
        model_variant = 'o1'
    elif args.gpt5mini:
        model_variant = 'gpt5mini'
    
    # Determine reasoning effort
    reasoning_effort = 'none'  # default for non-reasoning models
    if args.minimal:
        reasoning_effort = 'minimal'
    elif args.low:
        reasoning_effort = 'low'
    elif args.medium:
        reasoning_effort = 'medium'
    elif args.high:
        reasoning_effort = 'high'
    elif args.none:
        reasoning_effort = 'none'
    
    return model_variant, reasoning_effort

def calculate_stats(results):
    """Calculate mean and standard deviation from results."""
    import statistics
    
    if not results or len(results) == 0:
        return None
    
    valid_results = [r for r in results if r is not None]
    if len(valid_results) == 0:
        return None
    
    # Extract metrics
    elapsed_times = [r['elapsed_seconds'] for r in valid_results]
    prompt_tokens = [r['prompt_tokens'] for r in valid_results]  
    completion_tokens = [r['completion_tokens'] for r in valid_results]
    total_tokens = [r['total_tokens'] for r in valid_results]
    reasoning_tokens = [r['reasoning_tokens'] for r in valid_results]
    response_lengths = [r['response_length'] for r in valid_results]
    tokens_per_sec = [r['tokens_per_second'] for r in valid_results]
    
    # Calculate stats
    stats = {
        'n_cases': len(valid_results),
        'n_failed': len(results) - len(valid_results),
        'elapsed_mean': statistics.mean(elapsed_times),
        'elapsed_std': statistics.stdev(elapsed_times) if len(elapsed_times) > 1 else 0,
        'prompt_tokens_mean': statistics.mean(prompt_tokens),
        'prompt_tokens_std': statistics.stdev(prompt_tokens) if len(prompt_tokens) > 1 else 0,
        'completion_tokens_mean': statistics.mean(completion_tokens),
        'completion_tokens_std': statistics.stdev(completion_tokens) if len(completion_tokens) > 1 else 0,
        'total_tokens_mean': statistics.mean(total_tokens),
        'total_tokens_std': statistics.stdev(total_tokens) if len(total_tokens) > 1 else 0,
        'reasoning_tokens_mean': statistics.mean(reasoning_tokens),
        'reasoning_tokens_std': statistics.stdev(reasoning_tokens) if len(reasoning_tokens) > 1 else 0,
        'response_length_mean': statistics.mean(response_lengths),
        'response_length_std': statistics.stdev(response_lengths) if len(response_lengths) > 1 else 0,
        'tokens_per_sec_mean': statistics.mean(tokens_per_sec),
        'tokens_per_sec_std': statistics.stdev(tokens_per_sec) if len(tokens_per_sec) > 1 else 0
    }
    
    return stats

def save_to_log(model_deployment, reasoning_effort, results):
    """Save experiment results to log file with statistics."""
    log_file = "llm_timing_results.txt"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    stats = calculate_stats(results)
    
    if stats is None:
        # All failed
        log_line = f"{timestamp}\t{model_deployment}\t{reasoning_effort}\tALL_FAILED\t4\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\t0\n"
    else:
        log_line = (
            f"{timestamp}\t"
            f"{model_deployment}\t"
            f"{reasoning_effort}\t"
            f"SUCCESS\t"
            f"{stats['n_cases']}\t"
            f"{stats['n_failed']}\t"
            f"{stats['elapsed_mean']:.2f}\t"
            f"{stats['elapsed_std']:.2f}\t"
            f"{stats['prompt_tokens_mean']:.0f}\t"
            f"{stats['prompt_tokens_std']:.0f}\t"
            f"{stats['completion_tokens_mean']:.0f}\t"
            f"{stats['completion_tokens_std']:.0f}\t"
            f"{stats['total_tokens_mean']:.0f}\t"
            f"{stats['total_tokens_std']:.0f}\t"
            f"{stats['reasoning_tokens_mean']:.0f}\t"
            f"{stats['reasoning_tokens_std']:.0f}\t"
            f"{stats['response_length_mean']:.0f}\t"
            f"{stats['response_length_std']:.0f}\t"
            f"{stats['tokens_per_sec_mean']:.1f}\t"
            f"{stats['tokens_per_sec_std']:.1f}\n"
        )
    
    # Create header if file doesn't exist
    if not os.path.exists(log_file):
        header = "timestamp\tmodel_deployment\treasoning_effort\tstatus\tn_cases\tn_failed\telapsed_mean\telapsed_std\tprompt_tokens_mean\tprompt_tokens_std\tcompletion_tokens_mean\tcompletion_tokens_std\ttotal_tokens_mean\ttotal_tokens_std\treasoning_tokens_mean\treasoning_tokens_std\tresponse_length_mean\tresponse_length_std\ttokens_per_sec_mean\ttokens_per_sec_std\n"
        with open(log_file, 'w') as f:
            f.write(header)
    
    # Append result
    with open(log_file, 'a') as f:
        f.write(log_line)
    
    print(f"📝 Results saved to {log_file}")

def call_llm_single_case(model_variant, reasoning_effort, case_description, case_index):
    """Make a single LLM API call for one case and measure timing."""
    
    # Get credentials from environment
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    
    if not endpoint or not api_key:
        raise ValueError("Missing AZURE_OPENAI_ENDPOINT or AZURE_OPENAI_API_KEY environment variables")
    
    # Get model configuration
    model_config = MODEL_CONFIGS[model_variant]
    deployment_name = model_config['deployment_name']
    api_version = model_config['api_version']
    is_reasoning_model = model_config['is_reasoning_model']
    supports_reasoning_effort = model_config['supports_reasoning_effort']
    
    # Format prompt with case
    full_prompt = PROMPT.format(case_description=case_description)
    
    # Build request based on model type with proper token parameter
    request_data = {
        "messages": [
            {
                "role": "user",
                "content": full_prompt
            }
        ]
    }
    
    # Add appropriate token parameter based on model
    if model_variant.startswith('gpt5') or model_variant == 'o3':
        # GPT-5 and O3 models require max_completion_tokens
        request_data["max_completion_tokens"] = 12000
        request_data["temperature"] = 1.0
    elif model_variant == 'o1':
        # O1 models require max_completion_tokens and don't support temperature
        request_data["max_completion_tokens"] = 12000
        # No temperature for O1 models
    else:
        # GPT-4o and other models use max_tokens
        request_data["max_tokens"] = 12000
        request_data["temperature"] = 0.1
    
    # Add reasoning effort if supported and not 'none'
    if supports_reasoning_effort and reasoning_effort != 'none':
        request_data["reasoning_effort"] = reasoning_effort
    
    # Build URL
    url = f"{endpoint.rstrip('/')}/openai/deployments/{deployment_name}/chat/completions?api-version={api_version}"
    
    headers = {
        "Content-Type": "application/json",
        "api-key": api_key
    }
    
    print(f"  Case {case_index + 1}/4: Testing {deployment_name} (reasoning_effort: {reasoning_effort})")
    print(f"  Prompt length: {len(full_prompt)} characters")
    
    # Make request and measure time
    start_time = time.time()
    
    try:
        # Handle reasoning models differently
        if is_reasoning_model and model_variant in ['gpt5mini', 'gpt5nano', 'gpt5base', 'o3']:
            # Use direct HTTP request for reasoning models
            response = requests.post(
                url,
                headers=headers,
                json=request_data,
                timeout=300  # 5 minutes timeout
            )
            
            end_time = time.time()
            elapsed = end_time - start_time
            
            if response.status_code != 200:
                error_detail = ""
                try:
                    error_data = response.json()
                    error_detail = f" - Error details: {error_data}"
                except:
                    error_detail = f" - Response text: {response.text}"
                
                print(f"    ❌ API request failed: {response.status_code} {response.reason}{error_detail}")
                return None
            
            response_data = response.json()
            
            # Extract content
            content = ""
            if 'choices' in response_data and len(response_data['choices']) > 0:
                choice = response_data['choices'][0]
                if 'message' in choice and 'content' in choice['message']:
                    content = choice['message']['content']
            
            # Extract usage info
            usage = response_data.get('usage', {})
            prompt_tokens = usage.get('prompt_tokens', 0)
            completion_tokens = usage.get('completion_tokens', 0)
            total_tokens = usage.get('total_tokens', 0)
            
            # Extract reasoning tokens (specific to reasoning models)
            reasoning_tokens = 0
            if 'completion_tokens_details' in usage:
                reasoning_tokens = usage['completion_tokens_details'].get('reasoning_tokens', 0)
            
        else:
            # Use direct HTTP request for all models (no SDK dependency)
            response = requests.post(
                url,
                headers=headers,
                json=request_data,
                timeout=300  # 5 minutes timeout
            )
            
            end_time = time.time()
            elapsed = end_time - start_time
            
            if response.status_code != 200:
                error_detail = ""
                try:
                    error_data = response.json()
                    error_detail = f" - Error details: {error_data}"
                except:
                    error_detail = f" - Response text: {response.text}"
                
                print(f"    ❌ API request failed: {response.status_code} {response.reason}{error_detail}")
                return None
            
            response_data = response.json()
            
            # Extract content
            content = ""
            if 'choices' in response_data and len(response_data['choices']) > 0:
                choice = response_data['choices'][0]
                if 'message' in choice and 'content' in choice['message']:
                    content = choice['message']['content']
            
            # Extract usage info
            usage = response_data.get('usage', {})
            prompt_tokens = usage.get('prompt_tokens', 0)
            completion_tokens = usage.get('completion_tokens', 0)
            total_tokens = usage.get('total_tokens', 0)
            
            # For O1 and other models, reasoning tokens might be in completion_tokens_details
            reasoning_tokens = 0
            if 'completion_tokens_details' in usage:
                reasoning_tokens = usage['completion_tokens_details'].get('reasoning_tokens', 0)
        
        # Results
        print(f"    ✅ Request completed successfully!")
        print(f"    ⏱️  Response time: {elapsed:.2f} seconds")
        print(f"    🔢 Tokens - Prompt: {prompt_tokens}, Completion: {completion_tokens}, Total: {total_tokens}")
        
        if reasoning_tokens > 0:
            response_tokens = completion_tokens - reasoning_tokens
            print(f"    🧠 Reasoning tokens: {reasoning_tokens}, Response tokens: {response_tokens}")
        
        print(f"    📊 Token throughput: {total_tokens/elapsed:.1f} tokens/second")
        
        if content:
            print(f"    📝 Response length: {len(content)} characters")
            # Try to parse as JSON
            try:
                parsed = json.loads(content)
                if isinstance(parsed, list):
                    print(f"    🎯 JSON array with {len(parsed)} diagnoses")
                else:
                    print(f"    🎯 JSON object parsed successfully")
            except json.JSONDecodeError:
                print("    ⚠️  Response is not valid JSON")
        else:
            print("    ⚠️  Empty or null response content")
        
        return {
            'deployment_name': deployment_name,
            'reasoning_effort': reasoning_effort,
            'elapsed_seconds': elapsed,
            'prompt_tokens': prompt_tokens,
            'completion_tokens': completion_tokens,
            'total_tokens': total_tokens,
            'reasoning_tokens': reasoning_tokens,  # Will be 0 for non-reasoning models
            'response_length': len(content) if content else 0,
            'tokens_per_second': total_tokens/elapsed if elapsed > 0 else 0
        }
        
    except requests.exceptions.Timeout:
        end_time = time.time()
        elapsed = end_time - start_time
        print(f"    ❌ Request timed out after {elapsed:.2f} seconds")
        return None
        
    except Exception as e:
        end_time = time.time()
        elapsed = end_time - start_time
        print(f"    ❌ Request failed after {elapsed:.2f} seconds: {str(e)}")
        return None

def run_all_cases(model_variant, reasoning_effort):
    """Run all 4 clinical cases and return results."""
    model_config = MODEL_CONFIGS[model_variant]
    deployment_name = model_config['deployment_name']
    
    print(f"\n🚀 Starting LLM timing test with {deployment_name}")
    print(f"Reasoning effort: {reasoning_effort}")
    print(f"Testing {len(CLINICAL_CASES)} clinical cases...")
    print("=" * 70)
    
    results = []
    
    for i, case in enumerate(CLINICAL_CASES):
        print(f"\n📋 Case {i+1}/{len(CLINICAL_CASES)}")
        result = call_llm_single_case(model_variant, reasoning_effort, case, i)
        results.append(result)
        
        if result:
            print(f"    ✓ Success: {result['elapsed_seconds']:.2f}s, {result['total_tokens']} tokens")
        else:
            print(f"    ✗ Failed")
    
    return results

if __name__ == "__main__":
    args = parse_args()
    model_variant, reasoning_effort = get_model_and_effort(args)
    
    # Validate reasoning effort for model
    model_config = MODEL_CONFIGS[model_variant]
    if not model_config['supports_reasoning_effort'] and reasoning_effort not in ['none']:
        print(f"⚠️  Warning: {model_config['deployment_name']} doesn't support reasoning effort. Using 'none'.")
        reasoning_effort = 'none'
    
    # Run all cases
    results = run_all_cases(model_variant, reasoning_effort)
    
    # Save to log file with statistics
    deployment_name = model_config['deployment_name']
    save_to_log(deployment_name, reasoning_effort, results)
    
    # Print summary
    stats = calculate_stats(results)
    
    print("\n" + "="*70)
    print("EXPERIMENT SUMMARY:")
    print(f"Model: {deployment_name}")
    print(f"Reasoning Effort: {reasoning_effort}")
    
    if stats:
        print(f"Successful cases: {stats['n_cases']}/4")
        print(f"Failed cases: {stats['n_failed']}/4")
        print(f"Average time: {stats['elapsed_mean']:.2f}s ± {stats['elapsed_std']:.2f}s")
        print(f"Average tokens: {stats['total_tokens_mean']:.0f} ± {stats['total_tokens_std']:.0f}")
        print(f"Average throughput: {stats['tokens_per_sec_mean']:.1f} ± {stats['tokens_per_sec_std']:.1f} tok/s")
        if stats['reasoning_tokens_mean'] > 0:
            print(f"Average reasoning tokens: {stats['reasoning_tokens_mean']:.0f} ± {stats['reasoning_tokens_std']:.0f}")
        print(f"Average response length: {stats['response_length_mean']:.0f} ± {stats['response_length_std']:.0f} chars")
    else:
        print("❌ All cases failed")
    
    print("="*70)