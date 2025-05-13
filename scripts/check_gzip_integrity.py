#!/usr/bin/env python3
import gzip


def main():
    path = "data/news_tickers_500k_fixed.jsonl.gz"
    try:
        with gzip.open(path, "rb") as f:
            # read in 1 MB chunks to avoid huge memory use
            for chunk in iter(lambda: f.read(1024*1024), b""):
                pass
        print("✅ Decompressed end-to-end without error")
    except Exception as e:
        print("❌ Decompression error:", e)


if __name__ == "__main__":
    main()
