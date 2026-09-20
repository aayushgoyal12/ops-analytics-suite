import streamlit as st
import pandas as pd
import json
import io
import time
from google import genai
from google.genai import types

# 1. Page Config (Wide layout for clean UI)
st.set_page_config(
    page_title="Ops Analytics Suite | AI Invoice Batch Processor",
    page_icon="🧾",
    layout="wide"
)

# 2. Initialize Gemini Client safely
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    ai_client = genai.Client(api_key=api_key)
except Exception as e:
    st.error(f"API Key error: {e}")

# 3. Session State Setup for Credits
if "credits" not in st.session_state:
    st.session_state["credits"] = 100  # Default credits balance

# 4. Sidebar Layout
with st.sidebar:
    st.title("⚡ Ops Analytics")
    st.caption("AI-Powered Document Processing")
    st.divider()
    
    st.subheader("💳 Credit Balance")
    st.metric(label="Available Credits", value=st.session_state["credits"])
    st.info("1 Credit = 1 Document Extracted")
    
    st.divider()
    st.markdown("### 🎯 SaaS Features")
    st.markdown("- Multi-PDF Batch Processing\n- Auto-Merge Master Excel Export\n- Tally & Zoho Ready Format")

# 5. Main Dashboard Header
st.title("🧾 Master Invoice Batch Extractor")
st.write("Upload multiple invoices or receipts at once to auto-extract details into a single consolidated Master Excel report.")

st.divider()

# 6. Multi-File Uploader Block
uploaded_files = st.file_uploader(
    "Upload multiple Invoices/Receipts (PDF, PNG, JPG)",
    type=["pdf", "png", "jpg", "jpeg"],
    accept_multiple_files=True
)

if uploaded_files:
    num_files = len(uploaded_files)
    st.info(f"📁 Selected **{num_files} document(s)**. Total credits required: **{num_files}**")
    
    if st.button("🚀 Process All Documents", type="primary"):
        available_credits = st.session_state["credits"]

        if available_credits < num_files:
            st.error(f"Insufficient credits! You need {num_files} credits, but only have {available_credits} left.")
        else:
            extracted_records = []
            progress_bar = st.progress(0)
            status_text = st.empty()

            for idx, uploaded_file in enumerate(uploaded_files):
                status_text.text(f"Processing ({idx+1}/{num_files}): {uploaded_file.name}...")
                bytes_data = uploaded_file.read()
                mime_type = uploaded_file.type

                file_part = types.Part.from_bytes(
                    data=bytes_data,
                    mime_type=mime_type,
                )

                prompt = """
                Extract invoice details into raw JSON:
                - "vendor_name": Merchant/Company name
                - "date": Invoice date (YYYY-MM-DD)
                - "gstin": GST number if available
                - "taxable_value": Total value before tax
                - "tax_amount": Tax/GST amount
                - "total_amount": Final total amount
                Return ONLY raw JSON, no markdown formatting.
                """

                # Retry logic for temporary API overloads
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        response = ai_client.models.generate_content(
                            model="gemini-3.6-flash",
                            contents=[file_part, prompt]
                        )
                        clean_text = response.text.replace("```json", "").replace("```", "").strip()
                        data = json.loads(clean_text)
                        data["file_name"] = uploaded_file.name
                        extracted_records.append(data)
                        break
                    except Exception as e:
                        if attempt < max_retries - 1:
                            time.sleep(2)
                        else:
                            st.warning(f"Failed to extract {uploaded_file.name}: {e}")

                progress_bar.progress((idx + 1) / num_files)
                time.sleep(1)

            # Deduct Credits
            if extracted_records:
                st.session_state["credits"] -= len(extracted_records)
                st.success(f"✅ Processing Complete! Successfully extracted {len(extracted_records)} invoices.")

                # Master Data Table & Download
                df = pd.DataFrame(extracted_records)
                cols = ["file_name", "vendor_name", "date", "gstin", "taxable_value", "tax_amount", "total_amount"]
                df = df[[c for c in cols if c in df.columns]]
                
                st.subheader("📊 Master Summary Table")
                st.dataframe(df, use_container_width=True)

                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Master_Invoices')
                
                st.download_button(
                    label="📥 Download Master Excel Report",
                    data=buffer.getvalue(),
                    file_name="Master_Invoice_Summary.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary"
                )