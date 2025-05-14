#!/usr/bin/env python3
"""
build_dev_sample.py
-------------------
Draw a deterministic sample of *k* articles **with full sentences**
from the 10 k segmented file.  This sample becomes the input for
GPT-4o self-labelling (dev-gold).

Usage
-----
    python scripts/build_dev_sample.py             # k = 200
    python scripts/build_dev_sample.py --k 300     # different size
"""

from __future__ import annotations

import argparse
import gzip
import json
import pathlib
import random
from typing import List, Dict, Any

# ---------------------------------------------------------------------------

# <- contains "sentences"
SRC = pathlib.Path("data/news_segmented_10k.jsonl.gz")
OUT = pathlib.Path("data/dev_sample_200.jsonl")

# ---------------------------------------------------------------------------


def load_jsonl_gz(path: pathlib.Path) -> List[Dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def main(k: int = 200, seed: int = 42) -> None:
    if not SRC.exists():
        raise SystemExit(f"❌ Source file not found: {SRC}")

    random.seed(seed)
    records = load_jsonl_gz(SRC)
    if k > len(records):
        raise SystemExit(f"❌ k={k} larger than dataset ({len(records)})")

    sample = random.sample(records, k)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as fout:
        for rec in sample:
            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"✅ wrote {k} rows → {OUT}")


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Create deterministic dev sample")
    ap.add_argument("--k", type=int, default=200,
                    help="sample size (default 200)")
    ap.add_argument("--seed", type=int, default=42, help="RNG seed")
    args = ap.parse_args()
    main(args.k, args.seed)
