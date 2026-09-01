from __future__ import annotations
from datetime import datetime,timezone
from pathlib import Path
import pandas as pd, requests

DATA=Path("data");DATA.mkdir(exist_ok=True)
HEADERS={"User-Agent":"Mozilla/5.0"}

def fetch_reliance_power_price():
    endpoints=[
      "https://query1.finance.yahoo.com/v8/finance/chart/RELIANCE.NS",
      "https://query2.finance.yahoo.com/v8/finance/chart/RELIANCE.NS",
    ]
    for url in endpoints:
      try:
        r=requests.get(url,params={"range":"3mo","interval":"1d","events":"history"},headers=HEADERS,timeout=25);r.raise_for_status()
        x=r.json()["chart"]["result"][0]; ts=x.get("timestamp") or []; closes=x["indicators"]["quote"][0].get("close") or []
        rows=[{"date":datetime.fromtimestamp(t,tz=timezone.utc).date().isoformat(),"close":float(c)} for t,c in zip(ts,closes) if c is not None]
        if not rows:continue
        df=pd.DataFrame(rows).drop_duplicates("date").sort_values("date");df.to_csv(DATA/"price_history.csv",index=False)
        last=float(df.close.iloc[-1]);prev=float(df.close.iloc[-2]) if len(df)>1 else last;d5=float(df.close.iloc[-6]) if len(df)>5 else float(df.close.iloc[0])
        return {"symbol":"RELIANCE.NS","last_price":round(last,2),"daily_change_pct":round((last/prev-1)*100,2),"five_day_change_pct":round((last/d5-1)*100,2),"as_of":str(df.date.iloc[-1]),"history_rows":len(df)}
      except Exception as exc: print("PRICE ERROR",url,exc)
    return {}
