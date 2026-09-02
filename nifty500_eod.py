from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import requests

IST = ZoneInfo("Asia/Kolkata")
DATA = Path("data")
URL = "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"

def latest_two_closes(ticker):
    response = requests.get(
        URL.format(ticker=ticker),
        params={"range": "10d", "interval": "1d"},
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=30,
    )
    response.raise_for_status()
    result = response.json().get("chart", {}).get("result") or []
    if not result:
        raise RuntimeError("No price data")
    closes = result[0]["indicators"]["quote"][0].get("close", [])
    closes = [float(x) for x in closes if x is not None]
    if len(closes) < 2:
        raise RuntimeError("Not enough closes")
    return closes[-2], closes[-1]

def run():
    scan_path = DATA / "nifty500_scan.csv"
    audit_path = DATA / "nifty500_eod_audit.csv"
    if not scan_path.exists():
        raise RuntimeError("No morning prediction file found")

    scan = pd.read_csv(scan_path)
    if scan.empty:
        raise RuntimeError("Morning prediction file is empty")

    trade_date = str(scan.get("prediction_date", pd.Series([datetime.now(IST).strftime("%Y-%m-%d")])).iloc[0])
    rows = []

    for _, row in scan.iterrows():
        ticker = str(row["ticker"]).strip().upper()
        prediction = str(row.get("prediction", "NEUTRAL")).upper()
        try:
            previous, close = latest_two_closes(ticker + ".NS")
            move = round((close / previous - 1) * 100, 3) if previous else 0.0
            actual = "BULLISH" if move > 0.05 else "BEARISH" if move < -0.05 else "NEUTRAL"
            matched = prediction == actual
            rows.append({
                "trade_date": trade_date,
                "ticker": ticker,
                "priority": row.get("priority", ""),
                "set": row.get("set", ""),
                "prediction": prediction,
                "actual_eod": actual,
                "eod_move_pct": move,
                "matched": matched,
                "eod_checked_at": datetime.now(IST).strftime("%d %b %Y %I:%M %p IST"),
            })
        except Exception as exc:
            rows.append({
                "trade_date": trade_date,
                "ticker": ticker,
                "priority": row.get("priority", ""),
                "set": row.get("set", ""),
                "prediction": prediction,
                "actual_eod": "UNAVAILABLE",
                "eod_move_pct": None,
                "matched": None,
                "error": str(exc),
                "eod_checked_at": datetime.now(IST).strftime("%d %b %Y %I:%M %p IST"),
            })

    new = pd.DataFrame(rows)
    if audit_path.exists():
        old = pd.read_csv(audit_path)
        old = old[old.get("trade_date", pd.Series(dtype=str)).astype(str) != trade_date]
        new = pd.concat([old, new], ignore_index=True)

    new.to_csv(audit_path, index=False)
    print(f"EOD audit generated for {trade_date}: {len(rows)} stocks")

if __name__ == "__main__":
    run()
