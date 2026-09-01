from __future__ import annotations
from pathlib import Path
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo

DATA=Path("data"); DATA.mkdir(exist_ok=True)
PRED=DATA/"session_predictions.csv"
EOD=DATA/"eod_audit.csv"
IST=ZoneInfo("Asia/Kolkata")

def record_prediction(generated_at, prediction, price):
    if not isinstance(price,(int,float)): return
    ts=pd.to_datetime(generated_at,utc=True,errors="coerce")
    if pd.isna(ts): return
    local=ts.tz_convert(IST)
    row={"analysis_time":local.isoformat(),"trade_date":str(local.date()),"prediction":prediction.get("outlook","NEUTRAL"),"score":prediction.get("score"),"analysis_price":price}
    df=pd.DataFrame([row])
    if PRED.exists(): df=pd.concat([pd.read_csv(PRED),df],ignore_index=True)
    df.drop_duplicates(subset=["analysis_time"],keep="last").to_csv(PRED,index=False)

def audit_eod(current_price):
    if not PRED.exists() or not isinstance(current_price,(int,float)): return
    now=datetime.now(IST)
    if now.time().hour<15 or (now.time().hour==15 and now.time().minute<30): return
    p=pd.read_csv(PRED)
    today=str(now.date()); p=p[p["trade_date"]==today]
    if p.empty:return
    latest=p.iloc[-1]
    actual_change=(current_price/float(latest["analysis_price"])-1)*100
    actual="BULLISH" if actual_change>0.5 else "BEARISH" if actual_change<-0.5 else "NEUTRAL"
    row={"trade_date":today,"prediction_time":latest["analysis_time"],"predicted":latest["prediction"],"actual_eod":actual,"change_from_prediction_pct":round(actual_change,2),"matched":str(latest["prediction"])==actual}
    df=pd.DataFrame([row])
    if EOD.exists():
        old=pd.read_csv(EOD); df=pd.concat([old[dfilter] if False else old,df],ignore_index=True)
    df=df.drop_duplicates(subset=["trade_date"],keep="last")
    df.to_csv(EOD,index=False)
