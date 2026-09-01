from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

DATA_DIR = Path("data")
REPORT_FILE = DATA_DIR / "latest_report.json"
NEWS_FILE = DATA_DIR / "latest_news.csv"

st.set_page_config(
    page_title="Reliance Power 360",
    page_icon="⚡",
    layout="wide",
)

st.title("⚡ Reliance Power 360° Intelligence")
st.caption("Multi-source news intelligence • Official disclosures • Bullish/Bearish outlook")

if not REPORT_FILE.exists():
    st.warning("No analysis report yet. Run the GitHub Actions workflow first, then refresh this page.")
    st.stop()

with open(REPORT_FILE, "r", encoding="utf-8") as f:
    report = json.load(f)

summary = report.get("summary", {})
timeframes = report.get("timeframes", {})

st.caption(
    f"Last analysis: {report.get('generated_at', 'Unknown')} | "
    f"Model: {report.get('model_version', 'Unknown')}"
)

score = float(summary.get("news_score", 50))
outlook = summary.get("news_outlook", "NEUTRAL")
confidence = int(summary.get("confidence", 0))

col1, col2, col3 = st.columns(3)
col1.metric("Overall Outlook", outlook)
col2.metric("360 News Score", f"{score:.1f}/100")
col3.metric("Confidence", f"{confidence}%")

st.divider()
st.subheader("📅 Multi-Timeframe Outlook")

c1, c2, c3 = st.columns(3)

for col, key, title in [
    (c1, "few_days", "Next Few Days"),
    (c2, "few_weeks", "Next Few Weeks"),
    (c3, "few_months", "Next Few Months"),
]:
    item = timeframes.get(key, {})
    with col:
        st.markdown(f"### {title}")
        st.metric(
            item.get("outlook", "NEUTRAL"),
            f"{float(item.get('score', 50)):.1f}/100",
        )
        st.caption(f"Confidence: {item.get('confidence', 0)}%")

st.divider()
st.subheader("📰 News Intelligence")

a, b, c, d = st.columns(4)
a.metric("Articles", summary.get("article_count", 0))
b.metric("Bullish", summary.get("bullish_count", 0))
c.metric("Bearish", summary.get("bearish_count", 0))
d.metric("Neutral", summary.get("neutral_count", 0))

if NEWS_FILE.exists():
    news = pd.read_csv(NEWS_FILE)

    st.subheader("🔥 Highest-Impact News")

    if not news.empty:
        news = news.sort_values(
            ["impact", "sentiment_score"],
            ascending=[False, False],
        )

        for _, row in news.head(20).iterrows():
            sentiment = row.get("sentiment", "NEUTRAL")
            icon = "🟢" if sentiment == "BULLISH" else "🔴" if sentiment == "BEARISH" else "⚪"

            with st.expander(
                f"{icon} {row.get('title', 'Untitled')[:150]}"
            ):
                st.write(row.get("summary", ""))
                st.caption(
                    f"Source: {row.get('source', 'Unknown')} | "
                    f"Impact: {row.get('impact', 1)} | "
                    f"Sentiment score: {float(row.get('sentiment_score', 0)):.2f}"
                )
                link = row.get("link", "")
                if isinstance(link, str) and link.startswith("http"):
                    st.link_button("Open original source", link)

        st.subheader("📊 All Collected News")
        display_cols = [
            c for c in ["title", "source", "sentiment", "impact", "sentiment_score", "published"]
            if c in news.columns
        ]
        st.dataframe(news[display_cols], use_container_width=True, hide_index=True)

st.divider()
st.info(
    "This dashboard is a research and intelligence tool. "
    "Bullish/Bearish labels are model outputs, not guarantees or financial advice."
)
