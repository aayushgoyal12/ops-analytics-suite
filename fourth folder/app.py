import streamlit as st
from supabase import create_client, Client
import razorpay
import streamlit.components.v1 as components

# --- Secrets Initialization ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
RAZORPAY_KEY_ID = st.secrets["RAZORPAY_KEY_ID"]
RAZORPAY_KEY_SECRET = st.secrets["RAZORPAY_KEY_SECRET"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
rzp_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

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
        # Initialize 0 credits for new user
        supabase.table("user_credits").insert({"user_id": user_id, "credits_remaining": 0}).execute()
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
                alert("Payment Successful! You can now update your credits.");
            }},
            "theme": {{ "color": "#2563EB" }}
        }};
        var rzp1 = new Razorpay(options);
        rzp1.open();
        </script>
        """
        components.html(razorpay_html, height=0)

    # Manual Credit Add Button for Testing & Top-Up Simulation
    if st.sidebar.button(f"+ Add {added_credits} Credits (After Payment)"):
        new_balance = credits + added_credits
        supabase.table("user_credits").update({"credits_remaining": new_balance}).eq("user_id", user_id).execute()
        st.sidebar.success(f"Successfully added {added_credits} credits!")
        st.rerun()

    if st.sidebar.button("Log Out"):
        st.session_state.user = None
        st.rerun()

    # --- MAIN DASHBOARD APP ---
    st.title("💼 Accounting Client Document Hub")
    st.write("Upload client documents (invoices, receipts, sheets) for AI processing.")

    st.subheader("📄 Document Processor")
    uploaded_file = st.file_uploader("Upload an invoice or document (PDF / Images / Excel)", type=["pdf", "png", "jpg", "jpeg", "xlsx"])

    if uploaded_file is not None:
        st.write(f"**Selected File:** {uploaded_file.name}")
        
        if st.button("🚀 Process & Extract Data"):
            if credits < 1:
                st.error("❌ Out of credits! Please top-up from the sidebar to continue.")
            else:
                with st.spinner("Processing document..."):
                    # Deduct 1 credit in Supabase
                    new_credit_balance = credits - 1
                    supabase.table("user_credits").update({"credits_remaining": new_credit_balance}).eq("user_id", user_id).execute()
                    
                    # Process success response
                    st.success("✅ Document processed successfully!")
                    st.info(f"1 Credit deducted. Remaining credits: **⚡ {new_credit_balance}**")
                    
                    # Refresh app to update sidebar credit widget immediately
                    st.rerun()

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