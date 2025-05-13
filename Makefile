# ---------- CONFIG ---------------------------------------------------------
RAW          := data/news_2020_2025.jsonl.gz
SEGMENTED_10K:= data/news_segmented_10k.jsonl.gz
TICKERS_10K  := data/news_tickers_10k.jsonl.gz
SECTORED_10K := data/news_tickers_10k_sector.jsonl.gz
SENT_10K     := data/news_sentiment_10k.jsonl.gz
FINAL_10K    := data/news_final_10k.jsonl.gz

PYTHON       := python     # or "python3" on Unix

# ---------- TARGETS --------------------------------------------------------

.PHONY: all pipeline segment sample extract sectors enrich sentiment aggregate clean

all: pipeline

## Full pipeline on 10 k sample
pipeline: segment sample extract sectors enrich sentiment aggregate
	@echo "🎉  Finished end-to-end pipeline ⇒ $(FINAL_10K)"

## Step 1 – clean & sentence-segment raw
segment: $(RAW)
	$(PYTHON) scripts/segment_articles.py $(RAW) data/news_segmented.jsonl.gz

## Step 2 – deterministic 10 k sampling
sample: data/news_segmented.jsonl.gz
	$(PYTHON) scripts/sample_10k.py

## Step 3 – ticker extraction
extract: $(SEGMENTED_10K)
	$(PYTHON) scripts/extract_tickers.py $(SEGMENTED_10K) $(TICKERS_10K)

## Step 4 – build / refresh ticker→sector lookup
sectors:
	$(PYTHON) scripts/build_sector_map.py   # writes sector_map_filled.json

## Step 5 – add sector weights to articles
enrich: $(TICKERS_10K)
	$(PYTHON) scripts/enrich_articles.py $(TICKERS_10K) $(SECTORED_10K)

## Step 6 – sentence-level FinBERT sentiment (GPU-aware)
sentiment: $(SECTORED_10K)
	$(PYTHON) -m scripts.sentiment_inference $(SECTORED_10K) $(SENT_10K)

## Step 7 – aggregate to final JSON
aggregate: $(SENT_10K)
	$(PYTHON) scripts/aggregate_sentiment.py $(SENT_10K) $(FINAL_10K)

## Cleanup intermediates (keeps 10 k segmented sample)
clean:
	rm -f $(TICKERS_10K) $(SECTORED_10K) $(SENT_10K) $(FINAL_10K)
