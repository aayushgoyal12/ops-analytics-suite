import pdfplumber
import pandas as pd

def process_pdf_to_excel(pdf_path, output_excel):
    all_data = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            # 1. First try table extraction
            tables = page.extract_tables()
            if tables:
                for table in tables:
                    for row in table:
                        if any(row):
                            all_data.append(row)
            else:
                # 2. Fallback to line-by-line text parsing
                text = page.extract_text()
                if text:
                    for line in text.split('\n'):
                        parts = line.split()  # Space separated values
                        if parts:
                            all_data.append(parts)

    if not all_data:
        print("Error: PDF bilkul empty hai ya scanned image hai!")
        return

    # DataFrame creation
    df = pd.DataFrame(all_data)
    
    
   # Set first row as header cleanly
    cleaned_df = pd.DataFrame(df.values[1:], columns=df.iloc[0])

    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        cleaned_df.to_excel(writer, sheet_name='Extracted Data', index=False)
        
    print("Formatted Summary Excel Generated Successfully!")

if __name__ == "__main__":
    process_pdf_to_excel('second_folder/sample_test.pdf', 'Final_Summary_Report.xlsx')