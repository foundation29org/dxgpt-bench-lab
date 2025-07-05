import re
from collections import defaultdict
from datetime import datetime

def parse_evaluation_file(filepath):
    """Parse an evaluation file and extract case data."""
    results = {}
    current_model = None
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Detect model being processed
        if line.startswith("Processing: diagnoses-"):
            match = re.search(r'diagnoses-(.+)\.json', line)
            if match:
                current_model = match.group(1)
        
        # Parse case data
        elif line.startswith("Case ") and ":" in line and current_model:
            case_id = line.split(":")[0].strip()
            case_data = {
                'model': current_model,
                'gdx_list': [],
                'ddx_list': [],
                'best_match': ('', ''),
                'score': 0
            }
            
            # Read next lines for case details
            j = i + 1
            found_score = False
            while j < len(lines) and not found_score:
                detail_line = lines[j].strip()
                
                if detail_line.startswith("GDX list:"):
                    gdx_str = detail_line.replace("GDX list:", "").strip()
                    try:
                        case_data['gdx_list'] = eval(gdx_str)  # Convert string list to actual list
                    except:
                        case_data['gdx_list'] = []
                
                elif detail_line.startswith("DDX list:"):
                    ddx_str = detail_line.replace("DDX list:", "").strip()
                    try:
                        case_data['ddx_list'] = eval(ddx_str)
                    except:
                        case_data['ddx_list'] = []
                
                elif detail_line.startswith("Best match:"):
                    match_str = detail_line.replace("Best match:", "").strip()
                    # Parse format: 'GDX' <-> 'DDX'
                    parts = match_str.split(" <-> ")
                    if len(parts) == 2:
                        gdx_match = parts[0].strip().strip("'")
                        ddx_match = parts[1].strip().strip("'")
                        case_data['best_match'] = (gdx_match, ddx_match)
                
                elif detail_line.startswith("Confidence score:"):
                    score_str = detail_line.replace("Confidence score:", "").strip()
                    try:
                        score = float(score_str.split("/")[0])
                        case_data['score'] = score
                        found_score = True
                    except:
                        case_data['score'] = 0
                
                j += 1
            
            # Only store if we have valid data
            if case_data['gdx_list'] and case_data['ddx_list']:
                if case_id not in results:
                    results[case_id] = {}
                results[case_id][current_model] = case_data
        
        i += 1
    
    return results

def create_consolidated_report(file1, file2, output_file):
    """Create a consolidated report from two evaluation files."""
    # Parse both files
    results1 = parse_evaluation_file(file1)
    results2 = parse_evaluation_file(file2)
    
    # Merge results
    all_results = defaultdict(dict)
    for case_id, models in results1.items():
        all_results[case_id].update(models)
    for case_id, models in results2.items():
        all_results[case_id].update(models)
    
    # Sort cases
    sorted_cases = sorted(all_results.keys(), key=lambda x: (x[0], int(re.findall(r'\d+', x)[0]) if re.findall(r'\d+', x) else 0))
    
    # Create output
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"Consolidated O3DIFF Results\n")
        f.write(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"{'='*80}\n\n")
        
        for case_id in sorted_cases:
            models_data = all_results[case_id]
            
            # Get scores for all models in order: o3-pro, o3, o1, 4o
            model_order = ['o3-pro', 'o3', 'o1', '4o']
            scores = []
            for model in model_order:
                if model in models_data:
                    scores.append(int(models_data[model]['score']))
            
            # Write case header with scores
            f.write(f"{case_id} - {scores}\n")
            
            # Collect all unique GDX terms and count how many models use each as best match
            all_gdx = set()
            gdx_usage_count = defaultdict(int)
            gdx_number_map = {}
            
            for model in model_order:
                if model in models_data:
                    data = models_data[model]
                    all_gdx.update(data['gdx_list'])
                    best_gdx = data['best_match'][0]
                    gdx_usage_count[best_gdx] += 1
            
            # Sort GDX list and assign numbers
            sorted_gdx = sorted(list(all_gdx))
            for i, gdx in enumerate(sorted_gdx, 1):
                gdx_number_map[gdx] = i
            
            # Write GDX list with usage counts
            f.write(f"  GDX: [\n")
            for gdx in sorted_gdx:
                usage_count = gdx_usage_count.get(gdx, 0)
                usage_marks = f" ({'I' * usage_count})" if usage_count > 0 else ""
                f.write(f"    {gdx}{usage_marks}\n")
            f.write(f"  ]\n")
            
            # Write model details with nesting
            for model in model_order:
                if model in models_data:
                    data = models_data[model]
                    f.write(f"  {model}:\n")
                    
                    # Write best match GDX with its number
                    best_gdx = data['best_match'][0]
                    gdx_num = gdx_number_map.get(best_gdx, 0)
                    if gdx_num == 0:
                        # If not found in map, it means it's not in the GDX list for this case
                        f.write(f"    Best match GDX: {best_gdx} (N/A)\n")
                    else:
                        f.write(f"    Best match GDX: {best_gdx} ({gdx_num})\n")
                    
                    # Write DDX list with best match highlighted
                    f.write(f"    DDX list: [\n")
                    for ddx in data['ddx_list']:
                        if ddx == data['best_match'][1]:
                            f.write(f"      **{ddx.upper()}**\n")
                        else:
                            f.write(f"      {ddx}\n")
                    f.write(f"    ]\n")
            
            f.write("\n")

if __name__ == "__main__":
    create_consolidated_report(
        "O3DIFF_evaluation_20250704_170856.txt",
        "O3DIFF_evaluation_20250704_174821.txt",
        "consolidated_results.txt"
    )
    print("Consolidated report created: consolidated_results.txt")