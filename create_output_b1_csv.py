"""
Create CSV from Output B1 Sheet with Proper Encoding
"""

import pandas as pd
import sys
import io

# Fix encoding for Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def create_csv_from_output_b1():
    """Create CSV from Output B1 sheet"""
    
    input_file = r'D:\Projects\03.FI_crawldata\01_Data_raw\Copy of Chat room FX text 1 ngay.xlsx'
    output_file = r'D:\Projects\03.FI_crawldata\03_Task_Extract_ChatRoom\ground_truth.csv'
    
    try:
        # Read Output B1 sheet
        df = pd.read_excel(input_file, sheet_name="Output B1")
        
        print(f"Loaded Output B1 sheet:")
        print(f"Rows: {len(df)}")
        print(f"Columns: {list(df.columns)}")
        
        # Clean data
        df_clean = df.dropna(how='all')
        
        # Save to CSV
        df_clean.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f"SUCCESS: Created {output_file}")
        print(f"Records: {len(df_clean)}")
        
        # Read back and show structure
        df_verify = pd.read_csv(output_file, encoding='utf-8-sig')
        print(f"\\nVerified CSV structure:")
        for i, col in enumerate(df_verify.columns):
            print(f"{i+1}. {col}")
        
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    create_csv_from_output_b1()