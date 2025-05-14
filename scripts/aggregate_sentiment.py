#!/usr/bin/env python3
"""
aggregate_sentiment.py
----------------------
Collapse sentence-level FinBERT predictions + sector weights
into the final article-level JSON schema.

INPUT  : JSONL(.gz) from `sentiment_inference.py`
         Each record has keys
           • date, headline, sentences
           • tickers
           • sectors    : {"Technology": 0.58, ...}         (weights ≈ 1)
           • sentiments : [ {"label":"NEG","confidence":82}, ... ]

OUTPUT : JSONL.GZ 1-line-per-article, keys
           {
             "date": "2023-12-16",
             "headline_summary": "Interesting …",
             "overall": { "label":"NEG", "confidence":82.3 },
             "tickers": ["AAPL", …],
             "sectors_summary": {
                 "Technology": {"weight":0.58, "label":"NEG", "confidence":80.1},
                 …
             }
           }

Scoring rules
-------------
• Overall label = majority vote over sentence labels
  (NEG > NEU > POS as tie-break).
• Overall conf = mean conf of the majority-label sentences.
• Per-sector label = majority vote *restricted to sentences whose
  confidence ≥ 60 and that mention at least one ticker mapped to that
  sector*; if none, fall back to overall label.
• Per-sector confidence = mean of that sector’s winning sentences,
  else overall_conf.
"""

from __future__ import annotations

import argparse
import gzip
import json
import logging
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean
from typing import Dict, List

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

LABEL_ORDER = ["NEG", "NEU", "POS"]  # preference when counts tie
TICKER_RE = re.compile(r"\(([A-Z]{1,5})\)")  # crude “(AAPL)” etc.


# ---------------------------------------------------------------------------#
def majority_label(labels: List[str]) -> str:
    """Most frequent label; break ties using LABEL_ORDER preference."""
    cnt = Counter(labels)
    return sorted(cnt.items(), key=lambda kv: (-kv[1], LABEL_ORDER.index(kv[0])))[0][0]


def sector_from_sent(
    sent: str, ticker2sector: Dict[str, str], fallback: str = "Other"
) -> str:
    """Detect first ticker in sentence and map → sector; else fallback."""
    m = TICKER_RE.search(sent)
    if not m:
        return fallback
    return ticker2sector.get(m.group(1), fallback)


# ---------------------------------------------------------------------------#
def aggregate_article(art: dict, ticker2sector: Dict[str, str]) -> dict:
    # ---------- overall -------------------------------------------------- #
    labels = [s["label"] for s in art["sentiments"]]
    confs = [s["confidence"] for s in art["sentiments"]]

    overall_lbl = majority_label(labels)
    overall_conf = round(mean(c for l, c in zip(labels, confs) if l == overall_lbl), 2)

    # ---------- per-sector vote ----------------------------------------- #
    sector_votes: Dict[str, List[float]] = defaultdict(list)
    for sent, sdict in zip(art["sentences"], art["sentiments"]):
        if sdict["confidence"] < 60:
            continue  # ignore low-confidence lines
        sec = sector_from_sent(sent, ticker2sector)
        sector_votes[sec].append((sdict["label"], sdict["confidence"]))

    sectors_summary: Dict[str, dict] = {}
    for sec, weight in art["sectors"].items():
        if sec in sector_votes:
            lbls, cf = zip(*sector_votes[sec])
            sec_lbl = majority_label(lbls)
            sec_conf = round(mean(c for l, c in zip(lbls, cf) if l == sec_lbl), 2)
        else:
            sec_lbl, sec_conf = overall_lbl, overall_conf
        sectors_summary[sec] = {
            "weight": round(weight, 4),
            "label": sec_lbl,
            "confidence": sec_conf,
        }

    headline_summary = art["sentences"][0].replace(" <HEADLINE>", "")

    return {
        "date": art.get("date"),
        "headline_summary": headline_summary,
        "overall": {"label": overall_lbl, "confidence": overall_conf},
        "tickers": art.get("tickers", []),
        "sectors_summary": sectors_summary,
    }


# ---------------------------------------------------------------------------#
def run(inp: Path, outp: Path, ticker_map: Path):
    # load ticker → sector map once
    t2s = {}
    with open(ticker_map, encoding="utf-8") as f:
        for line in f:
            t, s = line.strip().split(",")
            if t != "ticker":
                t2s[t] = s

    opener = gzip.open if inp.suffix == ".gz" else open
    with opener(inp, "rt", encoding="utf-8") as fin, gzip.open(
        outp, "wt", encoding="utf-8"
    ) as fout:
        for line in fin:
            art = json.loads(line)
            fout.write(json.dumps(aggregate_article(art, t2s), ensure_ascii=False) + "\n")
    logging.info("✅ Aggregated sentiment → %s", outp)


# ---------------------------------------------------------------------------#
if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("input", type=Path, help="news_sentiment_*.jsonl(.gz)")
    p.add_argument("output", type=Path, help="news_final_*.jsonl.gz")
    p.add_argument(
        "--map",
        default="data/ticker2sector.csv",
        help="CSV file produced by build_ticker2sector.py",
    )
    args = p.parse_args()
    if not Path(args.input).exists():
        sys.exit(f"❌ {args.input} not found")
    run(args.input, args.output, Path(args.map))
