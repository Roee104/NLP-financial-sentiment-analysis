# ───────────────────────── CONFIG ──────────────────────────────────────────
SEGMENTED_10K := data/news_segmented_10k.jsonl.gz
TICKERS_10K   := data/news_tickers_10k.jsonl.gz
SECTORED_10K  := data/news_tickers_10k_sector.jsonl.gz
SENT_10K      := data/news_sentiment_10k.jsonl.gz
FINAL_10K     := data/news_final_10k.jsonl.gz

PYTHON := python      # change to python3 on some Unix systems

# ───────────────────────── TARGETS ─────────────────────────────────────────
.PHONY: all pipeline sample extract sectors enrich sentiment aggregate clean

all: pipeline     ## default target

# End-to-end pipeline using the 10 k sample committed to the repo.
pipeline: sample extract sectors enrich sentiment aggregate
	@echo "🎉  Finished pipeline ⇒ $(FINAL_10K)"

# --------------------------------------------------------------------------
# sample  – ensure the 10 k sample exists.
#          1) If data/news_segmented_10k.jsonl.gz is already tracked, do nothing.
#          2) Else if data/news_segmented.jsonl.gz exists, run sample_10k.py.
#          3) Otherwise exit with an error message.
# --------------------------------------------------------------------------
sample:
	@if [ -f $(SEGMENTED_10K) ]; then \
	      echo '✓ 10 k sample already present'; \
	elif [ -f data/news_segmented.jsonl.gz ]; then \
	      echo '→ Creating 10 k sample from full segmented file'; \
	      $(PYTHON) scripts/sample_10k.py; \
	else \
	      echo '❌  Cannot create 10 k sample: data/news_segmented.jsonl.gz not found'; \
	      exit 1; \
	fi

# --------------------------------------------------------------------------
# extract – ticker extraction
# --------------------------------------------------------------------------
$(TICKERS_10K): $(SEGMENTED_10K)
	$(PYTHON) scripts/extract_tickers.py $< $@

extract: $(TICKERS_10K)

# --------------------------------------------------------------------------
# sectors – builds / refreshes ticker→sector lookup (idempotent)
# --------------------------------------------------------------------------
sectors:
	$(PYTHON) scripts/build_ticker2sector.py    # writes sector_map_filled.json

# --------------------------------------------------------------------------
# enrich – add sector weights to each article
# --------------------------------------------------------------------------
$(SECTORED_10K): $(TICKERS_10K)
	$(PYTHON) scripts/enrich_articles.py $< $@

enrich: $(SECTORED_10K)

# --------------------------------------------------------------------------
# sentiment – sentence-level FinBERT prediction (GPU-aware)
# --------------------------------------------------------------------------
$(SENT_10K): $(SECTORED_10K)
	$(PYTHON) -m scripts.sentiment_inference $< $@

sentiment: $(SENT_10K)

# --------------------------------------------------------------------------
# aggregate – combine to article-level output
# --------------------------------------------------------------------------
$(FINAL_10K): $(SENT_10K)
	$(PYTHON) scripts/aggregate_sentiment.py $< $@

aggregate: $(FINAL_10K)

# --------------------------------------------------------------------------
# clean – remove intermediates (keeps 10 k sample)
# --------------------------------------------------------------------------
clean:
	rm -f $(TICKERS_10K) $(SECTORED_10K) $(SENT_10K) $(FINAL_10K)
	@echo '🧹  Cleaned intermediate files'
