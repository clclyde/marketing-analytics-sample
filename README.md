# Automated Marketing Analytics — Sample Dashboard

A quick, scoped sample built ahead of the marketing team meeting, to have something concrete to show rather than just describing the idea.

## What this is (and isn't)

- Built on **synthetic data** (not a real client), generated to look like realistic campaign performance across 5 channels (Google Ads, Meta Ads, Email, Organic Social, LinkedIn Ads) over ~90 days.
- Demonstrates the **architecture**, not a finished product: clean KPI calculations (CTR, CPL, CPA, ROAS), a funnel view, per-campaign breakdown, and an auto-generated insight summary.
- The insight summary is currently a template for this demo. In a real build, this would be generated live by an LLM reading the current numbers, the same pattern already proven in the Olist BI portfolio's AI Query Assistant.

## Why this architecture, specifically

This mirrors the exact pattern already proven working in the Olist BI project: when Looker Studio's direct Postgres connector failed, the fix was an **n8n workflow** pulling data on a schedule and writing clean results to Google Sheets, which Looker Studio then read from reliably. The same shape applies here: automate the pull from ad platforms/CRM → land it in a clean, structured layer → connect a dashboard on top → refresh on a schedule. This demo uses a static CSV standing in for that automated pull, everything downstream (the KPI logic, the dashboard) is built the same way it would be against real, live data.

## Running it locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploying it (same process as the Olist dashboard)

1. Push this folder to a GitHub repo
2. Go to share.streamlit.io, connect the repo, deploy
3. Same workflow already used successfully for the Olist BI portfolio (olist-bi-portfolio-clclyde.streamlit.app)

## Talking points if this comes up in the meeting

- This is a **sample**, not existing client work, be upfront about that if asked directly.
- The real value being demonstrated isn't the dashboard itself, it's the **automated pipeline** behind it: same architecture that already solved a real technical problem (the Looker Studio connector failure) in a previous project.
- Next step, if there's interest: swap the synthetic CSV for a real automated pull from an actual ad platform or CRM API, the dashboard layer barely needs to change.
