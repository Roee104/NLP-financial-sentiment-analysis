#!/usr/bin/env python3
import sys
import gzip
import json
import re

import spacy
from spacy.matcher import PhraseMatcher
from tqdm import tqdm

"""
Streaming hybrid ticker extractor (regex + PhraseMatcher).
Overwrites your previous version with batching and no multiprocessing.
"""

# 1) Minimal spaCy pipeline
nlp = spacy.load(
    "en_core_web_sm",
    disable=["parser", "tagger", "lemmatizer", "attribute_ruler"]
)

# 2) Load resources
company_dict = json.load(open("data/company_dict.json", encoding="utf-8"))
with open("data/ticker_master.csv", encoding="utf-8") as f:
    next(f)  # skip header
    WHITELIST = set(line.strip() for line in f)

# 3) Regex for $TICKER or bare TICKER
TICKER_RGX = re.compile(r"\$?([A-Z]{1,5})\b")

# 4) Build PhraseMatcher for company names
matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
patterns = [nlp.make_doc(name) for name in company_dict.keys()]
matcher.add("COMPANY", patterns)


def regex_extract(text: str):
    return {m for m in TICKER_RGX.findall(text) if m in WHITELIST}


def phrase_extract(doc):
    syms = set()
    for _, start, end in matcher(doc):
        name = doc[start:end].text.lower()
        tk = company_dict.get(name)
        if tk:
            syms.add(tk)
    return syms


def hybrid_extract(text: str, doc=None):
    syms = regex_extract(text)
    if doc is None:
        doc = nlp(text)
    syms |= phrase_extract(doc)
    return sorted(syms)


def run(input_path: str, output_path: str, batch_size: int = 200):
    with gzip.open(input_path, "rt", encoding="utf-8") as fin, \
            gzip.open(output_path, "wt", encoding="utf-8") as fout:

        batch_texts = []
        batch_arts = []

        for line in tqdm(fin, desc="Extracting tickers"):
            art = json.loads(line)
            text = " ".join(art.get("sentences", []))
            batch_texts.append(text)
            batch_arts.append(art)

            if len(batch_texts) >= batch_size:
                docs = list(nlp.pipe(batch_texts))
                for art, doc, txt in zip(batch_arts, docs, batch_texts):
                    art["tickers"] = hybrid_extract(txt, doc)
                    fout.write(json.dumps(art, ensure_ascii=False) + "\n")
                batch_texts.clear()
                batch_arts.clear()

        # process any remainder
        if batch_texts:
            docs = list(nlp.pipe(batch_texts))
            for art, doc, txt in zip(batch_arts, docs, batch_texts):
                art["tickers"] = hybrid_extract(txt, doc)
                fout.write(json.dumps(art, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: extract_tickers.py <in.jsonl.gz> <out.jsonl.gz>")
        sys.exit(1)
    run(sys.argv[1], sys.argv[2])
