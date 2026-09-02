from pathlib import Path
import json,pandas as pd,streamlit as st

st.set_page_config(page_title="NIFTY 500 Daily Intelligence",page_icon="📊",layout="wide")
D=Path(__file__).parent/"data"
NAMES={"RELIANCE":"Reliance Industries","RPOWER":"Reliance Power","TCS":"Tata Consultancy Services","INFY":"Infosys","SBIN":"State Bank of India","ITC":"ITC Limited","HDFCBANK":"HDFC Bank","ICICIBANK":"ICICI Bank","LT":"Larsen & Toubro","BHARTIARTL":"Bharti Airtel"}
def csv(n):
    try:return pd.read_csv(D/n) if (D/n).exists() else pd.DataFrame()
    except:return pd.DataFrame()
def js(n):
    try:return json.loads((D/n).read_text())
    except:return {}
def name(v):
    v=str(v).replace(".NS","").upper().strip()
    return NAMES.get(v,v)

r,s,a,n=js("nifty500_report.json"),csv("nifty500_scan.csv"),csv("nifty500_eod_audit.csv"),csv("nifty500_prediction_news.csv")
st.title("📊 NIFTY 500 Daily Intelligence")
st.caption(f"Prediction date: {r.get('prediction_date','Waiting')} • Prediction time: {r.get('prediction_time','—')} • EOD check: 5:00 PM IST")

# TABLE 1
st.header("🔮 Table 1 — Prediction: What do we expect and why?")
st.caption("This table explains which dated news and momentum evidence made each stock Bullish, Bearish or Neutral.")

if s.empty:
    st.warning("No prediction data yet.")
else:
    rows=[]
    for _,x in s.sort_values("priority").iterrows():
        ticker=str(x.get("ticker",""))
        nn=n[n["ticker"].astype(str)==ticker] if not n.empty and "ticker" in n else pd.DataFrame()
        bull=[]; bear=[]; neutral=[]
        for _,z in nn.iterrows():
            item=f"{z.get('published_at','Unknown time')} — {z.get('title','')}"
            if z.get("sentiment")=="BULLISH": bull.append(item)
            elif z.get("sentiment")=="BEARISH": bear.append(item)
            else: neutral.append(item)
        news_reason=("🟢 "+" | ".join(bull[:2])) if bull else ""
        if bear: news_reason += (" " if news_reason else "")+"🔴 "+" | ".join(bear[:2])
        if neutral: news_reason += (" " if news_reason else "")+"⚪ "+" | ".join(neutral[:1])
        if not news_reason: news_reason="No dated stock-specific news captured — momentum-led prediction."
        rows.append({
            "Priority":x.get("priority",""),
            "Stock":name(ticker),
            "Expected Direction":x.get("prediction","WAITING"),
            "Confidence %":x.get("confidence",""),
            "Why? — News":news_reason,
            "Why? — Momentum":f"1Y {x.get('1Y','—')}% | 6M {x.get('6M','—')}% | 1M {x.get('1M','—')}% | 1W {x.get('1W','—')}% | 1D {x.get('1D','—')}%",
        })
    st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)

# TABLE 2
st.header("🎯 Table 2 — 5 PM EOD Result: Did the prediction follow?")
st.caption("At 5 PM IST, the saved prediction is compared with the actual closing direction.")

if a.empty:
    st.info("No completed 5 PM EOD audit yet. Today's saved prediction will be checked after 5 PM IST.")
else:
    out=a.copy()
    out["Stock"]=out["ticker"].map(name)
    out["Result"]=out.get("matched",False).astype(str).str.lower().map({"true":"✅ YES — FOLLOWED","false":"❌ NO — DID NOT FOLLOW"}).fillna("—")
    cols=[x for x in ["trade_date","Stock","prediction","actual_eod","eod_move_pct","Result","prediction_reason","eod_reason","eod_checked_at"] if x in out]
    st.dataframe(out[cols],use_container_width=True,hide_index=True)
    valid=out[out["actual_eod"].isin(["BULLISH","BEARISH","NEUTRAL"])] if "actual_eod" in out else pd.DataFrame()
    if not valid.empty and "matched" in valid:
        win=(valid["matched"].astype(str).str.lower()=="true").mean()*100
        st.metric("Overall prediction accuracy",f"{win:.1f}%")
