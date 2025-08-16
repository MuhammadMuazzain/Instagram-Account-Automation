import os
import re
import time
import zipfile
import random
import string
import imaplib
import email as email_lib
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
from dotenv import load_dotenv

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from selenium.common.exceptions import NoSuchWindowException, WebDriverException

# Load environment variables
load_dotenv()

CATCHALL_INBOX = os.getenv("EMAIL_USER")
CATCHALL_PASSWORD = os.getenv("EMAIL_PASS")
IMAP_HOST = os.getenv("IMAP_SERVER")
EMAIL_DOMAIN = "arksbaymarketing.com"
EMAIL_RETRY_COUNT = 12
EMAIL_RETRY_INTERVAL = 5

GOOGLE_SHEET_NAME = "Instagram Accounts"
GOOGLE_CREDS_FILE = "service_account.json"


# ---------------- PROXY EXTENSION CREATOR ---------------- #
def create_proxy_auth_extension(proxy_host, proxy_port, proxy_user, proxy_pass, extension_path):
    manifest_json = """
    {
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "Chrome Proxy",
        "permissions": [
            "proxy",
            "tabs",
            "unlimitedStorage",
            "storage",
            "<all_urls>",
            "webRequest",
            "webRequestBlocking"
        ],
        "background": {
            "scripts": ["background.js"]
        },
        "minimum_chrome_version":"22.0.0"
    }
    """

    background_js = f"""
    var config = {{
            mode: "fixed_servers",
            rules: {{
              singleProxy: {{
                scheme: "http",
                host: "{proxy_host}",
                port: parseInt({proxy_port})
              }},
              bypassList: ["localhost"]
            }}
          }};
    chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{}});

    function callbackFn(details) {{
        return {{
            authCredentials: {{
                username: "{proxy_user}",
                password: "{proxy_pass}"
            }}
        }};
    }}

    chrome.webRequest.onAuthRequired.addListener(
                callbackFn,
                {{urls: ["<all_urls>"]}},
                ['blocking']
    );
    """

    with zipfile.ZipFile(extension_path, 'w') as zp:
        zp.writestr("manifest.json", manifest_json)
        zp.writestr("background.js", background_js)
    return extension_path


# ---------------- UTILITY FUNCTIONS ---------------- #
def generate_random_email(domain):
    return f"{''.join(random.choices(string.ascii_lowercase + string.digits, k=10))}@{domain}"


def generate_random_password(length=12):
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choices(chars, k=length))


def human_type(element, text):
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.05, 0.2))


def get_verification_code(imap_host, email_user, email_pass, max_retries=12, wait_seconds=5, after_time=None):
    if after_time is None:
        after_time = datetime.now(timezone.utc)

    for attempt in range(max_retries):
        try:
            mail = imaplib.IMAP4_SSL(imap_host)
            mail.login(email_user, email_pass)

            for folder in ["INBOX", "Social", "[Gmail]/Social", "Promotions"]:
                try:
                    mail.select(folder)
                    _, data = mail.search(None, '(FROM "no-reply@mail.instagram.com")')
                    if not data or not data[0]:
                        continue

                    for eid in data[0].split()[::-1]:
                        _, msg_data = mail.fetch(eid, "(RFC822)")
                        raw_email = msg_data[0][1]
                        msg = email_lib.message_from_bytes(raw_email)

                        email_date = parsedate_to_datetime(msg["Date"]).astimezone(timezone.utc)
                        if email_date < after_time:
                            continue

                        body = ""
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
                            return match.group(1)
                except:
                    continue
            mail.logout()
        except Exception as e:
            print(" Email check error:", e)

        time.sleep(wait_seconds)
    return None


def save_to_google_sheet(email, username, password ,proxy_host):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
        client = gspread.authorize(creds)

        # Open spreadsheet and target "Sheet2"
        sheet = client.open("Link_to_python").worksheet("Sheet2")

        # Get current UTC time
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

        # Append the row
        sheet.append_row([email, username, password,proxy_host, timestamp])
        print("Account info saved to Google Sheet!")

    except Exception as e:
        print(" Failed to save to Google Sheets:", str(e))


# ---------------- MAIN ACCOUNT CREATOR ---------------- #
def create_account(proxy_host, proxy_port, proxy_user, proxy_pass):
    email = generate_random_email(EMAIL_DOMAIN)
    username = email.split("@")[0]
    password = generate_random_password()
    print(f"📧 {email} | 🔑 {password}")

    email_sent_time = datetime.now(timezone.utc)
    ext_path = create_proxy_auth_extension(proxy_host, proxy_port, proxy_user, proxy_pass, "proxy_auth_ext.zip")

    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--lang=en-US,en;q=0.9")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")
    options.add_argument("--disable-extensions-except=" + os.path.abspath(ext_path))

    driver = None
    try:
        driver = uc.Chrome(options=options)
        wait = WebDriverWait(driver, 20)

        driver.get("https://www.instagram.com/accounts/emailsignup/")
        time.sleep(random.uniform(2, 4))

        human_type(wait.until(EC.presence_of_element_located((By.NAME, "emailOrPhone"))), email)
        human_type(driver.find_element(By.NAME, "fullName"), "John Doe")
        human_type(driver.find_element(By.NAME, "username"), username)
        human_type(driver.find_element(By.NAME, "password"), password)

        signup_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit' and text()='Sign up']")))
        time.sleep(1)
        driver.execute_script("arguments[0].click();", signup_btn)

        wait.until(EC.presence_of_element_located((By.XPATH, "//select[@title='Month:']")))
        driver.find_element(By.XPATH, "//select[@title='Month:']/option[2]").click()
        driver.find_element(By.XPATH, "//select[@title='Day:']/option[10]").click()
        driver.find_element(By.XPATH, "//select[@title='Year:']/option[25]").click()
        driver.find_element(By.XPATH, "//button[text()='Next']").click()

        code = get_verification_code(IMAP_HOST, CATCHALL_INBOX, CATCHALL_PASSWORD,
                                     EMAIL_RETRY_COUNT, EMAIL_RETRY_INTERVAL, after_time=email_sent_time)
        if code:
            code_input = wait.until(EC.presence_of_element_located((By.NAME, "email_confirmation_code")))
            human_type(code_input, code)
            code_input.send_keys(Keys.ENTER)
            save_to_google_sheet(email, username, password, proxy_host)
        else:
            print("❌ No verification code received.")

    except (NoSuchWindowException, WebDriverException) as e:
        print("❌ Browser error:", e)
    except Exception as e:
        print("❌ General error:", e)
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass


# ---------------- RUN MULTIPLE ACCOUNTS ---------------- #
proxies = [
    ("82.163.62.27", "4444", "13cb2eab3a", "wpJTtiur"),
    ("45.132.80.30", "4444", "13cb2eab3a", "wpJTtiur"),
    ("82.163.62.32", "4444", "13cb2eab3a", "wpJTtiur"),
    ("139.190.224.16", "4444", "13cb2eab3a", "wpJTtiur"),
    ("45.132.80.45", "4444", "13cb2eab3a", "wpJTtiur")
]

for i in range(10):
    proxy = random.choice(proxies)
    print(f"\n--- Creating account {i+1}/10 with proxy {proxy[0]} ---")
    create_account(*proxy)
    time.sleep(random.randint(3, 7))
