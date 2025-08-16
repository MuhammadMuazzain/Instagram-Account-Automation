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
from dotenv import load_dotenv
import os

load_dotenv()

# --------------------------------------------
# CONFIGURATION
# --------------------------------------------

CATCHALL_INBOX = os.getenv("EMAIL_USER")
CATCHALL_PASSWORD = os.getenv("EMAIL_PASS")
IMAP_HOST = os.getenv("IMAP_SERVER")
IMAP_PORT = 993
EMAIL_DOMAIN = "arksbaymarketing.com"
EMAIL_RETRY_COUNT = 6  # retry 6 times
EMAIL_RETRY_INTERVAL = 5  # wait 5 seconds between retries

# --------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------

def generate_random_email(domain):
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    return f"{username}@{domain}"

def generate_random_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choices(characters, k=length))

def get_verification_code(imap_host, email_user, email_pass, max_retries=12, wait_seconds=5):
    print("📨 Waiting for Instagram verification email...")

    for attempt in range(max_retries):
        try:
            mail = imaplib.IMAP4_SSL(imap_host)
            mail.login(email_user, email_pass)

            folders_to_check = ["INBOX", "Social", "[Gmail]/Social", "Promotions"]

            for folder in folders_to_check:
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
                            print(f"✅ Verification code found in folder '{folder}'")
                            return match.group(1)
                except Exception:
                    continue

            mail.logout()
        except Exception as e:
            print("❌ Email check error:", e)

        print(f"🔁 Retry {attempt + 1}/{max_retries}...")
        time.sleep(wait_seconds)

    print("⏰ Verification code not found.")
    return None

# --------------------------------------------
# MAIN SCRIPT
# --------------------------------------------

generated_email = generate_random_email(EMAIL_DOMAIN)
password = generate_random_password()

print("📧 Generated Email:", generated_email)
print("🔐 Generated Password:", password)

# ✅ Launch Undetected Chrome
options = uc.ChromeOptions()
options.add_argument("--start-maximized")

driver = uc.Chrome(options=options)
wait = WebDriverWait(driver, 20)

try:
    driver.get("https://www.instagram.com/accounts/emailsignup/")

    # Fill form
    email_input = wait.until(EC.presence_of_element_located((By.NAME, "emailOrPhone")))
    email_input.send_keys(generated_email)

    driver.find_element(By.NAME, "fullName").send_keys("John Doe")
    driver.find_element(By.NAME, "username").send_keys(generated_email.split("@")[0])
    driver.find_element(By.NAME, "password").send_keys(password)

    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))).click()

    time.sleep(5)  # wait for DOB form

    # Random DOB
    wait.until(EC.presence_of_element_located((By.XPATH, "//select[@title='Month:']")))
    driver.find_element(By.XPATH, "//select[@title='Month:']/option[2]").click()
    driver.find_element(By.XPATH, "//select[@title='Day:']/option[10]").click()
    driver.find_element(By.XPATH, "//select[@title='Year:']/option[25]").click()

    driver.find_element(By.XPATH, "//button[text()='Next']").click()

    time.sleep(10)  # wait for email delivery

    # Get code from email
    code = get_verification_code(IMAP_HOST, CATCHALL_INBOX, CATCHALL_PASSWORD, EMAIL_RETRY_COUNT, EMAIL_RETRY_INTERVAL)

    if code:
        code_input = wait.until(EC.presence_of_element_located((By.NAME, "email_confirmation_code")))
        code_input.send_keys(code)
        code_input.send_keys(Keys.ENTER)
        print("🎉 Verification complete!")
    else:
        print("⚠️ Could not complete verification - no code received.")

    time.sleep(10)

finally:
    driver.quit()

 #<input aria-label="Confirmation Code" autocomplete="off" class="_aaie _aaic _ag7n" dir="" maxlength="8" placeholder="Confirmation Code" spellcheck="true" type="text" value="" name="email_confirmation_code">
#<div class="html-div x14z9mp xat24cr x1lziwak xexx8yu xyri2b x18d9i69 x1c1uobl x9f619 x1bl4301 xjbqb8w x78zum5 x15mokao x1ga7v0g x16uus16 xbiv7yw xw7yly9 x1n2onr6 x1plvlek xryxfnj x1c4vz4f x2lah0s xdt5ytf xqjyukv x1qjc9v5 x1oa3qoh x1nhvcw1" style="--width: 100%;"><div aria-disabled="true" class="x1i10hfl xjqpnuy xc5r6h4 xqeqjp1 x1phubyo x972fbf x10w94by x1qhh985 x14e42zd xdl72j9 x2lah0s xe8uvvx xdj266r x14z9mp xat24cr x1lziwak x2lwn1j xeuugli xexx8yu x18d9i69 x1hl2dhg xggy1nq x1ja2u2z x1t137rt x1q0g3np x1lku1pv x1a2a7pz x6s0dn4 xjyslct x1obq294 x5a5i1n xde0f50 x15x8krk x1ejq31n x18oe1m7 x1sy0etr xstzfhl x9f619 x9bdzbf x1ypdohk x1f6kntn xwhw2v2 x10w6t97 xl56j7k x17ydfre xf7dkkf xv54qhq x1n2onr6 x2b8uid xlyipyv x87ps6o xcdnw81 x1i0vuye xh8yej3 x1tu34mt xzloghq xuzhngd x47corl x3nfvp2" role="button" tabindex="-1"><span class="xbyyjgo">Next</span></div></div>


