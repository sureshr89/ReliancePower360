from __future__ import annotations
import json, os, sys, re
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from email.utils import parsedate_to_datetime
from dateutil import parser as dateparser
import pandas as pd
import requests, feedparser

IST=ZoneInfo("Asia/Kolkata")
DATA=Path("data"); DATA.mkdir(parents=True,exist_ok=True)
PRICE_URL="https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
DEFAULT="RELIANCE.NS,RPOWER.NS,TCS.NS,INFY.NS,SBIN.NS,ITC.NS,HDFCBANK.NS,ICICIBANK.NS,LT.NS,BHARTIARTL.NS"
RSS=["https://news.google.com/rss/search?q={q}&hl=en-IN&gl=IN&ceid=IN:en"]
ALIASES={"RELIANCEPOWER.NS":"RPOWER.NS","RELIANCEPOWER":"RPOWER.NS"}
COMPANY={"RPOWER":"Reliance Power","RELIANCE":"Reliance Industries","TCS":"Tata Consultancy Services","INFY":"Infosys","SBIN":"State Bank of India","ITC":"ITC Limited","HDFCBANK":"HDFC Bank","ICICIBANK":"ICICI Bank","LT":"Larsen & Toubro","BHARTIARTL":"Bharti Airtel"}

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
 for k in ("published_parsed","updated_parsed"):
  v=e.get(k)
  if v:
   try:return datetime(*v[:6],tzinfo=ZoneInfo("UTC")).astimezone(IST)
   except:pass
 for k in ("published","updated","pubDate"):
  v=e.get(k)
  if v:
   try:
    x=dateparser.parse(str(v),fuzzy=True)
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
 name=COMPANY.get(symbol,symbol)
 symbol_q=symbol.replace("&","")
 queries=[
  f'"{name}"',
  f'"{name}" stock',
  f'"{name}" shares',
  f'"{name}" NSE',
  f'"{name}" results OR order OR contract OR profit OR loss',
  f'"{name}" site:moneycontrol.com',
  f'"{name}" site:livemint.com OR site:economictimes.indiatimes.com OR site:business-standard.com',
  f'"{name}" site:reuters.com OR site:businessline.com OR site:cnbctv18.com'
 ]
 items=[]; seen=set(); start=now-timedelta(days=1)
 for query in queries:
  url=RSS[0].format(q=requests.utils.quote(query))
  try:
   resp=requests.get(url,headers={"User-Agent":"Mozilla/5.0"},timeout=25)
   resp.raise_for_status(); feed=feedparser.parse(resp.content)
  except Exception: continue
  for e in getattr(feed,"entries",[]):
   dt=published(e)
   if not dt or dt<start or dt>now: continue
   title=re.sub(r"\s+"," ",e.get("title","")).strip()
   if not title: continue
   low=title.lower()
   # Strict stock relevance: company name, recognised symbol, or clear company reference.
   tokens=[name.lower(), symbol.lower(), symbol_q.lower()]
   if not any(t and t in low for t in tokens): continue
   key=re.sub(r"[^a-z0-9]+","",low)
   if key in seen: continue
   seen.add(key)
   src=e.get("source",{})
   source=src.get("title","Google News") if hasattr(src,"get") else "Google News"
   source_l=str(source).lower()
   weight=7
   if any(x in source_l for x in ["nse","bse","reliancepower.co.in","official"]): weight=10
   elif any(x in source_l for x in ["reuters","business standard","economic times","livemint","moneycontrol","businessline","cnbc"]): weight=8
   items.append({"ticker":symbol,"title":title,"source":source or "Google News","published_at":dt.strftime("%d %b %Y %I:%M %p IST"),"published_date":dt.strftime("%Y-%m-%d"),"link":e.get("link",""),"sentiment":sentiment(title),"weight":weight})
 return sorted(items,key=lambda x:x["published_at"],reverse=True)[:30]

def main():
 now=datetime.now(IST); rows=[]; all_news=[]; errors=[]
 tickers=[ALIASES.get(x.strip().upper(),x.strip().upper()) for x in os.getenv("NIFTY500_TICKERS",DEFAULT).split(",") if x.strip()]
 for ticker in tickers:
  try:
   d=hist(ticker); symbol=ticker.replace(".NS","")
   vals={k:ch(d,n) for k,n in {"1Y":252,"6M":126,"1M":21,"1W":5,"1D":1}.items()}
   momentum=sum(1 if v and v>0 else -1 if v and v<0 else 0 for v in vals.values())
   news=news_for(symbol,now); all_news.extend(news)
   bull=sum(x["weight"] for x in news if x["sentiment"]=="BULLISH")
   bear=sum(x["weight"] for x in news if x["sentiment"]=="BEARISH")
   neutral=sum(x["weight"] for x in news if x["sentiment"]=="NEUTRAL")
   ns=bull-bear
   # NEWS-FIRST RULE: without relevant dated stock news, confidence is capped at 55%.
   # Momentum can only support a news-driven prediction, never create a 95% prediction.
   if not news:
    score=momentum*0.25
    pred="NEUTRAL"
    confidence=50
    driver="NO RELEVANT NEWS"
   else:
    news_strength=abs(ns)/(bull+bear+neutral) if (bull+bear+neutral) else 0
    score=ns/7 + momentum*0.20
    if ns>=7: pred="BULLISH"
    elif ns<=-7: pred="BEARISH"
    else: pred="NEUTRAL"
    confidence=min(90,round(50 + min(30,news_strength*30) + min(10,abs(momentum)*2)))
    driver="NEWS" if abs(ns)>=7 else "MIXED"
   rows.append({"ticker":symbol,**vals,"set":"".join("+" if v and v>0 else "-" if v and v<0 else "0" for v in vals.values()),"momentum_score":momentum,"news_score":round(ns,2),"news_count":len(news),"news_bullish_weight":bull,"news_bearish_weight":bear,"news_neutral_weight":neutral,"primary_driver":driver,"prediction":pred,"confidence":confidence,"last_close":round(float(d.close.iloc[-1]),2)})
  except Exception as e:errors.append(f"{ticker}: {e}")
 if not rows:raise RuntimeError("No usable price data. "+" | ".join(errors[:5]))
 out=pd.DataFrame(rows).sort_values(["confidence","news_count","momentum_score"],ascending=False);out["priority"]=range(1,len(out)+1);out["prediction_date"]=now.strftime("%Y-%m-%d");out["prediction_time"]=now.strftime("%H:%M:%S IST")
 out.to_csv(DATA/"nifty500_scan.csv",index=False)
 pd.DataFrame(all_news,columns=["ticker","title","source","published_at","published_date","link","sentiment","weight"]).to_csv(DATA/"nifty500_prediction_news.csv",index=False)
 b=int((out.prediction=="BULLISH").sum());be=int((out.prediction=="BEARISH").sum())
 report={"generated_at":now.isoformat(),"prediction_date":now.strftime("%d %b %Y"),"prediction_time":now.strftime("%I:%M %p IST"),"universe_scanned":len(out),"bullish":b,"bearish":be,"neutral":int((out.prediction=="NEUTRAL").sum()),"market_direction":"BULLISH" if b>be else "BEARISH" if be>b else "NEUTRAL","news_window":[(now-timedelta(days=1)).strftime("%d %b %Y"),now.strftime("%d %b %Y")],"news_articles_saved":len(all_news),"scan_status":"OK","errors":errors}
 (DATA/"nifty500_report.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
 print(json.dumps(report,indent=2))
if __name__=="__main__":
 try:main()
 except Exception as e:print("SCAN FAILED:",e,file=sys.stderr);raise
