from pathlib import Path
import pandas as pd
DATA=Path("data")
def run():
 p=DATA/"nifty500_scan.csv"
 if not p.exists():return
 # Placeholder audit file: EOD price collector can populate actual prices without changing prediction snapshots.
 if not (DATA/"nifty500_eod_audit.csv").exists(): pd.DataFrame(columns=["trade_date","ticker","priority","set","prediction","actual_eod","eod_move_pct","matched"]).to_csv(DATA/"nifty500_eod_audit.csv",index=False)
if __name__=="__main__":run()
