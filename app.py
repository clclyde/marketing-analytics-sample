import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Automated Marketing Analytics — Sample", layout="wide")

# ---- Load data ----
@st.cache_data(ttl=300)
def load_data():
    df = pd.read_csv("marketing_sample_data.csv", parse_dates=["date"])
    df["ctr"] = df["clicks"] / df["impressions"]
    df["cpl"] = df["spend"] / df["leads"].replace(0, pd.NA)
    df["cpa"] = df["spend"] / df["closed_deals"].replace(0, pd.NA)
    # Assumed average deal value for ROAS illustration
    df["revenue"] = df["closed_deals"] * 8500
    df["roas"] = df["revenue"] / df["spend"].replace(0, pd.NA)
    return df

df = load_data()

# ---- Header ----
st.title("Automated Marketing Analytics — Sample Dashboard")
st.caption(
    "Concept demo built on synthetic data, showing the kind of automated, "
    "client-facing reporting pipeline this could become: campaign data flowing "
    "in on a schedule, transformed into clean KPIs, and refreshed automatically."
)
st.caption(f"Data last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M')} (sample data, static for this demo)")

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
    )
    st.plotly_chart(fig1, use_container_width=True)

with c2:
    by_channel = fdf.groupby("channel").agg(spend=("spend", "sum"), leads=("leads", "sum"), closed=("closed_deals", "sum")).reset_index()
    by_channel["cpl"] = by_channel["spend"] / by_channel["leads"].replace(0, pd.NA)
    fig2 = px.bar(by_channel.sort_values("cpl"), x="channel", y="cpl", title="Cost per Lead by Channel", text_auto=".0f")
    fig2.update_layout(height=380, yaxis_title="Cost per Lead (₱)")
    st.plotly_chart(fig2, use_container_width=True)

# ---- Row 2: Funnel + campaign table ----
c3, c4 = st.columns([1, 2])
with c3:
    funnel_vals = [fdf["impressions"].sum(), fdf["clicks"].sum(), fdf["leads"].sum(), fdf["closed_deals"].sum()]
    fig3 = go.Figure(go.Funnel(y=["Impressions", "Clicks", "Leads", "Closed Deals"], x=funnel_vals))
    fig3.update_layout(title="Overall Funnel", height=380)
    st.plotly_chart(fig3, use_container_width=True)

with c4:
    st.subheader("Campaign Performance")
    camp = fdf.groupby(["channel", "campaign"]).agg(
        spend=("spend", "sum"), leads=("leads", "sum"), closed=("closed_deals", "sum"), revenue=("revenue", "sum")
    ).reset_index()
    camp["cpl"] = (camp["spend"] / camp["leads"].replace(0, pd.NA)).round(0)
    camp["roas"] = (camp["revenue"] / camp["spend"].replace(0, pd.NA)).round(2)
    camp_display = camp[["channel", "campaign", "spend", "leads", "closed", "cpl", "roas"]].sort_values("roas", ascending=False)
    camp_display.columns = ["Channel", "Campaign", "Spend (₱)", "Leads", "Closed", "CPL (₱)", "ROAS"]
    st.dataframe(
        camp_display.style.format({"Spend (₱)": "₱{:,.0f}", "CPL (₱)": "₱{:,.0f}", "ROAS": "{:.1f}x"}),
        use_container_width=True, height=380,
    )

st.divider()

# ---- AI-style auto-generated insight summary (illustrative) ----
st.subheader("Auto-Generated Insight Summary")
best_channel = by_channel.sort_values("cpl").iloc[0]["channel"]
worst_channel = by_channel.sort_values("cpl").iloc[-1]["channel"]
st.info(
    f"Over the selected period, **{best_channel}** delivered the lowest cost per lead "
    f"(₱{by_channel.sort_values('cpl').iloc[0]['cpl']:,.0f}), while **{worst_channel}** was "
    f"the least efficient (₱{by_channel.sort_values('cpl').iloc[-1]['cpl']:,.0f}). "
    f"Overall ROAS across all channels was **{avg_roas:.1f}x**. "
    f"*(This summary is written by a template for this demo — in production, this would be "
    f"generated live by an LLM reading the current numbers each time the dashboard refreshes, "
    f"the same pattern used in the Olist BI portfolio's AI Query Assistant.)*"
)

st.caption(
    "This is a scoped sample built to illustrate the approach: synthetic data standing in for "
    "real client data sources (ad platforms, CRM), with the same clean-data-layer → dashboard → "
    "automated-refresh architecture used in the Olist BI project, adapted for marketing KPIs."
)
