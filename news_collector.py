from __future__ import annotations

import hashlib
from datetime import datetime, timezone

import feedparser
import pandas as pd

from config import RSS_SOURCES, NEWS_LIMIT_PER_SOURCE


def fetch_rss(url: str) -> list[dict]:
    feed = feedparser.parse(url)
    rows = []

    for entry in feed.entries[:NEWS_LIMIT_PER_SOURCE]:
        title = getattr(entry, "title", "").strip()
        link = getattr(entry, "link", "").strip()
        summary = getattr(entry, "summary", "").strip()
        published = getattr(entry, "published", "")

        if not title:
            continue

        key = hashlib.sha256((title + link).encode("utf-8")).hexdigest()

        rows.append({
            "id": key,
            "title": title,
            "summary": summary,
            "link": link,
            "published": published,
            "source": getattr(getattr(entry, "source", {}), "title", "Google News"),
            "collected_at": datetime.now(timezone.utc).isoformat(),
        })

    return rows


def collect_all_news() -> pd.DataFrame:
    rows = []
    for source_url in RSS_SOURCES:
        try:
            rows.extend(fetch_rss(source_url))
        except Exception as exc:
            print(f"RSS source failed: {exc}")

    if not rows:
        return pd.DataFrame(columns=[
            "id", "title", "summary", "link", "published",
            "source", "collected_at"
        ])

    df = pd.DataFrame(rows)
    df = df.drop_duplicates(subset=["id"]).reset_index(drop=True)
    return df
