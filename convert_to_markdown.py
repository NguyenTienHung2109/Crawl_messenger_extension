import pandas as pd
from docx import Document
import sys
import io

def convert_excel_to_markdown(file_path, output_path):
    """Convert Excel file to Markdown format"""
    try:
        df = pd.read_excel(file_path)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            filename = file_path.split('\\')[-1]
            f.write(f"# Excel File Analysis: {filename}\n\n")
            f.write(f"**File:** `{file_path}`\n")
            f.write(f"**Shape:** {df.shape[0]} rows × {df.shape[1]} columns\n\n")
            
            f.write("## Columns\n")
            for i, col in enumerate(df.columns):
                f.write(f"- {i+1}. `{col}`\n")
            f.write("\n")
            
            f.write("## Sample Data (First 10 rows)\n\n")
            f.write(df.head(10).to_markdown(index=False))
            f.write("\n\n")
            
            f.write("## Data Types\n")
            for col, dtype in df.dtypes.items():
                f.write(f"- `{col}`: {dtype}\n")
            f.write("\n")
            
            f.write("## Summary Statistics\n")
            if len(df.select_dtypes(include=['number']).columns) > 0:
                f.write(df.describe().to_markdown())
            else:
                f.write("No numeric columns found for statistical summary.\n")
        
        print(f"SUCCESS: Converted {file_path} to {output_path}")
        
    except Exception as e:
        print(f"ERROR converting {file_path}: {e}")

def convert_docx_to_markdown(file_path, output_path):
    """Convert Word document to Markdown format"""
    try:
        doc = Document(file_path)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            filename = file_path.split('\\')[-1]
            f.write(f"# Document Analysis: {filename}\n\n")
            f.write(f"**Source File:** `{file_path}`\n\n")
            
            for i, para in enumerate(doc.paragraphs):
                if para.text.strip():
                    text = para.text.strip()
                    if i == 0 or text.startswith(('Rule', 'Quy trình', 'Các câu lệnh')):
                        f.write(f"## {text}\n\n")
                    else:
                        f.write(f"- {text}\n")
            f.write("\n")
        
        print(f"SUCCESS: Converted {file_path} to {output_path}")
        
    except Exception as e:
        print(f"ERROR converting {file_path}: {e}")

def main():
    # Define file paths
    files_to_convert = [
        {
            'input': r'D:\Projects\03.FI_crawldata\01_Data_raw\Copy of Chat room FX text 1 ngay.xlsx',
            'output': r'D:\Projects\03.FI_crawldata\01_Data_raw\output_sample_analysis.md',
            'type': 'excel'
        },
        {
            'input': r'D:\Projects\03.FI_crawldata\01_Data_raw\test(2).xlsx',
            'output': r'D:\Projects\03.FI_crawldata\01_Data_raw\input_analysis.md',
            'type': 'excel'
        },
        {
            'input': r'D:\Projects\03.FI_crawldata\01_Data_raw\Rule-FX-Message.docx',
            'output': r'D:\Projects\03.FI_crawldata\01_Data_raw\rules_analysis.md',
            'type': 'docx'
        }
    ]
    
    print("Converting files to Markdown format...\n")
    
    for file_info in files_to_convert:
        if file_info['type'] == 'excel':
            convert_excel_to_markdown(file_info['input'], file_info['output'])
        elif file_info['type'] == 'docx':
            convert_docx_to_markdown(file_info['input'], file_info['output'])
    
    print("\nConversion completed!")

if __name__ == "__main__":
    main()