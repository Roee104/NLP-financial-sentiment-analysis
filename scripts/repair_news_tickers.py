#!/usr/bin/env python3
import gzip
import shutil
from pathlib import Path


def repair_gzip(in_path, out_path):
    # Temporary decompressed file
    tmp_path = Path(str(out_path) + ".tmp")
    print(f"Decrypting valid portion of {in_path}... this may take a moment.")
    # Decompress until EOFError
    with gzip.open(in_path, 'rb') as f_in, tmp_path.open('wb') as f_tmp:
        while True:
            try:
                chunk = f_in.read(1024 * 1024)
                if not chunk:
                    break
                f_tmp.write(chunk)
            except EOFError:
                print(
                    "⚠️  EOFError encountered: truncated stream. Stopping decompression.")
                break
    # Re-compress to new gzip
    print(f"Re-compressing to {out_path}...")
    with tmp_path.open('rb') as f_tmp, gzip.open(out_path, 'wb') as f_out:
        shutil.copyfileobj(f_tmp, f_out)
    # Clean up tmp
    tmp_path.unlink()
    print(f"✅ Repaired gzip written to {out_path}")


if __name__ == '__main__':
    import sys
    if len(sys.argv) != 3:
        print("Usage: repair_news_tickers.py <in.gz> <out.gz>")
        sys.exit(1)
    in_gz = Path(sys.argv[1])
    out_gz = Path(sys.argv[2])
    repair_gzip(in_gz, out_gz)
