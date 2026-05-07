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
# Extract USDT/BOB Venta
# -------------------------

usdt_match = re.search(
    r'USDT.*?Precio de Venta Bs ([0-9]+(?:\.[0-9]+)?)',
    text,
    re.IGNORECASE
)

usdt_bob = usdt_match.group(1) if usdt_match else "NOT FOUND"

print("USDT/BOB:", usdt_bob)

# -------------------------
# Extract Referencial Venta
# -------------------------

ref_match = re.search(
    r'Referencial.*?Precio de Venta Bs ([0-9]+(?:\.[0-9]+)?)',
    text,
    re.IGNORECASE
)

referencial = ref_match.group(1) if ref_match else "NOT FOUND"

print("Referencial:", referencial)

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
