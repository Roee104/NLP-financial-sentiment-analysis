#!/usr/bin/env python3
"""
aggregate_sentiment.py
----------------------
Combine sentence‑level FinBERT scores + sector weights into the
final article‑level JSON schema expected by downstream tools.

Input  : JSONL(.gz) produced by `sentiment_inference.py`, where each record has
          - article_id, published, headline, sentences
          - sectors  : {"Technology": 0.58, ...}    (weights sum≈1)
          - sentiments: [ {"label":"NEG","confidence":82}, ... ]  (len == sentences)

Output : JSONL.GZ with keys
          {
            "article_id": "...",
            "published" : "...",
            "headline_summary": "headline without <HEADLINE>",
            "overall" : {"label":"NEG", "confidence":82.3},
            "sectors_summary": {
                "Technology": {"weight":0.58, "label":"NEG", "confidence":80.1},
                ...
            }
          }

The script currently uses **simple majority vote** for labels and the
mean confidence of sentences that have that label. A more refined
mapping (e.g. weighting by sector‑specific sentences) can be plugged in later.
"""

from __future__ import annotations
import gzip
import json
import sys
import argparse
import logging
from collections import Counter, defaultdict
from statistics import mean
from pathlib import Path
from typing import Dict, List

LABEL_ORDER = ["NEG", "NEU", "POS"]  # tie‑break preference

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def majority_label(labels: List[str]) -> str:
    """Return the most common label with tie‑break using LABEL_ORDER."""
    counts = Counter(labels)
    # sort by count desc then LABEL_ORDER preference
    sorted_items = sorted(
        counts.items(), key=lambda kv: (-kv[1], LABEL_ORDER.index(kv[0])))
    return sorted_items[0][0]


def aggregate_article(art: dict) -> dict:
    """Aggregate one article dict into final schema."""
    labels = [s["label"] for s in art["sentiments"]]
    confidences = [s["confidence"] for s in art["sentiments"]]
    overall_lbl = majority_label(labels)
    overall_conf = round(mean(c for l, c in zip(
        labels, confidences) if l == overall_lbl), 2)

    sectors_summary: Dict[str, dict] = {}
    for sector, weight in art["sectors"].items():
        sectors_summary[sector] = {
            "weight": round(weight, 4),
            "label": overall_lbl,              # TODO: refine per‑sector label
            "confidence": overall_conf         # TODO: refine per‑sector conf
        }

    headline_summary = art["sentences"][0].replace(" <HEADLINE>", "")

    return {
        "date": art.get("date"),
        "published": art.get("published"),
        "headline_summary": headline_summary,
        "overall": {"label": overall_lbl, "confidence": overall_conf},
        "tickers": art.get("tickers", []),
        "sectors_summary": sectors_summary,
    }


def run(in_path: Path, out_path: Path) -> None:
    opener = gzip.open if in_path.suffix == ".gz" else open
    with opener(in_path, "rt", encoding="utf-8") as fin, gzip.open(out_path, "wt", encoding="utf-8") as fout:
        for line in fin:
            art = json.loads(line)
            agg = aggregate_article(art)
            fout.write(json.dumps(agg, ensure_ascii=False) + "\n")
    logging.info("✅ Aggregated sentiment → %s", out_path)


def cli():
    p = argparse.ArgumentParser(
        description="Aggregate sentence-level sentiment to article-level JSONL.GZ")
    p.add_argument("input", type=Path,
                   help="Input JSONL(.gz) from sentiment_inference.py")
    p.add_argument("output", type=Path, help="Output aggregated JSONL.gz")
    args = p.parse_args()
    run(args.input, args.output)


if __name__ == "__main__":
    cli()
