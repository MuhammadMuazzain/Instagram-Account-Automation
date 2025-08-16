from playwright.sync_api import sync_playwright
import random
import string
import time
import os
from datetime import datetime, timezone
import imaplib
import email as email_lib
import re
from dotenv import load_dotenv
from email.utils import parsedate_to_datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

load_dotenv()

CATCHALL_INBOX = os.getenv("EMAIL_USER")
CATCHALL_PASSWORD = os.getenv("EMAIL_PASS")
IMAP_HOST = os.getenv("IMAP_SERVER")
EMAIL_DOMAIN = "arksbaymarketing.com"
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


def get_verification_code(imap_host, email_user, email_pass, max_retries=12, wait_seconds=5, after_time=None):
    print("Waiting for a *fresh* Instagram verification email...")

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

                            body = None
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
            print("Email check error:", e)

        print(f"Retry {attempt + 1}/{max_retries}...")
        time.sleep(wait_seconds)

    print("Fresh verification code not found.")
    return None


def save_to_google_sheet(email, username, password):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
        client = gspread.authorize(creds)
        sheet = client.open("Link_to_python").worksheet("Sheet2")
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        sheet.append_row([email, username, password, timestamp])
        print("📋 Account info saved to Google Sheet!")
    except Exception as e:
        print("Failed to save to Google Sheets:", str(e))


def create_account():
    generated_email = generate_random_email(EMAIL_DOMAIN)
    username = generated_email.split("@")[0]
    password = generate_random_password()
    print("📧 Email:", generated_email)
    print("🔐 Password:", password)
    email_sent_time = datetime.now(timezone.utc)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(locale='en-US')
        page = context.new_page()
        page.goto("https://www.instagram.com/accounts/emailsignup/", timeout=60000)
        time.sleep(random.uniform(3, 5))

        page.fill("input[name='emailOrPhone']", generated_email)
        page.fill("input[name='fullName']", "John Doe")
        page.fill("input[name='username']", username)
        page.fill("input[name='password']", password)
        time.sleep(random.uniform(1.5, 2.5))

        page.click("button[type='submit']")
        time.sleep(random.uniform(2, 4))

        page.select_option("select[title='Month:']", index=1)
        page.select_option("select[title='Day:']", index=9)
        page.select_option("select[title='Year:']", index=24)
        page.click("button:text('Next')")
        time.sleep(random.uniform(2, 4))

        code = get_verification_code(IMAP_HOST, CATCHALL_INBOX, CATCHALL_PASSWORD, EMAIL_RETRY_COUNT,
                                     EMAIL_RETRY_INTERVAL, after_time=email_sent_time)

        if code:
            page.fill("input[name='email_confirmation_code']", code)
            page.keyboard.press("Enter")
            print("✅ Account verified and created!")
            save_to_google_sheet(generated_email, username, password)
        else:
            print("❌ No verification code received.")

        browser.close()


for i in range(10):
    print(f"\n--- Running account creation {i + 1}/10 ---")
    create_account()
    wait_time = random.randint(3, 7)
    print(f"⏳ Waiting {wait_time} seconds before next run...\n")
    time.sleep(wait_time)

