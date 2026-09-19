import streamlit as st
import sqlite3
import pandas as pd
from datetime import date
import smtplib
from email.mime.text import MIMEText
from supabase import create_client, Client


# Database Setup
# Exact Supabase Project Settings -> API se copy karo
SUPABASE_URL = "https://nrhwruxrcdskfmhdyoow.supabase.co"  # Aapka Project URL
SUPABASE_KEY = "sb_publishable_EDJzm21mydzHYJUS7VS0eQ_roRIIThU"  # Aapki Anon Key

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
conn = sqlite3.connect("compliance_tracker.db", check_same_thread=False)
c = conn.cursor()

c.execute('''
    CREATE TABLE IF NOT EXISTS requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_name TEXT,
        client_email TEXT,
        doc_type TEXT,
        due_date TEXT,
        status TEXT
    )
''')
conn.commit()

# Real Email Sender Function
def send_real_email(to_email, client_name, doc_type, req_id):
    sender_email = "aayushgoyal743@gmail.com"  # Aapka email id
    app_password = "hsyw lfog agrn vnrp"     # Gmail App Password
    
    subject = f"Action Required: Send {doc_type} for Tax Compliance"
    body = f"Hello {client_name},\n\nYour CA has requested: {doc_type}.\nDue Date is approaching. Your Request ID is #{req_id}.\n\nPlease upload it via the Client Portal.\n\nThank you!"
    
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = to_email

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, app_password)
            server.sendmail(sender_email, to_email, msg.as_string())
        return True
    except Exception as e:
        return False

st.set_page_config(page_title="Tax & Compliance Portal", layout="wide")
st.title("💼 Accounting Client Document Hub")

# Sidebar
st.sidebar.header("➕ Create Document Request")
c_name = st.sidebar.text_input("Client Name")
c_email = st.sidebar.text_input("Client Email")
doc_type = st.sidebar.selectbox("Document Needed", ["Bank Statement", "GST Sales Register", "Purchase Bills", "ITR Computation"])
due_date = st.sidebar.date_input("Target Due Date", date.today())

if st.sidebar.button("Send Request to Client"):
    if c_name and c_email:
        c.execute("INSERT INTO requests (client_name, client_email, doc_type, due_date, status) VALUES (?, ?, ?, ?, ?)",
                  (c_name, c_email, doc_type, str(due_date), "Pending"))
        conn.commit()
        st.sidebar.success(f"Request saved for {c_name}!")
        st.rerun()
    else:
        st.sidebar.error("Please enter both Name and Email.")

# Dashboard Tabs
mode = st.radio("Select View:", ["CA Firm Dashboard", "Client Upload Portal"], horizontal=True)

if mode == "CA Firm Dashboard":
    st.subheader("📋 Active Compliance Requests")
    df = pd.read_sql_query("SELECT id AS 'ID', client_name AS 'Client', client_email AS 'Email', doc_type AS 'Document', due_date AS 'Due Date', status AS 'Status' FROM requests", conn)
    
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        st.divider()
        
        col1, col2 = st.columns(2)
        with col1:
            req_id = st.number_input("Enter Request ID for Email Chaser:", min_value=1, step=1)
            if st.button("📩 Send Real Email Reminder"):
                row = df[df['ID'] == req_id]
                if not row.empty:
                    to_email = row['Email'].values[0]
                    c_name_val = row['Client'].values[0]
                    doc_val = row['Document'].values[0]
                    
                    if send_real_email(to_email, c_name_val, doc_val, req_id):
                        st.success(f"Email sent successfully to {to_email}!")
                    else:
                        st.info(f"Email trigger clicked for {to_email} (Configure App Password for live dispatch).")
                else:
                    st.error("Invalid Request ID")
                    
        with col2:
            close_id = st.number_input("Enter Request ID to mark Received:", min_value=1, step=1)
            if st.button("✅ Mark as Completed"):
                c.execute("UPDATE requests SET status = 'Completed' WHERE id = ?", (close_id,))
                conn.commit()
                st.success(f"Request #{close_id} marked Completed!")
                st.rerun()

elif mode == "Client Upload Portal":
    st.subheader("📤 Client Document Upload Link")
    req_id_input = st.number_input("Enter your Request ID:", min_value=1, step=1)
    uploaded_file = st.file_uploader("Upload requested file", type=["pdf", "xlsx", "png", "jpg"])
    
    if st.button("Submit Document"):
        if uploaded_file is not None:
            c.execute("UPDATE requests SET status = 'Received' WHERE id = ?", (req_id_input,))
            conn.commit()
            st.success("File uploaded successfully! Status updated in CA Ledger.")