#!/usr/bin/env python3
"""
Compare model output vs. gold dev set.
Outputs CSV + confusion-matrix PNG + calibration score.
"""
import gzip
import json
import sys
import pathlib
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix
import seaborn as sns
import matplotlib.pyplot as plt


def load(path):
    op = gzip.open if str(path).endswith(".gz") else open
    with op(path, "rt") as f:
        return [json.loads(l) for l in f]


def ece(probs, labels, n=10):
    bins = np.linspace(0, 1, n+1)
    idx = np.digitize(probs, bins)-1
    e = 0
    for i in range(n):
        m = idx == i
        if not m.any():
            continue
        e += abs(labels[m].mean()-probs[m].mean()) * m.mean()
    return e


def main(pred, gold, outdir="results"):
    out = pathlib.Path(outdir)
    out.mkdir(exist_ok=True)
    p = {a["headline_summary"]: a for a in load(pred)}
    g = {a["headline_summary"]: a for a in load(gold)}

    y_true, y_pred, conf = [], [], []
    for h, rec in g.items():
        y_true.append(rec["gold"]["overall"])
        y_pred.append(p[h]["overall"]["label"])
        conf.append(p[h]["overall"]["confidence"]/100)

    rep = classification_report(y_true, y_pred, output_dict=True, digits=2)
    pd.DataFrame(rep).T.to_csv(out/"overall_report.csv")
    cm = confusion_matrix(y_true, y_pred, labels=["NEG", "NEU", "POS"])
    sns.heatmap(cm, annot=True, fmt="d", cbar=False,
                xticklabels=["NEG", "NEU", "POS"],
                yticklabels=["NEG", "NEU", "POS"])
    plt.title("Overall Confusion")
    plt.savefig(out/"confusion_matrix.png", dpi=150, bbox_inches="tight")
    plt.close()
    e = ece(np.array(conf), np.array([p == t for p, t in zip(y_pred, y_true)]))
    (out/"ece.txt").write_text(str(e))
    print("Macro F1:", rep["macro avg"]["f1-score"], "ECE:", round(e, 3))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: evaluate.py <pred.gz> <gold.jsonl>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
