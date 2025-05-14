#!/usr/bin/env python3
"""
gpt_label_dev.py  – LLM-generate a 200-article dev-gold file
------------------------------------------------------------
Reads 200 sampled records (headline + sentences) and asks GPT-4o-mini to
produce article-level labels in **our final JSON schema**.

✦ Input  : data/dev_sample_200.jsonl
✦ Output : data/dev_gold_200.jsonl
✦ Cost   : ≈ 150 tokens × 200 ≈ $0.15 with gpt-4o-mini
"""

from __future__ import annotations
import os
import sys
import time
import json
from pathlib import Path
from typing import Dict
from tqdm.auto import tqdm
import openai

# ────────────────────────────────────────────────────────────
#  1.  API key
# ────────────────────────────────────────────────────────────
openai.api_key = os.getenv("OPENAI_API_KEY") or sys.exit(
    "❌ OPENAI_API_KEY env var not set"
)

# ────────────────────────────────────────────────────────────
#  2.  System prompt (note: headline_summary == ORIGINAL headline)
# ────────────────────────────────────────────────────────────
SYSTEM_MSG = (
    "You are «FinSent-Inspector», a senior equity-research editor.\n\n"
    "The user supplies a news article in this exact template:\n"
    "HEADLINE: <raw headline text>\n"
    "ARTICLE:\n<full article plain text>\n\n"
    "Return **one** minified JSON object with these keys *only*:\n"
    "{\n"
    '  "date":   <YYYY-MM-DD if clearly stated, else null>,\n'
    '  "published": null,\n'
    '  "headline_summary": <exact headline text, unchanged>,\n'
    '  "overall":  { "label": "NEG|NEU|POS", "confidence": <0-100> },\n'
    '  "tickers": [<uppercase symbols mentioned>],\n'
    '  "sectors_summary": {\n'
    '       <SectorName>: {\n'
    '           "weight": <float 0-1, 4 dp>,\n'
    '           "label":  "NEG|NEU|POS",\n'
    '           "confidence": <0-100>\n'
    '       }, … one entry per sector …\n'
    '  }\n'
    "}\n\n"
    "Allowed sector names: Technology, Healthcare, Finance, Energy, Industrials, "
    "Materials, Consumer, Utilities, RealEstate, Communication, Other.\n\n"
    "Sentiment rules: NEG = downside risk / bad news; POS = upside / good news; "
    "NEU = purely factual or mixed.  If unclear, output NEU with confidence ≤ 60.\n"
    "Sum of weights must be 1 (±0.01).  **Return raw JSON only – no markdown.**"
)

# ────────────────────────────────────────────────────────────
#  3.  Helpers
# ────────────────────────────────────────────────────────────
MAX_SENT = 40  # context budget


def get_headline(rec: dict) -> str:
    """Return headline string regardless of field name."""
    return rec.get("headline") or rec.get("headline_summary") or "UNKNOWN"


def build_prompt(article: Dict) -> str:
    body = "\n".join(article.get("sentences", [])[:MAX_SENT])
    return f"HEADLINE: {get_headline(article)}\nARTICLE:\n{body}"


# ────────────────────────────────────────────────────────────
#  4.  I/O paths
# ────────────────────────────────────────────────────────────
INP = Path("data/dev_sample_200.jsonl")
OUT = Path("data/dev_gold_200.jsonl")

records = [json.loads(l) for l in INP.open("r", encoding="utf-8")]

# ────────────────────────────────────────────────────────────
#  5.  Main loop
# ────────────────────────────────────────────────────────────
with OUT.open("w", encoding="utf-8") as fout:
    for art in tqdm(records, desc="GPT-labelling"):
        for attempt in range(3):
            try:
                resp = openai.chat.completions.create(
                    model="gpt-4o-mini",
                    temperature=0,
                    messages=[
                        {"role": "system", "content": SYSTEM_MSG},
                        {"role": "user",   "content": build_prompt(art)},
                    ],
                    timeout=30,
                )
                labelled = json.loads(resp.choices[0].message.content)
                fout.write(json.dumps(labelled, ensure_ascii=False) + "\n")
                break  # success
            except Exception as e:
                print("error:", type(e).__name__, "-", e)
                if attempt == 2:
                    print("❌ gave up on:",
                          get_headline(art)[:60], file=sys.stderr)
                time.sleep(1.5)  # back-off and retry

print(f"✅ wrote GPT dev gold → {OUT}")
