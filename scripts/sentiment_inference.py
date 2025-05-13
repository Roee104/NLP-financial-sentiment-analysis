#!/usr/bin/env python3
"""
Batched sentiment inference with FinBERT, sub-batching to avoid OOM,
with a tqdm progress bar showing articles processed.
"""
import gzip
import json
import sys
from itertools import accumulate
from tqdm.auto import tqdm
from models.finbert import FinBERT

# Articles per batch and sub-batch size
ARTICLE_BATCH_SIZE = 100
SUB_BATCH_SIZE = 32
# If you know the total number of articles (e.g., 500000), set it here for tqdm
TOTAL_ARTICLES = 500000


def main(in_path, out_path):
    model = FinBERT()
    with gzip.open(in_path, "rt", encoding="utf-8") as fin, \
            gzip.open(out_path, "wt", encoding="utf-8") as fout:

        # Wrap the input stream with tqdm for progress
        iterator = tqdm(fin, desc="Scoring sentiment", total=TOTAL_ARTICLES)

        buffer = []
        for line in iterator:
            buffer.append(json.loads(line))
            if len(buffer) >= ARTICLE_BATCH_SIZE:
                process_batch(buffer, model, fout)
                buffer.clear()
                iterator.set_postfix_str(
                    f"Batches processed: {int(iterator.n / ARTICLE_BATCH_SIZE)}")

        # Handle remainder
        if buffer:
            process_batch(buffer, model, fout)

    print(f"✅ Wrote sentiment-scored articles to {out_path}")


def process_batch(arts, model, fout):
    # Flatten sentences
    all_sents = [s for art in arts for s in art["sentences"]]
    all_scores = []
    # Sub-batch to avoid OOM
    for i in range(0, len(all_sents), SUB_BATCH_SIZE):
        sub = all_sents[i: i+SUB_BATCH_SIZE]
        all_scores.extend(model.predict(sub))

    # Split scores back into articles
    lengths = [len(art["sentences"]) for art in arts]
    splits = list(accumulate(lengths))
    start = 0
    for art, end in zip(arts, splits):
        art["sentiments"] = all_scores[start:end]
        fout.write(json.dumps(art, ensure_ascii=False) + "\n")
        start = end


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: sentiment_inference.py <in.jsonl.gz> <out.jsonl.gz>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
