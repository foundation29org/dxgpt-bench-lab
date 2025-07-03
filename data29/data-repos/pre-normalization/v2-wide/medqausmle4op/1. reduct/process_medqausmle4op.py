import json
import os

def process_jsonl_to_json(input_dir, output_file):
    """
    Process JSONL files from medqausmle4op and convert to JSON with id, case and diagnosis columns
    """
    
    all_data = []
    id_counter = 1
    
    jsonl_files = ['phrases_no_exclude_test.jsonl', 'phrases_no_exclude_train.jsonl']
    
    for jsonl_file in jsonl_files:
        input_path = os.path.join(input_dir, jsonl_file)
        
        if not os.path.exists(input_path):
            print(f"Warning: {input_path} not found, skipping...")
            continue
            
        print(f"Processing {jsonl_file}...")
        
        with open(input_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    data = json.loads(line.strip())
                    
                    # Get case and remove line breaks
                    case = data.get('question', '').replace('\n', ' ').replace('\r', ' ')
                    # Clean up multiple spaces
                    case = ' '.join(case.split())
                    
                    answer = data.get('answer', '')
                    
                    all_data.append({
                        'id': id_counter,
                        'case': case,
                        'diagnosis': answer
                    })
                    
                    id_counter += 1
                    
                except json.JSONDecodeError as e:
                    print(f"Error parsing line {line_num} in {jsonl_file}: {e}")
                except Exception as e:
                    print(f"Error processing line {line_num} in {jsonl_file}: {e}")
    
    print(f"\nTotal records processed: {len(all_data)}")
    
    with open(output_file, 'w', encoding='utf-8') as jsonfile:
        json.dump(all_data, jsonfile, indent=2, ensure_ascii=False)
    
    print(f"JSON file created: {output_file}")
    return len(all_data)

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_dir = os.path.join(base_dir, 'raw', 'medqausmle4op')
    output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'medqausmle4op_processed.json')
    
    process_jsonl_to_json(input_dir, output_file)