from __future__ import annotations

import re
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from config import BULLISH_WORDS, BEARISH_WORDS

analyzer = SentimentIntensityAnalyzer()


def keyword_adjustment(text: str) -> float:
    text = text.lower()
    bullish = sum(1 for word in BULLISH_WORDS if word in text)
    bearish = sum(1 for word in BEARISH_WORDS if word in text)
    return (bullish - bearish) * 0.05


def impact_score(title: str, summary: str) -> int:
    text = (title + " " + summary).lower()
    high_impact_terms = [
        "results", "earnings", "profit", "loss", "debt", "default",
        "order", "contract", "regulatory", "approval", "funding",
        "acquisition", "merger", "court", "investigation"
    ]
    hits = sum(1 for term in high_impact_terms if term in text)
    if hits >= 3:
        return 3
    if hits >= 1:
        return 2
    return 1


def classify_sentiment(score: float) -> str:
    if score >= 0.25:
        return "BULLISH"
    if score <= -0.25:
        return "BEARISH"
    return "NEUTRAL"


def analyse_news(df):
    if df.empty:
        return df

    scores = []
    labels = []
    impacts = []

    for _, row in df.iterrows():
        text = f"{row.get('title', '')} {row.get('summary', '')}"
        base = analyzer.polarity_scores(text)["compound"]
        score = max(-1.0, min(1.0, base + keyword_adjustment(text)))
        scores.append(round(score, 4))
        labels.append(classify_sentiment(score))
        impacts.append(impact_score(
            str(row.get("title", "")),
            str(row.get("summary", ""))
        ))

    out = df.copy()
    out["sentiment_score"] = scores
    out["sentiment"] = labels
    out["impact"] = impacts
    return out
