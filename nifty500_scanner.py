from __future__ import annotations
import json, os, sys, re
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from email.utils import parsedate_to_datetime
import pandas as pd
import requests, feedparser

IST=ZoneInfo("Asia/Kolkata")
DATA=Path("data"); DATA.mkdir(parents=True,exist_ok=True)
PRICE_URL="https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
DEFAULT="RELIANCE.NS,RPOWER.NS,TCS.NS,INFY.NS,SBIN.NS,ITC.NS,HDFCBANK.NS,ICICIBANK.NS,LT.NS,BHARTIARTL.NS"
RSS=["https://news.google.com/rss/search?q={q}&hl=en-IN&gl=IN&ceid=IN:en"]

def hist(t):
 r=requests.get(PRICE_URL.format(ticker=t),params={"range":"2y","interval":"1d"},headers={"User-Agent":"Mozilla/5.0"},timeout=30);r.raise_for_status()
 z=r.json().get("chart",{}).get("result") or []
 if not z: raise RuntimeError("No chart data")
 d=pd.DataFrame({"close":z[0]["indicators"]["quote"][0].get("close",[])}).dropna()
 if len(d)<2: raise RuntimeError("Not enough prices")
 return d

def ch(d,n):
 if len(d)<=n:return None
 a,b=float(d.close.iloc[-1-n]),float(d.close.iloc[-1])
 return round((b/a-1)*100,2) if a else None

def published(e):
 for k in ("published","updated"):
  v=e.get(k)
  if v:
   try:
    x=parsedate_to_datetime(v)
    if x.tzinfo is None:x=x.replace(tzinfo=IST)
    return x.astimezone(IST)
   except:pass
 return None

def sentiment(title):
 t=title.lower()
 pos=["order","contract","profit","profitability","approval","wins","win","growth","surge","rises","rise","upgrade","strong","record"]
 neg=["loss","default","bankruptcy","insolvency","probe","ed ","cbi ","fraud","penalty","downgrade","falls","fall","debt","notice"]
 p=sum(w in t for w in pos); n=sum(w in t for w in neg)
 return "BULLISH" if p>n else "BEARISH" if n>p else "NEUTRAL"

def news_for(symbol, now):
 name={"RPOWER":"Reliance Power","RELIANCE":"Reliance Industries"}.get(symbol,symbol)
 q=requests.utils.quote(f'"{name}" OR "{symbol}" shares OR "{symbol}" stock')
 items=[]
 for tpl in RSS:
  feed=feedparser.parse(tpl.format(q=q))
  if getattr(feed, "bozo", False):
   continue
  for e in feed.entries:
   dt=published(e)
   if not dt:
    continue
   if dt.date() not in {now.date(),(now-timedelta(days=1)).date()}:
    continue
   title=re.sub(r"\s+"," ",e.get("title","")).strip()
   link=e.get("link","")
   key=(title.lower(),dt.date())
   if title and key not in {(x["title"].lower(),x["published_date"]) for x in items}:
    items.append({"ticker":symbol,"title":title,"source":"Google News","published_at":dt.strftime("%d %b %Y %I:%M %p IST"),"published_date":dt.strftime("%Y-%m-%d"),"link":link,"sentiment":sentiment(title),"weight":7})
 return items[:20]

def main():
 now=datetime.now(IST); rows=[]; all_news=[]; errors=[]
 tickers=[x.strip().upper() for x in os.getenv("NIFTY500_TICKERS",DEFAULT).split(",") if x.strip()]
 for ticker in tickers:
  try:
   d=hist(ticker); symbol=ticker.replace(".NS","")
   vals={k:ch(d,n) for k,n in {"1Y":252,"6M":126,"1M":21,"1W":5,"1D":1}.items()}
   momentum=sum(1 if v and v>0 else -1 if v and v<0 else 0 for v in vals.values())
   news=news_for(symbol,now); all_news.extend(news)
   ns=sum((1 if x["sentiment"]=="BULLISH" else -1 if x["sentiment"]=="BEARISH" else 0)*x["weight"] for x in news)
   score=momentum+ns/10
   pred="BULLISH" if score>=2 else "BEARISH" if score<=-2 else "NEUTRAL"
   rows.append({"ticker":symbol,**vals,"set":"".join("+" if v and v>0 else "-" if v and v<0 else "0" for v in vals.values()),"momentum_score":momentum,"news_score":round(ns,2),"news_count":len(news),"prediction":pred,"confidence":min(95,round(50+abs(score)*8)),"last_close":round(float(d.close.iloc[-1]),2)})
  except Exception as e:errors.append(f"{ticker}: {e}")
 if not rows:raise RuntimeError("No usable price data. "+" | ".join(errors[:5]))
 out=pd.DataFrame(rows).sort_values(["confidence","momentum_score"],ascending=False);out["priority"]=range(1,len(out)+1);out["prediction_date"]=now.strftime("%Y-%m-%d");out["prediction_time"]=now.strftime("%H:%M:%S IST")
 out.to_csv(DATA/"nifty500_scan.csv",index=False)
 pd.DataFrame(all_news,columns=["ticker","title","source","published_at","published_date","link","sentiment","weight"]).to_csv(DATA/"nifty500_prediction_news.csv",index=False)
 b=int((out.prediction=="BULLISH").sum());be=int((out.prediction=="BEARISH").sum())
 report={"generated_at":now.isoformat(),"prediction_date":now.strftime("%d %b %Y"),"prediction_time":now.strftime("%I:%M %p IST"),"universe_scanned":len(out),"bullish":b,"bearish":be,"neutral":int((out.prediction=="NEUTRAL").sum()),"market_direction":"BULLISH" if b>be else "BEARISH" if be>b else "NEUTRAL","news_window":[(now-timedelta(days=1)).strftime("%d %b %Y"),now.strftime("%d %b %Y")],"scan_status":"OK","errors":errors}
 (DATA/"nifty500_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
 print(json.dumps(report,indent=2))
if __name__=="__main__":
 try:main()
 except Exception as e:print("SCAN FAILED:",e,file=sys.stderr);raise
