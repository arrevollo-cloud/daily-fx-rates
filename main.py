import requests
from bs4 import BeautifulSoup
import re
import smtplib
from email.mime.text import MIMEText
import os

# -------------------------
# EUR/USD
# -------------------------

fx = requests.get(
    "https://api.exchangerate.host/convert?from=EUR&to=USD"
).json()

eurusd = fx["result"]

# -------------------------
# Dolar Bolivia Hoy
# -------------------------

url = "https://dolarboliviahoy.com/"
html = requests.get(url).text

soup = BeautifulSoup(html, "html.parser")
text = soup.get_text(" ", strip=True)

# -------------------------
# Extract USDT/BOB Venta
# -------------------------

usdt_match = re.search(
    r'USDT.*?Precio de Venta Bs ([0-9]+\.[0-9]+)',
    text,
    re.IGNORECASE
)

usdt_bob = usdt_match.group(1) if usdt_match else "NOT FOUND"

# -------------------------
# Extract Referencial Venta
# -------------------------

ref_match = re.search(
    r'Referencial.*?Precio de Venta Bs ([0-9]+\.[0-9]+)',
    text,
    re.IGNORECASE
)

referencial = ref_match.group(1) if ref_match else "NOT FOUND"

# -------------------------
# Email Content
# -------------------------

message = f"""
EUR/USD: {eurusd:.4f}

USDT/BOB (Venta): {usdt_bob}

Referencial (Venta): {referencial}
"""

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

server = smtplib.SMTP_SSL("smtp.gmail.com", 465)

server.login(sender, password)

server.sendmail(sender, recipient, msg.as_string())

server.quit()

print("Email sent successfully.")
