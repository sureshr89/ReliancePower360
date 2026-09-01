from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
import streamlit as st

DATA=Path("data")
REPORT=DATA/"latest_report.json"
NEWS=DATA/"latest_news.csv"
AUDIT=DATA/"forecast_audit.csv"

st.set_page_config(page_title="Reliance Power 360",page_icon="⚡",layout="wide")

@st.cache_data(ttl=60)
def load_json(path):
    if not path.exists(): return {}
    try: return json.loads(path.read_text(encoding="utf-8"))
    except Exception: return {}

@st.cache_data(ttl=60)
def load_csv(path):
    try:
        if path.exists() and path.stat().st_size>0: return pd.read_csv(path)
    except Exception: pass
    return pd.DataFrame()

report=load_json(REPORT)
news=load_csv(NEWS)
audit=load_csv(AUDIT)
summary=report.get("summary",{})
price=report.get("price",{})
relation=report.get("news_price_relation",{})
today=report.get("today_explanation",{})
fc=report.get("forecast",{})
frames=report.get("timeframes",{})

st.title("⚡ Reliance Power 360° Intelligence")
st.caption("Fresh news • official disclosures • price movement • explanation • forecasts • prediction audit")
st.caption(f"Last scan: {report.get('generated_at','Waiting for first scan')} | Model: {report.get('model_version','Unknown')}")

if not report:
    st.warning("Dashboard is ready. Waiting for the first successful intelligence scan.")

# PRICE
st.subheader("📈 Reliance Power Price Today")
a,b,c,d=st.columns(4)
a.metric("Last Price",f"₹{price.get('last_price','—')}")
chg=price.get("daily_change_pct")
b.metric("Today",f"{chg:+.2f}%" if isinstance(chg,(int,float)) else "—")
chg5=price.get("five_day_change_pct")
c.metric("5-Day Move",f"{chg5:+.2f}%" if isinstance(chg5,(int,float)) else "—")
d.metric("Overall News Outlook",summary.get("news_outlook","WAITING"))

# WHY UP/DOWN
st.subheader("🔍 Why Did Reliance Power Move Today?")
st.write(today.get("explanation",relation.get("why_up_down","Waiting for fresh news and price data.")))
drivers=today.get("today_drivers",[])
if drivers:
    for x in drivers[:8]:
        icon="🟢" if x.get("direction")=="positive" else "🔴" if x.get("direction")=="negative" else "⚪"
        st.write(f"{icon} **{x.get('title','')}** — {x.get('source','Unknown')} | Impact {x.get('impact','—')}")
else:
    st.info("No ranked fresh-news drivers yet.")

# FORECAST
st.subheader("🔮 Forward Outlook")
cols=st.columns(3)
for col,key,title in zip(cols,["tomorrow","next_week","next_few_months"],["Tomorrow","Next Week","Next Few Months"]):
    x=fc.get(key,{})
    with col:
        st.metric(title,x.get("outlook","WAITING"),f"{x.get('score','—')}/100" if x else None)
st.caption(fc.get("reason","Forecast will appear after fresh news and price data are available."))

# EXISTING MULTI-TIMEFRAME
st.subheader("📅 Intelligence Timeframes")
cols=st.columns(3)
for col,key,title in zip(cols,["few_days","few_weeks","few_months"],["Few Days","Few Weeks","Few Months"]):
    x=frames.get(key,{})
    with col:
        st.metric(title,x.get("outlook","WAITING"),f"{x.get('score','—')}/100" if x else None)

# NEWS
st.subheader("📰 Fresh News Intelligence")
m1,m2,m3,m4=st.columns(4)
m1.metric("Articles",summary.get("article_count",len(news)))
m2.metric("Bullish",summary.get("bullish_count",0))
m3.metric("Bearish",summary.get("bearish_count",0))
m4.metric("Neutral",summary.get("neutral_count",0))

if news.empty:
    st.info("No fresh news collected yet. Run the GitHub Action and refresh this page.")
else:
    for col,val in {"impact":1,"sentiment_score":0.0,"sentiment":"NEUTRAL","title":"Untitled"}.items():
        if col not in news.columns: news[col]=val
    news=news.sort_values(["impact","sentiment_score"],ascending=[False,False])
    for _,r in news.head(20).iterrows():
        s=str(r.get("sentiment","NEUTRAL"))
        icon="🟢" if s=="BULLISH" else "🔴" if s=="BEARISH" else "⚪"
        with st.expander(f"{icon} {str(r.get('title','Untitled'))[:160]}"):
            st.write(str(r.get("summary","")))
            st.caption(f"Source: {r.get('source','Unknown')} | Impact: {r.get('impact','—')}")
            link=str(r.get("link",""))
            if link.startswith("http"): st.link_button("Open source",link)

# AUDIT
st.subheader("🎯 Previous Forecast vs What Happened")
if audit.empty:
    st.info("Forecast accuracy will build automatically after multiple scans and later price outcomes.")
else:
    st.dataframe(audit.sort_values("analysis_date",ascending=False),use_container_width=True,hide_index=True)
    if "matched" in audit.columns:
        accuracy=float(audit["matched"].mean()*100)
        st.metric("Current Recorded Match Rate",f"{accuracy:.1f}%")

st.divider()
st.caption("Research tool only. News can be correlated with a price move without proving it caused the move. Forecasts are probabilistic, not guaranteed.")
