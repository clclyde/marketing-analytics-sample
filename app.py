import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import gspread
import google.generativeai as genai

st.set_page_config(page_title="Automated Marketing Analytics — Sample", layout="wide")

DATA_TTL_SECONDS = 90
INSIGHT_TTL_SECONDS = 120


@st.cache_resource
def get_gsheets_client():
    return gspread.service_account_from_dict(dict(st.secrets["connections"]["gsheets"]))


# ---- Load data (live from Google Sheets) ----
@st.cache_data(ttl=DATA_TTL_SECONDS)
def load_data():
    gc = get_gsheets_client()
    sh = gc.open_by_url(st.secrets["connections"]["gsheets"]["spreadsheet"])
    ws = sh.worksheet(st.secrets["connections"]["gsheets"]["worksheet"])
    rows = ws.get_all_records()
    df = pd.DataFrame(rows)
    df = df.dropna(how="all")
    df["date"] = pd.to_datetime(df["date"])
    for col in ["spend", "impressions", "clicks", "leads", "closed_deals"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    df["ctr"] = df["clicks"] / df["impressions"]
    df["cpl"] = df["spend"] / df["leads"].replace(0, float("nan"))
    df["cpa"] = df["spend"] / df["closed_deals"].replace(0, float("nan"))
    # Assumed average deal value for ROAS illustration
    df["revenue"] = df["closed_deals"] * 8500
    df["roas"] = df["revenue"] / df["spend"].replace(0, float("nan"))
    return df

df = load_data()

# ---- Header ----
st.title("Automated Marketing Analytics — Sample Dashboard")
st.caption(
    "Live dashboard pulling from a shared Google Sheet, with automatically "
    "refreshing KPIs, charts, and an LLM-generated insight summary."
)
st.caption(f"Data last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M')} (auto-refreshes every ~{DATA_TTL_SECONDS}s)")

# ---- Filters ----
col_f1, col_f2 = st.columns([1, 3])
with col_f1:
    channels = st.multiselect("Channel", options=sorted(df["channel"].unique()), default=sorted(df["channel"].unique()))
with col_f2:
    date_range = st.date_input(
        "Date range",
        value=(df["date"].min().date(), df["date"].max().date()),
        min_value=df["date"].min().date(),
        max_value=df["date"].max().date(),
    )

if len(date_range) == 2:
    start, end = date_range
    mask = (df["channel"].isin(channels)) & (df["date"].dt.date >= start) & (df["date"].dt.date <= end)
    fdf = df[mask]
else:
    fdf = df[df["channel"].isin(channels)]

# ---- KPI strip ----
total_spend = fdf["spend"].sum()
total_leads = fdf["leads"].sum()
total_closed = fdf["closed_deals"].sum()
total_revenue = fdf["revenue"].sum()
avg_cpl = total_spend / total_leads if total_leads else 0
avg_roas = total_revenue / total_spend if total_spend else 0

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Spend", f"₱{total_spend:,.0f}")
k2.metric("Total Leads", f"{total_leads:,.0f}")
k3.metric("Closed Deals", f"{total_closed:,.0f}")
k4.metric("Avg. Cost per Lead", f"₱{avg_cpl:,.0f}")
k5.metric("ROAS", f"{avg_roas:.1f}x")

st.divider()

# ---- Row 1: Spend & leads over time ----
c1, c2 = st.columns(2)
with c1:
    daily = fdf.groupby("date").agg(spend=("spend", "sum"), leads=("leads", "sum")).reset_index()
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=daily["date"], y=daily["spend"], name="Spend (₱)", yaxis="y1"))
    fig1.add_trace(go.Scatter(x=daily["date"], y=daily["leads"], name="Leads", yaxis="y2"))
    fig1.update_layout(
        title="Spend vs. Leads Over Time",
        yaxis=dict(title="Spend (₱)"),
        yaxis2=dict(title="Leads", overlaying="y", side="right"),
        legend=dict(orientation="h", y=1.15),
        height=380,
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    st.plotly_chart(fig1, use_container_width=True)

with c2:
    by_channel = fdf.groupby("channel").agg(spend=("spend", "sum"), leads=("leads", "sum"), closed=("closed_deals", "sum")).reset_index()
    by_channel["cpl"] = by_channel["spend"] / by_channel["leads"].replace(0, float("nan"))
    fig2 = px.bar(by_channel.sort_values("cpl"), x="channel", y="cpl", title="Cost per Lead by Channel", text_auto=".0f")
    fig2.update_layout(height=380, yaxis_title="Cost per Lead (₱)", plot_bgcolor="white", paper_bgcolor="white")
    st.plotly_chart(fig2, use_container_width=True)

# ---- Row 2: Funnel + campaign table ----
c3, c4 = st.columns([1, 2])
with c3:
    funnel_vals = [fdf["impressions"].sum(), fdf["clicks"].sum(), fdf["leads"].sum(), fdf["closed_deals"].sum()]
    fig3 = go.Figure(go.Funnel(y=["Impressions", "Clicks", "Leads", "Closed Deals"], x=funnel_vals))
    fig3.update_layout(title="Overall Funnel", height=380, plot_bgcolor="white", paper_bgcolor="white")
    st.plotly_chart(fig3, use_container_width=True)

with c4:
    st.subheader("Campaign Performance")
    camp = fdf.groupby(["channel", "campaign"]).agg(
        spend=("spend", "sum"), leads=("leads", "sum"), closed=("closed_deals", "sum"), revenue=("revenue", "sum")
    ).reset_index()
    camp["cpl"] = (camp["spend"] / camp["leads"].replace(0, float("nan"))).round(0)
    camp["roas"] = (camp["revenue"] / camp["spend"].replace(0, float("nan"))).round(2)
    camp_display = camp[["channel", "campaign", "spend", "leads", "closed", "cpl", "roas"]].sort_values("roas", ascending=False)
    camp_display.columns = ["Channel", "Campaign", "Spend (₱)", "Leads", "Closed", "CPL (₱)", "ROAS"]
    st.dataframe(
        camp_display.style.format({"Spend (₱)": "₱{:,.0f}", "CPL (₱)": "₱{:,.0f}", "ROAS": "{:.1f}x"}),
        use_container_width=True, height=380,
    )

st.divider()

# ---- LLM-generated insight summary (Gemini) ----
st.subheader("Auto-Generated Insight Summary")

by_channel_sorted = by_channel.sort_values("cpl")
best_row = by_channel_sorted.iloc[0]
worst_row = by_channel_sorted.iloc[-1]


@st.cache_data(ttl=INSIGHT_TTL_SECONDS)
def generate_insight(best_channel, best_cpl, worst_channel, worst_cpl, roas, total_spend, total_leads):
    api_key = st.secrets.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing GEMINI_API_KEY in Streamlit secrets")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-3.6-flash")
    prompt = (
        "You are a marketing analyst writing a short, plain-language insight summary "
        "for a client-facing dashboard. Use the KPIs below. Be concise (2-3 sentences), "
        "confident, and specific with numbers. Do not use markdown headers.\n\n"
        f"Best-performing channel by cost per lead: {best_channel} (₱{best_cpl:,.0f} per lead)\n"
        f"Worst-performing channel by cost per lead: {worst_channel} (₱{worst_cpl:,.0f} per lead)\n"
        f"Overall ROAS: {roas:.1f}x\n"
        f"Total spend: ₱{total_spend:,.0f}\n"
        f"Total leads: {total_leads:,.0f}\n"
    )
    response = model.generate_content(prompt)
    text = (response.text or "").strip()
    if not text:
        raise RuntimeError("Empty response from Gemini")
    return text


try:
    insight_text = generate_insight(
        best_row["channel"], float(best_row["cpl"]),
        worst_row["channel"], float(worst_row["cpl"]),
        avg_roas, total_spend, total_leads,
    )
    st.info(insight_text)
except Exception:
    st.warning("Insight temporarily unavailable — the AI summary couldn't be generated right now. The dashboard's data and charts above are unaffected.")

st.caption(
    "Data source: a live Google Sheet, refreshed automatically. Insight summary generated "
    "by Gemini from the current KPIs above."
)
