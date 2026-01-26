import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Market Pulse AI", layout="wide")

st.markdown(
    """
    <style>
    .sig-buy { color: #22C55E; font-weight: 800; }
    .sig-sell { color: #EF4444; font-weight: 800; }
    .sig-hold { color: #A3A3A3; font-weight: 700; }

    th.col-ticker, td.col-ticker { width: 90px; }
    th.col-avg, td.col-avg { width: 90px; text-align: right; }
    th.col-vol, td.col-vol { width: 90px; text-align: right; }
    th.col-delta, td.col-delta { width: 100px; text-align: right; }
    th.col-signal, td.col-signal { width: 90px; text-align: center; }
    th.col-conf, td.col-conf { width: 110px; text-align: right; }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <style>
    table.mpa-table { width:100%; border-collapse: collapse; table-layout: fixed; }
    table.mpa-table th, table.mpa-table td { padding:8px; border-bottom: 1px solid rgba(255,255,255,0.12); vertical-align: top; }
    table.mpa-table th { font-weight: 700; }
    
    /* Column widths */
    th.col-time, td.col-time { width: 115px; }
    th.col-avg, td.col-avg { width: 95px; }
    th.col-delta, td.col-delta { width: 95px; }
    th.col-signal, td.col-signal { width: 80px; }
    th.col-headline, td.col-headline { width: auto; }

    td.col-headline {
        white-space: normal;
        overflow-wrap: break-word;
        word-break: break-word;
        line-height: 1.4;
    }
    </style>
    """,
    unsafe_allow_html=True
)

df = pd.read_csv("data/processed/signals_latest.csv")
df["hour"] = pd.to_datetime(df["hour"], utc=True)

st.title("Market Pulse AI")
st.caption("News sentiment driven market signals")

tab_overview, tab_ticker = st.tabs(["Overview", "Ticker Detail"])
#st.caption("RSS headlines -> ticker mapping -> FinBERT sentiment -> hourly signals")

def history_table_with_links(df_hist):
    rows_html = []

    for _, r in df_hist.iterrows():
        title = (r.get("rep_title") or "").replace('"', "&quot;")
        url = r.get("rep_url") or ""
        link = f'<a href="{url}" target="_blank" rel="noopener noreferrer">{title}</a>' if url else title

        delta = r.get("sentiment_delta")
        delta_str = "" if pd.isna(delta) else f"{delta:.3f}"

        rows_html.append(
            f"<tr>"
            f"<td class='col-time'>{r.get('time_local','')}</td>"
            f"<td class='col-avg'>{float(r.get('avg_sentiment', 0)):.3f}</td>"
            f"<td class='col-delta'>{delta_str}</td>"
            f"<td class='col-signal'><b>{r.get('signal','')}</b></td>"
            f"<td class='col-headline'>{link}</td>"
            f"</tr>"
        )

    html = (
        "<div style='overflow-x:auto;'>"
        "<table class='mpa-table'>"
        "<thead>"
        "<tr>"
        "<th class='col-time'>Time</th>"
        "<th class='col-avg'>Average Sentiment</th>"
        "<th class='col-delta'>Sentiment Delta</th>"
        "<th class='col-signal'>Signal</th>"
        "<th class='col-headline'>Headline</th>"
        "</tr>"
        "</thead>"
        "<tbody>"
        + "".join(rows_html) +
        "</tbody>"
        "</table>"
        "</div>"
    )

    st.markdown(html, unsafe_allow_html=True)

def latest_signals_table(df_latest):
    rows_html = []

    for _, r in df_latest.iterrows():
        sig = r.get("signal", "HOLD")
        sig_class = "sig-hold"
        if sig == "BUY":
            sig_class = "sig-buy"
        elif sig == "SELL":
            sig_class = "sig-sell"

        delta = r.get("sentiment_delta")
        delta_str = "" if pd.isna(delta) else f"{delta:.3f}"

        rows_html.append(
            f"<tr>"
            f"<td class='col-ticker'><b>{r.get('ticker','')}</b></td>"
            f"<td class='col-avg'>{float(r.get('avg_sentiment', 0)):.3f}</td>"
            f"<td class='col-vol'>{int(r.get('articles_window', 0))}</td>"
            f"<td class='col-delta'>{delta_str}</td>"
            f"<td class='col-signal'><span class='{sig_class}'>{sig}</span></td>"
            f"<td class='col-conf'>{float(r.get('confidence', 0)):.2f}</td>"
            f"</tr>"
        )

    html = (
        "<div style='overflow-x:auto;'>"
        "<table class='mpa-table'>"
        "<thead>"
        "<tr>"
        "<th class='col-ticker' style='text-align:left;'>Ticker</th>"
        "<th class='col-avg' style='text-align:right;'>Average Sentiment</th>"
        "<th class='col-vol' style='text-align:right;'>Articles</th>"
        "<th class='col-delta' style='text-align:right;'>Sentiment Delta</th>"
        "<th class='col-signal' style='text-align:center;'>Signal</th>"
        "<th class='col-conf' style='text-align:right;'>Confidence</th>"
        "</tr>"
        "</thead>"
        "<tbody>"
        + "".join(rows_html) +
        "</tbody>"
        "</table>"
        "</div>"
    )

    st.markdown(html, unsafe_allow_html=True)

