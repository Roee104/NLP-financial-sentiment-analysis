#!/usr/bin/env python3
"""
spot_check.py  (with TICKERS column)
------------------------------------
(1)  python spot_check.py
        → data/spot_check_20.tsv  (20 random rows)

(2)  Fill 'gold_overall' and/or 'gold_sectors_json', then:

        python spot_check.py --eval
"""

from __future__ import annotations
import argparse, csv, json, random, pathlib

DEV = pathlib.Path("data/dev_gold_200.jsonl")
OUT = pathlib.Path("data/spot_check_20.tsv")


def sample(n: int = 20):
    records = [json.loads(l) for l in open(DEV, encoding="utf-8")]
    picks = random.sample(records, n)

    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(
            [
                "headline",
                "overall_label",
                "tickers",          # NEW
                "top_sector",
                "sectors_summary",
                "gold_overall",
                "gold_sectors_json",
            ]
        )
        for r in picks:
            sectors = r["sectors_summary"]
            top_sector = max(sectors, key=lambda s: sectors[s]["weight"])
            ticker_str = ",".join(r.get("tickers", []))
            w.writerow(
                [
                    r["headline_summary"],
                    r["overall"]["label"],
                    ticker_str,
                    top_sector,
                    json.dumps(sectors, ensure_ascii=False),
                    "",
                    "",
                ]
            )
    print(f"✅ wrote {n}-row TSV → {OUT}")


def evaluate():
    total = correct = 0
    with OUT.open("r", encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            if row["gold_overall"].strip():
                total += 1
                if row["gold_overall"].strip().upper() == row["overall_label"]:
                    correct += 1
    if total == 0:
        print("⚠️  No rows have gold labels filled in.")
    else:
        print(f"Manual overall accuracy on {total} rows = {correct/total:.2%}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--eval", action="store_true")
    args = ap.parse_args()
    evaluate() if args.eval else sample()
