from __future__ import annotations
import math, re
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from config import RELEVANCE_TERMS, SECTOR_TERMS

V=SentimentIntensityAnalyzer()
BULL=["profit","growth","surge","rally","order","award","approval","expansion","turnaround","investment","funding","upgrade","wins","strong"]
BEAR=["loss","default","penalty","investigation","lawsuit","delay","downgrade","risk","selloff","fraud","weak","concern","debt"]

def relevance(text):
    t=text.lower()
    if any(x in t for x in RELEVANCE_TERMS): return 1.0
    if any(x in t for x in SECTOR_TERMS): return 0.35
    return 0.10

def sentiment(text):
    base=V.polarity_scores(text)["compound"]
    t=text.lower()
    base += .05*sum(w in t for w in BULL)
    base -= .05*sum(w in t for w in BEAR)
    return max(-1,min(1,base))

def impact(text, source_type):
    t=text.lower(); terms=["results","earnings","profit","loss","debt","default","order","award","regulatory","approval","funding","court","investigation","acquisition","project"]
    n=sum(x in t for x in terms)
    base=1+min(2,n)
    if source_type in ("OFFICIAL_RPOWER","EXCHANGE","GOVERNMENT"): base=min(3,base+1)
    return base

def analyse(df):
    if df.empty:return df
    out=df.copy(); scores=[]; labels=[]; impacts=[]; rel=[]
    for _,r in out.iterrows():
        text=f"{r.get('title','')} {r.get('summary','')}"
        s=sentiment(text); scores.append(s)
        labels.append("BULLISH" if s>=.2 else "BEARISH" if s<=-.2 else "NEUTRAL")
        impacts.append(impact(text,str(r.get("source_type","RSS"))))
        rel.append(relevance(text))
    out["sentiment_score"]=scores; out["sentiment"]=labels; out["impact"]=impacts; out["relevance"]=rel
    out["weighted_signal"]=out["sentiment_score"]*out["impact"]*out["source_reliability"]*out["relevance"]
    return out

def deduplicate(df):
    if df.empty:return df
    seen=set(); keep=[]
    for i,r in df.sort_values("source_reliability",ascending=False).iterrows():
        words=set(re.findall(r"[a-z0-9]+",str(r["title"]).lower()))
        sig=frozenset(list(words)[:25])
        duplicate=False
        for old in seen:
            if sig and len(sig & old)/max(1,len(sig|old))>.65: duplicate=True; break
        if not duplicate: seen.add(sig); keep.append(i)
    return df.loc[keep].reset_index(drop=True)

def outlook(df):
    if df.empty:return {"score":50.0,"outlook":"NEUTRAL","confidence":0}
    denom=(df["impact"]*df["source_reliability"]*df["relevance"]).sum()
    raw=df["weighted_signal"].sum()/denom if denom else 0
    score=max(0,min(100,50+raw*50))
    label="STRONG BULLISH" if score>=75 else "BULLISH" if score>=60 else "STRONG BEARISH" if score<=25 else "BEARISH" if score<=40 else "NEUTRAL"
    return {"score":round(score,2),"outlook":label,"confidence":int(round(abs(score-50)*2))}

def timeframes(base):
    transforms={"few_days":1.0,"few_weeks":.72,"few_months":.45}
    out={}
    for k,w in transforms.items():
        s=50+(base["score"]-50)*w
        label="STRONG BULLISH" if s>=75 else "BULLISH" if s>=60 else "STRONG BEARISH" if s<=25 else "BEARISH" if s<=40 else "NEUTRAL"
        out[k]={"score":round(s,2),"outlook":label,"confidence":int(round(abs(s-50)*2))}
    return out
