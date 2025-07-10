import json
import logging
from datetime import datetime
from typing import List, Dict, Tuple
from pathlib import Path
from utils.llm import get_llm

# Disable all logging except our custom prints
logging.basicConfig(level=logging.CRITICAL)
logger = logging.getLogger(__name__)

def load_diagnoses(file_path: str) -> Dict:
    """Load diagnoses from JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_diagnoses(case_data: Dict) -> Tuple[List[str], List[str]]:
    """Extract GDX and DDX diagnoses from a case."""
    gdx_list = []
    ddx_list = []
    
    # Extract GDX
    if 'gdx_details' in case_data:
        gdx_list = list(case_data['gdx_details'].keys())
    
    # Extract DDX
    if 'ddx_details' in case_data:
        ddx_list = list(case_data['ddx_details'].keys())
    
    return gdx_list, ddx_list

def find_closest_pair(gdx_list: List[str], ddx_list: List[str], llm) -> Tuple[str, str, float]:
    """Find the closest GDX-DDX pair and their confidence score using batch processing."""
    if not gdx_list or not ddx_list:
        return "", "", 0
    
    # Create all possible pairs
    pairs = []
    for gdx in gdx_list:
        for ddx in ddx_list:
            pairs.append({
                "gdx": gdx,
                "ddx": ddx
            })
    
    # Define prompt for batch processing
    batch_prompt = """For each pair of diagnostic terms below, rate how confident you would feel using them interchangeably in a clinical setting.

Scale from 1 to 10:
- 1 = Not confident at all (completely different terms, using one for the other would be a serious error)
- 2 = Very little confidence (mostly different terms with minimal relationship)
- 3 = Little confidence (related terms but with significant differences)
- 4 = Somewhat unsure (terms with some relationship but important differences)
- 5 = Moderately confident (related terms but with distinct nuances)
- 6 = Quite confident (similar terms with some minor differences)
- 7 = Confident (very similar terms, interchangeable in many contexts)
- 8 = Very confident (almost identical terms with subtle differences)
- 9 = Extremely confident (practically identical terms)
- 10 = Completely confident (terms that are fully interchangeable)

Examples:
- 'Left circumflex artery ischemia' <-> 'Acute lateral ST‑elevation myocardial infarction (left circumflex artery occlusion)' = 10/10 (because DDX includes GDX)
- 'Ectopic pregnancy due to pelvic inflammatory disease' <-> 'Ruptured ectopic pregnancy' = 9/10 (it captures the same core condition but misses the causal detail while adding a severity aspect)
- 'Systemic Lupus Erythematosus (SLE) with Libman-Sacks endocarditis' <-> 'Systemic lupus erythematosus' = 9/10 (captures the primary diagnosis but omits a key associated complication)
- 'IgA deficiency' <-> 'Anaphylactic transfusion reaction due to selective IgA deficiency' = 8/10 (represents the underlying condition but not the clinical consequence that arises from it)
- 'Ischemic colitis with transmural infarction' <-> 'Ischemic colitis' = 9/10 (includes the core condition but excludes the extent of tissue damage)

For each pair, respond with:
- GDX: [the GDX diagnosis]
- DDX: [the DDX diagnosis]  
- Score: [number from 1 to 10]"""
    
    # Define schema for structured output
    schema = {
        "type": "object",
        "properties": {
            "gdx": {"type": "string"},
            "ddx": {"type": "string"},
            "score": {"type": "number", "minimum": 1, "maximum": 10}
        },
        "required": ["gdx", "ddx", "score"]
    }
    
    try:
        # Process all pairs in a single batch
        results = llm.generate(
            batch_prompt,
            batch_items=pairs,
            schema=schema,
            temperature=0.3
        )
        
        # Find the best scoring pair
        best_score = 0
        best_gdx = ""
        best_ddx = ""
        
        for result in results:
            score = result.get('score', 0)
            if score > best_score:
                best_score = score
                best_gdx = result.get('gdx', '')
                best_ddx = result.get('ddx', '')
        
        return best_gdx, best_ddx, best_score
        
    except Exception as e:
        print(f"  ⚠️  Error in batch evaluation: {e}")
        # Fallback to individual evaluation if batch fails
        return find_closest_pair_fallback(gdx_list, ddx_list, llm)

def find_closest_pair_fallback(gdx_list: List[str], ddx_list: List[str], llm) -> Tuple[str, str, float]:
    """Fallback method using individual evaluations."""
    best_score = 0
    best_gdx = ""
    best_ddx = ""
    
    prompt_template = """How confident would you feel using these two diagnostic terms interchangeably in a clinical setting?
Scale from 1 to 10:
- 1 = Not confident at all (completely different terms, using one for the other would be a serious error)
- 2 = Very little confidence (mostly different terms with minimal relationship)
- 3 = Little confidence (related terms but with significant differences)
- 4 = Somewhat unsure (terms with some relationship but important differences)
- 5 = Moderately confident (related terms but with distinct nuances)
- 6 = Quite confident (similar terms with some minor differences)
- 7 = Confident (very similar terms, interchangeable in many contexts)
- 8 = Very confident (almost identical terms with subtle differences)
- 9 = Extremely confident (practically identical terms)
- 10 = Completely confident (terms that are fully interchangeable)

