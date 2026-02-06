# Market Pulse AI 📈📰

Market Pulse AI is a data pipeline and dashboard that generates stock market signals based on sentiment analysis of financial news. It scrapes news articles from various sources, associates them with specific stock tickers, analyzes the sentiment of each article using a FinBERT model, and generates hourly BUY/SELL/HOLD signals based on significant changes in sentiment.

## How It Works

The project follows a multi-step data processing pipeline:

1.  **Scrape:** Fetches recent financial news articles from RSS feeds (Yahoo Finance, MarketWatch) and NewsAPI.
2.  **Map Tickers:** Scans the title and summary of each article for company names, aliases, and stock tickers defined in the watchlist. It creates a new dataset mapping each relevant article to its corresponding ticker.
3.  **Sentiment Analysis:** Uses the `ProsusAI/finbert` model to calculate a sentiment score (from -1 for negative to +1 for positive) for each mapped article.
4.  **Signal Generation:** Aggregates sentiment scores by ticker on an hourly basis. It then calculates the change (delta) in average sentiment from the previous hour. A significant positive or negative delta triggers a BUY or SELL signal, respectively.
5.  **Dashboard:** A Streamlit application visualizes the generated signals, sentiment trends over time, and the underlying news articles that influenced the signals.

## Features
*   **Multi-Source News Aggregation:** Pulls data from configurable RSS feeds and the News API.
*   **Customizable Watchlist:** Easily configure the tickers and company name aliases to track in `src/config.py`.
*   **Financial-Tuned NLP:** Leverages FinBERT, a language model pre-trained on financial text, for more accurate sentiment analysis.
*   **Delta-Based Signal Logic:** Signals are generated based on the *rate of change* in news sentiment, not just the absolute sentiment level.
*   **Interactive Dashboard:** A web-based UI built with Streamlit to explore the data, view signals per ticker, and examine sentiment history.

## Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/tiffnyz/market-pulse-ai.git
    cd market-pulse-ai
    ```

2.  **Create a virtual environment and install dependencies:**
    ```bash
    python -m venv venv
    source venv/bin/activate
    pip install pandas "transformers[torch]" streamlit plotly python-dotenv feedparser requests tqdm
    ```

3.  **Set up API Key:**
    This project uses the [News API](https://newsapi.org/) for comprehensive news scraping.
    *   Get a free API key from News API.
    *   Create a file named `.env` in the root of the project directory.
    *   Add your API key to the `.env` file:
        ```
        NEWS_API_KEY="your_api_key_here"
        ```

## Usage

The project uses a `Makefile` to simplify running the data pipeline.

### Run the Full Pipeline
To execute all data processing steps in sequence (scrape, map, sentiment, signals), run:
```bash
make run
```
This command will create the final `data/processed/signals_latest.csv` file required by the dashboard.

### Run Individual Steps
You can also run each step of the pipeline individually:

1.  **Scrape news:**
    ```bash
    make scrape
    ```
2.  **Map news to tickers:**
    ```bash
    make map
    ```
3.  **Analyze sentiment:**
    ```bash
    make sentiment
    ```
4.  **Generate signals:**
    ```bash
    make signals
    ```

### Launch the Dashboard
After running the pipeline (`make run`), you can start the Streamlit dashboard:
```bash
make dashboard
```
Navigate to the local URL provided by Streamlit (usually `http://localhost:8501`) to view the dashboard.

The dashboard features two main views:
*   **Overview:** A table showing the latest signal, average sentiment, article volume, and sentiment delta for every ticker in the watchlist.
*   **Ticker Detail:** A detailed view for a selected ticker, including a time-series chart of its sentiment, key metrics, and a table of recent news headlines that contributed to the sentiment score.

## Configuration

You can customize the behavior of the scraper and signal generator by editing `src/config.py`:

*   `WATCHLIST`: A list of stock tickers to monitor.
*   `ALIASES`: A dictionary to help map company names and common terms to their respective tickers. This improves the accuracy of the ticker mapping step.
*   `RSS_FEEDS`: A dictionary of RSS feeds to scrape news from.
*   `WINDOW_HOURS`: The time window (in hours) for fetching recent news. The default is 120 hours (5 days).
