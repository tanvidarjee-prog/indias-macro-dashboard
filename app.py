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
    "Markets": """Markets are the fastest-moving part of this dashboard, and they react to the slow-moving parts. Rate expectations, inflation surprises and foreign investor flows show up in the rupee and in equity prices long before they appear in monthly CPI.

**Why the rupee matters for inflation:** India imports most of its crude oil, so a weaker rupee makes imported fuel costlier and can push CPI up. That is one reason RBI keeps an eye on USD/INR even though its formal mandate is inflation.

**How to use this page:** read it alongside the next three sections. When inflation or rate expectations shift, check whether the rupee and the Nifty moved with them. This page shows live prices only, so I draw no conclusion about the latest move.""",

    "Inflation": """Inflation in India has been volatile rather than steadily trending. In this dataset it first crossed 6% in **April 2022 (6.33%)**, hit **6.97% in May 2022**, and stayed above 6% on and off until August 2023.

The peak is **7.54% in July 2023**, up sharply from 5.57% only a month earlier. A one-month jump that large looks more like a food price shock than a change in underlying demand. That is a hypothesis, not a finding: vegetable prices are widely cited for that period, but this dataset has no food breakdown, so I cannot prove it here.

Since then inflation has come down a lot. It reached a low of **2.15% in July 2024** and ended the data at **2.95% in March 2025**. That is inside RBI's band but below the 4% target, so the policy worry shifted from inflation being too high to growth needing support.""",

    "Repo vs Inflation": """The real rate tells the story better than the repo rate alone.

**2020 to 2022: cheap money.** From June 2020 until October 2022 the real rate was negative. Repo sat at 4.00% until May 2022 while inflation rose, and the deepest point was **May 2022 at -2.97%** (repo 4.00%, inflation 6.97%). That supports the view that RBI was slow to respond. The fair counterpoint is that RBI was protecting the post-Covid recovery.

**2022 to 2023: catching up.** RBI then raised the repo rate from 4.00% to 6.50% (250 bps) between May 2022 and February 2023, and the real rate turned positive in November 2022. It slipped back below zero in July and August 2023 (-1.04% and -0.41%) when inflation spiked to 7.54% while repo stayed at 6.50%.

**2023 to 2025: tight.** Repo was held at 6.50% until the first cut in February 2025. With inflation falling, the real rate reached **+4.35% in July 2024** and was **+3.30% in March 2025**, which is tight relative to inflation of 2.95%. That is the setup for the rate cuts that followed in 2025.

**Caution:** inflation fell while rates were high, which is consistent with tightening working. It is not proof, because food prices and global commodity prices moved too.""",

    "Taylor Rule": """Against a simple Taylor benchmark (neutral rate 1.5%), RBI was **far behind the curve in 2022**. In May 2022 the actual repo rate was about **595 bps below** the benchmark. In July 2023 it was still about **430 bps below**, even after 250 bps of hikes, because inflation had reached 7.5%.

The gap turned positive in October 2023. After that RBI held repo well above what the rule suggests: about **+378 bps in July 2024** (inflation 2.15%) and still **+232 bps in March 2025**.

**Two ways to read that.** One: RBI was cautious and kept policy tighter than needed. Two: the benchmark is misleading because it reacts to every wiggle in headline inflation, while RBI looks through temporary food shocks and also weighs growth, which this simple rule leaves out. I lean towards the second reading, so I treat the gap as a comparison, not proof of a policy mistake.

**Robustness check:** moving the neutral rate between 1% and 2% shifts the lines but not the story. The March 2025 gap is +282 bps at 1% and +182 bps at 2%, and in both cases RBI was far below the benchmark in 2022 and above it by 2025.""",
}

INFO = {
    "Markets": """USD/INR, Nifty 50 and Sensex prices from Yahoo Finance for the last two years. The number under the chart is the change over roughly the last month (22 trading days). These are live market prices, not RBI data.

**How to read it:** a rising USD/INR means the rupee is weakening. A falling Nifty or Sensex means equities are repricing, often because of rate expectations, foreign investor flows or global risk.""",

    "Inflation": """CPI inflation (year on year) for India, from FRED. The green band is RBI's 2 to 6 percent tolerance band around a 4 percent target, which is the inflation targeting framework in place since 2016.

If inflation stays outside the band for three quarters in a row, RBI is considered to have failed the target and must explain why to the government. The data in this app ends in March 2025.""",

    "Repo vs Inflation": """The repo rate is the rate at which RBI lends to banks and is its main policy lever. It is compiled by hand from RBI policy announcements. Each CPI month is matched with the repo rate in force at that time.

**Real rate = repo rate minus inflation.** Negative means borrowing is cheap in real terms and savers lose purchasing power. Positive means policy is tight. This uses actual inflation, while RBI decides based on expected inflation, so the real rate here is a simple approximation.""",

    "Taylor Rule": """The Taylor rule gives a benchmark for the repo rate: **neutral real rate + inflation + 0.5 x (inflation - 4)**. This is the inflation-only version and it ignores the output gap, because there is no monthly GDP data here.

The gap is actual repo minus the benchmark, in basis points (100 bps = 1 percentage point). Negative means RBI was looser than the rule suggests, and positive means tighter. The neutral rate is an assumption, so try the slider.""",
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
