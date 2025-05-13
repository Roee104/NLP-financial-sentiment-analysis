# scripts/inspect_tickers.py
import gzip
import json
for i, line in enumerate(gzip.open("data/news_tickers_small.jsonl.gz", "rt", encoding="utf-8")):
    art = json.loads(line)
    print(art["headline"])
    print(" →", art["tickers"])
    if i >= 9:
        break
