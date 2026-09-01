# ReliancePower360

Multi-source public-information intelligence dashboard for Reliance Power.

## Included
- Reliance Power official website collection
- Press releases, regulatory filings and public notices
- Multiple Google News RSS searches
- GDELT global news API
- Sector news context
- Source reliability weighting
- Relevance filtering
- Cross-source duplicate reduction
- Sentiment and impact scoring
- Few-days / few-weeks / few-months outlook
- Historical signal logging
- Optional free public market context
- GitHub Actions scheduled runs
- Streamlit dashboard

## Important
This project analyses publicly available information. It does not guarantee future price movement and is not financial advice. Exchange-specific collectors are intentionally not faked: if a stable public endpoint is added, it should be verified against the actual exchange response before being treated as an official filing.

## Run
```bash
pip install -r requirements.txt
python run_analysis.py
streamlit run app.py
```
