
Dataset: CMU Delphi Epidata - FluView
Geo default: MA (US state codes)
Time window: Epiweeks 2024–2025

Normalized schema (table: observations):
- date (DATE, from release_date)
- region (TEXT, uppercase 2-letter)
- value (REAL, ILI weighted %)
- metric (TEXT, literal "ili")
- source_id (TEXT, PK = "{region_lower}-{epiweek}")

Cleaning rules:
- parse date; drop invalid
- uppercase region
- coerce value→float; drop missing/negative
- deduplicate by source_id

API contracts:
- POST /etl/run → {"rows_loaded": int}
- GET /stats → {"count": int, "min": number|null, "max": number|null, "start": string|null, "end": string|null, "regions": string[]}
- GET /data?limit=&offset=&region= → {"total": int, "rows": [...]}
- GET /download.csv → cleaned CSV

Storage:
- SQLite: data/disease.db (table observations)
- Download: cleaned.csv (columns in order above)

Definition of done (Step 1):
- This SPEC.md committed; no scope creep without editing this file.
