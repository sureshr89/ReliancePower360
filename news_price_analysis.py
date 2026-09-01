from __future__ import annotations
import pandas as pd

def explain_price_news_relation(news: pd.DataFrame, price: dict) -> dict:
    if news.empty or not price:
        return {"status":"INSUFFICIENT_DATA","explanation":"Fresh news and/or price data is not yet sufficient."}

    weighted=float(news.get("weighted_signal",pd.Series(dtype=float)).sum())
    news_bias="POSITIVE" if weighted>0 else "NEGATIVE" if weighted<0 else "MIXED"
    daily=float(price.get("daily_change_pct",0))
    five=float(price.get("five_day_change_pct",0))

    if daily>1 and news_bias=="POSITIVE":
        relation="News and price are moving in the same positive direction."
    elif daily<-1 and news_bias=="NEGATIVE":
        relation="News and price are moving in the same negative direction."
    elif daily>1 and news_bias=="NEGATIVE":
        relation="Price rose despite negative news; momentum, broader market, positioning or older expectations may be dominating."
    elif daily<-1 and news_bias=="POSITIVE":
        relation="Price fell despite positive news; profit-taking, valuation, market weakness or expectations may be dominating."
    else:
        relation="No strong same-day relationship detected; news impact may be delayed or mixed."

    return {
        "status":"OK","news_bias":news_bias,
        "daily_price_change_pct":daily,
        "five_day_price_change_pct":five,
        "relation":relation,
        "why_up_down":relation
    }
