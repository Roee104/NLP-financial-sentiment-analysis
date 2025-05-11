#!/usr/bin/env python3
from tqdm import tqdm
import gzip
import json
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from nlp.ticker_extractor import hybrid_extract_tickers


def process_file(input_path: str, output_path: str):
    with gzip.open(input_path, 'rt', encoding='utf-8') as fin, \
            gzip.open(output_path, 'wt', encoding='utf-8') as fout:
        for line in tqdm(fin, desc="Extracting tickers"):
            article = json.loads(line)
            text = " ".join(article.get("sentences", []))
            tickers = hybrid_extract_tickers(text)
            article["tickers"] = list(tickers)
            fout.write(json.dumps(article, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python extract_tickers.py <input.gz> <output.gz>")
        sys.exit(1)

    process_file(sys.argv[1], sys.argv[2])
