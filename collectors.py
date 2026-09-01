from __future__ import annotations
import hashlib
from datetime import datetime, timezone, timedelta
from urllib.parse import urljoin
import email.utils
import feedparser
import pandas as pd
import requests
from bs4 import BeautifulSoup
from config import GDELT_DOC_API,GDELT_QUERY,OFFICIAL_PAGES,RSS_SOURCES,SOURCE_RELIABILITY,NEWS_LOOKBACK_DAYS,RELEVANCE_TERMS

HEADERS={"User-Agent":"Mozilla/5.0 (compatible; ReliancePower360/2.0)"}
CUTOFF=datetime.now(timezone.utc)-timedelta(days=NEWS_LOOKBACK_DAYS)

def _dt(value):
    if not value:return None
    try:
        x=pd.to_datetime(value,utc=True,errors="coerce")
        return None if pd.isna(x) else x.to_pydatetime()
    except Exception:return None

def _fresh(value):
    x=_dt(value)
    return x is not None and x>=CUTOFF

def _row(title,summary,link,source,source_type,published=""):
    key=hashlib.sha256((str(title)+"|"+str(link)).encode()).hexdigest()
    return {"id":key,"title":str(title).strip(),"summary":str(summary).strip(),"link":str(link).strip(),"source":source,"source_type":source_type,"source_reliability":SOURCE_RELIABILITY.get(source_type,.5),"published":published,"collected_at":datetime.now(timezone.utc).isoformat()}

def collect_rss():
    rows=[]
    for name,url in RSS_SOURCES:
        try:
            feed=feedparser.parse(url)
            for e in feed.entries[:100]:
                title=getattr(e,"title","").strip(); published=getattr(e,"published","") or getattr(e,"updated","")
                text=f"{title} {getattr(e,'summary','')}".lower()
                # Sector feed is context only; require a Reliance Power term for company analysis.
                if not title or not _fresh(published): continue
                if name!="Google News - Sector" and not any(t in text for t in RELEVANCE_TERMS): continue
                rows.append(_row(title,getattr(e,"summary",""),getattr(e,"link",""),name,"RSS",published))
        except Exception as exc: print("RSS ERROR",name,exc)
    return rows

def collect_gdelt():
    rows=[]
    try:
        params={"query":GDELT_QUERY,"mode":"ArtList","format":"json","maxrecords":100,"sort":"DateDesc","timespan":f"{NEWS_LOOKBACK_DAYS}d"}
        r=requests.get(GDELT_DOC_API,params=params,headers=HEADERS,timeout=30);r.raise_for_status()
        for a in r.json().get("articles",[]):
            title=a.get("title") or ""; link=a.get("url") or ""; published=a.get("seendate") or ""
            if title and link and _fresh(published):
                rows.append(_row(title,a.get("domain") or "",link,a.get("domain") or "GDELT","GDELT",published))
    except Exception as exc: print("GDELT ERROR",exc)
    return rows

def collect_official():
    rows=[]; seen=set()
    for name,url in OFFICIAL_PAGES.items():
        try:
            r=requests.get(url,headers=HEADERS,timeout=30);r.raise_for_status();soup=BeautifulSoup(r.text,"lxml")
            for a in soup.find_all("a",href=True):
                title=" ".join(a.get_text(" ",strip=True).split()); href=urljoin(url,a["href"])
                if len(title)<15 or href in seen or href==url:continue
                # Reject navigation/category links; keep dated documents and concrete release/filing links.
                if any(x.lower()==title.lower() for x in ["Financials","Financial Results","Filing with Regulatory","Public Notice","Hydroelectricity Projects","Coal based Projects","Gas based Projects","Solar Power Projects"]):continue
                parent=a.parent.get_text(" ",strip=True) if a.parent else ""
                published=""
                for node in [a,a.parent]:
                    if node and node.get("datetime"): published=node.get("datetime");break
                if published and not _fresh(published):continue
                if href.lower().endswith(".pdf") or "/press" in href.lower() or "/filing" in href.lower() or "/notice" in href.lower():
                    rows.append(_row(title,parent[:1200],href,name,"OFFICIAL_RPOWER",published));seen.add(href)
        except Exception as exc: print("OFFICIAL ERROR",name,exc)
    return rows

def collect_all():
    rows=collect_rss()+collect_gdelt()+collect_official()
    for mod,fn in [("api_collectors","collect_optional_apis"),("exchange_collectors","collect_nse_bse_official")]:
        try:
            m=__import__(mod,fromlist=[fn]);rows.extend(getattr(m,fn)())
        except Exception as exc: print("OPTIONAL COLLECTOR ERROR",mod,exc)
    df=pd.DataFrame(rows)
    if df.empty:return df
    # Final freshness and company relevance guard.
    df=df[df["published"].apply(lambda x: (not str(x).strip()) or _fresh(x))]
    df=df.drop_duplicates(subset=["id"]).reset_index(drop=True)
    return df
