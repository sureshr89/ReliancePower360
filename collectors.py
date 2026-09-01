from __future__ import annotations
import hashlib
from datetime import datetime, timezone
from urllib.parse import urljoin
import feedparser, pandas as pd, requests
from bs4 import BeautifulSoup
from config import RSS_SOURCES, GDELT_QUERY, GDELT_DOC_API, OFFICIAL_PAGES, SOURCE_RELIABILITY

HEADERS={"User-Agent":"ReliancePower360/1.1 public-research-bot"}

def _row(title, summary, link, source, source_type, published=""):
    key=hashlib.sha256((title+"|"+link).encode()).hexdigest()
    return {"id":key,"title":str(title).strip(),"summary":str(summary).strip(),"link":str(link).strip(),
            "source":source,"source_type":source_type,
            "source_reliability":SOURCE_RELIABILITY.get(source_type,.5),
            "published":published,"collected_at":datetime.now(timezone.utc).isoformat()}

def collect_rss():
    rows=[]
    for name,url in RSS_SOURCES:
        try:
            feed=feedparser.parse(url)
            for e in feed.entries[:80]:
                title=getattr(e,"title","").strip()
                if title: rows.append(_row(title,getattr(e,"summary",""),getattr(e,"link",""),name,"RSS",getattr(e,"published","")))
        except Exception as e: print("RSS ERROR",name,e)
    return rows

def collect_gdelt():
    rows=[]
    try:
        p={"query":GDELT_QUERY,"mode":"ArtList","format":"json","maxrecords":100,"sort":"HybridRel"}
        r=requests.get(GDELT_DOC_API,params=p,headers=HEADERS,timeout=30); r.raise_for_status()
        for a in r.json().get("articles",[]):
            if a.get("title") and a.get("url"):
                rows.append(_row(a["title"],a.get("domain",""),a["url"],a.get("domain","GDELT"),"GDELT",a.get("seendate","")))
    except Exception as e: print("GDELT ERROR",e)
    return rows

def collect_official():
    rows=[]
    for name,url in OFFICIAL_PAGES.items():
        try:
            r=requests.get(url,headers=HEADERS,timeout=30); r.raise_for_status()
            soup=BeautifulSoup(r.text,"lxml")
            for a in soup.find_all("a",href=True):
                title=" ".join(a.get_text(" ",strip=True).split())
                href=urljoin(url,a["href"])
                if len(title)<8 or href.startswith("javascript:") or href==url: continue
                parent=a.parent.get_text(" ",strip=True) if a.parent else ""
                if href.lower().endswith(".pdf") or "reliancepower.co.in" in href:
                    rows.append(_row(title,parent[:1200],href,name,"OFFICIAL_RPOWER"))
        except Exception as e: print("OFFICIAL ERROR",name,e)
    return rows

def collect_all():
    rows=collect_rss()+collect_gdelt()+collect_official()
    df=pd.DataFrame(rows)
    if df.empty:return df
    return df.drop_duplicates(subset=["id"]).reset_index(drop=True)
