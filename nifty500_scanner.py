from __future__ import annotations
import os,json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd,requests
IST=ZoneInfo("Asia/Kolkata")
DATA=Path("data"); DATA.mkdir(exist_ok=True)
URL="https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
DEFAULT="RELIANCE.NS,RELIANCEPOWER.NS,TCS.NS,INFY.NS,SBIN.NS,ITC.NS,HDFCBANK.NS,ICICIBANK.NS,LT.NS,BHARTIARTL.NS"

def hist(t):
    r=requests.get(URL.format(ticker=t),params={"range":"2y","interval":"1d","includePrePost":"false"},headers={"User-Agent":"Mozilla/5.0"},timeout=30)
    r.raise_for_status()
    result=r.json().get("chart",{}).get("result")
    if not result: raise RuntimeError("No price history returned")
    q=result[0]["indicators"]["quote"][0]
    df=pd.DataFrame({"close":q.get("close",[])})
    return df.dropna()

def pct(d,n):
    if len(d)<=n:return None
    old=float(d["close"].iloc[-1-n]); new=float(d["close"].iloc[-1])
    return round((new/old-1)*100,2) if old else None

def run():
    raw=os.getenv("NIFTY500_TICKERS",DEFAULT)
    now=datetime.now(IST); rows=[]
    for t in [x.strip().upper() for x in raw.split(",") if x.strip()]:
        try:
            d=hist(t)
            v={k:pct(d,n) for k,n in {"1Y":252,"6M":126,"1M":21,"1W":5,"1D":1}.items()}
            score=sum(1 if v[k] is not None and v[k]>0 else -1 if v[k] is not None and v[k]<0 else 0 for k in v)
            pred="BULLISH" if score>=3 else "BEARISH" if score<=-3 else "NEUTRAL"
            rows.append({"ticker":t.replace(".NS",""),**v,"set":"".join("+" if v[k] is not None and v[k]>0 else "-" if v[k] is not None and v[k]<0 else "0" for k in v),"momentum_score":score,"prediction":pred,"confidence":min(95,50+abs(score)*9),"last_close":round(float(d["close"].iloc[-1]),2)})
        except Exception as e:
            rows.append({"ticker":t.replace(".NS",""),"prediction":"UNAVAILABLE","error":str(e),"confidence":0})
    out=pd.DataFrame(rows)
    if out.empty: raise RuntimeError("No tickers configured")
    for col in ["confidence","momentum_score"]:
        if col not in out.columns: out[col]=0
    out=out.sort_values(["confidence","momentum_score"],ascending=False,na_position="last")
    out["priority"]=range(1,len(out)+1);out["prediction_date"]=now.strftime("%Y-%m-%d");out["prediction_time"]=now.strftime("%H:%M:%S IST")
    out.to_csv(DATA/"nifty500_scan.csv",index=False)
    valid=out[out["prediction"].isin(["BULLISH","BEARISH","NEUTRAL"])]
    b=int((valid["prediction"]=="BULLISH").sum());be=int((valid["prediction"]=="BEARISH").sum())
    rep={"generated_at":now.isoformat(),"prediction_date":now.strftime("%d %b %Y"),"prediction_time":now.strftime("%I:%M %p IST"),"universe_scanned":int(len(valid)),"bullish":b,"bearish":be,"neutral":int((valid["prediction"]=="NEUTRAL").sum()),"market_direction":"BULLISH" if b>be else "BEARISH" if be>b else "NEUTRAL","scan_status":"OK" if len(valid) else "NO_PRICE_DATA"}
    (DATA/"nifty500_report.json").write_text(json.dumps(rep,indent=2),encoding="utf-8")
    print(json.dumps(rep,indent=2))
if __name__=="__main__":run()
