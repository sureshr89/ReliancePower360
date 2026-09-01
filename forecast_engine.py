from __future__ import annotations
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import pandas as pd

IST=ZoneInfo("Asia/Kolkata")

def _label(score):
    if score>=60:return "BULLISH"
    if score<=40:return "BEARISH"
    return "NEUTRAL"

def _news_time(df):
    if df.empty:return df
    out=df.copy()
    out["_published"]=pd.to_datetime(out.get("published",""),utc=True,errors="coerce").dt.tz_convert(IST)
    return out

def split_prediction_news(news):
    if news.empty:return news,news,{"today":0,"yesterday":0,"used_total":0}
    x=_news_time(news)
    now=datetime.now(IST)
    today=now.date()
    yesterday=(now-timedelta(days=1)).date()
    x["_date"]=x["_published"].dt.date
    td=x[x["_date"]==today].copy()
    yd=x[x["_date"]==yesterday].copy()
    used=pd.concat([td,yd],ignore_index=True).drop_duplicates()
    return td,yd,{"today":len(td),"yesterday":len(yd),"used_total":len(used)}

def build_explanations(news,price):
    td,yd,counts=split_prediction_news(news)
    used=pd.concat([td,yd],ignore_index=True).drop_duplicates() if not td.empty or not yd.empty else news.iloc[0:0]
    if used.empty:return {"today_drivers":[],"explanation":"No validated news from today or yesterday is available yet.","news_used":counts}
    ranked=used.assign(_abs=used["weighted_signal"].abs()).sort_values(["_abs","impact"],ascending=False).head(8)
    drivers=[]
    for _,r in ranked.iterrows():
        signal=float(r.get("weighted_signal",0))
        drivers.append({"direction":"positive" if signal>0 else "negative" if signal<0 else "mixed","title":str(r.get("title","")),"source":str(r.get("source","")),"published":str(r.get("published","")),"impact":int(r.get("impact",1)),"signal":round(signal,3)})
    daily=float(price.get("daily_change_pct",0)) if price else 0
    move="rose" if daily>0 else "fell" if daily<0 else "is flat"
    return {"today_drivers":drivers,"news_used":counts,"explanation":f"Reliance Power {move} {daily:+.2f}% in the latest available price data. Today's and yesterday's published news are the primary evidence used for the current prediction."}

def forecast(news,price,base):
    td,yd,counts=split_prediction_news(news)
    def sig(df):
        return float(df.get("weighted_signal",pd.Series(dtype=float)).sum()) if not df.empty else 0.0
    today_signal=sig(td); yesterday_signal=sig(yd)
    momentum=float(price.get("daily_change_pct",0)) if price else 0.0
    # Today 60%, yesterday 30%, current momentum 10% for current-session direction.
    raw=50 + today_signal*30 + yesterday_signal*15 + momentum*1.0
    score=max(0,min(100,raw))
    return {"current_session":{"score":round(score,1),"outlook":_label(score),"target":"Current / remaining market session"},"reason":"Current-session prediction uses only today and yesterday news as primary evidence, with current price momentum as supporting evidence.","news_window":{"today_articles":counts["today"],"yesterday_articles":counts["yesterday"],"used_total":counts["used_total"]}}
