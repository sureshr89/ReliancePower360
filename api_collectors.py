from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import requests

from collectors import _row

TIMEOUT = 25


def _request_json(url: str, params: dict[str, Any]) -> dict[str, Any]:
    response = requests.get(url, params=params, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()


def collect_newsapi() -> list[dict]:
    """Optional NewsAPI.org collector. Requires NEWSAPI_KEY."""
    key = os.getenv("NEWSAPI_KEY")
    if not key:
        return []

    rows = []
    try:
        data = _request_json(
            "https://newsapi.org/v2/everything",
            {
                "q": '"Reliance Power" OR RELIANCEPWR',
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": 100,
                "apiKey": key,
            },
        )
        for article in data.get("articles", []):
            title = article.get("title") or ""
            link = article.get("url") or ""
            if title and link:
                rows.append(
                    _row(
                        title,
                        article.get("description") or article.get("content") or "",
                        link,
                        article.get("source", {}).get("name") or "NewsAPI",
                        "API",
                        article.get("publishedAt") or "",
                    )
                )
    except Exception as exc:
        print("NEWSAPI ERROR", exc)
    return rows


def collect_finnhub() -> list[dict]:
    """Optional Finnhub company-news collector. Requires FINNHUB_API_KEY."""
    key = os.getenv("FINNHUB_API_KEY")
    if not key:
        return []

    rows = []
    try:
        data = _request_json(
            "https://finnhub.io/api/v1/company-news",
            {
                "symbol": "RELIANCE.NS",
                "from": "2025-01-01",
                "to": datetime.now(timezone.utc).date().isoformat(),
                "token": key,
            },
        )
        for article in data if isinstance(data, list) else []:
            title = article.get("headline") or ""
            link = article.get("url") or ""
            if title and link:
                rows.append(
                    _row(
                        title,
                        article.get("summary") or "",
                        link,
                        article.get("source") or "Finnhub",
                        "API",
                        datetime.fromtimestamp(article.get("datetime", 0), tz=timezone.utc).isoformat()
                        if article.get("datetime") else "",
                    )
                )
    except Exception as exc:
        print("FINNHUB ERROR", exc)
    return rows


def collect_marketaux() -> list[dict]:
    """Optional Marketaux collector. Requires MARKET_AUX_API_TOKEN."""
    token = os.getenv("MARKET_AUX_API_TOKEN")
    if not token:
        return []

    rows = []
    try:
        data = _request_json(
            "https://api.marketaux.com/v1/news/all",
            {
                "search": '"Reliance Power"',
                "language": "en",
                "limit": 100,
                "api_token": token,
            },
        )
        for article in data.get("data", []):
            title = article.get("title") or ""
            link = article.get("url") or ""
            if title and link:
                rows.append(
                    _row(
                        title,
                        article.get("description") or "",
                        link,
                        article.get("source") or "Marketaux",
                        "API",
                        article.get("published_at") or "",
                    )
                )
    except Exception as exc:
        print("MARKETAUX ERROR", exc)
    return rows


def collect_optional_apis() -> list[dict]:
    return collect_newsapi() + collect_finnhub() + collect_marketaux()
