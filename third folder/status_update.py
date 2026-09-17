import smtplib
from email.mime.text import MIMEText

def send_daily_status_email(sender_email, app_password, receiver_email):
    # 3-bullet daily summary
    tasks = [
        "Reconciled 120 client PDF bank statements into Excel",
        "Auto-generated executive audit summaries for Week 3",
        "Dispatched daily status updates to management"
    ]
    
    body = "Hi Founder,\n\nHere is today's automated status summary:\n\n"
    body += "\n".join([f"• {task}" for task in tasks])
    body += "\n\nBest,\nAutomated Bot"

    msg = MIMEText(body)
    msg['Subject'] = "Daily Status Report - Automated Summary"
    msg['From'] = sender_email
    msg['To'] = receiver_email

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, app_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        print("Daily Status Email Sent Successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")

if __name__ == "__main__":
    MY_EMAIL = "aayushgoyal743@gmail.com"      # Apna Gmail ID yahan likho
    APP_PASSWORD = "tzes bfrg gbtp regq"    # 16-digit App Password yahan paste karo
    
    # Send actual email to yourself
    send_daily_status_email(MY_EMAIL, APP_PASSWORD, MY_EMAIL)