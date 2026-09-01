from pathlib import Path
import json,pandas as pd,streamlit as st
D=Path("data")
def rd(n):
 p=D/n
 try:return pd.read_csv(p) if p.exists() else pd.DataFrame()
 except:return pd.DataFrame()
def rj(n):
 try:return json.loads((D/n).read_text())
 except:return {}
r=rj("nifty500_report.json");s=rd("nifty500_scan.csv");a=rd("nifty500_eod_audit.csv")
st.set_page_config(page_title="NIFTY 500 Daily Intelligence",page_icon="📊",layout="wide")
st.title("📊 NIFTY 500 Daily Intelligence")
st.caption(f"Prediction date: {r.get('prediction_date','—')} • {r.get('prediction_time','—')}")
x,y,z,w=st.columns(4);x.metric("Market Direction",r.get("market_direction","WAITING"));y.metric("Scanned",r.get("universe_scanned",0));z.metric("Bullish",r.get("bullish",0));w.metric("Bearish",r.get("bearish",0))
st.header("🏆 Priority Order & Stock Sets")
if s.empty:st.info("No scan yet.")
else:st.dataframe(s[[c for c in ["priority","ticker","set","1Y","6M","1M","1W","1D","prediction","confidence","last_close"] if c in s]],use_container_width=True,hide_index=True)
st.header("🎯 EOD Analysis")
if a.empty:st.info("No completed EOD audit yet.")
else:
 a["Result"]=a["matched"].astype(str).str.lower().map({"true":"✅ RIGHT","false":"❌ WRONG"}).fillna("—");right=(a.Result=="✅ RIGHT").sum();wrong=(a.Result=="❌ WRONG").sum();t=right+wrong
 p,q,r3=st.columns(3);p.metric("Right",right);q.metric("Wrong",wrong);r3.metric("Win %",f"{right/t*100 if t else 0:.1f}%");st.dataframe(a,use_container_width=True,hide_index=True)
