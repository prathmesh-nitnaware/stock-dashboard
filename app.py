import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go
import datetime
import feedparser

st.set_page_config(page_title="📈 Stock Dashboard", layout="wide")

# --- Sidebar Settings ---
st.sidebar.title("🔧 Settings")

ticker_input = st.sidebar.text_input("Enter Ticker(s) (comma-separated)", value="AAPL,TSLA")
tickers = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]

start_date = st.sidebar.date_input("Start Date", pd.to_datetime("2023-01-01"))
end_date = st.sidebar.date_input("End Date", pd.to_datetime("today"))

st.sidebar.markdown("---")
beginner_mode = st.sidebar.checkbox("🧑‍🎓 Beginner Mode", value=True)

with st.sidebar.expander("📖 Glossary (Tap to View)"):
    st.markdown("""
    **SMA**: Average price over N days.  
    **RSI**: Indicates overbought/oversold stock momentum (0–100).  
    **Candlestick**: Price movements per day (open, high, low, close).  
    **Close Price**: Final trading price of the day.  
    """)

# --- Fetch Data ---
@st.cache_data
def load_data(ticker, start, end):
    df = yf.download(ticker, start=start, end=end)
    df.reset_index(inplace=True)
    return df

@st.cache_data
def compute_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# --- App Header ---
st.title("📊 Real-Time Stock Market Dashboard")

for ticker in tickers:
    st.markdown(f"## 🔎 {ticker}")

    data = load_data(ticker, start_date, end_date)

    if data.empty:
        st.warning(f"No data for {ticker}. Try a different ticker.")
        continue

    # --- Natural Language Summary ---
    def generate_insights(df):
        if df.empty or len(df) < 2:
            return "Not enough data to generate insights."

        start_price = float(df['Close'].iloc[0])
        end_price = float(df['Close'].iloc[-1])
        change_pct = ((end_price - start_price) / start_price) * 100
        avg_price = float(df['Close'].mean())

        direction = "📈 increased" if change_pct > 0 else "📉 decreased" if change_pct < 0 else "➖ remained flat"
        summary = (
            f"Between **{start_date}** and **{end_date}**, the stock {direction} by "
            f"**{abs(change_pct):.2f}%**. \n\n"
            f"Average closing price: **${avg_price:.2f}**."
        )
        return summary

    st.markdown("### 🧠 Insight")
    st.info(generate_insights(data))

    # --- Show Table if Beginner Mode Enabled ---
    if beginner_mode:
        st.markdown("### 🧾 Recent Data")
        st.dataframe(data.tail())

    # --- CSV Download ---
    csv = data.to_csv(index=False).encode('utf-8')
    st.download_button(f"⬇️ Download {ticker} Data as CSV", data=csv, file_name=f"{ticker}_data.csv", mime="text/csv")

    # --- Closing Price Chart ---
    st.markdown("### 📈 Price Trend")
    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(x=data['Date'], y=data['Close'], name='Close Price'))
    fig_line.update_layout(title=f"{ticker} Closing Price", xaxis_title='Date', yaxis_title='Price', modebar_add=["toImage"])
    st.plotly_chart(fig_line, use_container_width=True)

    # --- RSI Chart ---
    st.markdown("### 📊 RSI (Relative Strength Index)")
    data['RSI'] = compute_rsi(data)
    fig_rsi = go.Figure()
    fig_rsi.add_trace(go.Scatter(x=data['Date'], y=data['RSI'], name='RSI', line=dict(color='orange')))
    fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought")
    fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold")
    fig_rsi.update_layout(title="RSI Indicator", yaxis_title="RSI", xaxis_title="Date", modebar_add=["toImage"])
    st.plotly_chart(fig_rsi, use_container_width=True)

    # --- Candlestick Chart ---
    st.markdown("### 📦 Candlestick Chart")
    fig_candle = go.Figure(data=[go.Candlestick(
        x=data['Date'],
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close']
    )])
    fig_candle.update_layout(title="Candlestick Chart", xaxis_title="Date", yaxis_title="Price", modebar_add=["toImage"])
    st.plotly_chart(fig_candle, use_container_width=True)

    # --- News Feed ---
    st.markdown("### 📰 Latest News")
    news_feed = feedparser.parse(f"https://finance.yahoo.com/rss/headline?s={ticker}")
    if news_feed.entries:
        for entry in news_feed.entries[:5]:
            st.markdown(f"- [{entry.title}]({entry.link})")
    else:
        st.write("No news found.")

# --- Multi-Ticker Comparison Chart ---
if len(tickers) > 1:
    st.markdown("## 📊 Compare Selected Stocks")
    fig_compare = go.Figure()
    for ticker in tickers:
        try:
            comp_data = load_data(ticker, start_date, end_date)
            fig_compare.add_trace(go.Scatter(x=comp_data['Date'], y=comp_data['Close'], name=ticker))
        except:
            continue
    fig_compare.update_layout(title="Stock Comparison", xaxis_title='Date', yaxis_title='Price', modebar_add=["toImage"])
    st.plotly_chart(fig_compare, use_container_width=True)
