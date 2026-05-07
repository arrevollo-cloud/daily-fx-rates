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
import csv
from datetime import datetime, date
from statistics import mean


DATA_FILE = "fx_history.csv"

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


today = date.today().isoformat()

file_exists = os.path.isfile(DATA_FILE)

with open(DATA_FILE, "a", newline="") as f:
    writer = csv.writer(f)

    # Write header once
    if not file_exists:
        writer.writerow([
            "date",
            "EUR_USD",
            "PARALELO_USD_BOB",
            "REFERENCIAL_USD_BOB"
        ])

    writer.writerow([
        today,
        round(eurusd, 4),
        float(usdt_bob),
        float(referencial)
    ])

def is_same_week(d1, d2):
    return d1.isocalendar()[:2] == d2.isocalendar()[:2]

today_dt = date.today()

weekly_rows = []

with open(DATA_FILE, newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        row_date = datetime.fromisoformat(row["date"]).date()
        if is_same_week(row_date, today_dt):
            weekly_rows.append({
                "date": row_date.strftime("%a"),
                "EUR": float(row["EUR_USD"]),
                "PAR": float(row["PARALELO_USD_BOB"]),
                "REF": float(row["REFERENCIAL_USD_BOB"])
            })

weekly_avg = {
    "EUR": mean(r["EUR"] for r in weekly_rows),
    "PAR": mean(r["PAR"] for r in weekly_rows),
    "REF": mean(r["REF"] for r in weekly_rows),
}

weekly_table = "Weekly Rates (Mon–Sun)\n"
weekly_table += "Day | EUR/USD | Paralelo USD/BOB | Referencial USD/BOB\n"
weekly_table += "--- | --- | --- | ---\n"

for r in weekly_rows:
    weekly_table += (
        f"{r['date']} | "
        f"{r['EUR']:.4f} | "
        f"{r['PAR']:.2f} | "
        f"{r['REF']:.2f}\n"
    )

weekly_table += (
    f"AVG | "
    f"{weekly_avg['EUR']:.4f} | "
    f"{weekly_avg['PAR']:.2f} | "
    f"{weekly_avg['REF']:.2f}\n"
)

this_month = today_dt.strftime("%Y-%m")

monthly_rows = []

with open(DATA_FILE, newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row["date"].startswith(this_month):
            monthly_rows.append(row)

monthly_avg = {
    "EUR": mean(float(r["EUR_USD"]) for r in monthly_rows),
    "PAR": mean(float(r["PARALELO_USD_BOB"]) for r in monthly_rows),
    "REF": mean(float(r["REFERENCIAL_USD_BOB"]) for r in monthly_rows),
}

monthly_table = "Monthly Average Rates\n"
monthly_table += "EUR/USD | Paralelo USD/BOB | Referencial USD/BOB\n"
monthly_table += "--- | --- | ---\n"
monthly_table += (
    f"{monthly_avg['EUR']:.4f} | "
    f"{monthly_avg['PAR']:.2f} | "
    f"{monthly_avg['REF']:.2f}\n"
)
# -------------------------
# Email Content
# -------------------------

message = f"""
DAILY FX RATES

EUR/USD: {eurusd:.4f}
Paralelo USD/BOB: {usdt_bob}
Referencial USD/BOB: {referencial}

{weekly_table}

{monthly_table}
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


