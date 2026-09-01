from __future__ import annotations
import json
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path
from collectors import collect_all
from intelligence import analyse, deduplicate, outlook, timeframes
from market_context import fetch_market_context
from price_tracker import fetch_reliance_power_price
from news_price_analysis import explain_price_news_relation
from forecast_engine import build_explanations, forecast, pending_outcomes
from forecast_audit import update_audit
from data_store import append_history

DATA=Path("data"); DATA.mkdir(exist_ok=True)

def main():
    # Every run fetches current sources. There is no fixed 2025 news window.
    raw=collect_all()
    analysed=deduplicate(analyse(raw))

    if not analysed.empty:
        analysed=analysed.sort_values(["impact","source_reliability","relevance"],ascending=False)

    analysed.to_csv(DATA/"latest_news.csv",index=False)

    base=outlook(analysed)
    frames=timeframes(base)
    market=fetch_market_context()
    price=fetch_reliance_power_price()
    relation=explain_price_news_relation(analysed,price)
    explanations=build_explanations(analysed,price)
    forecasts=forecast(analysed,price,base)

    summary={
        "news_score":base["score"],"news_outlook":base["outlook"],"confidence":base["confidence"],
        "article_count":int(len(analysed)),
        "bullish_count":int((analysed["sentiment"]=="BULLISH").sum()) if not analysed.empty else 0,
        "bearish_count":int((analysed["sentiment"]=="BEARISH").sum()) if not analysed.empty else 0,
        "neutral_count":int((analysed["sentiment"]=="NEUTRAL").sum()) if not analysed.empty else 0,
    }

    report={
      "generated_at":datetime.now(timezone.utc).isoformat(),
      "company":"Reliance Power",
      "model_version":"1.2-fresh-news-price-relation",
      "summary":summary,
      "timeframes":frames,
      "market_context":market,
      "price":price,
      "news_price_relation":relation,
      "today_explanation":explanations,
      "forecast":forecasts,
      "source_breakdown":analysed.groupby("source_type").size().to_dict() if not analysed.empty else {},
      "top_bullish_news":analysed[analysed["sentiment"]=="BULLISH"].head(10).to_dict("records") if not analysed.empty else [],
      "top_bearish_news":analysed[analysed["sentiment"]=="BEARISH"].head(10).to_dict("records") if not analysed.empty else [],
    }
    (DATA/"latest_report.json").write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
    history_path=DATA/"signal_history.csv"
    prior_history=pd.read_csv(history_path) if history_path.exists() else pd.DataFrame()
    update_audit(pending_outcomes(prior_history,price.get("last_price")))
    append_history({
        "generated_at":report["generated_at"],"score":base["score"],"outlook":base["outlook"],
        "few_days":frames["few_days"]["score"],"few_weeks":frames["few_weeks"]["score"],
        "few_months":frames["few_months"]["score"],"articles":summary["article_count"],
        "price":price.get("last_price"),"daily_price_change_pct":price.get("daily_change_pct")
    })
    print(json.dumps({"articles":summary["article_count"],"price":price,"relation":relation,"outlook":summary["news_outlook"]},indent=2))

if __name__=="__main__":
    main()
