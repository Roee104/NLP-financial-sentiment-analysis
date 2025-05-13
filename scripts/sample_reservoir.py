#!/usr/bin/env python3
import gzip
import random
from pathlib import Path

"""
Reservoir‐sample exactly 500 000 lines from the full 1 500 000‐line
file, streaming in constant memory.
"""
IN = Path("data/news_segmented.jsonl.gz")
OUT = Path("data/news_segmented_500k.jsonl.gz")
K = 500_000

reservoir = []

with gzip.open(IN, "rt", encoding="utf-8") as fin:
    for i, line in enumerate(fin):
        if i < K:
            reservoir.append(line)
        else:
            j = random.randint(0, i)
            if j < K:
                reservoir[j] = line

with gzip.open(OUT, "wt", encoding="utf-8") as fout:
    for line in reservoir:
        fout.write(line)

print(f"✅ Reservoir‐sampled {K} lines → {OUT}")
