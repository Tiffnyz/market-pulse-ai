import re
import time
from datetime import datetime, timezone

import feedparser
import pandas as pd

from src.config import WATCHLIST, RSS_FEEDS

TICKER_REGEX = re.compile(r"\\b(" + "|".join(WATCHLIST) + r")\\b")

def extract_tickers(text: str):
    if not text:
        return []
    return sorted(set(TICKER_REGEX.findall(text.upper())))

def fetch_rss():
    rows = []
    now = datetime.now(timezone.utc).isoformat()

    for source, url in RSS_FEEDS.items():
        feed = feedparser.parse(url)
        for entry in feed.entries:
            published = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc).isoformat()
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                published = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc).isoformat()
            title = getattr(entry, "title", "") or ""
            summary = getattr(entry, "summary", "") or ""
            link = getattr(entry, "link", "") or ""

            text = f"{title} {summary}".strip()
           # tickers = extract_tickers(text)

           # for t in tickers:
            rows.append({
                "scraped_utc": now,
                "published_utc": published,
                "source": source,
                "title": title,
                "summary": summary,
                "text": text,
                "url": link
            })


    return pd.DataFrame(rows)

if __name__ == "__main__":
    df = fetch_rss()
    out = f"data/raw/news_{int(time.time())}.csv"
    df.to_csv(out, index=False)
    print(f"saved {len(df)} rows -> {out}")
