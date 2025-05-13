#!/usr/bin/env python3
import gzip
from pathlib import Path
from tqdm.auto import tqdm

IN   = Path("data/news_segmented.jsonl.gz")
OUT  = Path("data/news_segmented_10k.jsonl.gz")
STEP = 150  # 1 500 000 / 10 000

# (Optional) set total to speed up tqdm
TOTAL = 1500000

with gzip.open(IN, "rt", encoding="utf-8") as fin, \
     gzip.open(OUT,"wt", encoding="utf-8") as fout:
    for i, line in enumerate(tqdm(fin, desc="Sampling 10k", total=TOTAL)):
        if i % STEP == 0:
            fout.write(line)

print(f"✅ Wrote ~{(i//STEP)+1:,} lines to {OUT}")
