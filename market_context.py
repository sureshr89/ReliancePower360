from __future__ import annotations
import requests

# Free public Yahoo chart endpoint. Optional context only; failures never stop news analysis.
def fetch_market_context():
    symbols={"nifty":"^NSEI","power_sector":"^CNXENERGY"}
    out={}
    for name,symbol in symbols.items():
        try:
            url=f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            data=requests.get(url,params={"range":"5d","interval":"1d"},timeout=20).json()
            result=data["chart"]["result"][0]
            closes=result["indicators"]["quote"][0]["close"]
            closes=[x for x in closes if x is not None]
            if len(closes)>=2:
                pct=(closes[-1]/closes[-2]-1)*100
                out[name]={"symbol":symbol,"daily_change_pct":round(pct,2)}
        except Exception as e:
            print("MARKET CONTEXT ERROR",name,e)
    return out
