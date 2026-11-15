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
    elif latest < 2:
        st.warning("Below RBI's comfort band")
    else:
        st.success("Within RBI's comfort band")

else:
    st.subheader("Repo rate vs inflation")
    cpi = load_inflation()
    repo = pd.read_csv("repo.csv", parse_dates=["date"]).sort_values("date")
repo["repo"] = pd.to_numeric(
    repo["repo"].astype(str).str.replace("%", "").str.strip(),
    errors="coerce",
)
repo = repo.dropna()

    # for each CPI month, attach the repo rate that was in force at that time
    merged = pd.merge_asof(cpi.sort_values("date"), repo, on="date").dropna()
    merged["real_rate"] = merged["repo"] - merged["inflation"]

    long = merged.melt(id_vars="date", value_vars=["repo", "inflation"],
                       var_name="series", value_name="percent")
    st.plotly_chart(px.line(long, x="date", y="percent", color="series",
                            title="Repo rate vs CPI inflation (%)"),
                    use_container_width=True)

    fig2 = px.line(merged, x="date", y="real_rate",
                   title="Real interest rate (repo minus inflation)")
    fig2.add_hline(y=0, line_dash="dash")
    st.plotly_chart(fig2, use_container_width=True)

    c1, c2, c3 = st.columns(3)
    c1.metric("Repo rate", f"{merged['repo'].iloc[-1]:.2f}%")
    c2.metric("Inflation", f"{merged['inflation'].iloc[-1]:.2f}%")
    c3.metric("Real rate", f"{merged['real_rate'].iloc[-1]:.2f}%")
