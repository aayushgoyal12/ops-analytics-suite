import streamlit as st
import pandas as pd
import json
import io
import time
from google import genai
from google.genai import types

# Initialize Gemini Client
api_key = st.secrets["GEMINI_API_KEY"]
ai_client = genai.Client(api_key=api_key)

# --- Multi-File Uploader ---
uploaded_files = st.file_uploader(
    "Upload multiple Invoices/Receipts (PDF, PNG, JPG)",
    type=["pdf", "png", "jpg", "jpeg"],
    accept_multiple_files=True
)

if uploaded_files:
    num_files = len(uploaded_files)
    st.info(f"Selected {num_files} document(s). Total credits required: {num_files}")
    
    if st.button("🚀 Process All Documents"):
        # Safely fetch user credits integer
        try:
            available_credits = int(st.session_state.get("credits", 10))
        except Exception:
            available_credits = 10

        if available_credits < num_files:
            st.error(f"Insufficient credits! You need {num_files} credits, but only have {available_credits} left.")
        else:
            extracted_records = []
            progress_bar = st.progress(0)
            status_text = st.empty()

            for idx, uploaded_file in enumerate(uploaded_files):
                status_text.text(f"Processing {uploaded_file.name} ({idx+1}/{num_files})...")
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

                # Retry logic for 503 errors
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

            # Credit deduction logic
            if extracted_records:
                new_credit_balance = available_credits - len(extracted_records)
                
                # Update Supabase
                try:
                    user_id = st.session_state.get("user_id")
                    if user_id:
                        supabase.table("user_credits").update(
                            {"credits_remaining": new_credit_balance}
                        ).eq("user_id", user_id).execute()
                    st.session_state["credits"] = new_credit_balance
                except Exception as e:
                    st.warning(f"Credits updated locally. Supabase note: {e}")

                st.success(f"Processing Complete! Deducted {len(extracted_records)} credits.")

                # Summary Table & Export
                df = pd.DataFrame(extracted_records)
                cols = ["file_name", "vendor_name", "date", "gstin", "taxable_value", "tax_amount", "total_amount"]
                df = df[[c for c in cols if c in df.columns]]
                
                st.subheader("📊 Master Extracted Summary")
                st.dataframe(df)

                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Master_Invoices')
                
                st.download_button(
                    label="📥 Download Master Excel Report",
                    data=buffer.getvalue(),
                    file_name="Master_Invoice_Summary.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )