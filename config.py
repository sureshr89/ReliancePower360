STOCK_NAME = "Reliance Power"
STOCK_QUERY = "Reliance Power"

# Fresh company news only: rolling lookback, never a fixed old 2025 window.
NEWS_LOOKBACK_DAYS = 30

RSS_SOURCES = [
    ("Google News - Company", "https://news.google.com/rss/search?q=%22Reliance+Power%22&hl=en-IN&gl=IN&ceid=IN:en"),
    ("Google News - Stock", "https://news.google.com/rss/search?q=%22Reliance+Power%22+stock&hl=en-IN&gl=IN&ceid=IN:en"),
    ("Google News - Results", "https://news.google.com/rss/search?q=%22Reliance+Power%22+results+OR+profit+OR+loss&hl=en-IN&gl=IN&ceid=IN:en"),
    ("Google News - Deals", "https://news.google.com/rss/search?q=%22Reliance+Power%22+order+OR+project+OR+funding+OR+investment&hl=en-IN&gl=IN&ceid=IN:en"),
    ("Google News - Risk", "https://news.google.com/rss/search?q=%22Reliance+Power%22+debt+OR+SEBI+OR+penalty+OR+investigation&hl=en-IN&gl=IN&ceid=IN:en"),
    ("Google News - Sector", "https://news.google.com/rss/search?q=India+power+sector+electricity+renewable&hl=en-IN&gl=IN&ceid=IN:en"),
]

GDELT_QUERY = '"Reliance Power"'
GDELT_DOC_API = "https://api.gdeltproject.org/api/v2/doc/doc"

OFFICIAL_PAGES = {
    "Reliance Power": "https://www.reliancepower.co.in/",
    "Press Releases": "https://www.reliancepower.co.in/press-release",
    "Regulatory Filings": "https://www.reliancepower.co.in/filing-with-regulatory",
    "Public Notices": "https://www.reliancepower.co.in/public-notice",
}

SOURCE_RELIABILITY = {
    "OFFICIAL_RPOWER": 1.00,
    "EXCHANGE": 0.98,
    "GOVERNMENT": 0.95,
    "API": 0.82,
    "GDELT": 0.75,
    "RSS": 0.70,
}

RELEVANCE_TERMS = ["reliance power", "reliancepwr", "rosa power", "sasan power", "vidarbha industries power"]
SECTOR_TERMS = ["power sector", "electricity", "thermal power", "renewable energy", "coal", "electricity demand", "power generation", "power tariff", "transmission"]
