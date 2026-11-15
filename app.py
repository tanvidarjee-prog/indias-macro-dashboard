import streamlit as st
import yfinance as yf
import plotly.express as px
import pandas as pd

st.title("India Macro Dashboard")

page = st.sidebar.radio("Section", ["Markets", "Inflation", "Repo vs Inflation"])

@st.cache_data(ttl=3600)
def load(ticker):
    df = yf.download(ticker, period="2y", auto_adjust=True, progress=False)
    if df.empty:
        return None
    if hasattr(df.columns, "get_level_values"):
        df.columns = df.columns.get_level_values(0)
    return df.reset_index()

def load_inflation():
    cpi = pd.read_csv("cpi.csv", parse_dates=["date"])
    cpi["inflation"] = cpi["cpi"].pct_change(12) * 100
    return cpi.dropna()

def load_repo():
    repo = pd.read_csv("repo.csv", parse_dates=["date"]).sort_values("date")
    repo["repo"] = pd.to_numeric(
        repo["repo"].astype(str).str.replace("%", "").str.strip(),
        errors="coerce",
    )
    return repo.dropna()

if page == "Markets":
    options = {"USD/INR": "INR=X", "Nifty 50": "^NSEI", "Sensex": "^BSESN"}
    choice = st.sidebar.selectbox("Pick an indicator", list(options))
    try:
        df = load(options[choice])
        if df is None:
            st.warning("Yahoo returned no data. Reboot app in a few minutes.")
        else:
            st.plotly_chart(px.line(df, x="Date", y="Close", title=choice),
                            use_container_width=True)
            latest = df["Close"].iloc[-1]
            month_ago = df["Close"].iloc[-22]
            st.metric(choice, f"{latest:,.2f}",
                      f"{(latest / month_ago - 1) * 100:.2f}% vs 1 month ago")
    except Exception as e:
        st.error(f"Something broke: {e}")

elif page == "Inflation":
    st.subheader("CPI Inflation (year-on-year)")
    cpi = load_inflation()
    fig = px.line(cpi, x="date", y="inflation", title="India CPI inflation (%)")
    fig.add_hrect(y0=2, y1=6, fillcolor="green", opacity=0.1,
                  annotation_text="RBI comfort band (2-6%)")
    fig.add_hline(y=4, line_dash="dash", annotation_text="Target 4%")
    st.plotly_chart(fig, use_container_width=True)
    latest = cpi["inflation"].iloc[-1]
    st.metric("Latest inflation", f"{latest:.2f}%")
    if latest > 6:
        st.error("Above RBI's comfort band")
    elif latest
