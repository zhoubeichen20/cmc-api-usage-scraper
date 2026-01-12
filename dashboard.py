import os
from datetime import datetime

import altair as alt
import pandas as pd
import plotly.express as px
import streamlit as st


CSV_PATH = "api_usage.csv"


def load_data(path: str) -> pd.DataFrame:
    if not os.path.exists(path):
        return pd.DataFrame()
    df = pd.read_csv(path)
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)
    if "scraped_at" in df.columns:
        df["scraped_at"] = pd.to_datetime(df["scraped_at"], errors="coerce", utc=True)
    if "credit_count" in df.columns:
        df["credit_count"] = pd.to_numeric(df["credit_count"], errors="coerce")
    return df


def main() -> None:
    st.set_page_config(page_title="CMC API Usage Dashboard", layout="wide")
    st.title("CoinMarketCap API Usage")
    st.caption("Powered by `api_usage.csv`")

    df = load_data(CSV_PATH)
    if df.empty:
        st.warning("No data found. Run `python scraper.py` to collect usage logs.")
        return

    latest_scrape = df["scraped_at"].max()
    if pd.notna(latest_scrape):
        st.info(f"Last scraped: {latest_scrape.strftime('%Y-%m-%d %H:%M:%S %Z')}")

    df = df.dropna(subset=["timestamp"])
    df["date"] = df["timestamp"].dt.date

    with st.sidebar:
        st.header("Filters")
        min_date = df["date"].min()
        max_date = df["date"].max()
        date_range = st.date_input(
            "Date range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )
        if isinstance(date_range, tuple) and len(date_range) == 2:
            start, end = date_range
            mask = (df["date"] >= start) & (df["date"] <= end)
            df = df.loc[mask]

    kpis = st.columns(4)
    kpis[0].metric("Requests", f"{len(df):,}")
    kpis[1].metric("Credits", f"{int(df['credit_count'].fillna(0).sum()):,}")
    kpis[2].metric("Unique IPs", f"{df['ip_address'].nunique():,}")
    kpis[3].metric("Endpoints", f"{df['endpoint'].nunique():,}")

    daily = (
        df.groupby("date", as_index=False)
        .agg(requests=("request_number", "count"), credits=("credit_count", "sum"))
        .sort_values("date")
    )

    st.subheader("Daily Requests")
    chart = alt.Chart(daily).mark_line(point=True).encode(
        x=alt.X("date:T", title="Date"),
        y=alt.Y("requests:Q", title="Requests"),
        tooltip=["date:T", "requests:Q"],
    )
    st.altair_chart(chart, use_container_width=True)

    st.subheader("Credit Consumption")
    fig = px.area(daily, x="date", y="credits", markers=True)
    fig.update_layout(margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Recent Requests")
    st.dataframe(df.sort_values("timestamp", ascending=False).head(100))


if __name__ == "__main__":
    main()
