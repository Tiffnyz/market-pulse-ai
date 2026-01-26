import glob
import re
import pandas as pd
from src.config import WATCHLIST, ALIASES, WINDOW_HOURS

def build_patterns():
    """
    Build regex patterns for each ticker based on:
    1) the ticker itself (TSLA)
    2) common finance formats ($TSLA, (TSLA))
    3) company name aliases (tesla, apple, etc.)
    """
    patterns = {}

    for ticker in WATCHLIST:
        pieces = []

        # ticker forms: TSLA, $TSLA, (TSLA)
        t = re.escape(ticker.upper())
        pieces.append(rf"(?<![A-Z0-9])\${t}(?![A-Z0-9])")
        pieces.append(rf"(?<![A-Z0-9])\({t}\)(?![A-Z0-9])")
        pieces.append(rf"(?<![A-Z0-9]){t}(?![A-Z0-9])")

        # aliases: tesla, apple, alphabet, etc.
        for name in ALIASES.get(ticker, []):
            n = re.escape(name.lower())
            pieces.append(rf"(?<![a-z]){n}(?![a-z])")

        patterns[ticker] = re.compile("|".join(pieces), flags=re.IGNORECASE)

    return patterns

def map_df(df: pd.DataFrame, out_path: str):
    if df.empty:
        print("Combined raw dataframe is empty")
        return

    patterns = build_patterns()
    rows = []

    for _, r in df.iterrows():
        text = f"{r.get('title','')} {r.get('summary','')} {r.get('text','')}"
        text = (text or "").strip()
        if not text:
            continue

        matched = []
        for ticker, rx in patterns.items():
            if rx.search(text):
                matched.append(ticker)

        for t in matched:
            rows.append({
                "timestamp_utc": r.get("timestamp_utc"),
                "source": r.get("source", ""),
                "published_utc": r.get("published_utc", ""),
                "ticker": t,
                "title": r.get("title", ""),
                "summary": r.get("summary", ""),
                "text": r.get("text", ""),
                "url": r.get("url", "")
            })

    out_df = pd.DataFrame(rows)
    out_df.to_csv(out_path, index=False)
    print(f"Mapped {len(out_df)} rows -> {out_path}")

def map_all_raw():
    files = glob.glob("data/raw/news_*.csv") + glob.glob("data/raw/newsapi_*.csv")
    if not files:
        raise SystemExit("No raw files found in data/raw/")

    # load and combine
    dfs = []
    skipped = 0

    for f in files:
        try:
            tmp = pd.read_csv(f)
            if tmp.empty:
                skipped += 1
                continue
            dfs.append(tmp)
        except pd.errors.EmptyDataError:
            skipped += 1
            continue

    if not dfs:
        raise SystemExit("All raw files were empty or unreadable. Run the scraper again.")

    df = pd.concat(dfs, ignore_index=True)
    print(f"Loaded {len(dfs)} raw files, skipped {skipped}")

    # dedupe repeated scrapes
    if "url" in df.columns:
        df = df.drop_duplicates(subset=["url"])
    else:
        df = df.drop_duplicates()

    # filter for last WINDOW_HOURS hours only
    if "published_utc" in df.columns:
        df["published_utc"] = pd.to_datetime(df["published_utc"], utc=True, errors="coerce")
        cutoff = pd.Timestamp.utcnow() - pd.Timedelta(hours=WINDOW_HOURS)
        df = df[df["published_utc"].isna() | (df["published_utc"] >= cutoff)]
    else:
        # fallback: use scraped time if published is missing (older schema)
        time_col = "timestamp_utc" if "timestamp_utc" in df.columns else None
        if time_col:
            df[time_col] = pd.to_datetime(df[time_col], utc=True, errors="coerce")
            cutoff = pd.Timestamp.utcnow() - pd.Timedelta(hours=WINDOW_HOURS)
            df = df[df[time_col].isna() | (df[time_col] >= cutoff)]

    out_path = "data/processed/news_all_mapped.csv"
    map_df(df, out_path)


if __name__ == "__main__":
    map_all_raw()