DDX Diagnosis: {ddx}
GDX Diagnosis: {gdx}

Respond ONLY with a number from 1 to 10."""
    
    for gdx in gdx_list:
        for ddx in ddx_list:
            prompt = prompt_template.format(ddx=ddx, gdx=gdx)
            try:
                response = llm.generate(prompt)
                score = float(response.strip())
                if score > best_score:
                    best_score = score
                    best_gdx = gdx
                    best_ddx = ddx
            except Exception as e:
                # Silent error handling
                continue
    
    return best_gdx, best_ddx, best_score

def process_file(file_path: str, llm, log_file) -> float:
    """Process a single JSON file and return average score."""
    print(f"\n{'='*80}")
    print(f"Processing: {file_path}")
    print(f"{'='*80}")
    
    log_file.write(f"\n{'='*80}\n")
    log_file.write(f"Processing: {file_path}\n")
    log_file.write(f"{'='*80}\n\n")
    
    data = load_diagnoses(file_path)
    all_scores = []
    
    # Count total cases
    total_cases = sum(len(cases) for cases in data.values())
    case_counter = 0
    
    # Process each section (A, B, C, etc.)
    for section, cases in data.items():
        for case in cases:
            case_counter += 1
            case_id = case.get('case_id', 'Unknown')
            
            print(f"\nProcessing case {case_id} ({case_counter}/{total_cases})")
            
            gdx_list, ddx_list = extract_diagnoses(case)
            
            if not gdx_list or not ddx_list:
                print(f"  ⚠️  Skipped (missing GDX or DDX)")
                log_file.write(f"Case {case_id}: Skipped (missing GDX or DDX)\n")
                continue
            
            best_gdx, best_ddx, score = find_closest_pair(gdx_list, ddx_list, llm)
            all_scores.append(score)
            
            print(f"  Best match: '{best_gdx}' <-> '{best_ddx}'")
            print(f"  Score: {score}/10")
            
            log_file.write(f"Case {case_id}:\n")
            log_file.write(f"  GDX list: {gdx_list}\n")
            log_file.write(f"  DDX list: {ddx_list}\n")
            log_file.write(f"  Total pairs evaluated: {len(gdx_list) * len(ddx_list)}\n")
            log_file.write(f"  Best match: '{best_gdx}' <-> '{best_ddx}'\n")
            log_file.write(f"  Confidence score: {score}/10\n\n")
    
    average_score = sum(all_scores) / len(all_scores) if all_scores else 0
    log_file.write(f"\nAverage confidence score for {file_path}: {average_score:.2f}/10\n")
    log_file.write(f"Total cases evaluated: {len(all_scores)}\n")
    
    return average_score

def main():
    """Main function to process selected JSON files."""
    # Configuration flags
    PROCESS_4O = True
    PROCESS_O1 = True
    PROCESS_O3_PRO = False
    PROCESS_O3 = False
    
    # Initialize LLM
    print("Initializing LLM with gpt-4o-summary model...")
    llm = get_llm("gpt-4o-summary")
    
    # Create timestamp for log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"O3DIFF_evaluation_{timestamp}.txt"
    
    # Define files to process
    files_to_process = []
    if PROCESS_4O:
        files_to_process.append(("diagnoses-4o.json", "4o"))
    if PROCESS_O1:
        files_to_process.append(("diagnoses-o1.json", "o1"))
    if PROCESS_O3_PRO:
        files_to_process.append(("diagnoses-o3-pro.json", "o3-pro"))
    if PROCESS_O3:
        files_to_process.append(("diagnoses-o3.json", "o3"))
    
    if not files_to_process:
        print("No files selected for processing. Please set at least one flag to True.")
        return
    
    results = {}
    
    with open(log_filename, 'w', encoding='utf-8') as log_file:
        log_file.write(f"O3DIFF Evaluation Log\n")
        log_file.write(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        log_file.write(f"Model: gpt-4o-summary\n")
        log_file.write(f"Files to process: {[f[0] for f in files_to_process]}\n")
        
        # Process each selected file
        for file_path, model_name in files_to_process:
            try:
                avg_score = process_file(file_path, llm, log_file)
                results[model_name] = avg_score
            except FileNotFoundError:
                print(f"\n⚠️  File not found: {file_path}")
                log_file.write(f"\n⚠️  File not found: {file_path}\n")
                continue
            except Exception as e:
                print(f"\n⚠️  Error processing {file_path}: {e}")
                log_file.write(f"\n⚠️  Error processing {file_path}: {e}\n")
                continue
        
        # Write summary
        log_file.write(f"\n{'='*80}\n")
        log_file.write(f"SUMMARY\n")
        log_file.write(f"{'='*80}\n\n")
        for model_name, score in results.items():
            log_file.write(f"diagnoses-{model_name}.json average score: {score:.2f}/10\n")
        
    print(f"\n{'='*80}")
    print(f"Evaluation complete!")
    print(f"Results saved to: {log_filename}")
    print(f"\nSummary:")
    for model_name, score in results.items():
        print(f"- diagnoses-{model_name}.json average score: {score:.2f}/10")

if __name__ == "__main__":
    main()