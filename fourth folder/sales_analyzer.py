import pandas as pd
import numpy as np

# Sample Sales Data
data = {
    "Rep_Name": ["Rahul Sharma", "Ankit Verma", "Pooja Mehta", "Suresh Kumar", "Vikram Singh"],
    "Department": ["North Zone", "South Zone", "North Zone", "West Zone", "East Zone"],
    "Target_Units": [100, 120, 90, 110, 150],
    "Actual_Units": [105, 45, 92, 50, 140],
    "Revenue_Generated": [525000, 225000, 460000, 250000, 700000]
}

def analyze_sales_performance():
    df = pd.DataFrame(data)
    
    # Target Achievement Percentage Calculate karo
    df["Achievement_%"] = (df["Actual_Units"] / df["Target_Units"]) * 100
    
    # Non-Performer Flagging Threshold (< 60% Achievement)
    df["Performance_Status"] = np.where(df["Achievement_%"] < 60, "NON-PERFORMER", "ON-TRACK")
    
    # Save Master Analytics Sheet
    df.to_excel("Sales_Performance_Report.xlsx", index=False)
    print("Sales Analytics Sheet generated successfully!")
    
    # Extract Non-Performers
    non_performers = df[df["Performance_Status"] == "NON-PERFORMER"]
    
    print("\n--- UNDERPERFORMER ALERT REPORT ---")
    for index, row in non_performers.iterrows():
        print(f"CRITICAL: {row['Rep_Name']} ({row['Department']}) achieved only {row['Achievement_%']:.1f}% of target!")

if __name__ == "__main__":
    analyze_sales_performance()