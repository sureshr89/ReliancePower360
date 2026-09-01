from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
from zoneinfo import ZoneInfo

DATA = Path("data")
IST = ZoneInfo("Asia/Kolkata")
# Refresh the dashboard UI every 15 seconds. GitHub scanning remains on its own schedule.\nst_autorefresh(interval=300_000, limit=None, key="rpower_5min_refresh")
st.set_page_config(page_title="Reliance Power 360", page_icon="⚡", layout="wide", initial_sidebar_state="collapsed")

@st.cache_data(ttl=300)
def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except Exception:
        return {}

@st.cache_data(ttl=300)
def load_csv(path):
    try:
        return pd.read_csv(path) if path.exists() and path.stat().st_size else pd.DataFrame()
    except Exception:
        return pd.DataFrame()

def mood(v):
    s=str(v or "WAITING").upper()
    return "🟢" if s=="BULLISH" else "🔴" if s=="BEARISH" else "⚪"

def num(v, suffix=""):
    return f"{v}{suffix}" if isinstance(v,(int,float)) else "—"

report=load_json(DATA/"latest_report.json")
news=load_csv(DATA/"latest_news.csv")
price_history=load_csv(DATA/"price_history.csv")
history=load_csv(DATA/"signal_history.csv")
audit=load_csv(DATA/"forecast_audit.csv")

summary=report.get("summary",{})
price=report.get("price",{})
today=report.get("today_explanation",{})
relation=report.get("news_price_relation",{})
forecast=report.get("forecast",{})
now_ist=datetime.now(IST)
scan_ist=pd.to_datetime(scan,utc=True,errors="coerce")
scan_label=scan_ist.tz_convert(IST).strftime("%d %b %Y, %I:%M:%S %p IST") if not pd.isna(scan_ist) else str(scan)
scan=report.get("generated_at","Waiting for live scan")

