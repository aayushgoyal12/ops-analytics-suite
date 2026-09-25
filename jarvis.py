import pandas as pd
import os
from datetime import datetime

FILE_NAME = "linkedin_outreach_tracker.csv"

def speak(text):
    """Mac ke built-in voice engine ka use karke bolne ke liye."""
    os.system(f"say '{text}'")

def jarvis_daily_briefing():
    print("\n" + "🤖 JARVIS DAILY BRIEFING ".center(60, "="))
    print(f"📅 Date: {datetime.now().strftime('%A, %d %B %Y')}\n")
    
    if not os.path.exists(FILE_NAME):
        msg = "Sir, outreach tracker file is missing."
        print(f"⚠️ {msg}")
        speak(msg)
        return
        
    df = pd.read_csv(FILE_NAME)
    total_leads = len(df)
    
    # Follow-up calculation
    today = datetime.now()
    pending_count = 0
    for _, row in df.iterrows():
        last_updated = datetime.strptime(str(row['Last Updated']), "%Y-%m-%d")
        if (today - last_updated).days >= 3 and row['Status'] != 'Converted':
            pending_count += 1
            
    # Terminal par data display
    print(f"📊 Total Leads in Pipeline: {total_leads}")
    print(f"🔔 Pending Follow-ups: {pending_count}")
    
    if total_leads > 0:
        print("\n--- Recent Leads ---")
        print(df[['Name', 'Company', 'Status']].to_string(index=False))

    # Jarvis ki aawaz wala message (Tony Stark style)
    voice_message = f"Hello Sir. Your current outreach pipeline has {total_leads} leads, and there are {pending_count} pending follow-ups for today. All systems are online."
    
    print(f"\n🗣️ Jarvis: \"{voice_message}\"")
    speak(voice_message)
    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    jarvis_daily_briefing()