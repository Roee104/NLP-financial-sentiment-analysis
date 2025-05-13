#!/usr/bin/env python3
import gzip
import json
import csv
import sys
from collections import Counter
from tqdm import tqdm

"""
Attach sector weights to each article based on ticker→sector map.
Inputs:
  data/news_tickers_500k.jsonl.gz
  data/ticker2sector.csv
Output:
  data/news_tickers_500k_sector.jsonl.gz
"""

# Load ticker→sector map, skipping unknowns
TICKER_SECTOR = {}
with open("data/ticker2sector.csv", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        sec = row["sector"].strip()
        if sec and sec.lower() != "unknown":
            TICKER_SECTOR[row["ticker"]] = sec


def main(inpath, outpath):
    skipped = 0
    with gzip.open(inpath, "rt", encoding="utf-8") as fin, \
            gzip.open(outpath, "wt", encoding="utf-8") as fout:
        for i, line in enumerate(tqdm(fin, desc="Enriching with sectors"), start=1):
            try:
                art = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"[Warning] skipping line {i}: {e}", file=sys.stderr)
                skipped += 1
                continue

            secs = [TICKER_SECTOR.get(tk) for tk in art.get("tickers", [])]
            secs = [s for s in secs if s]
            cnt = Counter(secs)
            total = sum(cnt.values()) or 1
            art["sectors"] = {s: cnt[s]/total for s in cnt}
            fout.write(json.dumps(art, ensure_ascii=False) + "\n")

    if skipped:
        print(f"⚠️ Skipped {skipped} malformed lines.", file=sys.stderr)
    print(f"✅ Wrote enriched articles to {outpath}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: enrich_articles.py <in.jsonl.gz> <out.jsonl.gz>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
