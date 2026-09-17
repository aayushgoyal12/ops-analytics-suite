import pandas as pd
from datetime import datetime
import os
import smtplib
from email.mime.text import MIMEText

EXCEL_FILE = "Master_Document_Ledger.xlsx"

def send_delay_alert(doc_id, sender_dept, receiver_dept, status, sender_email, app_password, receiver_email):
    body = f"URGENT: Physical Document Transfer Pending Alert\n\n"
    body += f"Document ID: {doc_id}\n"
    body += f"From: {sender_dept} Department\n"
    body += f"To: {receiver_dept} Department\n"
    body += f"Current Status: {status}\n\n"
    body += "Please action this request to avoid workflow bottlenecks."

    msg = MIMEText(body)
    msg['Subject'] = f"Action Required: Pending Document {doc_id}"
    msg['From'] = sender_email
    msg['To'] = receiver_email

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, app_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        print(f"Alert email sent for {doc_id} to {receiver_email}!")
    except Exception as e:
        print(f"Error sending alert: {e}")

def append_to_master_ledger(doc_id, sender_dept, receiver_dept, status):
    new_data = {
        "Timestamp": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        "Document_ID": [doc_id],
        "From_Department": [sender_dept],
        "To_Department": [receiver_dept],
        "Status": [status]
    }
    
    new_df = pd.DataFrame(new_data)

    if os.path.exists(EXCEL_FILE):
        existing_df = pd.read_excel(EXCEL_FILE)
        updated_df = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        updated_df = new_df

    updated_df.to_excel(EXCEL_FILE, index=False)
    print(f"Document {doc_id} successfully logged into Master Excel Ledger!")
    
    # Auto-trigger alert if status indicates delay or pending action
    if "Pending" in status or "Transit" in status:
        print(f"Triggering delay notification logic for {doc_id}...")

if __name__ == "__main__":
    append_to_master_ledger("DOC-8923", "Audit", "Management", "Pending Approval")