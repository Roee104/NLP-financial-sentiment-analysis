#!/usr/bin/env python3
import pandas as pd
import ast
import gzip
import json
from pathlib import Path

SRC = "data/nasdaq_exteral_data.csv"
DEST = "data/news_2020_2025.jsonl.gz"
Path("data").mkdir(exist_ok=True)


def clean_and_write(chunk, fout):
    chunk = chunk[
        (chunk["Date"] > "2019-12-31") &
        chunk["Article"].notna() &
        (chunk["Article"].str.strip() != "") &
        chunk["Article_title"].notna() &
        (chunk["Article_title"].str.strip() != "")
    ]

    for _, row in chunk.iterrows():
        raw = row["Stock_symbol"]
        try:
            tickers = ast.literal_eval(raw) if raw.strip().startswith("[") else [
                t.strip() for t in raw.split(",") if t.strip()
            ]
        except Exception:
            tickers = []

        record = {
            "date": row["Date"][:10],
            "headline": row["Article_title"].strip(),
            "body": row["Article"].strip(),
            "tickers": tickers
        }

        fout.write(json.dumps(record, ensure_ascii=False) + "\n")


print("⏳ Streaming and filtering CSV in chunks…")
count = 0
with gzip.open(DEST, "wt", encoding="utf-8") as fout:
    for chunk in pd.read_csv(
        SRC,
        usecols=["Date", "Article_title", "Article", "Stock_symbol"],
        encoding="utf-8-sig",
        dtype=str,
        chunksize=25_000,
        low_memory=False
    ):
        clean_and_write(chunk, fout)
        count += len(chunk)
        print(f"✅ Processed {count:,} rows...")

print(f"🎉 Done! Filtered articles written to {DEST}")
