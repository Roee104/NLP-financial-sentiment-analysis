#!/usr/bin/env python3
"""Randomly sample 200 articles from news_final_10k.jsonl.gz"""
import gzip
import json
import random
import pathlib

SRC = pathlib.Path("data/news_final_10k.jsonl.gz")
OUT = pathlib.Path("data/dev_sample_200.jsonl")

records = [json.loads(l) for l in gzip.open(SRC, "rt")]
sample = random.sample(records, 200)

with OUT.open("w", encoding="utf-8") as fout:
    for rec in sample:
        fout.write(json.dumps(rec, ensure_ascii=False) + "\n")

print("✅ wrote", OUT)
