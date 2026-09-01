from __future__ import annotations
from pathlib import Path
import pandas as pd

DATA=Path("data")
AUDIT=DATA/"forecast_audit.csv"

def update_audit(outcomes:list[dict]):
    if not outcomes:
        return
    new=pd.DataFrame(outcomes)
    if AUDIT.exists():
        old=pd.read_csv(AUDIT)
        new=pd.concat([old,new],ignore_index=True)
    new=new.drop_duplicates(subset=["analysis_date"],keep="last")
    new.to_csv(AUDIT,index=False)
