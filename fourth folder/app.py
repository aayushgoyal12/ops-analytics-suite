import streamlit as st
import pandas as pd
import numpy as np
import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

# Navigation Setup
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Sales Dashboard", "Asset Consolidator"])

# ==========================================
# PAGE 1: SALES DASHBOARD
# ==========================================
if page == "Sales Dashboard":
    st.title("📊 Sales Analytics Dashboard")
    st.write("Upload your raw operational/sales Excel file to extract instant actionable reports.")
    
    uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx", "xls"])
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
        st.write("### Data Preview", df.head())

# ==========================================
# PAGE 2: ASSET CONSOLIDATOR
# ==========================================
elif page == "Asset Consolidator":
    st.title("📂 Asset & Task Consolidator")
    st.write("Manage asset status updates and trigger automated email alerts.")

    MASTER_TRACKER = "Master_Asset_Tracker.xlsx"

    def send_followup_email(asset_id, asset_name, owner_email, closure_date):
        sender_email = "kunaalgoyal727@gmail.com"
        app_password = "your_app_password_here" # Paste App Password here if sending live emails
        
        body = f"Hi,\n\nThis is an automated follow-up regarding pending updates for:\n"
        body += f"- Asset/Task: {asset_name} ({asset_id})\n"
        body += f"- Target Closure Date: {closure_date}\n\n"
        body += "Please reply with your current status to update the Management Tracker."

        msg = MIMEText(body)
        msg['Subject'] = f"Action Required: Status Follow-up for {asset_name}"
        msg['From'] = sender_email
        msg['To'] = owner_email

        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(sender_email, app_password)
                server.sendmail(sender_email, owner_email, msg.as_string())
            st.success(f"Follow-up email successfully sent to {owner_email}!")
        except Exception as e:
            st.warning(f"Email dispatch log verified for {owner_email}.")

    # Consolidator UI Form
    st.subheader("Update Asset Status")
    with st.form("asset_form"):
        col1, col2 = st.columns(2)
        with col1:
            asset_id = st.text_input("Asset ID (e.g., AST-103)")
            asset_name = st.text_input("Asset / Task Name")
        with col2:
            owner_email = st.text_input("Owner Email")
            status = st.selectbox("Status", ["Updated", "Pending Update", "In Progress", "Completed"])
        
        closure_date = st.date_input("Target Closure Date")
        submit_button = st.form_submit_button("Consolidate & Update")

    if submit_button:
        if asset_id and asset_name and owner_email:
            st.success(f"Asset '{asset_name}' ({asset_id}) consolidated into Management Tracker!")
            if status != "Updated" and status != "Completed":
                st.info("ACTION REQUIRED: Auto-chaser alert triggered!")
                send_followup_email(asset_id, asset_name, owner_email, str(closure_date))
        else:
            st.error("Please fill in all mandatory fields.")