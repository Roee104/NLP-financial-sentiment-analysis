"""
Download NASDAQ + NYSE + AMEX symbol lists from NasdaqTrader
and save a deduplicated master CSV: data/ticker_master.csv
"""

import pandas as pd
import requests
import io
import os
import pathlib
import zipfile
import tempfile

BASE = "https://www.nasdaqtrader.com/dynamic/SymDir/"
FILES = {
    "nasdaq":   "nasdaqlisted.txt",
    "other":    "otherlisted.txt"
}


def fetch_txt(url):
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return resp.text


symbols = []
for key, fname in FILES.items():
    txt = fetch_txt(BASE + fname)
    # last line is a checksum; skip
    content = "\n".join(txt.splitlines()[:-1])
    df = pd.read_csv(io.StringIO(content), sep="|")
    col = "Symbol" if "Symbol" in df.columns else "ACT Symbol"
    symbols.extend(df[col].tolist())

# Deduplicate & sort
master = sorted({s.strip()
                for s in symbols if isinstance(s, str) and s.strip()})
path = pathlib.Path("data/ticker_master.csv")
path.parent.mkdir(exist_ok=True)
pd.Series(master, name="symbol").to_csv(path, index=False)
print(f"Wrote {len(master)} tickers to {path}")
