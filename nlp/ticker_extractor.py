import re
import spacy
from typing import List, Set

nlp = spacy.load("en_core_web_sm")

# Regex for patterns like (NYSE:A) or $AAPL
TICKER_PATTERN = re.compile(r'\$?[A-Z]{1,5}(?=[\s\W])')


def extract_regex_tickers(text: str) -> Set[str]:
    matches = TICKER_PATTERN.findall(text)
    return set(m.strip('$') for m in matches if 1 <= len(m.strip('$')) <= 5)


def extract_ner_tickers(text: str) -> Set[str]:
    doc = nlp(text)
    orgs = set(ent.text for ent in doc.ents if ent.label_ == "ORG")
    return orgs


def hybrid_extract_tickers(text: str) -> Set[str]:
    regex_tickers = extract_regex_tickers(text)
    org_names = extract_ner_tickers(text)
    return regex_tickers.union(org_names)
