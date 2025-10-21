"""
Lấy danh sách ngân hàng từ Ground Truth và tạo input mới
Chỉ sử dụng bank names có trong ground truth
"""

import pandas as pd

def get_banks_from_ground_truth():
    """Lấy tất cả bank names từ ground truth"""
    
    # Load ground truth
    gt_file = r'D:\Projects\03.FI_crawldata\03_Task_Extract_ChatRoom\ground_truth.csv'
    gt_df = pd.read_csv(gt_file, encoding='utf-8-sig')
    
    print("DANH SACH NGAN HANG TU GROUND TRUTH:")
    print("=" * 40)
    print(f"Ground truth columns: {list(gt_df.columns)}")
    print(f"Total deals: {len(gt_df)}")
    
    # Lấy tên ngân hàng từ Buy side và Sell side
    all_banks = set()
    
    if 'Buy side' in gt_df.columns:
        buy_banks = gt_df['Buy side'].dropna().unique()
        all_banks.update(buy_banks)
        print(f"\nBuy side banks: {list(buy_banks)}")
    
    if 'Sell side' in gt_df.columns:
        sell_banks = gt_df['Sell side'].dropna().unique()
        all_banks.update(sell_banks)
        print(f"Sell side banks: {list(sell_banks)}")
    
    # Loại bỏ NaN và empty
    valid_banks = [bank for bank in all_banks if pd.notna(bank) and str(bank).strip()]
    
    print(f"\nTAT CA NGAN HANG TRONG GROUND TRUTH:")
    for i, bank in enumerate(sorted(valid_banks), 1):
        print(f"{i:2d}. {bank}")
    
    return sorted(valid_banks)

def map_email_to_ground_truth_banks(email, valid_banks):
    """Map email thành bank name chỉ từ danh sách ground truth"""
    
    if pd.isna(email) or not isinstance(email, str):
        return None
    
    email_lower = email.lower()
    
    # Mapping cụ thể cho từng bank trong ground truth
    email_mappings = {
        # VIB variations
        'vib': 'VIB',
        
        # VPBank variations  
        'vpbank': 'VPBank',
        
        # VCB/Vietcombank variations
        'vcb': 'VCB',
        'vietcombank': 'VCB',
        
        # ACB variations
        'acb': 'ACB',
        
        # Techcombank variations
        'techcombank': 'TCB',
        'tcb': 'TCB',
        
        # BIDV variations
        'bidv': 'BIDV',
        
        # MBBank variations
        'mb': 'MBBank',
        'mbbank': 'MBBank',
        
        # Other banks
        'baca': 'BacABank',
        'bacabank': 'BacABank',
        'hdbank': 'HDBank',
        'tpbank': 'TPBank',
        'shb': 'SHB',
        'scb': 'SCB',
        'ocb': 'OCB',
        'msb': 'MSB',
        'eximbank': 'Eximbank',
        'vietinbank': 'VietinBank',
        'agribank': 'Agribank'
    }
    
    # Chỉ map nếu bank có trong ground truth
    for email_part, bank_name in email_mappings.items():
        if email_part in email_lower and bank_name in valid_banks:
            return bank_name
    
    # Nếu không tìm thấy match trong ground truth, return None
    return None

def create_filtered_input_with_banks():
    """Tạo input file mới chỉ với banks từ ground truth"""
    
    # Lấy danh sách banks từ ground truth
    valid_banks = get_banks_from_ground_truth()
    
    # Load input data gốc
    input_file = r'D:\Projects\03.FI_crawldata\03_Task_Extract_ChatRoom\input_data.csv'
    df = pd.read_csv(input_file, encoding='utf-8-sig')
    
    print(f"\nXU LY INPUT DATA:")
    print(f"Original data: {len(df)} messages")
    
    # Map emails thành bank names (chỉ từ ground truth)
    df['bank_name'] = df['trader'].apply(lambda x: map_email_to_ground_truth_banks(x, valid_banks))
    
    # Lọc chỉ những messages có bank trong ground truth
    df_filtered = df[df['bank_name'].notna()].copy()
    
    print(f"Filtered data: {len(df_filtered)} messages (chi co banks trong ground truth)")
    
    # Thống kê banks
    bank_counts = df_filtered['bank_name'].value_counts()
    print(f"\nDANH SACH BANKS SAU FILTER:")
    for bank, count in bank_counts.items():
        print(f"- {bank}: {count} messages")
    
    # Lưu file mới
    output_file = r'D:\Projects\03.FI_crawldata\03_Task_Extract_ChatRoom\input_filtered_banks.csv'
    df_filtered.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    print(f"\nFile moi da tao: {output_file}")
    print(f"Columns: {list(df_filtered.columns)}")
    print(f"Chi chua banks co trong ground truth: {sorted(df_filtered['bank_name'].unique())}")
    
    return df_filtered, valid_banks

def main():
    """Main function"""
    print("LAY BANK NAMES TU GROUND TRUTH VA TAO INPUT MOI")
    print("=" * 55)
    
    df_filtered, valid_banks = create_filtered_input_with_banks()
    
    print(f"\nKET QUA:")
    print(f"- Banks trong ground truth: {len(valid_banks)}")
    print(f"- Messages sau filter: {len(df_filtered)}")
    print(f"- Chi su dung banks: {valid_banks}")
    print(f"\nFile input moi: input_filtered_banks.csv")

if __name__ == "__main__":
    main()