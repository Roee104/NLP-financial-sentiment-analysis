# scripts/sample_articles.py
import gzip
import json
from itertools import islice

with gzip.open("data/news_segmented.jsonl.gz", "rt", encoding="utf-8") as fin, \
        gzip.open("data/news_segmented_small.jsonl.gz", "wt", encoding="utf-8") as fout:
    for line in islice(fin, 100):
        fout.write(line)
