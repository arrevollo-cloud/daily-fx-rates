import requests
import csv
import json
import os
from datetime import datetime, date
from statistics import mean

DATA_FILE = "fx_history.csv"
JSON_FILE = "fx.json"

print("Starting FX update script...")

#fix main

# ==================================================
# EUR / USD
# ==================================================
def get_eur_usd():
    r = requests.get("https://open.er-api.com/v6/latest/EUR", timeout=15)
    r.raise_for_status()
    return float(r.json()["rates"]["USD"])


# ==================================================
# USD / BOB Parallel (Binance P2P proxy, SELL)
# ==================================================
def get_usdt_bob_parallel():
    url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
    payload = {
        "page": 1,
        "rows": 10,
        "tradeType": "SELL",
        "asset": "USDT",
        "fiat": "BOB",
        "countries": [],
        "proMerchantAds": False
    }

    r = requests.post(url, json=payload, timeout=20)
    r.raise_for_status()
    return float(r.json()["data"][0]["adv"]["price"])


# ==================================================
# USD / BOB — BCB Valor Referencial (Venta)
# ==================================================
def get_bcb_valor_referencial_venta():
    url = "https://bcb.cucu.bo/api/v1/tc/usd"
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    return float(r.json()["tc_referencial_usd"]["venta"])


# ==================================================
# Fetch current rates
# ==================================================
eurusd = get_eur_usd()
parallel = get_usdt_bob_parallel()
referencial = get_bcb_valor_referencial_venta()

print("EUR/USD:", eurusd)
print("USD/BOB Parallel (Binance proxy):", parallel)
print("USD/BOB Referencial (BCB venta):", referencial)


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
            "USD_BOB_PARALLEL",
            "USD_BOB_REFERENCIAL"
        ])

    writer.writerow([
        today,
        round(eurusd, 4),
        round(parallel, 2),
        round(referencial, 2)
    ])


# ==================================================
# Weekly & Monthly averages
# ==================================================
def same_week(d1, d2):
    return d1.isocalendar()[:2] == d2.isocalendar()[:2]

today_dt = date.today()
this_month = today_dt.strftime("%Y-%m")

weekly = []
monthly = []

with open(DATA_FILE, newline="") as f:
    reader = csv.DictReader(f)
    for row in reader:
        d = datetime.fromisoformat(row["date"]).date()

        if same_week(d, today_dt):
            weekly.append(row)
        if row["date"].startswith(this_month):
            monthly.append(row)

weekly_avg = {
    "eurusd": mean(float(r["EUR_USD"]) for r in weekly),
    "parallel": mean(float(r["USD_BOB_PARALLEL"]) for r in weekly),
    "referencial": mean(float(r["USD_BOB_REFERENCIAL"]) for r in weekly),
}

monthly_avg = {
    "eurusd": mean(float(r["EUR_USD"]) for r in monthly),
    "parallel": mean(float(r["USD_BOB_PARALLEL"]) for r in monthly),
    "referencial": mean(float(r["USD_BOB_REFERENCIAL"]) for r in monthly),
}


# ==================================================
# Output JSON for iPhone widget
# ==================================================
output = {
    "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "daily": {
        "eurusd": round(eurusd, 5),
        "usd_bob_parallel": parallel,
        "usd_bob_referencial": referencial
    },
    "weekly_avg": {
        "eurusd": round(weekly_avg["eurusd"], 5),
        "usd_bob_parallel": weekly_avg["parallel"],
        "usd_bob_referencial": weekly_avg["referencial"]
    },
    "monthly_avg": {
        "eurusd": round(monthly_avg["eurusd"], 4),
        "usd_bob_parallel": round(monthly_avg["parallel"], 2),
        "usd_bob_referencial": round(monthly_avg["referencial"], 2)
    }
}

