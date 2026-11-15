import streamlit as st
import yfinance as yf
import plotly.express as px

st.title("India Macro Dashboard")

options = {"USD/INR": "INR=X", "Nifty 50": "^NSEI", "Sensex": "^BSESN"}
choice = st.sidebar.selectbox("Pick an indicator", list(options))

@st.cache_data(ttl=3600)
def load(ticker):
    df = yf.download(ticker, period="2y", auto_adjust=True, progress=False)
    if df.empty:
        return None
    if hasattr(df.columns, "get_level_values"):
        df.columns = df.columns.get_level_values(0)
    return df.reset_index()

try:
    df = load(options[choice])
    if df is None:
        st.warning("Yahoo returned no data. Try Reboot app in a few minutes.")
    else:
        st.plotly_chart(px.line(df, x="Date", y="Close", title=choice),
                        use_container_width=True)
        latest = df["Close"].iloc[-1]
        month_ago = df["Close"].iloc[-22]
        st.metric(choice, f"{latest:,.2f}",
                  f"{(latest / month_ago - 1) * 100:.2f}% vs 1 month ago")
except Exception as e:
    st.error(f"Something broke: {e}")
