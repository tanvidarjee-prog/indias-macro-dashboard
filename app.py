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
    "Markets": """This is the part of the dashboard that moves the fastest. The rupee and the stock market react to interest rate expectations and foreign investor flows way before anything shows up in the monthly inflation data.

The rupee matters for inflation more than you would think. India imports most of its crude oil, so when the rupee weakens, fuel gets costlier and that can push CPI up. It is one reason RBI keeps an eye on USD/INR even though inflation is its official job.

I would read this page next to the other three: when inflation or rate expectations shift, check whether the rupee and the Nifty moved too. The prices here are live, so I am not drawing a conclusion about the latest move.""",

    "Inflation": """Inflation in India does not move in a straight line. In this data it crossed 6% for the first time in **April 2022 (6.33%)**, touched **6.97% in May 2022**, and kept bouncing above 6% until August 2023.

The peak was **7.54% in July 2023**, a big jump from 5.57% just one month before. A jump that sudden looks like a food price shock, not a sudden rise in demand. I cannot prove that with this dataset because it has no food breakdown, but vegetable prices are widely blamed for that period, so I am treating it as a hypothesis.

After that, inflation fell a lot: **2.15% in July 2024**, and **2.95% in March 2025**, where my data ends. That is inside RBI's band but under the 4% target, so the conversation shifted from fighting inflation to supporting growth.""",

    "Repo vs Inflation": """The real rate tells the story better than the repo rate on its own, so here it is in order.

**2020 to 2022: money was cheap.** From June 2020 to October 2022 the real rate was negative in nearly every month, with just two exceptions (December 2020 and January 2021). Repo sat at 4.00% until May 2022 while inflation kept climbing, and the low point was **May 2022 at -2.97%** (repo 4.00%, inflation 6.97%). That is why I think RBI was slow to react. In its defence, it was trying not to choke the post-Covid recovery.

**2022 to 2023: catching up.** RBI hiked from 4.00% to 6.50% (250 bps) between May 2022 and February 2023, and the real rate turned positive in November 2022. Then it dipped below zero again in July and August 2023 (-1.04% and -0.41%), because inflation shot up to 7.54% while repo was stuck at 6.50%.

**2023 to 2025: tight.** RBI held at 6.50% until its first cut in February 2025. With inflation falling, the real rate hit **+4.35% in July 2024** and was **+3.30% in March 2025**. That is tight for an economy with 2.95% inflation, which fits with the rate cuts that followed in 2025.

One warning: inflation fell while rates were high, which fits the idea that tightening worked, but it does not prove it. Food prices and global commodity prices were moving too.""",

    "Taylor Rule": """Using a simple Taylor benchmark (with the neutral rate at 1.5%), RBI was **way behind the curve in 2022**. In May 2022 the actual repo rate was about **595 bps below** the benchmark. By July 2023 it was still about **430 bps below**, even after 250 bps of hikes, because inflation had climbed to 7.5%.

The gap turned positive in October 2023, and RBI then kept repo well above what the rule suggests: about **+378 bps in July 2024** (inflation was 2.15%) and still **+232 bps in March 2025**.

There are two ways to read this. Either RBI was being cautious and kept policy tighter than it needed to be. Or the benchmark is a bit unfair, because it reacts to every wiggle in headline inflation, while RBI tends to look through temporary food shocks and also cares about growth, which this simple rule ignores. I lean towards the second one, so I see the gap as a comparison and not as proof of a policy mistake.

**Does the neutral rate change the answer?** Not really. At 1% the March 2025 gap is +282 bps and at 2% it is +182 bps. Either way RBI was far below the benchmark in 2022 and above it by 2025.""",
}

