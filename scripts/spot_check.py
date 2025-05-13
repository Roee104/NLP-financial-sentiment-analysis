#!/usr/bin/env python3
"""
Randomly pick 20 GPT-labelled records for manual verification.
After editing the TSV, run this script again with --eval to compute accuracy.
"""
import random
import json
import csv
import argparse
import pandas as pd
import pathlib

DEV = "data/dev_gold_200.jsonl"
OUT = "data/spot_check_20.tsv"


def sample():
    recs = [json.loads(l) for l in open(DEV)]
    picks = random.sample(recs, 20)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(["headline", "model_overall", "gold_overall",
                    "model_sectors_json", "gold_sectors_json"])
        for r in picks:
            w.writerow([r["headline_summary"],
                        r["gold"]["overall"], "",
                        json.dumps(r["gold"]["sectors"], ensure_ascii=False), ""])
    print("👉 Review and fill gold_* columns in", OUT)


def evaluate():
    df = pd.read_csv(OUT, sep="\t")
    acc = (df["gold_overall"] == df["model_overall"]).mean()
    print(f"Manual overall accuracy on 20 = {acc:.1%}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--eval", action="store_true")
    args = p.parse_args()
    if args.eval:
        evaluate()
    else:
        sample()
