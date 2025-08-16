import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import imaplib
import email as email_lib
import re
import time
import random
import string
import os
from dotenv import load_dotenv
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
import gspread
from oauth2client.service_account import ServiceAccountCredentials

load_dotenv()

CATCHALL_INBOX = os.getenv("EMAIL_USER")
CATCHALL_PASSWORD = os.getenv("EMAIL_PASS")
IMAP_HOST = os.getenv("IMAP_SERVER")
IMAP_PORT = 993
EMAIL_DOMAIN = "arksbaymarketing.com"
# Proxy credentials and list
PROXY_USERNAME = "13cb2eab3a"
PROXY_PASSWORD = "wpJTtiur"
PROXY_PORT = 4444
PROXY_LIST = [
    "82.163.62.27",
    "45.132.80.30",
    "82.163.62.32",
    "139.190.224.16",
    "45.132.80.45"
]


EMAIL_RETRY_COUNT = 2
EMAIL_RETRY_INTERVAL = 2

GOOGLE_SHEET_NAME = "Instagram Accounts"  
GOOGLE_CREDS_FILE = "service_account.json"   

def generate_random_email(domain):
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    return f"{username}@{domain}"

def generate_random_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choices(characters, k=length))

def human_type(element, text):
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.07, 0.25))

def get_verification_code(imap_host, email_user, email_pass, max_retries=12, wait_seconds=5, after_time=None):
    print(" Waiting for a *fresh* Instagram verification email...")

    if after_time is None:
        after_time = datetime.now(timezone.utc)

    for attempt in range(max_retries):
        try:
            mail = imaplib.IMAP4_SSL(imap_host)
            mail.login(email_user, email_pass)

            folders = ["INBOX", "Social", "[Gmail]/Social", "Promotions"]

            for folder in folders:
                try:
                    mail.select(folder)
                    result, data = mail.search(None, '(FROM "no-reply@mail.instagram.com")')
                    if data and data[0]:
                        email_ids = data[0].split()[::-1]

                        for eid in email_ids:
                            result, msg_data = mail.fetch(eid, "(RFC822)")
                            raw_email = msg_data[0][1]
                            msg = email_lib.message_from_bytes(raw_email)

                            email_date = parsedate_to_datetime(msg["Date"]).astimezone(timezone.utc)
                            if email_date < after_time:
                                continue

                            if msg.is_multipart():
                                for part in msg.walk():
                                    if part.get_content_type() == "text/plain":
                                        body = part.get_payload(decode=True).decode()
                                        break
                            else:
                                body = msg.get_payload(decode=True).decode()

                            match = re.search(r"\b(\d{6})\b", body)
                            if match:
                                mail.logout()
                                print(f"✅ Fresh verification code found (at {email_date.isoformat()})")
                                return match.group(1)
                except:
                    continue
            mail.logout()
        except Exception as e:
            print(" Email check error:", e)

        print(f" Retry {attempt+1}/{max_retries}...")
        time.sleep(wait_seconds)

    print(" Fresh verification code not found.")
    return None

def save_to_google_sheet(email, username, password):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
        client = gspread.authorize(creds)

        # 🔁 Open spreadsheet and target "Sheet2"
        sheet = client.open("Link_to_python").worksheet("Sheet2")

        # Get current UTC time
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        # Append the row
        sheet.append_row([email, username, password, timestamp])
        print("📋 Account info saved to Google Sheet!")

    except Exception as e:
        print(" Failed to save to Google Sheets:", str(e))

# -------------------------------
# MAIN
# -------------------------------


def create_account():
    generated_email = generate_random_email(EMAIL_DOMAIN)
    username = generated_email.split("@")[0]
    password = generate_random_password()
    print("📧 Email:", generated_email)
    print("🔐 Password:", password)

    email_sent_time = datetime.now(timezone.utc)

    # options = uc.ChromeOptions()
    options=uc.ChromeOptions()

    # Randomly select a proxy
    selected_proxy_ip = "82.163.62.27"
    proxy_argument = f"--proxy-server=http://{PROXY_USERNAME}:{PROXY_PASSWORD}@{selected_proxy_ip}:{PROXY_PORT}"
    options.add_argument(proxy_argument)

    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--lang=en-US,en;q=0.9")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")

    driver = uc.Chrome(options=options)
    wait = WebDriverWait(driver, 20)

    try:
        driver.get("https://www.instagram.com/accounts/emailsignup/")
        time.sleep(random.uniform(2, 4))

        human_type(wait.until(EC.presence_of_element_located((By.NAME, "emailOrPhone"))), generated_email)
        human_type(driver.find_element(By.NAME, "fullName"), "John Doe")
        human_type(driver.find_element(By.NAME, "username"), username)
        human_type(driver.find_element(By.NAME, "password"), password)

        time.sleep(random.uniform(1.5, 2.5))
        # wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))).click()

        signup_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit' and text()='Sign up']")))
        disabled = signup_btn.get_attribute("disabled")
        print("Button disabled?", disabled)

# Wait to ensure form validation JS completes
        time.sleep(2)

# Use JS click (bypasses weird issues)
        driver.execute_script("arguments[0].click();", signup_btn)

        print("🔘 Clicked 'Sign Up' button")




        time.sleep(random.uniform(2, 4))

        wait.until(EC.presence_of_element_located((By.XPATH, "//select[@title='Month:']")))
        driver.find_element(By.XPATH, "//select[@title='Month:']/option[2]").click()
        driver.find_element(By.XPATH, "//select[@title='Day:']/option[10]").click()
        driver.find_element(By.XPATH, "//select[@title='Year:']/option[25]").click()
        driver.find_element(By.XPATH, "//button[text()='Next']").click()
        time.sleep(random.uniform(1,3))

        code = get_verification_code(IMAP_HOST, CATCHALL_INBOX, CATCHALL_PASSWORD, EMAIL_RETRY_COUNT, EMAIL_RETRY_INTERVAL, after_time=email_sent_time)

        if code:
            code_input = wait.until(EC.presence_of_element_located((By.NAME, "email_confirmation_code")))
            human_type(code_input, code)
            code_input.send_keys(Keys.ENTER)
            print("✅ Account verified and created!")

            save_to_google_sheet(generated_email, username, password)
        else:
            print("❌ No verification code received.")

    except Exception as e:
        print("⚠️ Error:", str(e))
    finally:
        driver.quit()


for i in range(10):
    print(f"\n--- Running account creation {i+1}/10 ---")
    create_account()
    wait_time = random.randint(3, 7)
    print(f"⏳ Waiting {wait_time} seconds before next run...\n")
    time.sleep(wait_time)
