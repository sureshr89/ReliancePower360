from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh

DATA=Path("data"); IST=ZoneInfo("Asia/Kolkata")
st.set_page_config(page_title="Reliance Power 360",page_icon="⚡",layout="wide")
st_autorefresh(interval=300000,limit=None,key="five_min_refresh")

@st.cache_data(ttl=300)
def csv(p):
    try:return pd.read_csv(p) if p.exists() and p.stat().st_size else pd.DataFrame()
    except Exception:return pd.DataFrame()
@st.cache_data(ttl=300)
def js(p):
    try:return json.loads(p.read_text()) if p.exists() else {}
    except Exception:return {}
def mood(x):
    x=str(x).upper();return "🟢" if x=="BULLISH" else "🔴" if x=="BEARISH" else "⚪"

r=js(DATA/"latest_report.json"); n=csv(DATA/"latest_news.csv"); ph=csv(DATA/"price_history.csv"); eod=csv(DATA/"eod_audit.csv")
s=r.get("summary",{}); p=r.get("price",{}); f=r.get("forecast",{}); drivers=r.get("today_explanation",{}); window=r.get("prediction_news_window",{})
now=datetime.now(IST); scan=pd.to_datetime(r.get("generated_at"),utc=True,errors="coerce")
scan_txt=scan.tz_convert(IST).strftime("%d %b %Y, %I:%M:%S %p IST") if not pd.isna(scan) else "Waiting"

st.title("⚡ Reliance Power 360°")
st.caption("Today + yesterday news intelligence • current-session prediction • EOD verification")
st.caption(f"Analysis: {scan_txt} • Auto-refresh: 5 minutes")

a,b,c,d,e=st.columns(5)
a.metric("Price",f"₹{p.get('last_price','—')}")
chg=p.get("daily_change_pct"); b.metric("Today",f"{chg:+.2f}%" if isinstance(chg,(int,float)) else "—")
c.metric("News Score",f"{s.get('news_score','—')}/100")
d.metric("Today News Used",window.get("today_articles",0))
e.metric("Yesterday News Used",window.get("yesterday_articles",0))

st.header("🔮 Today's Prediction")
st.caption("Only TODAY and YESTERDAY news are primary inputs. Weekly and monthly predictions are currently disabled.")
pred=f.get("current_session",{})
x,y=st.columns([1,2])
x.metric("Current / Remaining Session",f"{mood(pred.get('outlook'))} {pred.get('outlook','WAITING')}",f"{pred.get('score','—')}/100")
y.info(f.get("reason","Waiting for enough news and price data."))
st.caption(f"Evidence window: Today {window.get('today_articles',0)} • Yesterday {window.get('yesterday_articles',0)} • Total {window.get('used_total',0)}")

st.header("🔍 Why is the stock moving?")
st.write(drivers.get("explanation","Waiting for validated today/yesterday evidence."))
for item in drivers.get("today_drivers",[])[:8]:
    pub=pd.to_datetime(item.get("published"),utc=True,errors="coerce")
    ts=pub.tz_convert(IST).strftime("%d %b %Y, %I:%M %p IST") if not pd.isna(pub) else "Time unavailable"
    icon="🟢" if item.get("direction")=="positive" else "🔴" if item.get("direction")=="negative" else "⚪"
    st.markdown(f"{icon} **{item.get('title','Untitled')}**")
    st.caption(f"Source: {item.get('source','Unknown')} • Published: {ts} • Impact: {item.get('impact','—')}")

st.header("📊 Price & News")
l,rcol=st.columns(2)
with l:
    if not ph.empty and {"date","close"}.issubset(ph.columns):
        q=ph.copy();q["date"]=pd.to_datetime(q["date"],errors="coerce");q=q.dropna().sort_values("date").set_index("date")
        st.line_chart(q[["close"]],height=280)
with rcol:
    if not n.empty and "sentiment" in n.columns:
        st.bar_chart(n["sentiment"].fillna("NEUTRAL").value_counts(),height=280)

st.header("📰 Today & Yesterday News")
if n.empty: st.info("No collected news yet.")
else:
    n["_pub"]=pd.to_datetime(n.get("published"),utc=True,errors="coerce")
    n=n.sort_values("_pub",ascending=False)
    for _,row in n.head(40).iterrows():
        pub=row["_pub"]; ts=pub.tz_convert(IST).strftime("%d %b %Y, %I:%M %p IST") if not pd.isna(pub) else "Time unavailable"
        with st.expander(f"{mood(row.get('sentiment'))} {row.get('title','Untitled')}"):
            st.caption(f"Source: {row.get('source','Unknown')} • Published: {ts}")
            st.write(str(row.get("summary","")))
            if str(row.get("link","")).startswith("http"): st.link_button("Open original source",row["link"])

st.header("🎯 End-of-Day Check")
st.caption("After market close, the bot checks the latest pre-close prediction against the EOD outcome.")
if eod.empty: st.info("No completed EOD check yet.")
else: st.dataframe(eod.sort_values("trade_date",ascending=False),use_container_width=True,hide_index=True)

st.caption("Research tool only. Predictions are probabilistic, not guarantees.")
