from __future__ import annotations
from datetime import datetime, timedelta, timezone
import pandas as pd

def _label(score: float) -> str:
    if score >= 70: return "BULLISH"
    if score <= 30: return "BEARISH"
    return "NEUTRAL"

def build_explanations(news: pd.DataFrame, price: dict) -> dict:
    if news.empty:
        return {"today_drivers":[],"explanation":"No fresh company-relevant news collected yet."}
    ranked=news.sort_values("weighted_signal",key=lambda s:s.abs(),ascending=False).head(8)
    drivers=[]
    for _,r in ranked.iterrows():
        signal=float(r.get("weighted_signal",0))
        direction="positive" if signal>0 else "negative" if signal<0 else "mixed"
        drivers.append({
            "direction":direction,
            "title":str(r.get("title","")),
            "source":str(r.get("source","")),
            "impact":int(r.get("impact",1)),
            "signal":round(signal,3)
        })
    daily=float(price.get("daily_change_pct",0)) if price else 0
    move="rose" if daily>0 else "fell" if daily<0 else "was flat"
    return {"today_drivers":drivers,"explanation":f"Reliance Power {move} {daily:+.2f}% today. The ranked fresh-news drivers below are the bot's evidence-based candidates; the bot does not claim news proves causation."}

def forecast(news: pd.DataFrame, price: dict, base: dict) -> dict:
    # News signal is evidence, not certainty. Near-term reacts more strongly than long-term.
    weighted=float(news.get("weighted_signal",pd.Series(dtype=float)).sum()) if not news.empty else 0.0
    momentum=float(price.get("daily_change_pct",0)) if price else 0.0
    base_score=float(base.get("score",50))
    def calc(news_weight,momentum_weight):
        score=max(0,min(100,base_score+weighted*news_weight+momentum*momentum_weight))
        return {"score":round(score,1),"outlook":_label(score)}
    return {
        "tomorrow":calc(12,1.5),
        "next_week":calc(8,0.8),
        "next_few_months":calc(4,0.2),
        "reason":"Forecast combines fresh weighted news, current price momentum and the overall intelligence score. It is probabilistic, not a guarantee."
    }

def pending_outcomes(history: pd.DataFrame, today_price: float | None) -> list[dict]:
    # Evaluate earlier forecasts when enough time has passed and a current price is available.
    if history.empty or today_price is None: return []
    rows=[]
    for _,r in history.tail(60).iterrows():
        if pd.isna(r.get("price")): continue
        try:
            prior=float(r["price"])
            predicted=str(r.get("outlook","NEUTRAL"))
            actual_change=(today_price/prior-1)*100
            actual="BULLISH" if actual_change>1 else "BEARISH" if actual_change<-1 else "NEUTRAL"
            rows.append({
                "analysis_date":str(r.get("generated_at","")),
                "predicted":predicted,
                "actual_now":actual,
                "change_since_analysis_pct":round(actual_change,2),
                "matched":predicted==actual
            })
        except Exception:
            continue
    return rows
