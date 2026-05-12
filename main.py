import requests
import os
import time
import csv
import json

from datetime import datetime, date
from statistics import mean

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from webdriver_manager.chrome import ChromeDriverManager


DATA_FILE = "fx_history.csv"

print("Starting FX update script...")

# ==================================================
# EUR / USD (API)
# ==================================================
print("Fetching EUR/USD...")

fx = requests.get("https://open.er-api.com/v6/latest/EUR", timeout=15).json()
eurusd = fx["rates"]["USD"]

print("EUR/USD:", eurusd)


# ==================================================
# Selenium setup
# ==================================================
print("Launching headless browser...")

options = Options()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

driver.get("https://dolarboliviahoy.com/")
wait = WebDriverWait(driver, 20)

print("Page requested, waiting for content...")


# ==================================================
# Extract Referencial table (robust + fallback)
# ==================================================
referencial = None
usdt_bob = None

try:
    # --- Primary selector (robust, case-insensitive) ---
    table = wait.until(
        EC.presence_of_element_located((
            By.XPATH,
            "//h2[contains(translate(., "
            "'ABCDEFGHIJKLMNOPQRSTUVWXYZ', "
            "'abcdefghijklmnopqrstuvwxyz'), "
            "'referencial')]/following::table[1]"
        ))
    )

except TimeoutException:
    print("Primary selector failed, trying fallback...")

    try:
        # --- Fallback selector: any table containing 'Compra' ---
        table = wait.until(
            EC.presence_of_element_located((
                By.XPATH,
                "//table[.//td[contains(., 'Compra')]]"
            ))
        )
    except TimeoutException:
        print("ERROR: Referencial table not found. Aborting run.")
        driver.save_screenshot("selenium_error.png")
        driver.quit()
        raise SystemExit(1)


rows = table.find_elements(By.TAG_NAME, "tr")

for row in rows:
    cells = row.find_elements(By.TAG_NAME, "td")
    if len(cells) < 3:
        continue

    label = cells[0].text.strip()

    if label == "Compra":
        referencial = float(cells[1].text.replace(",", "."))
        usdt_bob = float(cells[2].text.replace(",", "."))
        break

driver.quit()

if referencial is None or usdt_bob is None:
    print("ERROR: Failed to extract Compra values.")
    raise SystemExit(1)

print("Referencial USD/BOB:", referencial)
print("USDT/BOB:", usdt_bob)


# ==================================================
# Store historical CSV
# ==================================================
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
        round(usdt_bob, 2),
        round(referencial, 2)
    ])

print("Historical CSV updated.")


# ==================================================
# Weekly averages
# ==================================================
def same_week(d1, d2):
    return d1.isocalendar()[:2] == d2.isocalendar()[:2]

today_dt = date.today()
weekly = []

with open(DATA_FILE, newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        row_date = datetime.fromisoformat(row["date"]).date()
        if same_week(row_date, today_dt):
            weekly.append(row)

weekly_avg = {
    "EUR": mean(float(r["EUR_USD"]) for r in weekly),
    "PAR": mean(float(r["PARALELO_USD_BOB"]) for r in weekly),
    "REF": mean(float(r["REFERENCIAL_USD_BOB"]) for r in weekly),
}


# ==================================================
# Monthly averages
# ==================================================
this_month = today_dt.strftime("%Y-%m")
monthly = []

with open(DATA_FILE, newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row["date"].startswith(this_month):
            monthly.append(row)

monthly_avg = {
    "EUR": mean(float(r["EUR_USD"]) for r in monthly),
    "PAR": mean(float(r["PARALELO_USD_BOB"]) for r in monthly),
    "REF": mean(float(r["REFERENCIAL_USD_BOB"]) for r in monthly),
}


# ==================================================
# Generate JSON output
# ==================================================
data = {
    "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

    "daily": {
        "eurusd": round(eurusd, 4),
        "usdt_bob": round(usdt_bob, 2),
        "referencial": round(referencial, 2),
    },

    "weekly_avg": {
        "eurusd": round(weekly_avg["EUR"], 4),
        "usdt_bob": round(weekly_avg["PAR"], 2),
        "referencial": round(weekly_avg["REF"], 2),
    },

    "monthly_avg": {
        "eurusd": round(monthly_avg["EUR"], 4),
        "usdt_bob": round(monthly_avg["PAR"], 2),
        "referencial": round(monthly_avg["REF"], 2),
    }
}

with open("fx.json", "w") as f:
    json.dump(data, f, indent=2)

print("fx.json generated successfully")
print(json.dumps(data, indent=2))
