import requests
import csv
import json
import os
from datetime import datetime, date
from statistics import mean

DATA_FILE = "fx_history.csv"
JSON_FILE = "fx.json"

print("Starting FX update script...")

# --------------------------------------------------
# Helpers
# --------------------------------------------------

def r2(x):
    return round(float(x), 2)

def today():
    return date.today().isoformat()

def get(row, *keys):
    """Return first existing key from CSV row"""
    for k in keys:
        if k in row and row[k] != "":
            return float(row[k])
    raise KeyError(f"None of keys found: {keys}")

# --------------------------------------------------
# Data sources
# --------------------------------------------------

def get_eur_usd():
    r = requests.get("https://open.er-api.com/v6/latest/EUR", timeout=15)
    r.raise_for_status()
    return r.json()["rates"]["USD"]

def get_usdt_bob_parallel():
    url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
    payload = {
        "page": 1,
        "rows": 5,
        "tradeType": "SELL",
        "asset": "USDT",
        "fiat": "BOB",
        "countries": [],
        "proMerchantAds": False
    }

    r = requests.post(url, json=payload, timeout=20)
    r.raise_for_status()
    return r.json()["data"][0]["adv"]["price"]

def get_bcb_valor_referencial():
    url = "https://bcb.cucu.bo/api/v1/tc/usd"
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    return r.json()["tc_referencial_usd"]["venta"]

# --------------------------------------------------
# Fetch current values
# --------------------------------------------------

eurusd = r2(get_eur_usd())
parallel = r2(get_usdt_bob_parallel())
referencial = r2(get_bcb_valor_referencial())

print("EUR/USD:", eurusd)
print("USD/BOB Parallel:", parallel)
print("USD/BOB Referencial:", referencial)

# --------------------------------------------------
# Store CSV history
# --------------------------------------------------

csv_exists = os.path.isfile(DATA_FILE)

with open(DATA_FILE, "a", newline="") as f:
    writer = csv.writer(f)

    if not csv_exists:
        writer.writerow([
            "date",
            "eurusd",
            "usd_bob_parallel",
            "usd_bob_referencial"
        ])

    writer.writerow([
        today(),
        eurusd,
        parallel,
        referencial
    ])

# --------------------------------------------------
# Weekly / Monthly averages (BACKWARD COMPATIBLE)
# --------------------------------------------------

def same_week(d1, d2):
    return d1.isocalendar()[:2] == d2.isocalendar()[:2]

today_dt = date.today()
month_prefix = today_dt.strftime("%Y-%m")

week = []
month = []

with open(DATA_FILE, newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        d = datetime.fromisoformat(row["date"]).date()

        if same_week(d, today_dt):
            week.append(row)
        if row["date"].startswith(month_prefix):
            month.append(row)

weekly_avg = {
    "eurusd": r2(mean(
        get(r, "eurusd", "EUR_USD") for r in week
    )),
    "parallel": r2(mean(
        get(r, "usd_bob_parallel", "USD_BOB_PARALLEL") for r in week
    )),
    "referencial": r2(mean(
        get(r, "usd_bob_referencial", "USD_BOB_REFERENCIAL") for r in week
    )),
}

monthly_avg = {
    "eurusd": r2(mean(
        get(r, "eurusd", "EUR_USD") for r in month
    )),
    "parallel": r2(mean(
        get(r, "usd_bob_parallel", "USD_BOB_PARALLEL") for r in month
    )),
    "referencial": r2(mean(
        get(r, "usd_bob_referencial", "USD_BOB_REFERENCIAL") for r in month
    )),
}

# --------------------------------------------------
# Output JSON for iPhone widget
# --------------------------------------------------

output = {
    "updated": datetime.now().strftime("%Y-%m-%d %H:%M"),

    "today": {
        "EUR/USD": eurusd,
        "USD/BOB Parallel": parallel,
        "USD/BOB Referencial": referencial
    },

    "weekly_avg": {
        "EUR/USD": weekly_avg["eurusd"],
        "USD/BOB Parallel": weekly_avg["parallel"],
        "USD/BOB Referencial": weekly_avg["referencial"]
    },

    "monthly_avg": {
        "EUR/USD": monthly_avg["eurusd"],
        "USD/BOB Parallel": monthly_avg["parallel"],
        "USD/BOB Referencial": monthly_avg["referencial"]
    }
}

with open(JSON_FILE, "w") as f:
    json.dump(output, f, indent=2)

print("fx.json generated successfully")
