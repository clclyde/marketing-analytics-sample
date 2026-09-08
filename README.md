# Automated Marketing Analytics — Sample Dashboard

A quick, scoped sample built ahead of the marketing team meeting, to have something concrete to show rather than just describing the idea.

## What this is (and isn't)

- Built on **synthetic data** (not a real client), generated to look like realistic campaign performance across 5 channels (Google Ads, Meta Ads, Email, Organic Social, LinkedIn Ads) over ~90 days.
- Live: pulls the source data from a Google Sheet on a short cache TTL (~90s), so the dashboard reflects new rows without a redeploy.
- Clean KPI calculations (CTR, CPL, CPA, ROAS), a funnel view, per-campaign breakdown, and an insight summary genuinely generated fresh by Gemini from the current KPIs each time the cache refreshes.

## Why this architecture, specifically

This mirrors the exact pattern already proven working in the Olist BI project: when Looker Studio's direct Postgres connector failed, the fix was an **n8n workflow** pulling data on a schedule and writing clean results to Google Sheets, which Looker Studio then read from reliably. The same shape applies here: automate the pull from ad platforms/CRM → land it in a clean, structured layer (a Google Sheet, read via a service account) → connect a dashboard on top → refresh on a schedule. Everything downstream (the KPI logic, the dashboard) is built the same way it would be against any other live data source.

## Running it locally

```bash
pip install -r requirements.txt
```

Create `.streamlit/secrets.toml` (gitignored — see `.streamlit/secrets.toml.example` for the exact shape) with:
- `GEMINI_API_KEY` — a Gemini API key
- `[connections.gsheets]` — the target spreadsheet URL, worksheet name, and a Google Cloud service account's credentials (shared as Viewer on the Sheet)

Then:

```bash
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
