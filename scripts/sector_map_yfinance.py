import yfinance as yf
import json
import gzip
import tqdm

# 1. Collect all unique tickers from the segmented dataset
tickers = set()
with gzip.open("data/news_segmented.jsonl.gz", "rt", encoding="utf-8") as f:
    for line in f:
        record = json.loads(line)
        tickers.update(record.get("tickers", []))

# 2. Query yfinance for each ticker
sector_map = {}
for ticker in tqdm.tqdm(sorted(tickers)):
    try:
        sector = yf.Ticker(ticker).info.get("sector")
        sector_map[ticker] = sector  # May be None
    except Exception:
        pass  # Skip broken tickers or lookups

# 3. Save the partial map
with open("data/sector_map_raw.json", "w", encoding="utf-8") as f:
    json.dump(sector_map, f, indent=2)
