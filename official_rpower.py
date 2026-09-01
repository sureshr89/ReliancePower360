from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

OFFICIAL_PAGES = {
    "Reliance Power Press Release": "https://www.reliancepower.co.in/press-release",
    "Reliance Power Regulatory Filing": "https://www.reliancepower.co.in/filing-with-regulatory",
    "Reliance Power Public Notice": "https://www.reliancepower.co.in/public-notice",
}

HEADERS = {
    "User-Agent": "ReliancePower360 research bot/0.2 (+public information collector)"
}


def _clean(text: str) -> str:
    return " ".join(text.split())


def collect_official_rpower() -> pd.DataFrame:
    rows = []

    for source_name, page_url in OFFICIAL_PAGES.items():
        response = requests.get(page_url, headers=HEADERS, timeout=25)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")

        # Collect visible document links and their nearby text.
        for link in soup.find_all("a", href=True):
            title = _clean(link.get_text(" ", strip=True))
            href = urljoin(page_url, link["href"])

            if not title or len(title) < 6:
                continue
            if "javascript:" in href.lower() or href == page_url:
                continue

            # Keep only likely announcements/documents and avoid navigation links.
            title_lower = title.lower()
            relevant_terms = [
                "result", "disclosure", "release", "notice", "board",
                "financial", "regulation", "agm", "order", "award",
                "penalty", "debt", "warrant", "management", "update",
                "clarification", "rating", "investor", "monitoring"
            ]
            if not any(term in title_lower for term in relevant_terms):
                continue

            key = hashlib.sha256(
                (source_name + title + href).encode("utf-8")
            ).hexdigest()

            rows.append({
                "id": key,
                "title": title,
                "summary": f"Official Reliance Power disclosure collected from {source_name}.",
                "link": href,
                "published": "",
                "source": source_name,
                "source_type": "OFFICIAL_RPOWER",
                "source_reliability": 1.0,
                "collected_at": datetime.now(timezone.utc).isoformat(),
            })

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(rows).drop_duplicates(subset=["id"]).reset_index(drop=True)
