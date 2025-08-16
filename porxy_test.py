from selenium import webdriver
from selenium.webdriver.chrome.options import Options

PROXY = "82.163.62.27:4444"
USERNAME = "13cb2eab3a"
PASSWORD = "wpJTtiur"

options = Options()
options.add_argument(f'--proxy-server=http://{PROXY}')
driver = webdriver.Chrome(options=options)
driver.get("https://www.instagram.com")
