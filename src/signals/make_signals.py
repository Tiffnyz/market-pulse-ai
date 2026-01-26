import glob
import pandas as pd

BUY_DELTA = 0.20
SELL_DELTA = -0.20
MIN_VOLUME = 2

def load_latest_sentiment():
    files = sorted(glob.glob("data/processed/news_*_sentiment.csv"))
    if not files:
        raise SystemExit("No sentiment files found. Run: python -m src.nlp.sentiment")
    latest = files[-1]
    df = pd.read_csv(latest)
    if df.empty:
        raise SystemExit(f"Sentiment file is empty: {latest}")
    return df

def main():
    df = load_latest_sentiment()

    # Use published time for bucketing; fallback to scrape time
    df["published_utc"] = pd.to_datetime(df.get("published_utc"), utc=True, errors="coerce")
    df["timestamp_utc"] = pd.to_datetime(df.get("timestamp_utc"), utc=True, errors="coerce")

    ts = df["published_utc"].copy()
    ts = ts.fillna(df["timestamp_utc"])
    df["hour"] = ts.dt.floor("H")

    # representative article per ticker-hour: largest absolute sentiment
    tmp = df.copy()
    tmp["abs_sent"] = tmp["sentiment_score"].abs()

    rep = (
        tmp.sort_values(["ticker", "hour", "abs_sent"], ascending=[True, True, False])
        .groupby(["ticker", "hour"], as_index=False)
        .head(1)[["ticker", "hour", "title", "url", "sentiment_score"]]
        .rename(columns={
            "title": "rep_title",
            "url": "rep_url",
            "sentiment_score": "rep_article_sentiment"
        })
    )

    agg = (
        df.groupby(["hour", "ticker"])
          .agg(avg_sentiment=("sentiment_score", "mean"),
               volume=("sentiment_score", "count"))
          .reset_index()
          .sort_values(["ticker", "hour"])
    )

    agg["sentiment_delta"] = agg.groupby("ticker")["avg_sentiment"].diff()

    agg["signal"] = "HOLD"
    agg.loc[(agg["sentiment_delta"] > BUY_DELTA) & (agg["volume"] >= MIN_VOLUME), "signal"] = "BUY"
    agg.loc[(agg["sentiment_delta"] < SELL_DELTA) & (agg["volume"] >= MIN_VOLUME), "signal"] = "SELL"

    agg["confidence"] = (agg["sentiment_delta"].abs().fillna(0) * (agg["volume"] ** 0.5)).clip(0, 3) / 3.0

    agg = agg.merge(rep, on=["ticker", "hour"], how="left")

    out_path = "data/processed/signals_latest.csv"
    agg.to_csv(out_path, index=False)
    print(f"Saved -> {out_path} ({len(agg)} rows)")

if __name__ == "__main__":
    main()
