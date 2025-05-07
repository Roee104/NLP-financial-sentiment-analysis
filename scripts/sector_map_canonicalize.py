#!/usr/bin/env python3
import json
import csv
from pathlib import Path
from rapidfuzz import process, fuzz

# 1) Load the filled-in sector map
raw_map = json.load(open("data/sector_map_filled.json", encoding="utf-8"))

# 2) Define the 11 canonical GICS sectors
CANONICAL = [
    "Communication Services",
    "Consumer Discretionary",
    "Consumer Staples",
    "Energy",
    "Financials",
    "Health Care",
    "Industrials",
    "Information Technology",
    "Materials",
    "Real Estate",
    "Utilities"
]

# 3) Manual overrides for known oddballs
manual = {
    "Consumer Cyclical":    "Consumer Discretionary",
    "Consumer Defensive":   "Consumer Staples",
    "Financial Services":   "Financials",
    "Healthcare":           "Health Care",
}

# 4) Discover all unique raw sector strings
unique_raw = sorted({v for v in raw_map.values() if v})
print(f"{len(unique_raw)} unique raw sector names found.")

# 5) Compute best fuzzy match for each raw name
suggestions = {}
for raw in unique_raw:
    best, score, _ = process.extractOne(raw, CANONICAL, scorer=fuzz.WRatio)
    suggestions[raw] = (best, score)

# 6) Identify ambiguous matches (score < 90 AND not in manual)
ambiguous = {
    raw: suggestions[raw]
    for raw in unique_raw
    if raw not in manual and suggestions[raw][1] < 90
}
if ambiguous:
    print("\nAmbiguous raw sectors (<90% match and no manual override):")
    for raw, (best, score) in ambiguous.items():
        print(f"  {raw!r} → {best!r} ({score:.1f}%)")
else:
    print("No ambiguous sector names left (after manual overrides).")

# 7) Build the final ticker→sector map
ticker2sector = {}
for ticker, raw in raw_map.items():
    if not raw:
        sector = ""  # still unknown
    elif raw in manual:
        sector = manual[raw]
    else:
        sector = suggestions[raw][0]
    ticker2sector[ticker] = sector

# 8) Write out to CSV
Path("data").mkdir(exist_ok=True)
with open("data/ticker2sector.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["ticker", "sector"])
    for t, sect in sorted(ticker2sector.items()):
        w.writerow([t, sect])

print("\n✅ Wrote data/ticker2sector.csv")
