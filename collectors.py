from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from urllib.parse import urljoin

import feedparser
import pandas as pd
import requests
from bs4 import BeautifulSoup

from config import (
    GDELT_DOC_API,
    GDELT_QUERY,
    OFFICIAL_PAGES,
    RSS_SOURCES,
    SOURCE_RELIABILITY,
)

HEADERS = {"User-Agent": "ReliancePower360/1.2 public-research-bot"}


def _row(title, summary, link, source, source_type, published=""):
    key = hashlib.sha256((str(title) + "|" + str(link)).encode()).hexdigest()
    return {
        "id": key,
        "title": str(title).strip(),
        "summary": str(summary).strip(),
        "link": str(link).strip(),
        "source": source,
        "source_type": source_type,
        "source_reliability": SOURCE_RELIABILITY.get(source_type, 0.50),
        "published": published,
        "collected_at": datetime.now(timezone.utc).isoformat(),
    }


def collect_rss():
    rows = []
    for name, url in RSS_SOURCES:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:80]:
                title = getattr(entry, "title", "").strip()
                if title:
                    rows.append(
                        _row(
                            title,
                            getattr(entry, "summary", ""),
                            getattr(entry, "link", ""),
                            name,
                            "RSS",
                            getattr(entry, "published", ""),
                        )
                    )
        except Exception as exc:
            print("RSS ERROR", name, exc)
    return rows


def collect_gdelt():
    rows = []
    try:
        params = {
            "query": GDELT_QUERY,
            "mode": "ArtList",
            "format": "json",
            "maxrecords": 100,
            "sort": "HybridRel",
        }
        response = requests.get(
            GDELT_DOC_API, params=params, headers=HEADERS, timeout=30
        )
        response.raise_for_status()
        for article in response.json().get("articles", []):
            title = article.get("title") or ""
            link = article.get("url") or ""
            if title and link:
                rows.append(
                    _row(
                        title,
                        article.get("domain") or "",
                        link,
                        article.get("domain") or "GDELT",
                        "GDELT",
                        article.get("seendate") or "",
                    )
                )
    except Exception as exc:
        print("GDELT ERROR", exc)
    return rows


def collect_official():
    rows = []
    seen = set()
    for name, url in OFFICIAL_PAGES.items():
        try:
            response = requests.get(url, headers=HEADERS, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")
            for link in soup.find_all("a", href=True):
                title = " ".join(link.get_text(" ", strip=True).split())
                href = urljoin(url, link["href"])
                if (
                    len(title) < 8
                    or href.startswith("javascript:")
                    or href == url
                    or href in seen
                ):
                    continue
                parent = (
                    link.parent.get_text(" ", strip=True)
                    if link.parent else ""
                )
                if href.lower().endswith(".pdf") or "reliancepower.co.in" in href:
                    rows.append(
                        _row(
                            title,
                            parent[:1200],
                            href,
                            name,
                            "OFFICIAL_RPOWER",
                        )
                    )
                    seen.add(href)
        except Exception as exc:
            print("OFFICIAL ERROR", name, exc)
    return rows


def collect_all():
    rows = collect_rss() + collect_gdelt() + collect_official()

    try:
        from api_collectors import collect_optional_apis
        rows.extend(collect_optional_apis())
    except Exception as exc:
        print("OPTIONAL API COLLECTORS ERROR", exc)

    try:
        from exchange_collectors import collect_nse_bse_official
        rows.extend(collect_nse_bse_official())
    except Exception as exc:
        print("EXCHANGE COLLECTORS ERROR", exc)

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.drop_duplicates(subset=["id"]).reset_index(drop=True)
