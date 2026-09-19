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

# --- LOGGED IN USER VIEW ---
if st.session_state.user:
    user_id = st.session_state.user.id
    user_email = st.session_state.user.email
    st.sidebar.write(f"Logged in: **{user_email}**")

    # Fetch Credits
    credit_data = supabase.table("user_credits").select("credits_remaining").eq("user_id", user_id).execute()
    credits = credit_data.data[0]["credits_remaining"] if credit_data.data else 0

    st.sidebar.metric(label="Available Credits", value=f"⚡ {credits}")
    st.sidebar.divider()

    # Razorpay Checkout Options
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
            "theme": {{ "color": "#2563EB" }}
        }};
        var rzp1 = new Razorpay(options);
        rzp1.open();
        </script>
        """
        components.html(razorpay_html, height=0)

    if st.sidebar.button("Log Out"):
        st.session_state.user = None
        st.rerun()

    # --- MAIN DASHBOARD APP ---
    st.title("💼 Accounting Client Document Hub")
    st.write("Welcome to your Ops Analytics Dashboard!")

# --- NOT LOGGED IN (SHOW LOGIN FORM) ---
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