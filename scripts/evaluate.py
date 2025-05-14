#!/usr/bin/env python3
"""
evaluate.py
-----------
Compare pipeline predictions vs. GPT-gold labels
and save:

  • overall_report.csv       (classification report)
  • confusion_matrix.png     (normalised heat-map)
  • ece.txt                  (Expected Calibration Error)

Usage
-----
    python scripts/evaluate.py \
        data/news_final_10k.jsonl.gz \
        data/dev_gold_200.jsonl
"""

from __future__ import annotations

import argparse
import gzip
import json
import pathlib
from collections import defaultdict
from typing import Dict, Iterator, List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.metrics import classification_report, confusion_matrix

LABELS = ["NEG", "NEU", "POS"]
OUTDIR = pathlib.Path("results")
OUTDIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------


def load(path: pathlib.Path) -> Iterator[Dict]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as f:
        for line in f:
            yield json.loads(line)


def expected_calibration_error(
    confidences: List[float], correct: List[int], n_bins: int = 10
) -> float:
    """Equal-width ECE over *n_bins*."""
    bins = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    for lo, hi in zip(bins[:-1], bins[1:]):
        idx = [i for i, p in enumerate(confidences) if lo <= p < hi]
        if not idx:
            continue
        acc = np.mean([correct[i] for i in idx])
        conf = np.mean([confidences[i] for i in idx])
        ece += abs(acc - conf) * len(idx) / len(confidences)
    return ece


# ---------------------------------------------------------------------------


def main(pred_path: str, gold_path: str) -> None:
    pred_file = pathlib.Path(pred_path)
    gold_file = pathlib.Path(gold_path)

    preds = {r["headline_summary"]: r for r in load(pred_file)}
    golds = {r["headline_summary"]: r for r in load(gold_file)}

    shared = preds.keys() & golds.keys()
    if not shared:
        raise SystemExit("❌ No overlapping headline_summary keys!")

    if len(preds) != len(set(preds)):
        print("⚠ duplicate headlines in predictions (keeping last occurrence)")

    y_true, y_pred, conf = [], [], []
    for h in shared:
        y_true.append(golds[h]["overall"]["label"])
        y_pred.append(preds[h]["overall"]["label"])
        conf.append(preds[h]["overall"]["confidence"] / 100)

    # ---------- 1. classification report -------------------------------
    rpt = classification_report(
        y_true, y_pred, labels=LABELS, output_dict=True)
    pd.DataFrame(rpt).T.to_csv(
        OUTDIR / "overall_report.csv", float_format="%.3f")
    print(pd.DataFrame(rpt).T.round(3))

    # ---------- 2. confusion matrix ------------------------------------
    cm = confusion_matrix(y_true, y_pred, labels=LABELS, normalize="true")
    plt.figure(figsize=(4, 3))
    sns.heatmap(
        cm,
        annot=True,
        cmap="Reds",          # light = good, dark = bad
        xticklabels=LABELS,
        yticklabels=LABELS,
        fmt=".2f",
        annot_kws={"size": 9},
    )
    plt.title("Normalised Confusion Matrix")
    plt.xlabel("Predicted")
    plt.ylabel("Gold")
    plt.tight_layout()
    plt.savefig(OUTDIR / "confusion_matrix.png", dpi=200)
    plt.close()

    # ---------- 3. calibration -----------------------------------------
    correct_bin = [1 if a == b else 0 for a, b in zip(y_true, y_pred)]
    ece_val = expected_calibration_error(conf, correct_bin)
    (OUTDIR / "ece.txt").write_text(f"ECE overall = {ece_val:.4f}\n")
    print(f"ECE overall = {ece_val:.4f}")

    print("✅ metrics & plots written to", OUTDIR)


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("pred", help="news_final_10k.jsonl[.gz]")
    ap.add_argument("gold", help="dev_gold_200.jsonl")
    args = ap.parse_args()
    main(args.pred, args.gold)
