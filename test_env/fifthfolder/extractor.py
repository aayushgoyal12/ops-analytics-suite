import streamlit as st
import google.genai as genai
from google.genai import types
import pandas as pd
import json
from PIL import Image

st.set_page_config(page_title="AI Document Parser", layout="centered")
st.title("📄 Bulk PDF/Invoice Data Extractor")
st.caption("Upload multiple invoices (PDF/Images) to extract clean structured Excel data")

api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")

# Multi-file upload enabled
uploaded_files = st.file_uploader("Upload Invoice Images/PDFs", type=["png", "jpg", "jpeg", "pdf"], accept_multiple_files=True)

if uploaded_files and api_key:
    st.write(f"📁 **Total files selected:** {len(uploaded_files)}")

    if st.button("Extract Data for All Files"):
        client = genai.Client(api_key=api_key)
        all_extracted_data = []
        
        progress_bar = st.progress(0)
        status_text = st.empty()

        for idx, file in enumerate(uploaded_files):
            status_text.text(f"Processing ({idx+1}/{len(uploaded_files)}): {file.name}...")
            
            try:
                is_pdf = file.name.endswith(".pdf")
                if is_pdf:
                    file_bytes = file.read()
                    mime_type = "application/pdf"
                    content_part = types.Part.from_bytes(data=file_bytes, mime_type=mime_type)
                else:
                    image = Image.open(file)
                    content_part = image

                prompt = """
                Extract details from this invoice:
                - Vendor Name
                - Invoice Number
                - Invoice Date
                - Total Amount
                - Tax Amount
                Return strictly as a JSON object.
                """

                response = client.models.generate_content(
                    model='gemini-3.6-flash',
                    contents=[content_part, prompt],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json"
                    )
                )

                data = json.loads(response.text)
                data['File Name'] = file.name
                all_extracted_data.append(data)

            except Exception as e:
                st.error(f"Error in {file.name}: {str(e)}")

            progress_bar.progress((idx + 1) / len(uploaded_files))

        if all_extracted_data:
            df = pd.DataFrame(all_extracted_data)
            
            # Reorder columns to show File Name first
            cols = ['File Name'] + [col for col in df.columns if col != 'File Name']
            df = df[cols]

            st.success("All Files Processed Successfully!")
            st.dataframe(df)

            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Consolidated CSV", csv, "bulk_invoices.csv", "text/csv")

elif not api_key:
    st.info("Please enter your Gemini API Key in the sidebar to proceed.")