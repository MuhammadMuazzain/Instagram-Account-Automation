import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import imaplib
import email as email_lib
import re
import time
import random
import string
import os
from dotenv import load_dotenv

load_dotenv()

# -------------------------------
# CONFIGURATION
# -------------------------------

CATCHALL_INBOX = os.getenv("EMAIL_USER")
CATCHALL_PASSWORD = os.getenv("EMAIL_PASS")
IMAP_HOST = os.getenv("IMAP_SERVER")
IMAP_PORT = 993
EMAIL_DOMAIN = "arksbaymarketing.com"
EMAIL_RETRY_COUNT = 6
EMAIL_RETRY_INTERVAL = 5

# -------------------------------
# HELPERS
# -------------------------------

def generate_random_email(domain):
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    return f"{username}@{domain}"

def generate_random_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choices(characters, k=length))

def human_type(element, text):
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.07, 0.25))  # simulate human typing

def get_verification_code(imap_host, email_user, email_pass, max_retries=12, wait_seconds=5):
    print("📨 Waiting for Instagram verification email...")
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
                        email_ids = data[0].split()
                        latest_email_id = email_ids[-1]
                        result, msg_data = mail.fetch(latest_email_id, "(RFC822)")
                        raw_email = msg_data[0][1]
                        msg = email_lib.message_from_bytes(raw_email)

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
                            print(f"✅ Code found in folder '{folder}'")
                            return match.group(1)
                except:
                    continue
            mail.logout()
        except Exception as e:
            print("❌ Email check error:", e)

        print(f"🔁 Retry {attempt+1}/{max_retries}...")
        time.sleep(wait_seconds)

    print("⏰ Code not found.")
    return None

# -------------------------------
# MAIN
# -------------------------------

generated_email = generate_random_email(EMAIL_DOMAIN)
password = generate_random_password()

print("📧 Email:", generated_email)
print("🔐 Password:", password)

# Realistic browser options
options = uc.ChromeOptions()
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
    time.sleep(random.uniform(3, 6))

    email_input = wait.until(EC.presence_of_element_located((By.NAME, "emailOrPhone")))
    human_type(email_input, generated_email)

    full_name = driver.find_element(By.NAME, "fullName")
    human_type(full_name, "John Doe")

    username = driver.find_element(By.NAME, "username")
    human_type(username, generated_email.split("@")[0])

    password_input = driver.find_element(By.NAME, "password")
    human_type(password_input, password)

    time.sleep(random.uniform(1.5, 2.5))
    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))).click()
    time.sleep(random.uniform(4, 6))

    # Birthday
    wait.until(EC.presence_of_element_located((By.XPATH, "//select[@title='Month:']")))
    driver.find_element(By.XPATH, "//select[@title='Month:']/option[2]").click()
    driver.find_element(By.XPATH, "//select[@title='Day:']/option[10]").click()
    driver.find_element(By.XPATH, "//select[@title='Year:']/option[25]").click()
    driver.find_element(By.XPATH, "//button[text()='Next']").click()
    time.sleep(random.uniform(5, 7))

    # Email Polling
    code = get_verification_code(IMAP_HOST, CATCHALL_INBOX, CATCHALL_PASSWORD, EMAIL_RETRY_COUNT, EMAIL_RETRY_INTERVAL)
    if code:
        code_input = wait.until(EC.presence_of_element_located((By.NAME, "email_confirmation_code")))
        human_type(code_input, code)
        code_input.send_keys(Keys.ENTER)
        print("🎉 Account verified and created!")
    else:
        print("⚠️ No verification code received.")

    input("🧍‍♂️ Press ENTER to close browser manually...")
finally:
    driver.quit()