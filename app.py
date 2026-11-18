import streamlit as st
import yfinance as yf
import plotly.express as px
import pandas as pd

st.set_page_config(page_title="India Macro Dashboard", layout="wide")

# ---------------------------------------------------------------
# EDIT YOUR TEXT HERE. Only change the words between the triple
# quotes. Do not delete the triple quotes or the commas.
# Use a blank line between paragraphs. Use ** around words to bold.
# ---------------------------------------------------------------

TAKE = {
    "Markets": """Write your take on the markets here.""",
    "Inflation": """Write your take on inflation here.""",
    "Repo vs Inflation": """Write your take on the repo rate and real rate here.""",
    "Taylor Rule": """Write your take on the Taylor rule gap here.""",
}

INFO = {
    "Markets": """USD/INR, Nifty 50 and Sensex prices from Yahoo Finance for the last two years. The number under the chart is the change over roughly the last month.""",
    "Inflation": """CPI inflation, year on year, from FRED. The green band is RBI's 2 to 6 percent tolerance band around a 4 percent target. Data ends in March 2025.""",
    "Repo vs Inflation": """The real rate is the repo rate minus inflation. When it is negative, borrowing is cheap in real terms. When it is positive, policy is tight.""",
    "Taylor Rule": """The Taylor rule gives a benchmark for the repo rate: neutral real rate + inflation + 0.5 x (inflation - 4). This is the inflation-only version and it ignores the output gap. The neutral rate is an assumption, so try the slider. RBI does not follow this rule strictly, so read the gap as a comparison, not a verdict.""",
}

SOURCES = "Sources: FRED (CPI inflation), RBI policy announcements (repo rate, compiled by hand), Yahoo Finance (markets). CPI data ends in March 2025."

# ---------------------------------------------------------------

page = st.sidebar.radio("Section", ["Markets", "Inflation", "Repo vs Inflation", "Taylor Rule"])


@st.cache_data(ttl=3600)
def load(ticker):
    df = yf.download(ticker, period="2y", auto_adjust=True, progress=False)
    if df.empty:
        return None
    if hasattr(df.columns, "get_level_values"):
        df.columns = df.columns.get_level_values(0)
    return df.reset_index()


def load_inflation():
    try:
        cpi = pd.read_csv("cpi.csv", parse_dates=["date"])
    except FileNotFoundError:
        st.error("cpi.csv not found. Upload it to the top level of your repo.")
        st.stop()
    cpi = cpi.sort_values("date")
    # this FRED file is already year-on-year inflation in percent
    cpi["inflation"] = pd.to_numeric(cpi["cpi"], errors="coerce")
    cpi = cpi[cpi["date"] >= "2019-01-01"]
    return cpi.dropna()


def load_repo():
    try:
        repo = pd.read_csv("repo.csv", parse_dates=["date"])
    except FileNotFoundError:
        st.error("repo.csv not found. Upload it to the top level of your repo.")
        st.stop()
    repo = repo.sort_values("date")
    repo["repo"] = pd.to_numeric(
        repo["repo"].astype(str).str.replace("%", "").str.strip(),
        errors="coerce",
    )
    return repo.dropna()


def show_markets():
    st.subheader("Markets")
    options = {"USD/INR": "INR=X", "Nifty 50": "^NSEI", "Sensex": "^BSESN"}
    choice = st.sidebar.selectbox("Pick an indicator", list(options))
    try:
        df = load(options[choice])
        if df is None:
            st.warning("Yahoo returned no data. Reboot app in a few minutes.")
            return
        fig = px.line(df, x="Date", y="Close", title=choice)
        st.plotly_chart(fig, use_container_width=True)
        latest = df["Close"].iloc[-1]
        month_ago = df["Close"].iloc[-22]
        change = (latest / month_ago - 1) * 100
        st.metric(choice, f"{latest:,.2f}", f"{change:.2f}% vs 1 month ago")
    except Exception as e:
        st.error(f"Something broke: {e}")


