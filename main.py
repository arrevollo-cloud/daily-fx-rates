import requests
from bs4 import BeautifulSoup
import re
import smtplib
from email.mime.text import MIMEText
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import time

print("Starting script...")

# -------------------------
# EUR/USD
# -------------------------

print("Fetching EUR/USD...")

fx = requests.get(
    "https://open.er-api.com/v6/latest/EUR"
).json()

print(fx)

eurusd = fx["rates"]["USD"]

print("EUR/USD:", eurusd)

# -------------------------
# Dolar Bolivia Hoy
# -------------------------

print("Launching browser...")

options = Options()

options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

driver.get("https://dolarboliviahoy.com/")

print("Page loaded.")

# Wait for JavaScript rendering

time.sleep(5)

page_text = driver.find_element(By.TAG_NAME, "body").text

print(page_text)

driver.quit()

referencial = "NOT FOUND"
usdt_bob = "NOT FOUND"

# Find section

lines = page_text.splitlines()

for i, line in enumerate(lines):

    if "Referencial BCB vs Paralelo" in line:

        print("FOUND SECTION")

        # Search nearby lines for Compra row

        for j in range(i, min(i + 10, len(lines))):

            current = lines[j]

            print(current)

            if "Compra" in current:

                parts = current.split()

                numbers = []

                for p in parts:

                    try:
                        float(p)
                        numbers.append(p)
                    except:
                        pass

                if len(numbers) >= 2:
                    referencial = numbers[0]
                    usdt_bob = numbers[1]

print("Referencial:", referencial)
print("USDT/BOB:", usdt_bob)

# -------------------------
# Email Content
# -------------------------

message = f"""
EUR/USD: {eurusd:.4f}

USDT/BOB (Venta): {usdt_bob}

Referencial (Venta): {referencial}
"""

print(message)

# -------------------------
# Send Email
# -------------------------

sender = os.environ["EMAIL_ADDRESS"]

password = os.environ["EMAIL_PASSWORD"]

recipient = os.environ["RECIPIENT_EMAIL"]

msg = MIMEText(message)

msg["Subject"] = "Daily FX Rates"

msg["From"] = sender

msg["To"] = recipient

print("Connecting to Gmail SMTP...")

server = smtplib.SMTP_SSL("smtp.gmail.com", 465)

server.login(sender, password)

print("Sending email...")

server.sendmail(sender, recipient, msg.as_string())

server.quit()

print("Email sent successfully.")
