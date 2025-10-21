"""
Create Input CSV from Data Sheet in test(2).xlsx
Extract the input chat room data from the Data sheet
"""

import pandas as pd
import sys
import io

# Fix encoding for Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def create_input_from_data_sheet():
    """Create input CSV from Data sheet in test(2).xlsx"""
    
    input_file = r'D:\Projects\03.FI_crawldata\01_Data_raw\test(2).xlsx'
    output_file = r'D:\Projects\03.FI_crawldata\03_Task_Extract_ChatRoom\input_data.csv'
    
    try:
        # Check available sheets
        excel_file = pd.ExcelFile(input_file)
        print(f"Available sheets in test(2).xlsx: {excel_file.sheet_names}")
        
        # Read Data sheet
        if "Data" in excel_file.sheet_names:
            df = pd.read_excel(input_file, sheet_name="Data")
            print(f"Successfully loaded 'Data' sheet")
        else:
            print(f"'Data' sheet not found. Trying first sheet...")
            df = pd.read_excel(input_file, sheet_name=0)
        
        print(f"\nLoaded Data sheet:")
        print(f"- Rows: {len(df):,}")
        print(f"- Columns: {list(df.columns)}")
        
        # Show structure
        print(f"\nData structure:")
        print(df.head(10))
        
        # Clean data - remove empty rows
        df_clean = df.dropna(how='all')
        
        # Remove rows where all values are NaN except potentially the first column
        mask = df_clean.iloc[:, 1:].notna().any(axis=1)
        df_clean = df_clean[mask]
        
        print(f"\nAfter cleaning:")
        print(f"- Rows: {len(df_clean):,}")
        print(df_clean.head(10))
        
        # Save to CSV
        df_clean.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f"\nInput data CSV created successfully!")
        print(f"- File: {output_file}")
        print(f"- Records: {len(df_clean):,}")
        
        return df_clean
        
    except Exception as e:
        print(f"Error creating input from Data sheet: {e}")
        return None

def analyze_input_structure():
    """Analyze the structure of input data"""
    
    csv_file = r'D:\Projects\03.FI_crawldata\03_Task_Extract_ChatRoom\input_data.csv'
    
    try:
        df = pd.read_csv(csv_file, encoding='utf-8-sig')
        
        print(f"\nINPUT DATA ANALYSIS:")
        print(f"- Total rows: {len(df):,}")
        print(f"- Columns: {list(df.columns)}")
        
        # Check for chat room data structure
        for col in df.columns:
            non_null_count = df[col].notna().sum()
            print(f"- {col}: {non_null_count} non-null values")
            
            # Show sample values
            sample_values = df[col].dropna().head(3).tolist()
            print(f"  Sample: {sample_values}")
        
        return df
        
    except Exception as e:
        print(f"Error analyzing input structure: {e}")
        return None

def main():
    """Main function"""
    print("CREATE INPUT DATA FROM DATA SHEET")
    print("=" * 40)
    
    # Create CSV from Data sheet
    df = create_input_from_data_sheet()
    
    if df is not None:
        # Analyze structure
        analyze_input_structure()
        
        print(f"\nSUCCESS: Input data CSV ready")
        print(f"This represents the raw chat room messages to be processed")
    else:
        print(f"FAILED: Could not create input data CSV")

if __name__ == "__main__":
    main()