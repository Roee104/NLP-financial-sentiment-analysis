#!/usr/bin/env python3
"""
enrich_articles.py
------------------
Attach sector weights to each article based on a ticker→sector CSV.
The script passes through `date` and `tickers` so later stages can
use them, and writes a new JSONL(.gz) with an added `sectors` dict.

Usage:
    python scripts/enrich_articles.py \
        data/news_tickers_10k.jsonl.gz \
        data/news_tickers_10k_sector.jsonl.gz
"""
import gzip
import json
import csv
import sys
from collections import Counter
from pathlib import Path
from tqdm.auto import tqdm

# ---------------------------------------------------------------------------
# Load ticker→sector map   (skip rows with Unknown)
# ---------------------------------------------------------------------------
TICKER_SECTOR = {}
with open("data/ticker2sector.csv", newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        sec = row["sector"].strip()
        if sec and sec.lower() != "unknown":
            TICKER_SECTOR[row["ticker"]] = sec

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main(inp: str, out: str) -> None:
    skipped = 0
    with gzip.open(inp, "rt", encoding="utf-8") as fin, \
            gzip.open(out, "wt", encoding="utf-8") as fout:
        for i, line in enumerate(tqdm(fin, desc="Enriching with sectors"), 1):
            try:
                art = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"[warn] bad JSON line {i}: {e}", file=sys.stderr)
                skipped += 1
                continue

            # Map tickers → sectors and normalise to weights
            secs = [TICKER_SECTOR.get(tk) for tk in art.get("tickers", [])]
            secs = [s for s in secs if s]
            cnt = Counter(secs)
            tot = sum(cnt.values()) or 1

            enriched = {
                "date": art.get("date"),
                "headline": art.get("headline"),
                "sentences": art["sentences"],
                "tickers": art.get("tickers", []),
                "sectors": {s: cnt[s] / tot for s in cnt}
            }
            fout.write(json.dumps(enriched, ensure_ascii=False) + "\n")

    if skipped:
        print(f"⚠️  skipped {skipped} malformed lines", file=sys.stderr)
    print(f"✅ Wrote enriched articles → {out}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: enrich_articles.py <in.jsonl.gz> <out.jsonl.gz>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
