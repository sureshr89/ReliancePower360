from pathlib import Path
import json
import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="NIFTY 500 Daily Intelligence", page_icon="📊", layout="wide")
D=Path(__file__).parent/"data"

NAMES={"RELIANCE":"Reliance Industries","RPOWER":"Reliance Power","TCS":"Tata Consultancy Services","INFY":"Infosys","SBIN":"State Bank of India","ITC":"ITC Limited","HDFCBANK":"HDFC Bank","ICICIBANK":"ICICI Bank","LT":"Larsen & Toubro","BHARTIARTL":"Bharti Airtel"}
INDEXES=[("NIFTY 50","^NSEI"),("NIFTY BANK","^NSEBANK"),("SENSEX","^BSESN"),("NIFTY IT","^CNXIT"),("NIFTY MIDCAP 50","^NSEMDCP50")]

def csv(n):
    try: return pd.read_csv(D/n) if (D/n).exists() else pd.DataFrame()
    except Exception: return pd.DataFrame()

def js(n):
    try: return json.loads((D/n).read_text())
    except Exception: return {}

def name(v):
    v=str(v).replace(".NS","").upper().strip()
    return NAMES.get(v,v)

@st.cache_data(ttl=45)
def live_index(symbol):
    try:
        from urllib.parse import quote
        url="https://query1.finance.yahoo.com/v8/finance/chart/"+quote(symbol,safe="")
        j=requests.get(url,params={"range":"2d","interval":"1m"},headers={"User-Agent":"Mozilla/5.0"},timeout=8).json()
        z=j["chart"]["result"][0]
        vals=[x for x in z["indicators"]["quote"][0].get("close",[]) if x is not None]
        if not vals: return None,None
        last=float(vals[-1])
        prev=z.get("meta",{}).get("chartPreviousClose") or z.get("meta",{}).get("previousClose")
        move=(last/float(prev)-1)*100 if prev else None
        return last,move
    except Exception:
        return None,None

r=js("nifty500_report.json")
s=csv("nifty500_scan.csv")
a=csv("nifty500_eod_audit.csv")
n=csv("nifty500_prediction_news.csv")

st.title("📊 NIFTY 500 Daily Intelligence")
st.caption(f"Prediction date: {r.get('prediction_date','Waiting')} • Prediction time: {r.get('prediction_time','—')} • EOD audit: 5:00 PM IST")
st.caption("Dashboard refresh: every 1 minute • Prediction news: previous day + prediction-day news published before prediction time")
try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=60*1000,key="live_refresh")
except Exception:
    pass

st.header("📈 Live Market — 5 Key Indices")
idx=[]
for label,symbol in INDEXES:
    last,move=live_index(symbol)
    idx.append({"Index":label,"Live Value":"—" if last is None else f"{last:,.2f}","Today":"—" if move is None else f"{move:+.2f}%","Direction":"WAITING" if move is None else ("🟢 UP" if move>0 else "🔴 DOWN" if move<0 else "⚪ FLAT")})
st.dataframe(pd.DataFrame(idx),use_container_width=True,hide_index=True)

st.header("🔮 Table 1 — Prediction: What do we expect and why?")
st.caption("The saved prediction snapshot shows exactly what evidence was available before the prediction.")
if s.empty:
    st.warning("No prediction data yet.")
else:
    rows=[]
    for _,x in s.sort_values("priority").iterrows():
        ticker=str(x.get("ticker",""))
        nn=n[n["ticker"].astype(str)==ticker] if not n.empty and "ticker" in n else pd.DataFrame()
        headlines=[]
        if not nn.empty:
            for _,z in nn.head(3).iterrows():
                tag={"BULLISH":"🟢","BEARISH":"🔴"}.get(str(z.get("sentiment")),"⚪")
                headlines.append(f"{tag} {z.get('title','')}")
        rows.append({
            "Priority":x.get("priority",""),
            "Stock":name(ticker),
            "Prediction":x.get("prediction","WAITING"),
            "Confidence %":x.get("confidence",""),
            "Evidence": " | ".join(headlines) if headlines else "⚪ INSUFFICIENT NEWS EVIDENCE — prediction held neutral until dated stock news is collected.",
            "Momentum evidence":f"1Y {x.get('1Y','—')}% | 6M {x.get('6M','—')}% | 1M {x.get('1M','—')}% | 1W {x.get('1W','—')}% | 1D {x.get('1D','—')}%"
        })
    st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)

    st.subheader("📰 Exact Article Headings Used")
    if n.empty:
        st.info("No dated article headings were saved in this prediction snapshot.")
    else:
        articles=n.copy()
        articles["Stock"]=articles["ticker"].map(name)
        articles["News Signal"]=articles["sentiment"].map({"BULLISH":"🟢 BULLISH","BEARISH":"🔴 BEARISH","NEUTRAL":"⚪ NEUTRAL"}).fillna("⚪ NEUTRAL")
        cols=[z for z in ["Stock","News Signal","weight","published_date","published_at","source","title","link"] if z in articles]
        st.dataframe(articles[cols],use_container_width=True,hide_index=True)

st.header("🎯 Table 2 — 5 PM EOD Result: Did the prediction follow?")
st.caption("The actual EOD direction is compared with the saved pre-EOD prediction.")
if a.empty:
    st.info("No completed EOD audit yet. The saved prediction will be checked at 5:00 PM IST.")
else:
    out=a.copy()
    if "ticker" in out: out["Stock"]=out["ticker"].map(name)
    out["Result"]=out.get("matched",False).astype(str).str.lower().map({"true":"✅ YES — FOLLOWED","false":"❌ NO — DID NOT FOLLOW"}).fillna("—")
    cols=[x for x in ["trade_date","Stock","prediction","actual_eod","eod_move_pct","Result","prediction_reason","eod_reason","eod_checked_at"] if x in out]
    st.dataframe(out[cols],use_container_width=True,hide_index=True)
    valid=out[out["actual_eod"].isin(["BULLISH","BEARISH","NEUTRAL"])] if "actual_eod" in out else pd.DataFrame()
    if not valid.empty and "matched" in valid:
        win=(valid["matched"].astype(str).str.lower()=="true").mean()*100
        c1,c2,c3=st.columns(3)
        c1.metric("Predictions",len(valid))
        c2.metric("Correct",int((valid["matched"].astype(str).str.lower()=="true").sum()))
        c3.metric("Win %",f"{win:.1f}%")
