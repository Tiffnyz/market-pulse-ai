import os
import requests
from datetime import datetime, timezone
import pandas as pd
from dotenv import load_dotenv
from src.config import WINDOW_HOURS

load_dotenv(".env")

API_KEY = os.getenv("NEWS_API_KEY")
BASE_URL = "https://newsapi.org/v2/everything"

def fetch_news(query, hours=WINDOW_HOURS, page_size=100):
    from_dt = (datetime.now(timezone.utc) - pd.Timedelta(hours=hours)).isoformat()

    params = {
        "q": query,
        "from": from_dt,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": page_size,
        "apiKey": API_KEY,
    }

    r = requests.get(BASE_URL, params=params)
    data = r.json()
    print("totalResults:", data.get("totalResults"))
    r.raise_for_status()
    return r.json()["articles"]

def scrape_watchlist(watchlist):
    rows = []
    now = datetime.now(timezone.utc).isoformat()

    for ticker, aliases in watchlist.items():
        query = " OR ".join(aliases)
        articles = fetch_news(query)

        for a in articles:
            rows.append({
                "timestamp_utc": now,
                "published_utc": a["publishedAt"],
                "source": a["source"]["name"],
                "title": a["title"],
                "summary": a["description"],
                "text": f"{a['title']} {a.get('description','')}",
                "url": a["url"],
            })

    return pd.DataFrame(rows)

if __name__ == "__main__":
    from src.config import ALIASES
    df = scrape_watchlist(ALIASES)
    out = "data/raw/newsapi_latest.csv"
    df.to_csv(out, index=False)
    print(f"Saved {len(df)} rows -> {out}")
