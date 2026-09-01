from __future__ import annotations

import os
import requests
from bs4 import BeautifulSoup

from collectors import _row

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ReliancePower360/1.2)",
    "Accept": "text/html,application/xhtml+xml",
}


def collect_nse_bse_official() -> list[dict]:
    """Optional official-source collector.

    Exchange endpoints frequently change and may require cookies or approved access.
    This module intentionally returns no fabricated filings. Set official feed/page URLs
    through environment variables when a verified public endpoint is available.
    """
    rows = []
    sources = [
        ("NSE Official Feed", os.getenv("NSE_OFFICIAL_FEED_URL")),
        ("BSE Official Feed", os.getenv("BSE_OFFICIAL_FEED_URL")),
    ]

    for name, url in sources:
        if not url:
            continue
        try:
            response = requests.get(url, headers=HEADERS, timeout=25)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")
            for link in soup.find_all("a", href=True):
                title = " ".join(link.get_text(" ", strip=True).split())
                href = link.get("href", "")
                if len(title) >= 8 and href.startswith("http"):
                    rows.append(
                        _row(
                            title,
                            "Verified public exchange source collected from configured official URL.",
                            href,
                            name,
                            "EXCHANGE",
                            "",
                        )
                    )
        except Exception as exc:
            print("EXCHANGE COLLECTOR ERROR", name, exc)

    return rows
