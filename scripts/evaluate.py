#!/usr/bin/env python3
"""
evaluate.py  (NEW SCHEMA)
Compare model predictions (news_final_10k…) vs gold (dev_gold_200.jsonl).

Assumes both files have top-level keys:
  headline_summary, overall.{label,confidence}

Outputs:
  results/overall_report.csv
  results/confusion_matrix.png
  results/ece.txt
"""

from __future__ import annotations
import gzip
import json
import pathlib
import argparse
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.metrics import classification_report, confusion_matrix

LABELS = ["NEG", "NEU", "POS"]
OUTDIR = pathlib.Path("results")
OUTDIR.mkdir(exist_ok=True)


def load(path: pathlib.Path):
    op = gzip.open if path.suffix == ".gz" else open
    with op(path, "rt", encoding="utf-8") as f:
        for line in f:
            yield json.loads(line)


def ece(probs, correct, bins: int = 10):
    bins = np.linspace(0, 1, bins + 1)
    tot = 0
    for lo, hi in zip(bins[:-1], bins[1:]):
        idx = [i for i, p in enumerate(probs) if lo <= p < hi]
        if not idx:
            continue
        acc = np.mean([correct[i] for i in idx])
        conf = np.mean([probs[i] for i in idx])
        tot += abs(acc - conf) * len(idx) / len(probs)
    return tot


def main(pred_path: str, gold_path: str):
    pred = {r["headline_summary"]: r for r in load(pathlib.Path(pred_path))}
    gold = {r["headline_summary"]: r for r in load(pathlib.Path(gold_path))}
    shared = pred.keys() & gold.keys()
    if not shared:
        raise SystemExit("No overlapping headlines between pred and gold!")

    y_true, y_pred, confs = [], [], []
    for h in shared:
        y_true.append(gold[h]["overall"]["label"])
        y_pred.append(pred[h]["overall"]["label"])
        confs.append(pred[h]["overall"]["confidence"] / 100)

    report = classification_report(
        y_true, y_pred, labels=LABELS, output_dict=True
    )
    pd.DataFrame(report).T.to_csv(
        OUTDIR / "overall_report.csv", float_format="%.3f")

    cm = confusion_matrix(y_true, y_pred, labels=LABELS, normalize="true")
    sns.heatmap(cm, annot=True, cmap="Blues",
                xticklabels=LABELS, yticklabels=LABELS, fmt=".2f")
    plt.title("Normalized Confusion Matrix")
    plt.xlabel("Pred")
    plt.ylabel("Gold")
    plt.tight_layout()
    plt.savefig(OUTDIR / "confusion_matrix.png", dpi=200)
    plt.close()

    correct_bin = [1 if a == b else 0 for a, b in zip(y_true, y_pred)]
    (OUTDIR /
     "ece.txt").write_text(f"ECE overall = {ece(confs, correct_bin):.4f}\n")

    print("✅ metrics written to", OUTDIR)


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("pred")
    a.add_argument("gold")
    args = a.parse_args()
    main(args.pred, args.gold)
