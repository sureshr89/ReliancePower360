from __future__ import annotations
from pathlib import Path
import pandas as pd

DATA=Path("data")
DATA.mkdir(exist_ok=True)
HISTORY=DATA/"signal_history.csv"

def append_history(row: dict) -> None:
    new=pd.DataFrame([row])
    if HISTORY.exists():
        old=pd.read_csv(HISTORY)
        new=pd.concat([old,new],ignore_index=True)
    new.to_csv(HISTORY,index=False)