st.markdown("""
<style>
.block-container{max-width:1450px;padding-top:1.4rem;padding-bottom:2rem}
div[data-testid="stMetric"]{border:1px solid rgba(128,128,128,.20);padding:16px;border-radius:14px;background:rgba(128,128,128,.035)}
h1{margin-bottom:.1rem}
.section-title{font-size:1.35rem;font-weight:700;margin-top:1rem;margin-bottom:.45rem}
.small-note{opacity:.7;font-size:.85rem}
</style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
left,right=st.columns([3,1])
with left:
    st.title("⚡ Reliance Power 360°")
    st.caption("Live market intelligence • fresh news • price drivers • forward scenarios")
with right:
    st.markdown("**Latest analysis**")
    st.caption(f"Analysis generated: {scan_label}")
    now_ist=datetime.now(IST)
    st.caption(f"🟢 Auto-refresh every 5 minutes • {now_ist.strftime('%d %b %Y, %I:%M:%S %p IST')}")

if not report:
    st.warning("Waiting for the first successful live scan.")

# ---------- TOP DECISION PANEL ----------
st.markdown('<div class="section-title">Market Snapshot</div>', unsafe_allow_html=True)
c1,c2,c3,c4,c5=st.columns(5)
c1.metric("Reliance Power", f"₹{price['last_price']:.2f}" if isinstance(price.get("last_price"),(int,float)) else "Waiting")
d=price.get("daily_change_pct")
c2.metric("Today", f"{d:+.2f}%" if isinstance(d,(int,float)) else "Waiting")
w=price.get("five_day_change_pct")
c3.metric("5-Day Move", f"{w:+.2f}%" if isinstance(w,(int,float)) else "Waiting")
c4.metric("News Score", f"{summary.get('news_score','—')}/100")
c5.metric("Current Bias", f"{mood(summary.get('news_outlook'))} {summary.get('news_outlook','WAITING')}")

# ---------- MAIN STORY ----------
st.markdown('<div class="section-title">What is driving the stock now?</div>', unsafe_allow_html=True)
main,side=st.columns([2,1])
with main:
    explanation=today.get("explanation") or relation.get("why_up_down") or "Live price/news relationship will appear after the next complete scan."
    st.info(explanation)
    drivers=today.get("today_drivers",[])
    if drivers:
        for x in drivers[:5]:
            st.markdown(f"{'🟢' if x.get('direction')=='positive' else '🔴' if x.get('direction')=='negative' else '⚪'} **{x.get('title','Untitled')}**")
            st.caption(f"{x.get('source','Unknown')} • Impact {x.get('impact','—')}")
    else:
        st.caption("No validated same-day drivers available yet.")
with side:
    st.markdown("**Evidence status**")
    st.metric("Fresh articles", summary.get("article_count",len(news)))
    st.metric("Bullish signals", summary.get("bullish_count",0))
    st.metric("Bearish signals", summary.get("bearish_count",0))

# ---------- FORECAST ----------
st.markdown('<div class="section-title">Forward Outlook</div>', unsafe_allow_html=True)
st.caption("Scenario signals derived from fresh news, weighted source quality and current momentum. Not a price target.")
a,b,c=st.columns(3)
targets={"tomorrow":(now_ist+pd.Timedelta(days=1)).strftime("%d %b %Y"),"next_week":(now_ist+pd.Timedelta(days=7)).strftime("%d %b %Y"),"next_few_months":(now_ist+pd.Timedelta(days=90)).strftime("%d %b %Y")}
for col,key,label in [(a,"tomorrow","Tomorrow"),(b,"next_week","Next Week"),(c,"next_few_months","Next Few Months")]:
    x=forecast.get(key,{})
    with col:
        outlook=x.get("outlook","WAITING")
        st.metric(f"{label} • {targets[key]}", f"{mood(outlook)} {outlook}", f"{x.get('score','—')}/100")
st.caption(forecast.get("reason","Forecast will become available when price and fresh-news inputs are both available."))

# ---------- CHARTS ----------
st.markdown('<div class="section-title">Visual Intelligence</div>', unsafe_allow_html=True)
ch1,ch2=st.columns(2)

with ch1:
    st.markdown("**Price trend**")
    if not price_history.empty and {"date","close"}.issubset(price_history.columns):
        ph=price_history.copy()
        ph["date"]=pd.to_datetime(ph["date"],errors="coerce")
        ph=ph.dropna(subset=["date"]).sort_values("date").set_index("date")
        st.line_chart(ph[["close"]],height=320)
    else:
        st.caption("Price history is not available yet.")

with ch2:
    st.markdown("**News balance**")
    if not news.empty and "sentiment" in news.columns:
        order=["BULLISH","BEARISH","NEUTRAL"]
        counts=news["sentiment"].fillna("NEUTRAL").value_counts().reindex(order,fill_value=0)
        st.bar_chart(counts,height=320)
    else:
        st.caption("Fresh-news sentiment will appear after a scan.")

if not history.empty and "score" in history.columns:
    st.markdown("**Intelligence score over time**")
    h=history.copy()
    if "generated_at" in h.columns:
        h["generated_at"]=pd.to_datetime(h["generated_at"],errors="coerce")
        h=h.dropna(subset=["generated_at"]).sort_values("generated_at").set_index("generated_at")
    st.line_chart(h[["score"]],height=260)

# ---------- NEWS ----------
st.markdown('<div class="section-title">Fresh News Feed</div>', unsafe_allow_html=True)
st.caption("Only relevant collected items should influence the score. Read the source before acting.")
if news.empty:
    st.info("No fresh news is available yet.")
else:
    for col,default in {"impact":1,"sentiment":"NEUTRAL","title":"Untitled","published":""}.items():
        if col not in news.columns: news[col]=default
    if "published" in news.columns:
        news["_published"]=pd.to_datetime(news["published"],utc=True,errors="coerce")
        news=news.sort_values(["_published","impact"],ascending=[False,False],na_position="last")
    else:
        news=news.sort_values("impact",ascending=False)
    filter_choice=st.radio("Show",["All","Bullish","Bearish","Neutral"],horizontal=True)
    shown=news if filter_choice=="All" else news[news["sentiment"]==filter_choice.upper()]
    for _,r in shown.head(30).iterrows():
        s=str(r.get("sentiment","NEUTRAL")).upper()
        icon=mood(s)
        date=str(r.get("published",""))
        pub=pd.to_datetime(date,utc=True,errors="coerce")
        published_label=pub.tz_convert(IST).strftime("%d %b %Y, %I:%M %p IST") if not pd.isna(pub) else "Publication time unavailable"
        with st.expander(f"{icon} {r.get('title','Untitled')}"):
            if str(r.get("summary","")).strip(): st.write(str(r.get("summary","")))
            st.caption(f"{r.get('source','Unknown')} • Published: {published_label}")
            link=str(r.get("link",""))
            if link.startswith("http"): st.link_button("Read original source",link)

# ---------- AUDIT ----------
st.markdown('<div class="section-title">Forecast Track Record</div>', unsafe_allow_html=True)
if audit.empty:
    st.caption("The track record will build as earlier forecasts receive enough later price data for evaluation.")
else:
    if "matched" in audit.columns:
        st.metric("Recorded directional match rate",f"{audit['matched'].astype(bool).mean()*100:.1f}%")
    st.dataframe(audit.sort_values("analysis_date",ascending=False),use_container_width=True,hide_index=True)

st.divider()
st.caption("Research and intelligence tool only. A news item may correlate with a price move without proving causation. Forecasts are probabilistic and are not financial advice.")
