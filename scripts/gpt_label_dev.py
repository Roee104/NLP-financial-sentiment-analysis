#!/usr/bin/env python3
"""
Refined GPT‑4o labelling script
------------------------------
Creates data/dev_gold_200.jsonl with full‑schema labels:
  date, headline_summary (rewritten), overall {label, confidence},
  tickers, sectors_summary {weight, label, confidence}

Input : data/dev_sample_200.jsonl   (200 articles, headline + sentences)
Output: data/dev_gold_200.jsonl
Cost  : ≈150 tokens × 200 ≈ $0.15 with gpt‑4o‑mini
"""
import os, json, time, sys, openai
from pathlib import Path
from typing import Dict
from tqdm.auto import tqdm
from dotenv import load_dotenv

load_dotenv()

# ── OpenAI key ───────────────────────────────────────────────────────────
openai.api_key = os.getenv("OPENAI_API_KEY") or sys.exit("OPENAI_API_KEY env var not set")

# ── System message with explicit schema ─────────────────────────────────
SYSTEM_MSG = (
    "You are \"FinSent-Inspector\", a senior equity-research editor.\n\n"
    "The user will give you a news article in this exact format:\n"
    "HEADLINE: <headline text>\n"
    "ARTICLE:\n<full article text>\n\n"
    "Return ONE minified JSON object with these keys and nothing else:\n"
    "{\n"
    "  \"date\":              <YYYY-MM-DD if clearly stated, else null>,\n"
    "  \"published\":         null,\n"
    "  \"headline_summary\":  <rewrite headline in ≤15 words>,\n"
    "  \"overall\": {\n"
    "     \"label\": \"NEG|NEU|POS\",\n"
    "     \"confidence\": <integer 0-100>\n"
    "  },\n"
    "  \"tickers\": [<uppercase ticker symbols mentioned>],\n"
    "  \"sectors_summary\": {\n"
    "      <Sector1>: {\n"
    "        \"weight\": <float 0-1, 4 dp>,\n"
    "        \"label\":  \"NEG|NEU|POS\",\n"
    "        \"confidence\": <integer 0-100>\n"
    "      },\n"
    "      … one entry per sector you identify …\n"
    "  }\n"
    "}\n\n"
    "Allowed sector names: Technology, Healthcare, Finance, Energy, Industrials, "
    "Materials, Consumer, Utilities, RealEstate, Communication, Other.\n\n"
    "Sentiment rules: NEG = downside risk / bad news; POS = upside / good news; "
    "NEU = purely factual or mixed. If unclear, choose NEU with confidence ≤ 60.\n\n"
    "Sum of weights must be 1. Return only minified JSON (no markdown fences)."
)

# ── Helper to build the user prompt ──────────────────────────────────────
MAX_SENT = 40  # first 40 sentences are enough context

def build_prompt(article: Dict) -> str:
    if "sentences" in article:
        body_text = "\n".join(article["sentences"][:MAX_SENT])
    else:                                         # aggregated file
        body_text = article.get("body", "")[:8000]   # or ""
    return f"HEADLINE: {article['headline_summary']}\nARTICLE:\n{body_text}"

# ── Main ────────────────────────────────────────────────────────────────
INP = Path("data/dev_sample_200.jsonl")
OUT = Path("data/dev_gold_200.jsonl")

records = [json.loads(l) for l in INP.open("r", encoding="utf-8")]

with OUT.open("w", encoding="utf-8") as fout:
    for art in tqdm(records, desc="GPT‑labelling"):
        for attempt in range(3):
            try:
                resp = openai.chat.completions.create(
                    model="gpt-4o-mini",
                    temperature=0,
                    messages=[
                        {"role": "system", "content": SYSTEM_MSG},
                        {"role": "user",   "content": build_prompt(art)}
                    ]
                )
                labelled = json.loads(resp.choices[0].message.content)
                fout.write(json.dumps(labelled, ensure_ascii=False)+"\n")
                break
            except Exception as e:
                print("error:", type(e).__name__, "-", e)
                if attempt==2:
                    print("❌ failed on article:", art["headline_summary"][:60], file=sys.stderr)
                time.sleep(1.5)  # simple backoff

print("✅ wrote GPT dev gold →", OUT)
