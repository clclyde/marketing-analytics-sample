# Automated Marketing Analytics — Sample Dashboard

A quick, scoped sample built ahead of the marketing team meeting, to have something concrete to show rather than just describing the idea.

## What this is (and isn't)

- Built on **synthetic data** (not a real client), generated to look like realistic campaign performance across 5 channels (Google Ads, Meta Ads, Email, Organic Social, LinkedIn Ads) over ~90 days.
- Live: pulls the source data from a Google Sheet on a short cache TTL (~90s), so the dashboard reflects new rows without a redeploy.
- Clean KPI calculations (CTR, CPL, CPA, ROAS), a funnel view, per-campaign breakdown, and an insight summary genuinely generated fresh by Gemini from the current KPIs each time the cache refreshes.
- A second tab, "Ask the Data", is a Gemini-powered chatbot that can answer questions about marketing terminology (CTR, CPL, CPA, ROAS, funnel stages) and about the data itself, grounded in the same live snapshot the dashboard uses. Capped at 20 messages per session as a cost/abuse guard.
- Gated behind a shared password (`APP_PASSWORD` in secrets) so the deployed URL isn't wide open — appropriate for showing to a specific audience, not a substitute for real per-user auth.

## Why this architecture, specifically

This mirrors the exact pattern already proven working in the Olist BI project: when Looker Studio's direct Postgres connector failed, the fix was an **n8n workflow** pulling data on a schedule and writing clean results to Google Sheets, which Looker Studio then read from reliably. The same shape applies here: automate the pull from ad platforms/CRM → land it in a clean, structured layer (a Google Sheet, read via a service account) → connect a dashboard on top → refresh on a schedule. Everything downstream (the KPI logic, the dashboard) is built the same way it would be against any other live data source.

## Running it locally

```bash
pip install -r requirements.txt
```

Create `.streamlit/secrets.toml` (gitignored — see `.streamlit/secrets.toml.example` for the exact shape) with:
- `GEMINI_API_KEY` — a Gemini API key
- `APP_PASSWORD` — the shared password gating the app (if unset, the app runs without a password — fine for local dev only)
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

- This is a **sample**, not existing client work, be upfront about that if asked directly (the in-app banner says so too).
- The real value being demonstrated isn't the dashboard itself, it's the **automated pipeline** behind it: same architecture that already solved a real technical problem (the Looker Studio connector failure) in a previous project.
- Next step, if there's interest: swap the synthetic Sheet for a real automated pull from an actual ad platform or CRM API, the dashboard layer barely needs to change.

## Known limitations (not yet production-ready)

Honest list, in case it comes up:

- **Access control is a shared password, not real auth.** Fine for a controlled demo/meeting; anyone with the password and link can see everything. A real rollout needs per-user login (Streamlit supports SSO on paid tiers, or this could sit behind the company's existing identity provider).
- **The source Google Sheet is still manually updated**, not fed by a real ad-platform/CRM integration. That's the natural next step, and the dashboard layer wouldn't need to change much to consume a real automated feed.
- **Revenue/ROAS uses an assumed ₱8,500 average deal value**, not real deal data — clearly flagged in the UI, but worth restating out loud if asked.
- **No usage monitoring or alerting** on the Gemini API calls beyond the per-session chat cap; a spike in traffic (e.g. the link getting shared widely) could still increase API cost without anyone noticing right away.
- **Hosted on Streamlit Community Cloud's free tier**, which can idle/sleep after a period of no traffic and has modest resource limits — fine for a meeting demo, not for guaranteed uptime at scale.
