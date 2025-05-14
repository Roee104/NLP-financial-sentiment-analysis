#!/usr/bin/env python3
"""
sample_10k.py
-------------
Create a *deterministic* 10 000-article subset from the full
`data/news_segmented.jsonl.gz`, using reservoir sampling with a fixed RNG
seed.  Re-run at any time and you will get **exactly the same 10 000 rows**,
so the dev-gold set and the evaluation script always match.

Usage
-----
    python scripts/sample_10k.py                           # default 10 k
    python scripts/sample_10k.py --k 5000 --seed 123       # other size
    python scripts/sample_10k.py --in  myfile.jsonl.gz \
                                 --out data/sample.jsonl.gz
"""

from __future__ import annotations
import gzip, random, argparse, pathlib
from tqdm.auto import tqdm


def reservoir_sample(in_path: pathlib.Path,
                     out_path: pathlib.Path,
                     k: int = 10_000,
                     seed: int = 42,
                     total_hint: int | None = None) -> None:
    """
    Stream `in_path`, keep a reservoir of size *k*, then write to `out_path`.
    Deterministic because we pass an explicit RNG seed.
    """
    rnd = random.Random(seed)
    reservoir: list[str] = []

    opener = gzip.open if in_path.suffix == ".gz" else open
    with opener(in_path, "rt", encoding="utf-8") as fin:
        for i, line in enumerate(tqdm(fin, desc=f"Sampling {k:,}",
                                      total=total_hint)):
            if i < k:
                reservoir.append(line)
            else:
                j = rnd.randint(0, i)
                if j < k:
                    reservoir[j] = line

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(out_path, "wt", encoding="utf-8") as fout:
        fout.writelines(reservoir)

    print(f"✅ Wrote exactly {k:,} articles → {out_path}")


def cli():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in",  dest="inp",
                    default="data/news_segmented.jsonl.gz",
                    help="Full segmented corpus (.jsonl or .jsonl.gz)")
    ap.add_argument("--out", dest="outp",
                    default="data/news_segmented_10k.jsonl.gz",
                    help="Destination sample file")
    ap.add_argument("--k", type=int, default=10_000,
                    help="Number of rows to sample (default 10 000)")
    ap.add_argument("--seed", type=int, default=42,
                    help="Random seed (deterministic sample)")
    args = ap.parse_args()

    reservoir_sample(pathlib.Path(args.inp),
                     pathlib.Path(args.outp),
                     k=args.k,
                     seed=args.seed)


if __name__ == "__main__":
    cli()
