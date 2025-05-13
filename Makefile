# ───────────── CONFIG ──────────────────────────────────────────────────────
SEGMENTED_10K := data/news_segmented_10k.jsonl.gz
TICKERS_10K   := data/news_tickers_10k.jsonl.gz
SECTORED_10K  := data/news_tickers_10k_sector.jsonl.gz
SENT_10K      := data/news_sentiment_10k.jsonl.gz
FINAL_10K     := data/news_final_10k.jsonl.gz

PYTHON := python3          # change to python3 if required

# ───────────── TARGETS ─────────────────────────────────────────────────────
.PHONY: all pipeline sample extract sectors enrich sentiment aggregate clean

all: pipeline

## End-to-end run on the 10 k sample
pipeline: sample extract sectors enrich sentiment aggregate
	@echo "🎉  Finished pipeline ⇒ $(FINAL_10K)"

## Step 1 – make 10 k sample *only if it doesn't already exist*
$(SEGMENTED_10K): data/news_segmented.jsonl.gz
	$(PYTHON) scripts/sample_10k.py           

sample: $(SEGMENTED_10K)                    # alias for dependency

## Step 2 – ticker extraction
$(TICKERS_10K): $(SEGMENTED_10K)
	$(PYTHON) scripts/extract_tickers.py $< $@

extract: $(TICKERS_10K)

## Step 3 – build / refresh ticker→sector lookup (idempotent)
sectors:
	$(PYTHON) scripts/build_sector_map.py

## Step 4 – add sector weights
$(SECTORED_10K): $(TICKERS_10K)
	$(PYTHON) scripts/enrich_articles.py $< $@

enrich: $(SECTORED_10K)

## Step 5 – sentence-level FinBERT sentiment (GPU)
$(SENT_10K): $(SECTORED_10K)
	$(PYTHON) -m scripts.sentiment_inference $< $@

sentiment: $(SENT_10K)

## Step 6 – aggregate article-level JSON
$(FINAL_10K): $(SENT_10K)
	$(PYTHON) scripts/aggregate_sentiment.py $< $@

aggregate: $(FINAL_10K)

## Utility: remove intermediates (keeps 10 k sample)
clean:
	rm -f $(TICKERS_10K) $(SECTORED_10K) $(SENT_10K) $(FINAL_10K)
	@echo "🧹  Cleaned intermediates"
