from __future__ import annotations

import pandas as pd


def label_from_score(score: float) -> str:
    if score >= 75:
        return "STRONG BULLISH"
    if score >= 60:
        return "BULLISH"
    if score <= 25:
        return "STRONG BEARISH"
    if score <= 40:
        return "BEARISH"
    return "NEUTRAL"


def confidence_from_score(score: float) -> int:
    return int(round(abs(score - 50) * 2))


def calculate_news_score(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "news_score": 50.0,
            "news_outlook": "NEUTRAL",
            "confidence": 0,
            "article_count": 0,
            "bullish_count": 0,
            "bearish_count": 0,
            "neutral_count": 0,
        }

    weighted = df["sentiment_score"] * df["impact"]
    weight_total = df["impact"].sum()
    normalized = (weighted.sum() / weight_total) if weight_total else 0.0

    score = max(0.0, min(100.0, 50 + normalized * 50))

    bullish = int((df["sentiment"] == "BULLISH").sum())
    bearish = int((df["sentiment"] == "BEARISH").sum())
    neutral = int((df["sentiment"] == "NEUTRAL").sum())

    return {
        "news_score": round(score, 2),
        "news_outlook": label_from_score(score),
        "confidence": confidence_from_score(score),
        "article_count": int(len(df)),
        "bullish_count": bullish,
        "bearish_count": bearish,
        "neutral_count": neutral,
    }


def build_timeframe_outlook(news_score: float) -> dict:
    # Initial model: short-term news has strongest influence.
    days = news_score
    weeks = 50 + (news_score - 50) * 0.75
    months = 50 + (news_score - 50) * 0.50

    return {
        "few_days": {
            "score": round(days, 2),
            "outlook": label_from_score(days),
            "confidence": confidence_from_score(days),
        },
        "few_weeks": {
            "score": round(weeks, 2),
            "outlook": label_from_score(weeks),
            "confidence": confidence_from_score(weeks),
        },
        "few_months": {
            "score": round(months, 2),
            "outlook": label_from_score(months),
            "confidence": confidence_from_score(months),
        },
    }
