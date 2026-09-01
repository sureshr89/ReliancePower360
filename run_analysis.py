from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path
from collectors import collect_all
from intelligence import analyse, deduplicate, outlook, timeframes

DATA=Path("data"); DATA.mkdir(exist_ok=True)

def main():
    raw=collect_all()
    analysed=analyse(raw)
    analysed=deduplicate(analysed)
    if not analysed.empty:
        analysed=analysed.sort_values(["impact","source_reliability","relevance"],ascending=False)
    analysed.to_csv(DATA/"latest_news.csv",index=False)
    base=outlook(analysed)
    report={
      "generated_at":datetime.now(timezone.utc).isoformat(),
      "company":"Reliance Power",
      "model_version":"1.0-multisource-360",
      "summary":{
        "news_score":base["score"],"news_outlook":base["outlook"],"confidence":base["confidence"],
        "article_count":int(len(analysed)),
        "bullish_count":int((analysed.get("sentiment")=="BULLISH").sum()) if not analysed.empty else 0,
        "bearish_count":int((analysed.get("sentiment")=="BEARISH").sum()) if not analysed.empty else 0,
        "neutral_count":int((analysed.get("sentiment")=="NEUTRAL").sum()) if not analysed.empty else 0,
      },
      "timeframes":timeframes(base),
      "source_breakdown":analysed.groupby("source_type").size().to_dict() if not analysed.empty else {},
      "top_bullish_news":analysed[analysed["sentiment"]=="BULLISH"].head(10).to_dict("records") if not analysed.empty else [],
      "top_bearish_news":analysed[analysed["sentiment"]=="BEARISH"].head(10).to_dict("records") if not analysed.empty else [],
    }
    (DATA/"latest_report.json").write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
    print(json.dumps(report,indent=2,ensure_ascii=False))

if __name__=="__main__": main()
