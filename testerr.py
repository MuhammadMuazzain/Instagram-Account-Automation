import requests

proxies = {
    "http": "http://13cb2eab3a:wpJTtiur@82.163.62.27:4444",
    "https": "http://13cb2eab3a:wpJTtiur@82.163.62.27:4444"
}

try:
    response = requests.get("https://www.google.com", proxies=proxies)
    print(response.text)
except Exception as e:
    print("Proxy connection failed:", e)