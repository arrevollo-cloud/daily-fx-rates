import requests
from bs4 import BeautifulSoup
import re
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import time
import csv
import json
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
# Store Historical CSV
# -------------------------

today = date.today().isoformat()

file_exists = os.path.isfile(DATA_FILE)

with open(DATA_FILE, "a", newline="") as f:
    writer = csv.writer(f)

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

# -------------------------
# Weekly Calculations
# -------------------------

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

# -------------------------
# Monthly Calculations
# -------------------------

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

# -------------------------
# Generate JSON
# -------------------------

data = {
    "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

    "daily": {
        "eurusd": round(float(eurusd), 4),
        "usdt_bob": float(usdt_bob),
        "referencial": float(referencial)
    },

    "weekly_avg": {
        "eurusd": round(weekly_avg["EUR"], 4),
        "usdt_bob": round(weekly_avg["PAR"], 2),
        "referencial": round(weekly_avg["REF"], 2)
    },

    "monthly_avg": {
        "eurusd": round(monthly_avg["EUR"], 4),
        "usdt_bob": round(monthly_avg["PAR"], 2),
        "referencial": round(monthly_avg["REF"], 2)
    }
}

with open("fx.json", "w") as f:
    json.dump(data, f, indent=2)

print("fx.json generated successfully")

print(json.dumps(data, indent=2))
