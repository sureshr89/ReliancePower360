from __future__ import annotations
import hashlib, re
from datetime import datetime, timezone
from urllib.parse import urljoin
import feedparser, pandas as pd, requests
from bs4 import BeautifulSoup
from config import RSS_SOURCES, GDELT_QUERY, GDELT_DOC_API, OFFICIAL_PAGES, SOURCE_RELIABILITY

HEADERS={"User-Agent":"ReliancePower360/1.0 public-research-bot"}

def _row(title, summary, link, source, source_type, published=""):
    key=hashlib.sha256((title+"|"+link).encode()).hexdigest()
    return {"id":key,"title":title.strip(),"summary":summary.strip(),"link":link.strip(),
            "source":source,"source_type":source_type,
            "source_reliability":SOURCE_RELIABILITY[source_type],
            "published":published,"collected_at":datetime.now(timezone.utc).isoformat()}

def collect_rss():
    rows=[]
    for name,url in RSS_SOURCES:
        try:
            feed=feedparser.parse(url)
            for e in feed.entries[:60]:
                title=getattr(e,"title","").strip()
                link=getattr(e,"link","").strip()
                if title: rows.append(_row(title,getattr(e,"summary",""),link,name,"RSS",getattr(e,"published","")))
        except Exception as e: print("RSS",name,e)
    return rows

def collect_gdelt():
    rows=[]
    try:
        params={"query":GDELT_QUERY,"mode":"ArtList","format":"json","maxrecords":100,"sort":"HybridRel"}
        r=requests.get(GDELT_DOC_API,params=params,headers=HEADERS,timeout=30); r.raise_for_status()
        for a in r.json().get("articles",[]):
            title=a.get("title",""); link=a.get("url","")
            if title and link: rows.append(_row(title,a.get("socialimage",""),link,a.get("domain","GDELT"),"GDELT",a.get("seendate","")))
    except Exception as e: print("GDELT",e)
    return rows

def collect_official():
    rows=[]
    for name,url in OFFICIAL_PAGES.items():
        try:
            r=requests.get(url,headers=HEADERS,timeout=30); r.raise_for_status()
            soup=BeautifulSoup(r.text,"lxml")
            seen=set()
            for a in soup.find_all("a",href=True):
                title=" ".join(a.get_text(" ",strip=True).split()); href=urljoin(url,a["href"])
                if len(title)<8 or href in seen: continue
                if any(x in href.lower() for x in ["javascript:","#"]): continue
                context=" ".join(a.parent.get_text(" ",strip=True).split()) if a.parent else ""
                # Keep document/announcement-like links and company-domain pages.
                if href.lower().endswith((".pdf",".html",".htm")) or "reliancepower.co.in" in href:
                    rows.append(_row(title,context[:1000],href,name,"OFFICIAL_RPOWER"))
                    seen.add(href)
        except Exception as e: print("OFFICIAL",name,e)
    return rows

def collect_exchange_search():
    # Exchange endpoints change frequently; this collector uses public search URLs as leads
    # and marks them separately so the engine never pretends they are official filings unless verified.
    rows=[]
    queries=[
      ("NSE corporate announcements search","https://www.google.com/search?q=site%3Anseindia.com+%22Reliance+Power%22+announcement"),
      ("BSE corporate announcements search","https://www.google.com/search?q=site%3Abseindia.com+%22Reliance+Power%22+announcement"),
    ]
    for name,url in queries:
        rows.append(_row(name,"Public search lead for official exchange disclosure discovery",url,name,"EXCHANGE"))
    return rows

def collect_all():
    rows=collect_rss()+collect_gdelt()+collect_official()+collect_exchange_search()
    df=pd.DataFrame(rows)
    if df.empty: return df
    return df.drop_duplicates(subset=["id"]).reset_index(drop=True)
