import wikipediaapi
import json
import re
from tqdm import tqdm

# Load raw map
sector_map = json.load(open("data/sector_map_raw.json", encoding="utf-8"))

# Instantiate with a proper User-Agent for Wikimedia policy
wp = wikipediaapi.Wikipedia(
    user_agent="fin-sentiment-project/1.0 (https://github.com/Roee104/NLP-financial-sentiment-analysis)",
    language="en"
)

for ticker, sector in tqdm(list(sector_map.items())):
    if sector:
        continue  # already have it

    # Try base page, then "(company)" fallback
    page = wp.page(ticker)
    if not page.exists():
        page = wp.page(f"{ticker} (company)")
        if not page.exists():
            continue

    # Scrape the 'Sector' field from the infobox HTML
    m = re.search(r"Sector</th><td.*?>(.*?)<", page.text, re.I | re.S)
    if m:
        sector_map[ticker] = m.group(1).strip()

# Save filled map
with open("data/sector_map_filled.json", "w", encoding="utf-8") as f:
    json.dump(sector_map, f, indent=2, ensure_ascii=False)

print("✅ Wikipedia-based sector filling complete.")
