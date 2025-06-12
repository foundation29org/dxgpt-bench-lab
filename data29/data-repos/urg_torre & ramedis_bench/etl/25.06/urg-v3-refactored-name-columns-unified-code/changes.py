from pathlib import Path
from typing import Tuple, List, Dict
import pandas as pd
from utils.bert import calculate_semantic_similarity
from utils.icd10 import ICD10Taxonomy

"""
example of first 3 rows:
id,case,golden-diagnosis,golden-diagnosis-long,diagnostic_code/s,death,critical,pediatric,severity,icd10_diagnosis_name,icd10_chapter_code,icd10_block_code,icd10_category_code,icd10_category_name,icd10_disease_group_code,icd10_disease_group_name,icd10_disease_code,icd10_disease_name,icd10_disease_variant_code
[filas de ejemplo eliminadas: contenían casos reales]
"""

data_path = Path("before.csv")

# do not change the code above
# code below, properly implement the following:
# - we want to create a new csv file with the following columns:
#   - id
#   - case
#   - diagnosis (golden-diagnosis already)
#   - icd10_diagnosis (icd10_diagnosis_name)
#   - category: <icd10_category_name>
#   - block: <icd10_disease_group_name>
#   - sub_block: <icd10_disease_name>
#   - diagnostic_code (from all the columns which names finish as "_code" currently take the value of the one with a longer value)
#   - death
#   - critical
#   - pediatric
#   - severity

def find_longest_diagnostic_code(row: pd.Series) -> str:
    """Find the diagnostic code with the longest value from all columns ending with '_code'"""
    code_columns = [col for col in row.index if col.endswith('_code')]
    longest_code = ""
    
    for col in code_columns:
        code_value = str(row[col]) if pd.notna(row[col]) else ""
        if len(code_value) > len(longest_code):
            longest_code = code_value
    
    return longest_code

def transform_dataset(input_path: Path, output_path: Path) -> None:
    """Transform the dataset to the required format"""
    print(f"Reading data from {input_path}...")
    df = pd.read_csv(input_path)
    
    print(f"Processing {len(df)} rows...")
    
    # Create the new dataset with required columns
    new_df = pd.DataFrame({
        'id': df['id'],
        'case': df['case'],
        'diagnosis': df['golden-diagnosis'],
        'icd10_diagnosis': df['icd10_diagnosis_name'],
        'category': df['icd10_category_name'],
        'block': df['icd10_disease_group_name'],
        'sub_block': df['icd10_disease_name'],
        'diagnostic_code': df.apply(find_longest_diagnostic_code, axis=1),
        'death': df['death'],
        'critical': df['critical'],
        'pediatric': df['pediatric'],
        'severity': df['severity']
    })
    
    print(f"Saving transformed data to {output_path}...")
    new_df.to_csv(output_path, index=False)
    print(f"Successfully saved {len(new_df)} rows to {output_path}")
    
    # Display summary statistics
    print("\nDataset Summary:")
    print(f"Total cases: {len(new_df)}")
    print(f"Deaths: {new_df['death'].sum()}")
    print(f"Critical cases: {new_df['critical'].sum()}")
    print(f"Pediatric cases: {new_df['pediatric'].sum()}")
    print(f"Average severity: {new_df['severity'].mean():.2f}")
    
    # Show unique categories
    print(f"\nUnique categories: {new_df['category'].nunique()}")
    print(f"Unique blocks: {new_df['block'].nunique()}")
    print(f"Unique sub-blocks: {new_df['sub_block'].nunique()}")

def main():
    """Main execution function"""
    input_file = data_path
    output_file = Path("transformed_dataset.csv")
    
    if not input_file.exists():
        print(f"Error: Input file {input_file} not found!")
        return
    
    try:
        transform_dataset(input_file, output_file)
        print(f"\nTransformation completed successfully!")
        print(f"Input: {input_file}")
        print(f"Output: {output_file}")
        
    except Exception as e:
        print(f"Error during transformation: {e}")
        raise

if __name__ == "__main__":
    main()
