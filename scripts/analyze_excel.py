
import pandas as pd
import sys

def analyze_excel(file_path):
    try:
        # Load the excel file
        df = pd.read_excel(file_path)
        
        print(f"--- Analysis of {file_path} ---")
        print(f"Shape: {df.shape}")
        print("\nColumns:")
        for col in df.columns:
            print(f"- {col}")
            
        print("\nFirst 3 rows:")
        print(df.head(3).to_markdown(index=False))
        
        # Check for potential grouping columns
        print("\nRows with data in column 4 (Potential Category):")
        # Get the column name for index 4
        col4 = df.columns[4]
        # Filter rows where col4 is not null
        relevant_rows = df[df[col4].notna()]
        print(relevant_rows.to_markdown(index=True))

    except Exception as e:
        print(f"Error reading Excel file: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python analyze_excel.py <file_path>")
        sys.exit(1)
    
    analyze_excel(sys.argv[1])