def show_inflation():
    st.subheader("CPI Inflation (year-on-year)")
    cpi = load_inflation()
    fig = px.line(cpi, x="date", y="inflation", title="India CPI inflation (%)")
    fig.add_hrect(y0=2, y1=6, fillcolor="green", opacity=0.1,
                  annotation_text="RBI comfort band 2 to 6 percent")
    fig.add_hline(y=4, line_dash="dash", annotation_text="Target 4 percent")
    st.plotly_chart(fig, use_container_width=True)
    latest = cpi["inflation"].iloc[-1]
    asof = cpi["date"].iloc[-1].strftime("%b %Y")
    st.metric(f"Inflation (as of {asof})", f"{latest:.2f}%")
    if latest > 6:
        st.error("Above the RBI comfort band")
    elif 2 > latest:
        st.warning("Below the RBI comfort band")
    else:
        st.success("Within the RBI comfort band")


def show_repo_vs_inflation():
    st.subheader("Repo rate vs inflation")
    cpi = load_inflation()
    repo = load_repo()
    merged = pd.merge_asof(cpi.sort_values("date"), repo, on="date").dropna()
    if merged.empty:
        st.warning("CPI and repo dates do not overlap. Add an earlier row to repo.csv.")
        return
    merged["real_rate"] = merged["repo"] - merged["inflation"]
    long = merged.melt(id_vars="date", value_vars=["repo", "inflation"],
                       var_name="series", value_name="percent")
    fig1 = px.line(long, x="date", y="percent", color="series",
                   title="Repo rate vs CPI inflation (%)")
    st.plotly_chart(fig1, use_container_width=True)
    fig2 = px.line(merged, x="date", y="real_rate",
                   title="Real interest rate (repo minus inflation)")
    fig2.add_hline(y=0, line_dash="dash")
    st.plotly_chart(fig2, use_container_width=True)
    asof = merged["date"].iloc[-1].strftime("%b %Y")
    st.caption(f"Latest values are as of {asof}, the last month of CPI data.")
    c1, c2, c3 = st.columns(3)
    c1.metric(f"Repo rate ({asof})", f"{merged['repo'].iloc[-1]:.2f}%")
    c2.metric(f"Inflation ({asof})", f"{merged['inflation'].iloc[-1]:.2f}%")
    c3.metric(f"Real rate ({asof})", f"{merged['real_rate'].iloc[-1]:.2f}%")


def show_taylor_rule():
    st.subheader("Taylor rule: where should the repo rate have been?")
    neutral = st.slider("Neutral real rate (assumption, in %)", 0.0, 3.0, 1.5, 0.25)
    cpi = load_inflation()
    repo = load_repo()
    m = pd.merge_asof(cpi.sort_values("date"), repo, on="date").dropna()
    if m.empty:
        st.warning("CPI and repo dates do not overlap. Add an earlier row to repo.csv.")
        return
    m["taylor"] = neutral + m["inflation"] + 0.5 * (m["inflation"] - 4)
    m["gap_bps"] = (m["repo"] - m["taylor"]) * 100
    long = m.melt(id_vars="date", value_vars=["repo", "taylor"],
                  var_name="series", value_name="percent")
    fig = px.line(long, x="date", y="percent", color="series",
                  title="Actual repo vs Taylor rule benchmark (%)")
    st.plotly_chart(fig, use_container_width=True)
    fig2 = px.line(m, x="date", y="gap_bps",
                   title="Gap: actual repo minus Taylor benchmark (basis points)")
    fig2.add_hline(y=0, line_dash="dash")
    st.plotly_chart(fig2, use_container_width=True)
    asof = m["date"].iloc[-1].strftime("%b %Y")
    gap = m["gap_bps"].iloc[-1]
    c1, c2, c3 = st.columns(3)
    c1.metric(f"Actual repo ({asof})", f"{m['repo'].iloc[-1]:.2f}%")
    c2.metric(f"Taylor benchmark ({asof})", f"{m['taylor'].iloc[-1]:.2f}%")
    c3.metric(f"Gap ({asof})", f"{gap:.0f} bps")
    if gap > 0:
        st.info("Latest month: repo is ABOVE the benchmark, so policy is tighter than the rule suggests.")
    else:
        st.info("Latest month: repo is BELOW the benchmark, so policy is looser than the rule suggests.")


def show_notes(name):
    st.divider()
    st.markdown("### About this section")
    st.markdown(INFO[name])
    st.markdown("### My take")
    st.markdown(TAKE[name])
    st.caption(SOURCES)


if page == "Markets":
    show_markets()
elif page == "Inflation":
    show_inflation()
elif page == "Repo vs Inflation":
    show_repo_vs_inflation()
else:
    show_taylor_rule()

show_notes(page)
