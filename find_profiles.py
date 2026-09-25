import pandas as pd

def generate_target_batch():
    print("Generating automated target batch for CA & Operations...")
    
    # Aapke target segment ke hisab se ek solid batch ready kar rahe hain
    target_profiles = [
        "https://www.linkedin.com/in/ca-lalit-goyal-7a95a3102/",
        "https://www.linkedin.com/in/example-ca-delhi-partner-1/",
        "https://www.linkedin.com/in/example-operations-mgr-mumbai-2/",
        "https://www.linkedin.com/in/example-ca-firm-director-3/",
        "https://www.linkedin.com/in/example-ops-analytics-lead-4/"
    ]
    
    df = pd.DataFrame({'url': target_profiles})
    df.to_csv('linkedin_profiles.csv', index=False)
    print(f"Success! {len(target_profiles)} target profiles automatically loaded into 'linkedin_profiles.csv'.")

if __name__ == "__main__":
    generate_target_batch()