INFO = {
    "Markets": """These are USD/INR, Nifty 50 and Sensex prices from Yahoo Finance for the last two years. The number under the chart is the change over about the last month (22 trading days). It is live market data, not RBI data.

**How to read it:** if USD/INR is rising, the rupee is getting weaker. If the Nifty or Sensex is falling, investors are repricing stocks, often because of rate expectations, foreign money flows or global nervousness.""",

    "Inflation": """This is India's CPI inflation (year on year) from FRED. The green band is RBI's comfort zone: a 4% target with 2 percentage points of room on either side, so 2% to 6%. India has used this inflation targeting setup since 2016.

If inflation stays outside the band for three quarters in a row, RBI is considered to have missed its target and has to explain why to the government. The data in this app ends in March 2025.""",

    "Repo vs Inflation": """The repo rate is what RBI charges banks for short-term loans, and it is RBI's main lever. I put this series together by hand from RBI's policy announcements, and each month of CPI is matched with the repo rate that was in force then.

**Real rate = repo rate minus inflation.** If it is negative, borrowing is cheap in real terms and savers lose purchasing power. If it is positive, policy is tight. A caveat: I use actual inflation here, while RBI decides based on where it expects inflation to go, so this is a simplified version.""",

    "Taylor Rule": """The Taylor rule gives a benchmark for where the repo rate could be: **neutral real rate + inflation + 0.5 x (inflation - 4)**. This is the simple inflation-only version. It leaves out the output gap, because I do not have monthly GDP data.

The gap is the actual repo minus the benchmark, in basis points (100 bps = 1 percentage point). Negative means RBI was looser than the rule suggests, positive means tighter. The neutral rate is an assumption, so play with the slider.""",
}

