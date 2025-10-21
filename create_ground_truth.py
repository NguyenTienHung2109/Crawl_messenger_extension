"""
Create Ground Truth CSV from Excel File
Convert the original chat room data to CSV format
"""

import pandas as pd
import os

def create_ground_truth_csv():
    """Convert Excel file to CSV ground truth"""
    
    # Input and output paths
    input_file = r'D:\Projects\03.FI_crawldata\01_Data_raw\Copy of Chat room FX text 1 ngay.xlsx'
    output_file = r'D:\Projects\03.FI_crawldata\03_Task_Extract_ChatRoom\ground_truth.csv'
    
    print("Creating ground truth CSV...")
    print(f"Source: {input_file}")
    print(f"Target: {output_file}")
    
    try:
        # Read Excel file
        df = pd.read_excel(input_file)
        
        print(f"\nLoaded data:")
        print(f"- Rows: {len(df):,}")
        print(f"- Columns: {list(df.columns)}")
        print(f"- Date range: {df['time'].min()} to {df['time'].max()}")
        print(f"- Unique traders: {df['trader'].nunique()}")
        
        # Clean data
        df_clean = df.copy()
        
        # Remove any completely empty rows
        df_clean = df_clean.dropna(how='all')
        
        # Ensure proper data types
        df_clean['time'] = df_clean['time'].astype(str)
        df_clean['trader_name'] = df_clean['trader_name'].astype(str)
        df_clean['trader'] = df_clean['trader'].astype(str)
        df_clean['mess'] = df_clean['mess'].fillna('').astype(str)
        
        # Save to CSV with UTF-8 encoding
        df_clean.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        print(f"\nGround truth CSV created successfully!")
        print(f"- Final rows: {len(df_clean):,}")
        print(f"- File size: {os.path.getsize(output_file) / 1024 / 1024:.2f} MB")
        print(f"- Saved to: {output_file}")
        
        # Show sample data
        print(f"\nSample data (first 5 rows):")
        for idx, row in df_clean.head().iterrows():
            print(f"{idx+1}. [{row['time']}] {row['trader_name']}: {row['mess'][:50]}...")
        
        return df_clean
        
    except Exception as e:
        print(f"Error creating ground truth: {e}")
        return None

def verify_csv_file():
    """Verify the created CSV file"""
    
    csv_file = r'D:\Projects\03.FI_crawldata\03_Task_Extract_ChatRoom\ground_truth.csv'
    
    try:
        # Read back the CSV
        df_csv = pd.read_csv(csv_file, encoding='utf-8-sig')
        
        print(f"\nCSV Verification:")
        print(f"- Rows in CSV: {len(df_csv):,}")
        print(f"- Columns: {list(df_csv.columns)}")
        print(f"- No missing critical data: {df_csv[['time', 'trader', 'mess']].notna().all().all()}")
        
        # Check for trading messages
        trading_messages = 0
        for idx, row in df_csv.iterrows():
            message = str(row['mess'])
            if any(word in message.lower() for word in ['bid', 'ask', 'offer', 'buy', 'sell', 'done']):
                trading_messages += 1
        
        print(f"- Trading messages found: {trading_messages:,} ({trading_messages/len(df_csv)*100:.1f}%)")
        
        return True
        
    except Exception as e:
        print(f"Error verifying CSV: {e}")
        return False

def main():
    """Main function"""
    print("GROUND TRUTH CSV CREATION")
    print("=" * 40)
    
    # Create CSV
    df = create_ground_truth_csv()
    
    if df is not None:
        # Verify CSV
        verify_csv_file()
        
        print(f"\nSUCCESS: Ground truth CSV ready for analysis")
        print(f"Use this file as input for all extraction solutions")
    else:
        print(f"FAILED: Could not create ground truth CSV")

if __name__ == "__main__":
    main()