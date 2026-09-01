STOCK_NAME = "Reliance Power"
STOCK_SYMBOL = "RELIANCEPWR"
NEWS_LIMIT_PER_SOURCE = 30

NEWS_QUERIES = [
    '"Reliance Power"',
    '"Reliance Power" stock',
    '"Reliance Power" results OR earnings',
    '"Reliance Power" debt OR project OR order',
    '"Reliance Power" regulatory',
]

RSS_SOURCES = [
    "https://news.google.com/rss/search?q=Reliance+Power&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=Reliance+Power+stock&hl=en-IN&gl=IN&ceid=IN:en",
    "https://news.google.com/rss/search?q=Reliance+Power+results+OR+project+OR+debt&hl=en-IN&gl=IN&ceid=IN:en",
]

BULLISH_WORDS = [
    "profit", "growth", "surge", "gain", "rally", "order", "contract",
    "approval", "expansion", "reduction in debt", "turnaround", "record",
    "upgrade", "strong", "positive", "investment", "funding", "wins"
]

BEARISH_WORDS = [
    "loss", "decline", "fall", "drop", "debt", "default", "downgrade",
    "penalty", "investigation", "lawsuit", "delay", "weak", "concern",
    "risk", "selloff", "fraud", "dispute"
]
