# Marketing Analytics Dashboard — Project Context

## What this project is

A sample marketing analytics dashboard (Streamlit), originally built on a static synthetic CSV to demonstrate an approach ahead of an internal meeting. It's now being upgraded from a static demo into a genuinely live, automated dashboard.

**Current live version**: https://marketing-analytics-sample.streamlit.app/
**Repo**: (this folder, pushed to `clclyde/marketing-analytics-sample` on GitHub)

## Current architecture (as of the static-CSV version)

- `app.py` — Streamlit app: loads `marketing_sample_data.csv`, computes KPIs (CTR, CPL, CPA, ROAS), renders a KPI strip, a spend-vs-leads time chart, a cost-per-lead-by-channel chart, a funnel chart, a campaign performance table, and an insight summary box.
- `marketing_sample_data.csv` — synthetic data, 5 channels (Google Ads, Meta Ads, Email, Organic Social, LinkedIn Ads), ~90 days, columns: `date, channel, campaign, spend, impressions, clicks, leads, closed_deals`.
- The insight summary is currently a **hardcoded template** (numbers plugged into a fixed sentence), not LLM-generated. This is the first thing changing.
- Deployed on Streamlit Community Cloud, Python 3.11/3.12 (do not use 3.14, dependency wheels aren't reliably available for it yet).

## What's changing in this pass

### 1. Live Google Sheets data source, replacing the static CSV

- There is an existing Google Sheet that gets updated with new marketing data. **Ask the user for the actual Sheet URL/ID and confirm the exact column names by reading the first few rows directly**, don't assume they match `marketing_sample_data.csv`'s columns exactly, map explicitly.
- Use a **Google Cloud service account** for read access (the standard Streamlit pattern), not a public CSV export link. Steps: create a service account in Google Cloud Console, enable the Sheets API, share the target Sheet with the service account's email (viewer access is enough), store the service account JSON credentials in Streamlit's **Secrets** (TOML format) — never commit the credentials file to the repo.
- Use `gspread` (or `st.connection` with `streamlit-gsheets` if it simplifies auth, evaluate both, pick whichever is more reliable) to read the Sheet into a DataFrame.
- Keep `@st.cache_data`, but set a short TTL (e.g., 60–120 seconds) so the app periodically re-pulls fresh data without needing a manual redeploy. Confirm this actually works by editing the real Sheet and watching the app pick up the change within that window, don't just assume the cache logic is correct from reading the code.

### 2. Charts must genuinely update when the underlying data changes

- This should mostly fall out naturally once the cache TTL is short and charts are built from the freshly-pulled DataFrame, but verify explicitly: add a row to the real Sheet, wait past the TTL, reload the app, confirm the new row is reflected in at least the KPI strip and the relevant chart. Show this verification, don't just assert it works.

### 3. Real LLM-generated insights via Gemini

- Replace the current hardcoded template with an actual call to the Gemini API (`google-generativeai` package). The user has Gemini API credits available; store the API key as `GEMINI_API_KEY` in Streamlit Secrets, never hardcode it.
- Prompt Gemini with the current computed KPIs (best/worst channel by CPL, overall ROAS, any notable trend) and ask for a short, plain-language insight summary, similar tone to the current template but genuinely generated fresh each time.
- **Cache the Gemini response** (e.g., alongside the data cache, same TTL or slightly longer) rather than calling the API on every filter interaction or page rerun. Streamlit reruns the whole script on most interactions, an uncached LLM call here would be slow and needlessly burn API credits.
- Handle the API call failing gracefully (rate limit, network issue, bad key) — fall back to a clear "insight temporarily unavailable" message, never let it crash the whole dashboard.

### 4. Redesign to a light theme

- Currently unstyled/default Streamlit theming. Add a `.streamlit/config.toml` with an explicit `[theme]` section (light background, readable text/primary colors), don't rely on the viewer's system dark/light mode setting, which is what's likely causing inconsistent appearance right now.
- Keep the existing KPI-strip-plus-charts layout structure, this is a visual theme pass, not a layout rebuild.

## Verification standard for this project

Real evidence, not claims, matching the standard used throughout this whole civic tech / dashboard workstream:
- Show the actual Sheet edit → actual dashboard refresh → confirm the specific new value appears, don't just say "caching should work."
- Show an actual Gemini API response in a test run, not a description of what it should say.
- Screenshot or describe the light theme rendering correctly, confirm no leftover dark-mode-only elements (e.g., text that's invisible against a light background).
- Confirm the app still deploys and runs cleanly on Streamlit Cloud after all changes, not just locally.

## Known constraints / things to ask the user about, don't assume

- The exact Google Sheet's URL, tab name, and column structure — not yet provided, ask directly.
- Whether the Sheet is the final data or itself gets fed by something else upstream (e.g., manually updated, or by a separate process) — relevant context but not required to complete this pass.
- Gemini model choice — default to a fast, low-cost model (e.g., `gemini-2.0-flash` or newer equivalent) unless told otherwise, this is a lightweight summarization task, not something needing a larger model.
