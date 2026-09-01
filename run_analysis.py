from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from news_collector import collect_all_news
from sentiment_engine import analyse_news
from scoring import calculate_news_score, build_timeframe_outlook

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)


def main():
    raw = collect_all_news()
    analysed = analyse_news(raw)

    if not analysed.empty:
        analysed = analysed.sort_values(
            ["impact", "sentiment_score"],
            ascending=[False, False]
        )

    analysed.to_csv(DATA_DIR / "latest_news.csv", index=False)

    summary = calculate_news_score(analysed)
    timeframes = build_timeframe_outlook(summary["news_score"])

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "company": "Reliance Power",
        "model_version": "0.1-news-only",
        "summary": summary,
        "timeframes": timeframes,
        "top_bullish_news": analysed[analysed["sentiment"] == "BULLISH"]
            .head(5)[["title", "source", "impact", "sentiment_score", "link"]]
            .to_dict("records") if not analysed.empty else [],
        "top_bearish_news": analysed[analysed["sentiment"] == "BEARISH"]
            .head(5)[["title", "source", "impact", "sentiment_score", "link"]]
            .to_dict("records") if not analysed.empty else [],
    }

    with open(DATA_DIR / "latest_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
