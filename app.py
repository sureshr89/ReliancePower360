from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import streamlit as st

try:
    from streamlit_autorefresh import st_autorefresh
except Exception:
    st_autorefresh=None

DATA=Path("data")
IST=ZoneInfo("Asia/Kolkata")

st.set_page_config(page_title="Reliance Power 360",page_icon="⚡",layout="centered",initial_sidebar_state="collapsed")
if st_autorefresh:
    st_autorefresh(interval=300000,limit=None,key="refresh")

st.markdown("""<style>
.block-container{max-width:720px;padding:1rem .75rem 3rem}
h1{font-size:1.55rem!important} h2{font-size:1.15rem!important}
div[data-testid="stMetric"]{border:1px solid rgba(128,128,128,.2);border-radius:12px;padding:.5rem}
@media(max-width:600px){.block-container{padding:.7rem .55rem 2rem}h1{font-size:1.35rem!important}}
</style>""",unsafe_allow_html=True)

@st.cache_data(ttl=300)
def load_json(path):
    try:return json.loads(path.read_text()) if path.exists() else {}
    except Exception:return {}

@st.cache_data(ttl=300)
def load_csv(path):
    try:return pd.read_csv(path) if path.exists() and path.stat().st_size else pd.DataFrame()
    except Exception:return pd.DataFrame()

def mood(value):
    v=str(value).upper()
    return "🟢" if v=="BULLISH" else "🔴" if v=="BEARISH" else "⚪"

def format_news_date(value):
    ts=pd.to_datetime(value,utc=True,errors="coerce")
    return ts.tz_convert(IST).strftime("%d %b %Y, %I:%M %p IST") if not pd.isna(ts) else "Publication time unavailable"

report=load_json(DATA/"latest_report.json")
news=load_csv(DATA/"latest_news.csv")
eod=load_csv(DATA/"eod_audit.csv")
now=datetime.now(IST)
today=now.date()
yesterday=(now-pd.Timedelta(days=1)).date()
window=report.get("prediction_news_window",{})
forecast=report.get("forecast",{}).get("current_session",{})

st.title("⚡ Reliance Power 360°")
st.caption("Date-based news prediction • end-of-day verification")
st.caption(f"Prediction date: {today.strftime('%d %b %Y')}")

st.header("🔮 Current Prediction")
c1,c2=st.columns(2)
c1.metric("Prediction",f"{mood(forecast.get('outlook','WAITING'))} {forecast.get('outlook','WAITING')}")
c2.metric("Score",f"{forecast.get('score','—')}/100")
st.caption(f"News used before this prediction: {yesterday.strftime('%d %b %Y')} and {today.strftime('%d %b %Y')} (only news published before the prediction time should count).")

if not news.empty:
    if "published" in news.columns:
        news["_pub"]=pd.to_datetime(news["published"],utc=True,errors="coerce")
        news["_ist"]=news["_pub"].dt.tz_convert(IST)
        news["_date"]=news["_ist"].dt.date
    else:
        news["_date"]=pd.NaT

    used_today=news[news["_date"]==today].sort_values("_pub",ascending=False)
    used_yesterday=news[news["_date"]==yesterday].sort_values("_pub",ascending=False)

    st.header("📅 News Used Before This Prediction")

    st.subheader(f"🟢 {today.strftime('%d %b %Y')} — {len(used_today)} articles")
    if used_today.empty:
        st.caption("No dated news available for this date.")
    else:
        for _,row in used_today.iterrows():
            st.markdown(f"{mood(row.get('sentiment'))} **{row.get('title','Untitled')}**")
            st.caption(f"{row.get('source','Unknown')} • {format_news_date(row.get('published'))}")

    st.divider()

    st.subheader(f"🟡 {yesterday.strftime('%d %b %Y')} — {len(used_yesterday)} articles")
    if used_yesterday.empty:
        st.caption("No dated news available for this date.")
    else:
        for _,row in used_yesterday.iterrows():
            st.markdown(f"{mood(row.get('sentiment'))} **{row.get('title','Untitled')}**")
            st.caption(f"{row.get('source','Unknown')} • {format_news_date(row.get('published'))}")
else:
    st.header("📅 News Used for Prediction")
    st.info("No collected news data available yet.")

st.divider()
st.header("🎯 EOD Result — Did Our Prediction Win?")
st.caption("Each prediction is compared with the actual end-of-day direction. RIGHT = win, WRONG = loss.")

if eod.empty:
    st.info("No completed EOD audit yet.")
else:
    audit=eod.copy()
    audit["result"]=audit["matched"].apply(lambda x:"✅ RIGHT" if str(x).lower()=="true" else "❌ WRONG") if "matched" in audit.columns else "—"

    preferred=["trade_date","prediction_time","predicted","actual_eod","change_from_prediction_pct","result"]
    cols=[x for x in preferred if x in audit.columns]
    st.dataframe(audit[cols].sort_values("trade_date",ascending=False),use_container_width=True,hide_index=True)

    if "result" in audit.columns:
        right=int((audit["result"]=="✅ RIGHT").sum())
        wrong=int((audit["result"]=="❌ WRONG").sum())
        total=right+wrong
        accuracy=(right/total*100) if total else 0
        a,b,c=st.columns(3)
        a.metric("Wins / Right",right)
        b.metric("Losses / Wrong",wrong)
        c.metric("Win Percentage",f"{accuracy:.1f}%")

st.caption("Research tool only. Prediction outcomes are recorded for audit and improvement.")