GLOSSARY = [
    ("Repo rate", """This is the rate RBI charges banks when it lends them money for a short period, with government securities as collateral. "Repo" is short for repurchase: the bank sells securities to RBI and agrees to buy them back a bit later at a slightly higher price. That small difference is the interest.

It is RBI's main policy rate. When RBI **raises** it, borrowing gets costlier, spending cools down and inflation eases. When RBI **cuts** it, borrowing gets cheaper and growth gets a push.

**Why it matters to you:** since October 2019, many floating-rate loans (home loans, for example) are linked to an external benchmark that is usually the repo rate. So when it changes, your EMI can follow fairly quickly."""),

    ("Reverse repo rate, SDF and MSF", """The reverse repo is the repo flipped around: RBI borrows money from banks, and banks earn the reverse repo rate on the cash they park with RBI.

It used to be the floor of RBI's rate corridor, but in April 2022 RBI brought in the **Standing Deposit Facility (SDF)**, set 0.25 percentage points below the repo rate, and that is now the floor. The **Marginal Standing Facility (MSF)** is the emergency borrowing window for banks, set 0.25 points above repo, and that is the ceiling.

So the picture is: SDF (repo minus 0.25) at the bottom, repo in the middle, MSF (repo plus 0.25) at the top."""),

    ("Inflation", """Inflation means prices are rising in general, so each rupee buys a bit less than it did before. It is usually reported **year on year**, which compares this month's prices with the same month last year.

Some inflation is normal in a growing economy. **Too much** hurts savers and poorer households the most. **Too little** can be a sign that demand is weak."""),

    ("CPI (Consumer Price Index)", """The Consumer Price Index follows the prices of a fixed basket of things households buy: food, fuel, housing, clothes, transport, health and so on. In India it is published every month by MoSPI.

**Food and beverages make up almost half of the basket.** That is why a spike in vegetable prices can move the whole inflation number. RBI's target is based on CPI, and it is the inflation measure this dashboard uses."""),

    ("Headline vs core inflation", """**Headline inflation** is the full CPI number. **Core inflation** leaves out the jumpy items, usually food and fuel, to show the underlying trend. RBI looks at both, because a food price shock can push headline inflation up even when demand has not changed."""),

    ("WPI (Wholesale Price Index)", """The Wholesale Price Index tracks prices of goods that businesses trade in bulk. It is published by the Office of the Economic Adviser under DPIIT. It covers goods only (no services), and it is not what RBI targets.

It can still be a useful early signal, because higher costs for producers often reach consumers later."""),

    ("Base effect", """Year-on-year inflation depends on last year's prices as well as this year's. If prices were flat or even fell a year ago, inflation this year can look high even when prices are rising normally. It works the other way too.

So before getting excited about a spike or a drop, it is worth asking what the base was a year earlier."""),

    ("Real interest rate", """**Real rate = nominal interest rate minus inflation.** If the repo rate is 6.50% and inflation is 3%, the real rate is +3.50%, which means policy is actually tight. If it is negative, borrowing is cheap in real terms and savers lose purchasing power.

The Repo vs Inflation section of this dashboard works it out month by month."""),

    ("Inflation targeting and the 2 to 6 percent band", """Since 2016 India has used flexible inflation targeting. The target is **4% CPI inflation, with a comfort band of 2 percentage points on either side (2% to 6%)**. The government sets it in consultation with RBI.

If inflation stays outside the band for three quarters in a row, RBI is considered to have failed and has to explain to the government why. That is the green band on the Inflation chart."""),

    ("MPC (Monetary Policy Committee)", """The Monetary Policy Committee is the group that decides the repo rate. It has six members: three from RBI (including the Governor) and three external members appointed by the government. Decisions go by majority vote, and the Governor has the casting vote if there is a tie.

It meets at least four times a year, and usually six. Every date in repo.csv is either an MPC meeting or an announcement made outside the regular schedule."""),

    ("Basis point (bps)", """A basis point is one hundredth of a percentage point. 25 bps is 0.25%, and 100 bps is 1 percentage point. Going from 6.00% to 6.50% is a 50 bps move. Economists use bps so nobody mixes up "percent" and "percentage points"."""),

    ("Neutral rate and output gap", """The **neutral real rate** is the interest rate that neither speeds the economy up nor slows it down. Nobody can observe it directly, only estimate it, which is why the Taylor Rule section has a slider for it.

The **output gap** is how far actual GDP is from where it could be. Positive means the economy is running hot, negative means there is slack. The simple Taylor rule here leaves the output gap out."""),

    ("Taylor rule", """A rule of thumb for setting interest rates: raise them when inflation is above target, and (in the full version) when the economy is running above its potential. The version here is **neutral real rate + inflation + 0.5 x (inflation - 4)**.

Think of it as a benchmark to compare against, not a rule RBI follows. Central banks also weigh growth, the exchange rate and food price shocks."""),

    ("CRR and SLR", """These are two other tools RBI uses on banks. The **Cash Reserve Ratio (CRR)** is the share of deposits a bank has to keep with RBI as cash. The **Statutory Liquidity Ratio (SLR)** is the share it has to hold in safe, liquid assets like government securities.

Raise either one and banks have less left to lend. This dashboard focuses on the repo rate, though."""),

    ("USD/INR", """This is how many rupees it takes to buy one US dollar. **When USD/INR rises, the rupee is getting weaker.** That matters for inflation because India imports crude oil and plenty of other things priced in dollars, so a weaker rupee makes imports costlier."""),

    ("Nifty 50 and Sensex", """**Nifty 50** tracks 50 large companies listed on the NSE, and **Sensex** tracks 30 large companies listed on the BSE. They are rough thermometers for how the Indian stock market is doing, and both react to rate expectations, foreign investor flows and global risk."""),
]

SOURCES = "Sources: FRED (CPI inflation), RBI policy announcements (repo rate, compiled by hand), Yahoo Finance (markets). CPI data ends in March 2025."

# ---------------------------------------------------------------

page = st.sidebar.radio("Section", ["Markets", "Inflation", "Repo vs Inflation", "Taylor Rule", "Concepts Explained"])


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


def show_concepts():
    st.subheader("Concepts explained")
    st.write("New to macro? Here is a plain-English guide to the terms used in this dashboard.")
    st.markdown("""**How a repo rate change reaches inflation:** RBI changes the repo rate, banks change their lending and deposit rates, people and businesses borrow and spend differently, demand and prices shift, and eventually inflation moves. It takes months, not days, which is why RBI has to act before inflation is obviously a problem.""")
    first = True
    for title, text in GLOSSARY:
        with st.expander(title, expanded=first):
            st.markdown(text)
        first = False
    st.caption("These explanations are simplified. For official definitions, check RBI and MoSPI.")


def show_notes(name):
    st.divider()
    st.markdown("### Quick context")
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
elif page == "Taylor Rule":
    show_taylor_rule()
else:
    show_concepts()

if page != "Concepts Explained":
    show_notes(page)
