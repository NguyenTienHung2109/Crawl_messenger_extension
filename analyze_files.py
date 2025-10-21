import pandas as pd
from docx import Document
import sys
import io

# Set UTF-8 encoding for output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def analyze_excel_files():
    print('=== ANALYZING EXCEL FILES ===')
    
    # Read main output file
    try:
        df1 = pd.read_excel(r'D:\Projects\03.FI_crawldata\01_Data_raw\Copy of Chat room FX text 1 ngay.xlsx')
        print('Copy of Chat room FX text 1 ngay.xlsx (OUTPUT SAMPLE):')
        print(f'Shape: {df1.shape}')
        print(f'Columns: {list(df1.columns)}')
        print('Sample data:')
        for i, row in df1.head().iterrows():
            print(f"Row {i}: {dict(row)}")
        print('\n')
    except Exception as e:
        print(f'Error reading output file: {e}')
    
    # Read input file
    try:
        df2 = pd.read_excel(r'D:\Projects\03.FI_crawldata\01_Data_raw\test(2).xlsx')
        print('test(2).xlsx (INPUT):')
        print(f'Shape: {df2.shape}')
        print(f'Columns: {list(df2.columns)}')
        print('Sample data:')
        for i, row in df2.head().iterrows():
            print(f"Row {i}: {dict(row)}")
        print('\n')
    except Exception as e:
        print(f'Error reading input file: {e}')

def analyze_rule_document():
    print('=== ANALYZING RULE DOCUMENT ===')
    try:
        doc = Document(r'D:\Projects\03.FI_crawldata\01_Data_raw\Rule-FX-Message.docx')
        print('Rule-FX-Message.docx content:')
        for i, para in enumerate(doc.paragraphs):
            if para.text.strip():
                print(f'{i+1}. {para.text}')
        print('\n')
    except Exception as e:
        print(f'Error reading rule document: {e}')

if __name__ == "__main__":
    analyze_excel_files()
    analyze_rule_document()