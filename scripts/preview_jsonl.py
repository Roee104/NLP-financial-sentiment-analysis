import gzip
import json

with gzip.open('data/news_cleaned.jsonl.gz', 'rt', encoding='utf-8') as fin:
    for _ in range(5):
        print(json.dumps(json.loads(fin.readline()), indent=2, ensure_ascii=False))
