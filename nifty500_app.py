from pathlib import Path
import json
import pandas as pd
import streamlit as st

st.set_page_config(page_title="NIFTY 500 Daily Intelligence",page_icon="📊",layout="wide")
D=Path(__file__).parent/"data"
def csv(n):
    try:return pd.read_csv(D/n) if (D/n).exists() else pd.DataFrame()
    except:return pd.DataFrame()
def js(n):
    try:return json.loads((D/n).read_text(encoding="utf-8"))
    except:return {}
r=js("nifty500_report.json");s=csv("nifty500_scan.csv");a=csv("nifty500_eod_audit.csv")
st.title("📊 NIFTY 500 Daily Intelligence")
st.caption(f"Prediction date: {r.get('prediction_date','Waiting')} • {r.get('prediction_time','—')}")
c1,c2,c3,c4=st.columns(4);c1.metric("Market Direction",r.get("market_direction","WAITING"));c2.metric("Stocks Scanned",r.get("universe_scanned",0));c3.metric("Bullish",r.get("bullish",0));c4.metric("Bearish",r.get("bearish",0))
st.header("🏆 Priority Order & Stock Sets")
if s.empty: st.warning("No scan data yet. Run GitHub Actions → NIFTY 500 Daily Scanner → Run workflow.")
else:
 cols=[x for x in ["priority","ticker","set","1Y","6M","1M","1W","1D","prediction","confidence","last_close"] if x in s.columns]
 st.dataframe(s[cols],use_container_width=True,hide_index=True)
st.header("🎯 EOD Analysis")
if a.empty:st.info("No completed EOD audit yet.")
else:
 st.dataframe(a,use_container_width=True,hide_index=True)
