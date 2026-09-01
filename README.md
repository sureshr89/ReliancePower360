# Reliance Power 360

Free Reliance Power news intelligence and outlook engine.

## Phase 1
- Collect broad Reliance Power news through RSS
- Remove duplicate articles
- Score article sentiment
- Estimate article impact
- Produce bullish / bearish / neutral outlook
- Generate outlook for few days, few weeks and few months
- Save the latest report as JSON and CSV

## Current architecture

```
RSS / News Sources
        ↓
News Collector
        ↓
Duplicate Removal
        ↓
Sentiment + Impact Engine
        ↓
360 Score
        ↓
Few Days / Weeks / Months Outlook
        ↓
data/latest_report.json
```

## Run locally

```bash
pip install -r requirements.txt
python run_analysis.py
```

## Important

The current version is a news-intelligence model, not a trading system and not financial advice. Technical price data, exchange announcements, fundamentals, sector indicators and historical prediction accuracy will be added in later phases.

## Next phase

Build the Streamlit dashboard after the analysis engine is producing stable reports.
