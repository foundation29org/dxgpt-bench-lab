import json
import os
from glob import glob

def extract_all_gdx(directory):
    """Extract all unique GDX values from JSON files in the directory."""
    all_gdx = set()
    
    # Find all JSON files
    json_files = glob(os.path.join(directory, "*.json"))
    
    print(f"Found {len(json_files)} JSON files to process")
    
    for json_file in json_files:
        print(f"Processing: {os.path.basename(json_file)}")
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different JSON structures
            if isinstance(data, list):
                # Array of cases
                for case in data:
                    if 'diagnoses' in case and isinstance(case['diagnoses'], list):
                        for diagnosis in case['diagnoses']:
                            if 'name' in diagnosis:
                                all_gdx.add(diagnosis['name'])
            elif isinstance(data, dict):
                # Dictionary structure - check for different possible keys
                for key in data:
                    if isinstance(data[key], list):
                        for case in data[key]:
                            if 'diagnoses' in case and isinstance(case['diagnoses'], list):
                                for diagnosis in case['diagnoses']:
                                    if 'name' in diagnosis:
                                        all_gdx.add(diagnosis['name'])
                            # Also check gdx_details structure
                            elif 'gdx_details' in case and isinstance(case['gdx_details'], dict):
                                all_gdx.update(case['gdx_details'].keys())
                
        except Exception as e:
            print(f"  Error processing {json_file}: {e}")
    
    return all_gdx

def main():
    """Main function to extract and save GDX values."""
    # Get current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Extract all GDX values
    all_gdx = extract_all_gdx(current_dir)
    
    print(f"\nTotal unique GDX values found: {len(all_gdx)}")
    
    # Sort by length (longest first) and then alphabetically
    sorted_gdx = sorted(all_gdx, key=lambda x: (-len(x), x))
    
    # Save to file
    output_file = os.path.join(current_dir, "all_gdx_sorted.txt")
    with open(output_file, 'w', encoding='utf-8') as f:
        for gdx in sorted_gdx:
            f.write(f"{gdx}\n")
    
    print(f"\nGDX values saved to: {output_file}")
    print(f"First 5 (longest):")
    for i, gdx in enumerate(sorted_gdx[:5], 1):
        print(f"  {i}. {gdx} (length: {len(gdx)})")
    
    print(f"\nLast 5 (shortest):")
    for i, gdx in enumerate(sorted_gdx[-5:], len(sorted_gdx)-4):
        print(f"  {i}. {gdx} (length: {len(gdx)})")

if __name__ == "__main__":
    main()