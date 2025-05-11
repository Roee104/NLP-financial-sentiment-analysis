"""
Custom spaCy pipeline component that tags any token which:

  • Consists of 1‑5 uppercase letters, AND
  • Exists in the supplied whitelist of valid US tickers

as a `TICKER` named‑entity.

Usage
-----
    import spacy
    from fin_sentiment.nlp.ticker_component import make_ticker_component

    nlp = spacy.load("en_core_web_lg")
    nlp.add_pipe(make_ticker_component(nlp, whitelist), last=True)
"""

from spacy.matcher import Matcher
from spacy.tokens import Span
from typing import Set


def make_ticker_component(nlp, whitelist: Set[str], name: str = "ticker_component"):
    """
    Parameters
    ----------
    nlp : spacy.Language
    whitelist : set[str]
        A Python set containing all valid ticker strings.
    name : str
        Name used by spaCy in the pipeline registry.
    """

    matcher = Matcher(nlp.vocab)
    # 1‑5 capital letters (no digits, no dots)
    pattern = [{"TEXT": {"REGEX": r"^[A-Z]{1,5}$"}}]
    matcher.add("TICKER", [pattern])

    def ticker_component(doc):
        matches = matcher(doc)
        new_ents = list(doc.ents)

        for _, start, end in matches:
            span = Span(doc, start, end, label=doc.vocab.strings["TICKER"])
            if (
                span.text in whitelist
                and not any(e.start == span.start for e in new_ents)
            ):
                new_ents.append(span)

        doc.ents = new_ents
        return doc

    return ticker_component