with tab_overview:
    latest_by_ticker = (
        df.sort_values("hour")
          .groupby("ticker", as_index=False)
          .tail(1)
          .sort_values("avg_sentiment", ascending=False)
    )
    # total articles across the whole window for each ticker
    window_articles = df.groupby("ticker")["volume"].sum().rename("articles_window").reset_index()
    latest_by_ticker = latest_by_ticker.merge(window_articles, on="ticker", how="left")

    st.subheader("Latest Signals")
    latest_signals_table(
        latest_by_ticker[["ticker", "avg_sentiment", "volume", "articles_window", "sentiment_delta", "signal", "confidence"]]
    )
with tab_ticker:
    tickers = sorted(df["ticker"].unique())
    ticker = st.selectbox("Select ticker", tickers)

    sub = df[df["ticker"] == ticker].sort_values("hour").copy()
    # convert UTC hour to local readable time
    sub["time_local"] = (
        sub["hour"]
        .dt.tz_convert("America/Indiana/Indianapolis")
        .dt.strftime("%b %d, %I %p")
    )
    latest = sub.iloc[-1]

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("Avg Sentiment", f"{latest['avg_sentiment']:.3f}")

    articles_window = int(sub["volume"].sum())
    hours_tracked = int(sub["hour"].nunique())

    WINDOW_HOURS = 120
    c2.metric(f"Articles (last {WINDOW_HOURS//24} days)", articles_window, help="Total number of articles used to compute sentiment in this time window")
    c3.metric("Hours with coverage", hours_tracked)

    c4.metric(
        "Delta",
        "N/A" if pd.isna(latest["sentiment_delta"]) else f"{latest['sentiment_delta']:.3f}"
    )

    signal_color = (
        "#22C55E" if latest["signal"] == "BUY"
        else "#EF4444" if latest["signal"] == "SELL"
        else "#A3A3A3"
    )

    c5.markdown(
        f"""
        <div style="
            padding:10px;
            border-radius:12px;
            background:{signal_color};
            text-align:center;
            font-weight:800;
            color:#0B1020;
        ">
            {latest['signal']}
        </div>
        """,
        unsafe_allow_html=True
    )

    fig = px.line(
        sub,
        x="hour",
        y="avg_sentiment",
        template="plotly_dark",
        title=f"{ticker} Sentiment Over Time"
    )
    fig.update_traces(line=dict(width=3))

    st.plotly_chart(fig, width="stretch")


    history = sub.sort_values("hour", ascending=False).head(30).copy()
    st.subheader("Recent History")
    history_table_with_links(history)
    # st.dataframe(
    #     history[
    #         ["time_local", "avg_sentiment", "sentiment_delta", "rep_title", "signal", "confidence"]
    #     ]
    #     .rename(columns={"time_local": "time", "rep_title":"headline"})
    #     .style
    #     .format({
    #         "avg_sentiment": "{:.3f}",
    #         "sentiment_delta": lambda x: "" if pd.isna(x) else f"{x:.3f}",
    #         "confidence": "{:.2f}",
    #     }),
    #     use_container_width=True,
    #     height=40*len(history),
    #     hide_index=True
    # )


# tickers = sorted(df["ticker"].unique())
# ticker = st.selectbox("Ticker", tickers)

# sub = df[df["ticker"] == ticker].sort_values("hour")
# latest = sub.iloc[-1]

# c1, c2, c3 = st.columns(3)
# c1.metric("Latest Avg Sentiment", f"{latest['avg_sentiment']:.3f}")
# c2.metric("Latest Delta", "N/A" if pd.isna(latest["sentiment_delta"]) else f"{latest['sentiment_delta']:.3f}")
# c3.metric("Latest Signal", latest["signal"])

# fig = px.line(sub, x="hour", y="avg_sentiment", title=f"{ticker}: Hourly Avg Sentiment")
# st.plotly_chart(fig, width='stretch')

# st.subheader("Recent Signals")
# st.dataframe(sub.sort_values("hour", ascending=False).head(30), width='stretch')
