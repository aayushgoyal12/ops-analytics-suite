import pandas as pd
import os
from datetime import datetime

FILE_NAME = "linkedin_outreach_tracker.csv"

def initialize_tracker():
    """CSV file create karta hai agar pehle se nahi hai."""
    if not os.path.exists(FILE_NAME):
        df = pd.DataFrame(columns=["Name", "Company", "Profile URL", "Status", "Date Added", "Last Updated"])
        df.to_csv(FILE_NAME, index=False)

def add_lead(name, company, profile_url, status="Connection Sent"):
    """Naya lead CSV file mein add karta hai."""
    initialize_tracker()
    df = pd.read_csv(FILE_NAME)
    
    # Check if lead already exists
    if not df[df['Profile URL'] == profile_url].empty:
        print(f"Lead '{name}' already exists in tracker!")
        return
        
    new_row = {
        "Name": name,
        "Company": company,
        "Profile URL": profile_url,
        "Status": status,
        "Date Added": datetime.now().strftime("%Y-%m-%d"),
        "Last Updated": datetime.now().strftime("%Y-%m-%d")
    }
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(FILE_NAME, index=False)
    print(f"Lead '{name}' successfully added!")

def view_leads():
    """Saare leads ko terminal par table format mein display karta hai."""
    initialize_tracker()
    df = pd.read_csv(FILE_NAME)
    if df.empty:
        print("\nTracker is currently empty!")
    else:
        print("\n" + "="*80)
        print(" LINKEDIN OUTREACH TRACKER TABLE ".center(80, "="))
        print("="*80)
        print(df.to_string(index=False))
        print("="*80 + "\n")

def check_follow_ups():
    """Check karta hai ki kis lead ko follow-up ki zaroorat hai (3 din ya usse zyada purane)."""
    initialize_tracker()
    df = pd.read_csv(FILE_NAME)
    
    if df.empty:
        return
    
    today = datetime.now()
    print("\n" + "="*80)
    print(" FOLLOW-UP REMINDERS ".center(80, "="))
    print("="*80)
    
    follow_up_needed = False
    for index, row in df.iterrows():
        last_updated = datetime.strptime(str(row['Last Updated']), "%Y-%m-%d")
        days_passed = (today - last_updated).days
        
        if days_passed >= 3 and row['Status'] != 'Converted':
            print(f"Name: {row['Name']} | Company: {row['Company']}")
            print(f"Status: {row['Status']} | Days Since Last Update: {days_passed} days")
            print("-" * 80)
            follow_up_needed = True
            
    if not follow_up_needed:
        print("Koi bhi pending follow-up nahi hai aaj ke liye!")
    print("="*80 + "\n")

if __name__ == "__main__":
    # 1. Naye leads yahan add kar sakte ho (agar aur add karne hon)
    # add_lead("Name", "Company Name", "Profile URL")
    
    # 2. Poori table view karo
    view_leads()
    
    # 3. Follow-up reminders check karo
    check_follow_ups()