import gzip
import json
import csv
import os
import yfinance as yf
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

INPUT_PATH = "data/news_tickers.jsonl.gz"
OUTPUT_PATH = "data/ticker2sector.csv"

# -- Utility: Get sector from yfinance


def get_sector_yfinance(ticker):
    try:
        info = yf.Ticker(ticker).info
        return info.get("sector", None)
    except Exception:
        return None

# -- Utility: Get sector from Wikipedia fallback


def get_sector_wikipedia(ticker):
    try:
        url = f"https://en.wikipedia.org/wiki/{ticker}_(ticker_symbol)"
        resp = requests.get(url, timeout=5)
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, "html.parser")
        for row in soup.select("table.infobox tr"):
            if "Sector" in row.text:
                return row.text.split(":")[-1].strip()
    except Exception:
        return None

# -- Step 1: Load all unique tickers


def load_unique_tickers(path):
    unique = set()
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)
            for ticker in data.get("tickers", []):
                unique.add(ticker)
    return sorted(unique)

# -- Step 2: Build mapping


def build_ticker2sector(tickers):
    mapping = {}
    for ticker in tqdm(tickers, desc="Mapping tickers to sectors"):
        sector = get_sector_yfinance(ticker)
        if not sector:
            sector = get_sector_wikipedia(ticker)
        mapping[ticker] = sector if sector else "Unknown"
    return mapping

# -- Step 3: Save to CSV


def save_to_csv(mapping, out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ticker", "sector"])
        for ticker, sector in mapping.items():
            writer.writerow([ticker, sector])


# -- Main
if __name__ == "__main__":
    tickers = load_unique_tickers(INPUT_PATH)
    mapping = build_ticker2sector(tickers)
    save_to_csv(mapping, OUTPUT_PATH)
    print(f"✅ Saved {len(mapping)} entries to {OUTPUT_PATH}")
