from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import random
import string

# 🔧 Function to generate random email
def generate_random_email(domain="arksbaymarketing.com"):
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    return f"{username}@{domain}"

# 🔧 Function to generate random password
def generate_random_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choices(characters, k=length))

# ✅ Generate email and password
email = generate_random_email()
password = generate_random_password()

print("Generated Email:", email)
print("Generated Password:", password)

# 🔧 Setup ChromeDriver
service = Service(executable_path="chromedriver.exe")
driver = webdriver.Chrome(service=service)

driver.maximize_window()

# 🌐 Open Instagram signup page
driver.get("https://www.instagram.com/accounts/emailsignup/")

# 🕒 Wait for fields to load
wait = WebDriverWait(driver, 20)

try:
    # ✅ Input Email
    email_input = wait.until(EC.presence_of_element_located((By.NAME, "emailOrPhone")))
    email_input.send_keys(email)

    # ✅ Input Full Name
    fullname_input = driver.find_element(By.NAME, "fullName")
    fullname_input.send_keys("John Doe")  # You can randomize this too if needed

    # ✅ Input Username
    username_input = driver.find_element(By.NAME, "username")
    username_input.send_keys(email.split('@')[0])  # Using part of email as username

    # ✅ Input Password
    password_input = driver.find_element(By.NAME, "password")
    password_input.send_keys(password)

    # ✅ Click the Sign Up button
    signup_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']")))
    signup_button.click()

    # 🕒 Wait for DOB page to load
    time.sleep(5)

    # ✅ Select Birthday Fields
    # Random realistic birthday
    month = random.choice(['January', 'February', 'March', 'April', 'May', 'June',
                           'July', 'August', 'September', 'October', 'November', 'December'])
    day = str(random.randint(1, 28))
    year = str(random.randint(1990, 2000))

    # ✅ Select Month
    month_dropdown = wait.until(EC.presence_of_element_located((By.XPATH, "//select[@title='Month:']")))
    month_dropdown.click()
    month_option = driver.find_element(By.XPATH, f"//select[@title='Month:']/option[text()='{month}']")
    month_option.click()

    # ✅ Select Day
    day_dropdown = driver.find_element(By.XPATH, "//select[@title='Day:']")
    day_dropdown.click()
    day_option = driver.find_element(By.XPATH, f"//select[@title='Day:']/option[text()='{day}']")
    day_option.click()

    # ✅ Select Year
    year_dropdown = driver.find_element(By.XPATH, "//select[@title='Year:']")
    year_dropdown.click()
    year_option = driver.find_element(By.XPATH, f"//select[@title='Year:']/option[text()='{year}']")
    year_option.click()

    # ✅ Click Next button
    next_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Next']")))
    next_button.click()

    # 🕒 Wait to observe before quitting
    time.sleep(10)

finally:
    driver.quit()
