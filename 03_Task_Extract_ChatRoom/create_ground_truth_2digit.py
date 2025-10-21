"""
Create new ground truth với chỉ 2 số cuối cho Price column
Dựa trên current market rate 25,398
"""

import pandas as pd

def convert_actual_to_2digit_price(actual_price, current_rate=25398):
    """Convert actual price về 2 số cuối"""
    if pd.isna(actual_price):
        return None
    
    actual = int(actual_price)
    
    # Lấy 2 số cuối
    last_2_digits = actual % 100
    
    return last_2_digits

def create_2digit_ground_truth():
    """Tạo ground truth mới với chỉ 2 số cuối"""
    
    # Load original ground truth
    gt_file = r'D:\Projects\03.FI_crawldata\03_Task_Extract_ChatRoom\ground_truth.csv'
    df = pd.read_csv(gt_file, encoding='utf-8-sig')
    
    print("CREATE NEW GROUND TRUTH - CHI 2 SO CUOI")
    print("=" * 45)
    print(f"Original GT deals: {len(df)}")
    
    # Create new column Actual_price_2digit
    df['Actual_price_2digit'] = df['Actual price'].apply(convert_actual_to_2digit_price)
    
    print(f"Added Actual_price_2digit column")
    print(f"2-digit range: {df['Actual_price_2digit'].min()} - {df['Actual_price_2digit'].max()}")
    
    # Show sample conversions
    print(f"\nSAMPLE CONVERSIONS:")
    print("Actual Price -> Actual_price_2digit")
    for i in range(10):
        actual = int(df.iloc[i]['Actual price'])
        two_digit = int(df.iloc[i]['Actual_price_2digit'])
        print(f"{actual:,} -> {two_digit:02d}")
    
    # Rename columns to remove spaces
    df.rename(columns={
        'Buy side': 'Buy_side',
        'Sell side': 'Sell_side', 
        'Actual price': 'Actual_price'
    }, inplace=True)
    
    # Keep all columns including new one
    columns_to_keep = ['STT', 'Buy_side', 'Amount', 'Price', 'Sell_side', 'Actual_price', 'Actual_price_2digit']
    df_clean = df[columns_to_keep].copy()
    
    # Save new ground truth
    output_file = r'D:\Projects\03.FI_crawldata\03_Task_Extract_ChatRoom\ground_truth_2digit.csv'
    df_clean.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    print(f"\nNew ground truth saved: {output_file}")
    print(f"Format: Same as original nhung Price chi co 2 so cuoi")
    
    # Show sample của new GT
    print(f"\nSAMPLE NEW GROUND TRUTH:")
    print(df_clean.head().to_string(index=False))
    
    return df

def main():
    """Main function"""
    print("GROUND TRUTH CONVERSION - 2 DIGIT PRICES")
    print("Current market rate: 25,398")
    print("Rule: Price column chi chua 2 so cuoi cua Actual price")
    print()
    
    create_2digit_ground_truth()

if __name__ == "__main__":
    main()