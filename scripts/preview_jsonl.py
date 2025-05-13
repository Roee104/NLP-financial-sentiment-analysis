import gzip
import json

# with gzip.open('data/news_cleaned.jsonl.gz', 'rt', encoding='utf-8') as fin:
#     for _ in range(5):
#         print(json.dumps(json.loads(fin.readline()), indent=2, ensure_ascii=False))
import gzip
path = "data/news_tickers_500k.jsonl.gz"
with gzip.open(path, "rt", encoding="utf-8") as f:
    count = sum(1 for _ in f)
print(f"Line count: {count}")
