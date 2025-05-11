#!/usr/bin/env python3
import json
import gzip
import re
import html
import unicodedata
import nltk
import sys
from tqdm.auto import tqdm

# Load sentence tokenizer
sent_tok = nltk.data.load('tokenizers/punkt/english.pickle')


def tidy(txt: str) -> str:
    """
    - Unescape HTML entities
    - Collapse whitespace
    - Normalize Unicode to NFKC
    - Trim
    """
    txt = html.unescape(txt)
    txt = re.sub(r'\s+', ' ', txt)
    return unicodedata.normalize('NFKC', txt).strip()


def segment_file(input_path, output_path):
    with gzip.open(input_path, 'rt', encoding='utf-8') as fin, \
            gzip.open(output_path, 'wt', encoding='utf-8') as fout:

        for line in tqdm(fin, desc="Segmenting articles"):
            art = json.loads(line)

            # Clean headline and tag it
            headline = tidy(art["headline"]) + " <HEADLINE>"

            # Clean and split body
            body_sents = [tidy(s) for s in sent_tok.tokenize(
                tidy(art["body"])) if s.strip()]

            # Attach sentence list
            art["sentences"] = [headline] + body_sents
            art["tickers"] = []  # Placeholder for tickers

            fout.write(json.dumps(art, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python segment.py <infile.jsonl.gz> <outfile.jsonl.gz>")
        sys.exit(1)

    segment_file(sys.argv[1], sys.argv[2])
