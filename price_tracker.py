from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import requests

DATA = Path("data")
DATA.mkdir(exist_ok=True)

def fetch_reliance_power_price() -> dict:
    # Public Yahoo Finance chart endpoint; used for research context.
    url = "https://query1.finance.yahoo.com/v8/finance/chart/RELIANCE.NS"
    try:
        r = requests.get(url, params={"range":"3mo","interval":"1d"}, timeout=25)
        r.raise_for_status()
        x = r.json()["chart"]["result"][0]
        ts = x.get("timestamp", [])
        quote = x["indicators"]["quote"][0]
        closes = quote.get("close", [])
        rows=[]
        for t,c in zip(ts,closes):
            if c is not None:
                rows.append({"date":datetime.fromtimestamp(t,tz=timezone.utc).date().isoformat(),"close":float(c)})
        if not rows:
            return {}
        df=pd.DataFrame(rows)
        df.to_csv(DATA/"price_history.csv",index=False)
        last=float(df["close"].iloc[-1])
        prev=float(df["close"].iloc[-2]) if len(df)>1 else last
        d5=float(df["close"].iloc[-6]) if len(df)>5 else df["close"].iloc[0]
        return {
            "symbol":"RELIANCE.NS","last_price":round(last,2),
            "daily_change_pct":round((last/prev-1)*100,2) if prev else 0,
            "five_day_change_pct":round((last/d5-1)*100,2) if d5 else 0,
            "history_rows":len(df)
        }
    except Exception as exc:
        print("PRICE ERROR",exc)
        return {}
