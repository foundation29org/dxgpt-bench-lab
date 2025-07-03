"""
Quick script to extract all unique diagnosis names from before.json and save to text file
"""

import json

# Load the JSON data
with open('before.json', 'r', encoding='utf-8') as f:
    cases = json.load(f)

# Extract all diagnosis names using a set to avoid duplicates
unique_diagnoses = set()
total_diagnoses = 0

for case in cases:
    for diagnosis in case.get('diagnoses', []):
        if 'name' in diagnosis:
            unique_diagnoses.add(diagnosis['name'])
            total_diagnoses += 1

# Convert to sorted list for consistent output
sorted_diagnoses = sorted(unique_diagnoses)

# Save to text file
with open('diagnoses_names.txt', 'w', encoding='utf-8') as f:
    for diagnosis in sorted_diagnoses:
        f.write(diagnosis + '\n')

print(f"Total diagnoses found: {total_diagnoses}")
print(f"Unique diagnoses: {len(unique_diagnoses)}")
print(f"Duplicates removed: {total_diagnoses - len(unique_diagnoses)}")
print(f"Saved to diagnoses_names.txt")
print(f"\nFirst 10 unique diagnoses (alphabetically sorted):")
for i, diag in enumerate(sorted_diagnoses[:10]):
    print(f"{i+1}. {diag}")