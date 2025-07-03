"""
Quick script to remove 'icd10_diagnosis' key from after.json
"""

import json

# Load the JSON data
with open('after.json', 'r', encoding='utf-8') as f:
    cases = json.load(f)

# Remove icd10_diagnosis from each case
removed_count = 0
for case in cases:
    if 'icd10_diagnosis' in case:
        del case['icd10_diagnosis']
        removed_count += 1

# Save the modified data back to the same file
with open('after.json', 'w', encoding='utf-8') as f:
    json.dump(cases, f, ensure_ascii=False, indent=2)

print(f"Removed 'icd10_diagnosis' from {removed_count} cases")
print(f"Total cases processed: {len(cases)}")
print("File 'after.json' has been updated")