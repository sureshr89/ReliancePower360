STOCK_NAME = "Reliance Power"
STOCK_QUERY = "Reliance Power"
RSS_SOURCES = [
    ("Google News - Company", "https://news.google.com/rss/search?q=%22Reliance+Power%22&hl=en-IN&gl=IN&ceid=IN:en"),
    ("Google News - Stock", "https://news.google.com/rss/search?q=%22Reliance+Power%22+stock&hl=en-IN&gl=IN&ceid=IN:en"),
    ("Google News - Projects", "https://news.google.com/rss/search?q=%22Reliance+Power%22+project+OR+order+OR+results+OR+debt&hl=en-IN&gl=IN&ceid=IN:en"),
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
    "GDELT": 0.75,
    "RSS": 0.70,
}
RELEVANCE_TERMS = ["reliance power", "reliancepwr", "rosa power", "sasan power", "vidarbha industries power"]
SECTOR_TERMS = ["power sector", "electricity", "thermal power", "renewable energy", "coal", "electricity demand", "power generation"]
