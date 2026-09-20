import streamlit as st
from supabase import create_client, Client
import razorpay
import streamlit.components.v1 as components
import json
import pandas as pd
from io import BytesIO
from google import genai
from google import genai
from google.genai import types

# --- Secrets Initialization ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
RAZORPAY_KEY_ID = st.secrets["RAZORPAY_KEY_ID"]
RAZORPAY_KEY_SECRET = st.secrets["RAZORPAY_KEY_SECRET"]
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
rzp_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
ai_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# --- Session Management ---
if "user" not in st.session_state:
    st.session_state.user = None

st.sidebar.title("🔐 Account & Credits")

# --- LOGGED IN VIEW ---
if st.session_state.user:
    user_id = st.session_state.user.id
    user_email = st.session_state.user.email
    st.sidebar.write(f"Logged in: **{user_email}**")

    # Fetch Current Credits
    credit_data = supabase.table("user_credits").select("credits_remaining").eq("user_id", user_id).execute()
    
    if not credit_data.data:
        try:
            supabase.table("user_credits").upsert({"user_id": user_id, "credits_remaining": 0}).execute()
            credits = 0
        except Exception:
            credits = 0
    else:
        credits = credit_data.data[0]["credits_remaining"]

    st.sidebar.metric(label="Available Credits", value=f"⚡ {credits}")
    st.sidebar.divider()

    # Credit Top-Up Options
    st.sidebar.subheader("💳 Top-Up Credits")
    pack = st.sidebar.radio("Select Pack:", ["50 Credits — ₹249", "100 Credits — ₹499"])
    
    amount_map = {
        "50 Credits — ₹249": (24900, 50),
        "100 Credits — ₹499": (49900, 100)
    }
    amount_in_paise, added_credits = amount_map[pack]

    if st.sidebar.button("Pay with Razorpay"):
        order = rzp_client.order.create({
            "amount": amount_in_paise,
            "currency": "INR",
            "payment_capture": 1
        })

        razorpay_html = f"""
        <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
        <script>
        var options = {{
            "key": "{RAZORPAY_KEY_ID}",
            "amount": "{amount_in_paise}",
            "currency": "INR",
            "name": "Ops Analytics Suite",
            "description": "{added_credits} Extra Credits",
            "order_id": "{order['id']}",
            "prefill": {{ "email": "{user_email}" }},
            "handler": function (response){{
                alert("Payment Successful! Click '+ Add Credits' below.");
            }},
            "theme": {{ "color": "#2563EB" }}
        }};
        var rzp1 = new Razorpay(options);
        rzp1.open();
        </script>
        """
        components.html(razorpay_html, height=0)

    if st.sidebar.button(f"+ Add {added_credits} Credits (After Payment)"):
        new_balance = credits + added_credits
        supabase.table("user_credits").update({"credits_remaining": new_balance}).eq("user_id", user_id).execute()
        st.sidebar.success(f"Successfully added {added_credits} credits!")
        st.rerun()

    if st.sidebar.button("Log Out"):
        st.session_state.user = None
        st.rerun()

    # --- MAIN DASHBOARD APP ---
    st.title("💼 AI Invoice & Receipt Extractor")
    st.write("Upload client invoices or receipts to automatically extract structured data to Excel.")

    st.subheader("📄 Document Upload")
    uploaded_file = st.file_uploader("Upload an invoice/receipt (PNG, JPG, JPEG, PDF)", type=["png", "jpg", "jpeg", "pdf"])

    if uploaded_file is not None:
        st.write(f"**Selected File:** {uploaded_file.name}")
        
        if st.button("🚀 Process & Extract Data"):
            if credits < 1:
                st.error("❌ Out of credits! Please top-up from the sidebar to continue.")
            elif not ai_client:
                st.error("❌ GEMINI_API_KEY is not configured in secrets!")
            else:
                with st.spinner("Analyzing document with AI..."):
                    try:
                        bytes_data = uploaded_file.getvalue()
                        mime_type = uploaded_file.type

                        prompt = """
                        Extract data from this invoice/receipt into a strict JSON object with these exact keys:
                        - "vendor_name": Name of seller/vendor
                        - "invoice_number": Invoice or receipt number
                        - "date": Invoice date (YYYY-MM-DD)
                        - "gstin": GST number if available
                        - "taxable_value": Total value before tax
                        - "tax_amount": Tax/GST amount
                        - "total_amount": Final total amount
                        Return ONLY raw JSON, no markdown formatting.
                        """
                        file_part = types.Part.from_bytes(
                            data=bytes_data,
                            mime_type=mime_type,
                        )

                        response = ai_client.models.generate_content(
                            model="gemini-3.6-flash",
                            contents=[file_part, prompt]
                        )  

                        clean_text = response.text.replace("```json", "").replace("```", "").strip()
                        extracted_json = json.loads(clean_text)

                        # Deduct 1 credit in Supabase
                        new_credit_balance = credits - 1
                        supabase.table("user_credits").update({"credits_remaining": new_credit_balance}).eq("user_id", user_id).execute()

                        st.success("✅ Extraction Complete!")
                        st.info(f"1 Credit deducted. Remaining credits: **⚡ {new_credit_balance}**")

                        # Display Data in Pandas Table
                        df = pd.DataFrame([extracted_json])
                        st.subheader("📊 Extracted Data Preview")
                        st.dataframe(df, use_container_width=True)

                        # Export to Excel Download Button
                        output = BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            df.to_excel(writer, index=False, sheet_name='Extracted Data')
                        excel_data = output.getvalue()

                        st.download_button(
                            label="📥 Download Excel Report",
                            data=excel_data,
                            file_name=f"Extracted_{uploaded_file.name}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )

                    except Exception as e:
                        st.error(f"Error processing file: {e}")

# --- NOT LOGGED IN ---
else:
    st.title("🔐 Welcome to Ops Analytics Suite")
    st.info("Please log in or sign up from the sidebar to access your workspace.")

    menu = st.sidebar.selectbox("Action", ["Login", "Sign Up"])
    email = st.sidebar.text_input("Email")
    password = st.sidebar.text_input("Password", type="password")

    if menu == "Sign Up":
        if st.sidebar.button("Create Account"):
            try:
                res = supabase.auth.sign_up({"email": email, "password": password})
                st.sidebar.success("Account created! You can now log in.")
            except Exception as e:
                st.sidebar.error(f"Sign up failed: {e}")

    elif menu == "Login":
        if st.sidebar.button("Log In"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.user = res.user
                st.rerun()
            except Exception as e:
                st.sidebar.error("Invalid email or password.")