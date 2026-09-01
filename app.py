from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

DATA_DIR = Path("data")
REPORT_FILE = DATA_DIR / "latest_report.json"
NEWS_FILE = DATA_DIR / "latest_news.csv"

st.set_page_config(page_title="Reliance Power 360", page_icon="⚡", layout="wide")

@st.cache_data(ttl=60)
def load_report():
    default = {
        "generated_at": "Waiting for first data scan",
        "model_version": "1.1-multisource-360",
        "summary": {
            "news_score": 50, "news_outlook": "NEUTRAL", "confidence": 0,
            "article_count": 0, "bullish_count": 0,
            "bearish_count": 0, "neutral_count": 0,
        },
        "timeframes": {
            "few_days": {"score": 50, "outlook": "NEUTRAL", "confidence": 0},
            "few_weeks": {"score": 50, "outlook": "NEUTRAL", "confidence": 0},
            "few_months": {"score": 50, "outlook": "NEUTRAL", "confidence": 0},
        },
    }
    try:
        if REPORT_FILE.exists():
            with REPORT_FILE.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
    except Exception as exc:
        st.warning(f"Report file could not be read: {exc}")
    return default

@st.cache_data(ttl=60)
def load_news():
    try:
        if NEWS_FILE.exists() and NEWS_FILE.stat().st_size > 0:
            return pd.read_csv(NEWS_FILE)
    except Exception as exc:
        st.warning(f"News file could not be read: {exc}")
    return pd.DataFrame()

report = load_report()
summary = report.get("summary") or {}
timeframes = report.get("timeframes") or {}

st.title("⚡ Reliance Power 360° Intelligence")
st.caption("Multi-source news intelligence • Official disclosures • Bullish/Bearish outlook")

if report.get("generated_at") == "Waiting for first data scan":
    st.info("Dashboard is running. Waiting for the first automated intelligence scan.")

st.caption(f"Last analysis: {report.get('generated_at', 'Unknown')} | Model: {report.get('model_version', 'Unknown')}")

score = float(summary.get("news_score", 50) or 50)
outlook = str(summary.get("news_outlook", "NEUTRAL"))
confidence = int(summary.get("confidence", 0) or 0)

c1, c2, c3 = st.columns(3)
c1.metric("Overall Outlook", outlook)
c2.metric("360 News Score", f"{score:.1f}/100")
c3.metric("Confidence", f"{confidence}%")

st.divider()
st.subheader("📅 Multi-Timeframe Outlook")
cols = st.columns(3)
for col, key, title in zip(cols, ["few_days", "few_weeks", "few_months"], ["Next Few Days", "Next Few Weeks", "Next Few Months"]):
    item = timeframes.get(key) or {}
    with col:
        st.markdown(f"### {title}")
        st.metric(str(item.get("outlook", "NEUTRAL")), f"{float(item.get('score', 50) or 50):.1f}/100")
        st.caption(f"Confidence: {int(item.get('confidence', 0) or 0)}%")

st.divider()
st.subheader("📰 News Intelligence")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Articles", int(summary.get("article_count", 0) or 0))
m2.metric("Bullish", int(summary.get("bullish_count", 0) or 0))
m3.metric("Bearish", int(summary.get("bearish_count", 0) or 0))
m4.metric("Neutral", int(summary.get("neutral_count", 0) or 0))

news = load_news()
if news.empty:
    st.info("No collected news is available yet. The dashboard itself is working; data will appear after the first successful scan.")
else:
    st.subheader("🔥 Highest-Impact News")
    for required, default in {"impact": 1, "sentiment_score": 0.0, "sentiment": "NEUTRAL", "title": "Untitled"}.items():
        if required not in news.columns:
            news[required] = default

    news = news.sort_values(["impact", "sentiment_score"], ascending=[False, False], na_position="last")

    for _, row in news.head(20).iterrows():
        sentiment = str(row.get("sentiment", "NEUTRAL"))
        icon = "🟢" if sentiment == "BULLISH" else "🔴" if sentiment == "BEARISH" else "⚪"
        with st.expander(f"{icon} {str(row.get('title', 'Untitled'))[:150]}"):
            st.write(str(row.get("summary", "")))
            st.caption(f"Source: {row.get('source', 'Unknown')} | Impact: {row.get('impact', 1)} | Sentiment score: {float(row.get('sentiment_score', 0) or 0):.2f}")
            link = str(row.get("link", ""))
            if link.startswith("http"):
                st.link_button("Open original source", link)

    st.subheader("📊 All Collected News")
    display_cols = [c for c in ["title", "source", "sentiment", "impact", "sentiment_score", "published"] if c in news.columns]
    st.dataframe(news[display_cols], use_container_width=True, hide_index=True)

st.divider()
st.caption("Research and intelligence tool only. Bullish/Bearish labels are model outputs, not guarantees or financial advice.")
