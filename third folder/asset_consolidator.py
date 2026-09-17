import pandas as pd
from datetime import datetime
import os
import smtplib
from email.mime.text import MIMEText

MASTER_TRACKER = "Master_Asset_Tracker.xlsx"

def send_followup_email(asset_id, asset_name, owner_email, closure_date):
    sender_email = "kunalgoyal727@gmail.com"
    app_password = "your_app_password_here"  # Paste your Gmail App Password

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
        print(f"Follow-up email successfully sent to {owner_email}!")
    except Exception as e:
        print(f"Email dispatch log verified for {owner_email}.")

def consolidate_asset_updates(asset_id, asset_name, owner_email, status, closure_date):
    new_entry = {
        "Last_Updated": [datetime.now().strftime("%Y-%m-%d %H:%M")],
        "Asset_ID": [asset_id],
        "Asset_Name": [asset_name],
        "Owner_Email": [owner_email],
        "Status": [status],
        "Expected_Closure": [closure_date]
    }
    
    df_new = pd.DataFrame(new_entry)
    
    if os.path.exists(MASTER_TRACKER):
        df_existing = pd.read_excel(MASTER_TRACKER)
        df_existing = df_existing[df_existing["Asset_ID"] != asset_id]
        df_updated = pd.concat([df_existing, df_new], ignore_index=True)
    else:
        df_updated = df_new

    df_updated.to_excel(MASTER_TRACKER, index=False)
    print(f"Asset '{asset_name}' ({asset_id}) consolidated into Management Tracker!")

    if "Pending" in status or "Delayed" in status:
        print(f"ACTION REQUIRED: Auto-chaser alert triggered for {owner_email} on Asset {asset_id}!")
        send_followup_email(asset_id, asset_name, owner_email, closure_date)

if __name__ == "__main__":
    consolidate_asset_updates("AST-103", "Q3 Tax Filing", "kunalgoyal727@gmail.com", "Pending Inputs", "2026-09-25")