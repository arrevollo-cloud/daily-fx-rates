import requests
from bs4 import BeautifulSoup
import re
import smtplib
from email.mime.text import MIMEText
import os

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

print("Fetching Bolivia rates...")

url = "https://dolarboliviahoy.com/"

html = requests.get(url).text

print("Page downloaded.")

soup = BeautifulSoup(html, "html.parser")

text = soup.get_text(" ", strip=True)

# -------------------------
# Extract Referencial + Paralelo
# -------------------------

match = re.search(
    r'Compra\s+([0-9]+(?:\.[0-9]+)?)\s+([0-9]+(?:\.[0-9]+)?)',
    text
)

if match:
    referencial = match.group(1)
    usdt_bob = match.group(2)
else:
    referencial = "NOT FOUND"
    usdt_bob = "NOT FOUND"

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
