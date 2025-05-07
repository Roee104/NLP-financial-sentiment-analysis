#!/usr/bin/env python3
import gzip, json, re, csv
from pathlib import Path
import pandas as pd

# —————— CONFIG ——————
# 1) Input & output paths
IN_FILE  = "data/news_segmented.jsonl.gz"
OUT_FILE = "data/news_checked.jsonl.gz"
LOG_FILE = "logs/bad_tickers.log"

# 2) Load your master ticker list
ticker_df = pd.read_csv("data/ticker2sector.csv")
ALL_TICKERS = set(ticker_df["ticker"])  # e.g. {'AAPL','MSFT',...}

# 3) Build a regex to find any valid ticker in text
pattern = re.compile(r"\b(" + "|".join(map(re.escape, ALL_TICKERS)) + r")\b", re.IGNORECASE)

# 4) Any words you never want to treat as tickers
MANUAL_EXCLUDE = {"A"}  # e.g. single-letter “A”

# Make sure the logs directory exists
Path("logs").mkdir(exist_ok=True)

with gzip.open(IN_FILE, "rt", encoding="utf-8") as fin, \
     gzip.open(OUT_FILE, "wt", encoding="utf-8") as fout, \
     open(LOG_FILE, "w", encoding="utf-8") as log:

    for line in fin:
        rec = json.loads(line)
        text = (rec["headline"] + " " + rec["body"]).upper()

        # 1) Keep only tickers that appear in text
        good = [t for t in rec["tickers"] 
                if pattern.search(text) and t not in MANUAL_EXCLUDE]

        # 2) If none remain, try extracting all possible tickers from text
        if not good:
            found = set(pattern.findall(text))
            found -= MANUAL_EXCLUDE
            good = sorted(found)

        # 3) Log any still-empty lists for manual review
        if not good:
            log.write(f"{rec['date']} | orig={rec['tickers']} | head={rec['headline'][:50]}...\n")

        # 4) Replace and write out
        rec["tickers"] = good
        fout.write(json.dumps(rec, ensure_ascii=False) + "\n")

print("✅ Done — bad tickers filtered and recovered. See", OUT_FILE, "and log in", LOG_FILE)
