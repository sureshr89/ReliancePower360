from pathlib import Path
import json,pandas as pd,streamlit as st
st.set_page_config(page_title="NIFTY 500 Daily Intelligence",page_icon="📊",layout="wide")
D=Path(__file__).parent/"data"
def csv(n):
 try:return pd.read_csv(D/n) if (D/n).exists() else pd.DataFrame()
 except:return pd.DataFrame()
def js(n):
 try:return json.loads((D/n).read_text())
 except:return {}
r,s,a,n=js("nifty500_report.json"),csv("nifty500_scan.csv"),csv("nifty500_eod_audit.csv"),csv("nifty500_prediction_news.csv")
st.title("📊 NIFTY 500 Daily Intelligence")
st.caption(f"Prediction: {r.get('prediction_date','Waiting')} • {r.get('prediction_time','—')} | News evidence window: {' + '.join(r.get('news_window',[]))}")
c1,c2,c3,c4=st.columns(4);c1.metric("Market",r.get("market_direction","WAITING"));c2.metric("Scanned",r.get("universe_scanned",0));c3.metric("Bullish",r.get("bullish",0));c4.metric("Bearish",r.get("bearish",0))
st.header("🏆 Priority Order & Prediction")
if s.empty:st.warning("No scan data yet.")
else:st.dataframe(s[[x for x in ["priority","ticker","set","1Y","6M","1M","1W","1D","news_count","news_score","prediction","confidence","last_close"] if x in s]],use_container_width=True,hide_index=True)
st.header("📰 Why was this prediction made?")
st.caption("Only dated news from the prediction date and previous calendar day is used. Publication date/time and sentiment are shown.")
if n.empty:st.info("No dated stock-specific news was collected for this prediction window.")
else:st.dataframe(n[[x for x in ["ticker","sentiment","weight","published_date","published_at","source","title","link"] if x in n]],use_container_width=True,hide_index=True)
st.header("🎯 5 PM EOD Audit — Did the prediction win?")
if a.empty:st.info("No completed EOD audit yet.")
else:
 valid=a[a["actual_eod"].isin(["BULLISH","BEARISH","NEUTRAL"])].copy() if "actual_eod" in a else a
 if not valid.empty and "matched" in valid:
  win=(valid["matched"].astype(str).str.lower()=="true").mean()*100
  st.metric("Win percentage",f"{win:.1f}%")
 st.dataframe(a,use_container_width=True,hide_index=True)
