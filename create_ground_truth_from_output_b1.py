"""
Create Ground Truth CSV from Sheet "Output B1"
Extract data from specific sheet in the Excel file
"""

import pandas as pd
import os

def create_ground_truth_from_output_b1():
    """Create ground truth CSV from Output B1 sheet"""
    
    # Input and output paths
    input_file = r'D:\Projects\03.FI_crawldata\01_Data_raw\Copy of Chat room FX text 1 ngay.xlsx'
    output_file = r'D:\Projects\03.FI_crawldata\03_Task_Extract_ChatRoom\ground_truth.csv'
    
    print("Creating ground truth CSV from Output B1 sheet...")
    print(f"Source: {input_file}")
    print(f"Target: {output_file}")
    
    try:
        # First, check available sheets
        excel_file = pd.ExcelFile(input_file)
        print(f"\nAvailable sheets: {excel_file.sheet_names}")
        
        # Try to read "Output B1" sheet
        if "Output B1" in excel_file.sheet_names:
            df = pd.read_excel(input_file, sheet_name="Output B1")
            print(f"Successfully loaded 'Output B1' sheet")
        else:
            # Try variations of the sheet name
            possible_names = ["Output B1", "OutputB1", "Output_B1", "Sheet2", "B1"]
            sheet_found = False
            
            for sheet_name in possible_names:
                if sheet_name in excel_file.sheet_names:
                    df = pd.read_excel(input_file, sheet_name=sheet_name)
                    print(f"Found and loaded sheet: '{sheet_name}'")
                    sheet_found = True
                    break
            
            if not sheet_found:
                print(f"Could not find 'Output B1' sheet. Available sheets: {excel_file.sheet_names}")
                # Load the second sheet if exists
                if len(excel_file.sheet_names) > 1:
                    df = pd.read_excel(input_file, sheet_name=excel_file.sheet_names[1])
                    print(f"Using sheet: '{excel_file.sheet_names[1]}'")
                else:
                    return None
        
        print(f"\nLoaded data from Output B1:")
        print(f"- Rows: {len(df):,}")
        print(f"- Columns: {list(df.columns)}")
        
        # Display sample data
        print(f"\nSample data structure:")
        print(df.head())
        
        # Clean and prepare data
        df_clean = df.copy()
        
        # Remove completely empty rows
        df_clean = df_clean.dropna(how='all')
        
        # Save to CSV with UTF-8 encoding
        df_clean.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f"\nGround truth CSV created successfully!")
        print(f"- Final rows: {len(df_clean):,}")
        print(f"- File size: {os.path.getsize(output_file) / 1024:.2f} KB")
        print(f"- Saved to: {output_file}")
        
        # Show data types and structure
        print(f"\nData types:")
        for col in df_clean.columns:
            print(f"- {col}: {df_clean[col].dtype}")
        
        return df_clean
        
    except Exception as e:
        print(f"Error creating ground truth from Output B1: {e}")
        return None

def verify_output_b1_csv():
    """Verify the created CSV from Output B1"""
    
    csv_file = r'D:\Projects\03.FI_crawldata\03_Task_Extract_ChatRoom\ground_truth.csv'
    
    try:
        # Read back the CSV
        df_csv = pd.read_csv(csv_file, encoding='utf-8-sig')
        
        print(f"\nCSV Verification:")
        print(f"- Rows in CSV: {len(df_csv):,}")
        print(f"- Columns: {list(df_csv.columns)}")
        
        # Show sample of actual data
        print(f"\nFirst 10 rows of ground truth:")
        for idx, row in df_csv.head(10).iterrows():
            print(f"{idx+1:2d}. {dict(row)}")
        
        return True
        
    except Exception as e:
        print(f"Error verifying CSV: {e}")
        return False

def main():
    """Main function"""
    print("GROUND TRUTH CSV FROM OUTPUT B1 SHEET")
    print("=" * 45)
    
    # Create CSV from Output B1 sheet
    df = create_ground_truth_from_output_b1()
    
    if df is not None:
        # Verify CSV
        verify_output_b1_csv()
        
        print(f"\nSUCCESS: Ground truth CSV created from Output B1 sheet")
        print(f"Ready for extraction analysis")
    else:
        print(f"FAILED: Could not create ground truth CSV from Output B1")

if __name__ == "__main__":
    main()