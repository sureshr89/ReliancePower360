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
window=r.get("news_window",[])
st.caption(f"Prediction: {r.get('prediction_date','Waiting')} • {r.get('prediction_time','—')} | News evidence: {' + '.join(window) if window else 'No saved news window'}")
c1,c2,c3,c4=st.columns(4);c1.metric("Market",r.get("market_direction","WAITING"));c2.metric("Scanned",r.get("universe_scanned",0));c3.metric("Bullish",r.get("bullish",0));c4.metric("Bearish",r.get("bearish",0))
st.header("🏆 Priority Order & Prediction")
if s.empty: st.warning("No scan data yet.")
else:
 cols=[x for x in ["priority","ticker","set","1Y","6M","1M","1W","1D","momentum_score","news_count","news_score","prediction","confidence","last_close"] if x in s]
 st.dataframe(s[cols],use_container_width=True,hide_index=True)
st.header("🧠 How each prediction was calculated")
if s.empty: st.info("Run a fresh scan to create the prediction snapshot.")
else:
 for _,x in s.sort_values("priority").iterrows():
  ticker=x.get("ticker","")
  with st.expander(f"#{int(x.get('priority',0))} {ticker} → {x.get('prediction','WAITING')} ({x.get('confidence','—')}%)"):
   st.write(f"Momentum score: **{x.get('momentum_score','—')}** | News score: **{x.get('news_score','—')}** | Final prediction: **{x.get('prediction','—')}**")
   st.caption(f"Momentum inputs — 1Y {x.get('1Y','—')}% • 6M {x.get('6M','—')}% • 1M {x.get('1M','—')}% • 1W {x.get('1W','—')}% • 1D {x.get('1D','—')}%")
   nn=n[n["ticker"].astype(str)==str(ticker)] if not n.empty and "ticker" in n else pd.DataFrame()
   if nn.empty: st.info("No dated stock-specific news was captured for this stock. This prediction was momentum-led.")
   else: st.dataframe(nn[[z for z in ["sentiment","weight","published_date","published_at","source","title"] if z in nn]],use_container_width=True,hide_index=True)
st.header("🎯 5 PM EOD Audit — Prediction vs Actual")
if a.empty: st.info("No completed EOD audit yet.")
else:
 valid=a[a["actual_eod"].isin(["BULLISH","BEARISH","NEUTRAL"])].copy() if "actual_eod" in a else a
 if not valid.empty and "matched" in valid:
  m=valid["matched"].astype(str).str.lower()=="true"
  c1,c2,c3=st.columns(3);c1.metric("Total",len(valid));c2.metric("Correct",int(m.sum()));c3.metric("Win %",f"{m.mean()*100:.1f}%")
 st.dataframe(a,use_container_width=True,hide_index=True)
