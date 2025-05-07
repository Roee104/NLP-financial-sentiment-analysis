#!/usr/bin/env python3
"""
clean_tickers.py
    Filter / recover tickers so every article’s tickers actually appear in its text.
    Fixes false positives like English words that slipped through the old regex.

Run:
    python scripts/clean_tickers.py
"""

import gzip
import json
import re
from pathlib import Path
import pandas as pd

# ---------- Paths ----------
IN_FILE = "data/news_segmented.jsonl.gz"
OUT_FILE = "data/news_cleaned.jsonl.gz"
LOG_FILE = "logs/clean_tickers.log"

# ---------- Load master ticker list ----------
ticker_df = pd.read_csv("data/ticker2sector.csv", dtype=str)
ALL_TICKERS = set(ticker_df["ticker"].dropna())

# ---------- Compile regexes ----------
# 1) Ticker in parentheses (e.g. "(AAPL)")
paren_pattern = re.compile(
    r"\(\s*(" + "|".join(map(re.escape, ALL_TICKERS)) + r")\s*\)"
)

# 2) Whole‑word ticker search, **case‑sensitive**
full_pattern = re.compile(
    r"\b(" + "|".join(map(re.escape, ALL_TICKERS)) + r")\b"
)

# ---------- Manual exclusions ----------
MANUAL_EXCLUDE = {"A"}        # single‑letter 'A' often English article

# ---------- Ensure log dir ----------
Path("logs").mkdir(exist_ok=True)

n_in, n_out, n_empty = 0, 0, 0

with gzip.open(IN_FILE, "rt", encoding="utf-8") as fin, \
        gzip.open(OUT_FILE, "wt", encoding="utf-8") as fout, \
        open(LOG_FILE, "w", encoding="utf-8") as log:

    for line in fin:
        n_in += 1
        rec = json.loads(line)
        text = f"{rec['headline']} {rec['body']}"

        # ----- Step 1: Parentheses heuristic -----
        found = paren_pattern.findall(text)
        found = [t for t in found if t not in MANUAL_EXCLUDE]

        # ----- Step 2: Filter metadata tickers -----
        if not found:
            kept = [
                t for t in rec["tickers"]
                if full_pattern.search(text) and t not in MANUAL_EXCLUDE
            ]
            found = kept

        # ----- Step 3: Full‑text recovery (case‑sensitive) -----
        if not found:
            matches = {
                m.group(1) for m in full_pattern.finditer(text)
                if len(m.group(1)) <= 5              # length guard
                and m.group(1) not in MANUAL_EXCLUDE
            }
            found = sorted(matches)

        # ----- Step 4: Log if still empty -----
        if not found:
            n_empty += 1
            log.write(
                f"{rec['date']} | orig={rec['tickers']} | "
                f"headline={rec['headline'][:60]}...\n"
            )

        rec["tickers"] = found
        fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
        n_out += 1

print(
    f"✅ Cleaned {n_out}/{n_in} articles. Empty‑ticker rows logged: {n_empty}")
print(f"   Output written to {OUT_FILE}")
