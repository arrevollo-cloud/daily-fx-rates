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

# -------------------------
# Extract Referencial table (DOM-based)
# -------------------------

referencial = "NOT FOUND"
usdt_bob = "NOT FOUND"

# Find the table that comes after the "Referencial" header
table = driver.find_element(
    By.XPATH,
    "//h2[contains(., 'Referencial')]//following::table[1]"
)

rows = table.find_elements(By.TAG_NAME, "tr")

for row in rows:
    cells = row.find_elements(By.TAG_NAME, "td")
    if not cells:
        continue

    label = cells[0].text.strip()

    if label == "Compra":
        referencial = cells[1].text.strip().replace(",", ".")
        usdt_bob = cells[2].text.strip().replace(",", ".")
        break

     
driver.quit()
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
