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

# Default values

referencial = "NOT FOUND"
usdt_bob = "NOT FOUND"

# Find all tables

tables = soup.find_all("table")

print(f"Found {len(tables)} tables")

for table in tables:

    rows = table.find_all("tr")

    for row in rows:

        cols = row.find_all(["td", "th"])

        values = [c.get_text(strip=True) for c in cols]

        print(values)

        # Look for Compra row with at least 3 columns

        if len(values) >= 3 and "Compra" in values[0]:

            referencial = values[1]
            usdt_bob = values[2]

            print("MATCH FOUND")

            break

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
