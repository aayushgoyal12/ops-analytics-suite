import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


# Message that will be sent with the connection request
connection_message = (
    "Hi, CA practices me batch invoice data entry aur GST matching fast karne ke liye "
    "ek AI-powered tool build kiya hai. 10-second demo check karne ke liye profile pe reply kariye."
)


def run_linkedin_outreach():
    # 1. Load profile URLs
    try:
        df = pd.read_csv("linkedin_profiles.csv")
        urls = df["url"].tolist()
    except FileNotFoundError:
        print("❌ linkedin_profiles.csv file nahi mili!")
        return
    except KeyError:
        print("❌ CSV me 'url' column nahi mila!")
        return

    if not urls:
        print("❌ Koi URL nahi mila CSV me.")
        return

    print(f"🚀 Starting LinkedIn outreach for {len(urls)} profiles using your active session...")

    # 2. Chrome options – use your real Chrome profile so you stay logged in
    options = Options()

    # ⚠️ IMPORTANT: Replace with your actual macOS username
    # Run this in terminal to find it → echo $HOME
    options.add_argument(
        "--user-data-dir=/Users//kunalgoyal727gmail.com/Library/Application Support/Google/Chrome"
    )
    options.add_argument("--profile-directory=Default")

    # Stability & anti-detection flags
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # 3. Start browser
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    wait = WebDriverWait(driver, 15)

    # 4. Main loop
    try:
        for idx, url in enumerate(urls, start=1):
            print(f"\n[{idx}/{len(urls)}] Opening profile: {url}")
            driver.get(url)
            time.sleep(3)  # let page load

            try:
                # Try to find the "Connect" button
                connect_btn = wait.until(
                    EC.element_to_be_clickable((
                        By.XPATH,
                        "//button[contains(@aria-label, 'Invite') or contains(., 'Connect')]"
                    ))
                )
                connect_btn.click()
                time.sleep(1.5)

                # Click "Add a note"
                try:
                    add_note_btn = wait.until(
                        EC.element_to_be_clickable((
                            By.XPATH,
                            "//button[contains(., 'Add a note')]"
                        ))
                    )
                    add_note_btn.click()
                    time.sleep(1)

                    # Type the message
                    note_box = wait.until(
                        EC.presence_of_element_located((By.ID, "custom-message"))
                    )
                    note_box.clear()
                    note_box.send_keys(connection_message)
                    time.sleep(0.8)

                    # Click Send
                    send_btn = wait.until(
                        EC.element_to_be_clickable((
                            By.XPATH,
                            "//button[contains(., 'Send')]"
                        ))
                    )
                    send_btn.click()
                    print("✅ Connection request + note sent")

                except Exception:
                    # Sometimes LinkedIn doesn't show "Add a note" (already connected / limit)
                    print("⚠️  Could not add note (maybe already connected or limit reached)")

            except Exception as e:
                print(f"❌ Connect button not found / already pending → {str(e)[:80]}")

            # Small random delay to look more human
            time.sleep(4 + (idx % 3))

    finally:
        print("\n🏁 Outreach finished. Closing browser in 5 seconds...")
        time.sleep(5)
        driver.quit()


if __name__ == "__main__":
    run_linkedin_outreach()