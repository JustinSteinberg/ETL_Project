# Disease ETL (FluView → SQLite → API + SvelteKit UI)

## Overview
Minimal ETL that fetches influenza-like illness (ILI) from CMU Delphi FluView, normalizes into a 6-column schema, stores in SQLite, and exposes a tiny API and UI (chart, table, US heatmap).

## Schema
Table: `observations`
- `date` (TEXT, ISO YYYY-MM-DD, Monday of epiweek)
- `region` (TEXT, USPS state code, e.g., MA)
- `value` (REAL, weighted ILI %)
- `metric` (TEXT, 'ili')
- `source_id` (TEXT, PK, `<state>-<YYYYWW>`)
- `epiweek` (INTEGER, YYYYWW)

## Setup
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # add DELPHI_API_KEY=...
uvicorn app:app --reload --port 8000
