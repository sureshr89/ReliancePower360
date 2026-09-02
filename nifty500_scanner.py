from __future__ import annotations
import json, os, sys
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import requests

IST = ZoneInfo("Asia/Kolkata")
DATA = Path("data")
DATA.mkdir(parents=True, exist_ok=True)
URL = "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
DEFAULT = "RELIANCE.NS,RPOWER.NS,TCS.NS,INFY.NS,SBIN.NS,ITC.NS,HDFCBANK.NS,ICICIBANK.NS,LT.NS,BHARTIARTL.NS"

def get_history(ticker):
    response = requests.get(
        URL.format(ticker=ticker),
        params={"range": "2y", "interval": "1d"},
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=30,
    )
    response.raise_for_status()
    result = response.json().get("chart", {}).get("result") or []
    if not result:
        raise RuntimeError("Yahoo returned no chart data")
    closes = result[0].get("indicators", {}).get("quote", [{}])[0].get("close", [])
    frame = pd.DataFrame({"close": closes}).dropna()
    if len(frame) < 2:
        raise RuntimeError("Not enough valid closing prices")
    return frame

def change(frame, days):
    if len(frame) <= days:
        return None
    old = float(frame["close"].iloc[-1-days])
    new = float(frame["close"].iloc[-1])
    return round((new / old - 1) * 100, 2) if old else None

def main():
    now = datetime.now(IST)
    tickers = [x.strip().upper() for x in os.getenv("NIFTY500_TICKERS", DEFAULT).split(",") if x.strip()]
    rows, errors = [], []

    for ticker in tickers:
        try:
            frame = get_history(ticker)
            values = {name: change(frame, days) for name, days in {"1Y":252,"6M":126,"1M":21,"1W":5,"1D":1}.items()}
            score = sum(1 if v is not None and v > 0 else -1 if v is not None and v < 0 else 0 for v in values.values())
            prediction = "BULLISH" if score >= 3 else "BEARISH" if score <= -3 else "NEUTRAL"
            rows.append({
                "ticker": ticker.replace(".NS", ""),
                **values,
                "set": "".join("+" if v is not None and v > 0 else "-" if v is not None and v < 0 else "0" for v in values.values()),
                "momentum_score": score,
                "prediction": prediction,
                "confidence": min(95, 50 + abs(score) * 9),
                "last_close": round(float(frame["close"].iloc[-1]), 2),
            })
        except Exception as exc:
            errors.append(f"{ticker}: {exc}")

    if not rows:
        raise RuntimeError("Scanner received no usable price data. " + " | ".join(errors[:5]))

    out = pd.DataFrame(rows).sort_values(["confidence", "momentum_score"], ascending=False)
    out["priority"] = range(1, len(out) + 1)
    out["prediction_date"] = now.strftime("%Y-%m-%d")
    out["prediction_time"] = now.strftime("%H:%M:%S IST")

    scan_path = DATA / "nifty500_scan.csv"
    report_path = DATA / "nifty500_report.json"
    out.to_csv(scan_path, index=False)

    bullish = int((out["prediction"] == "BULLISH").sum())
    bearish = int((out["prediction"] == "BEARISH").sum())
    neutral = int((out["prediction"] == "NEUTRAL").sum())
    report = {
        "generated_at": now.isoformat(),
        "prediction_date": now.strftime("%d %b %Y"),
        "prediction_time": now.strftime("%I:%M %p IST"),
        "universe_scanned": int(len(out)),
        "bullish": bullish,
        "bearish": bearish,
        "neutral": neutral,
        "market_direction": "BULLISH" if bullish > bearish else "BEARISH" if bearish > bullish else "NEUTRAL",
        "scan_status": "OK",
        "errors": errors,
    }
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Generated {scan_path} ({scan_path.stat().st_size} bytes)")
    print(f"Generated {report_path} ({report_path.stat().st_size} bytes)")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"SCAN FAILED: {exc}", file=sys.stderr)
        raise
