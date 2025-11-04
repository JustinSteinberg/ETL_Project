# etl/load.py

"""
load.py
-------
Persist and retrieve transformed rows in SQLite.

Design notes:
- Table 'observations' holds our normalized schema:
  (date TEXT, region TEXT, value REAL, metric TEXT, source_id TEXT PK, epiweek INTEGER)
- `source_id` is a stable primary key: "<state-lower>-<YYYYWW>" so re-running ETL
  for the same window will upsert (idempotent).
- We keep a tiny migration/backfill for 'epiweek' to support older rows.
"""

import sqlite3
from pathlib import Path
import pandas as pd
from datetime import date as dt_date

DATA_PATH = Path("data/disease.db")
TABLE = "observations"

def _ensure_db():
    """
    Create the SQLite DB and table if they don't exist.
    Also perform a lightweight migration to make sure the 'epiweek' column exists.
    """
    DATA_PATH.parent.mkdir(exist_ok=True, parents=True)
    with sqlite3.connect(DATA_PATH) as conn:
        conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE} (
            date TEXT,
            region TEXT,
            value REAL,
            metric TEXT,
            source_id TEXT PRIMARY KEY,
            epiweek INTEGER
        );
        """)
        # use a cursor to fetch pragma results
        cur = conn.execute(f"PRAGMA table_info({TABLE})")
        cols = {row[1] for row in cur.fetchall()}
        if "epiweek" not in cols:
            conn.execute(f"ALTER TABLE {TABLE} ADD COLUMN epiweek INTEGER")
        conn.commit()
    _migrate_existing_rows()

def _iso_monday_from_epiweek(epi: int) -> str:
    """
    Convert an epiweek integer (YYYYWW) to the ISO week Monday (YYYY-MM-DD).
    """
    s = str(int(epi))
    year, week = int(s[:4]), int(s[4:6])
    return dt_date.fromisocalendar(year, week, 1).isoformat()

def _migrate_existing_rows():
    """
    Backfill 'epiweek' and correct 'date' for rows that predate the epiweek column.

    Strategy:
      - Derive epiweek from the trailing part of 'source_id' ("state-YYYYWW")
      - Replace 'date' with the ISO Monday of that epiweek.
      - If parsing fails, leave the record untouched.
    """
    with sqlite3.connect(DATA_PATH) as conn:
        cur = conn.cursor()
        # Fill epiweek from source_id suffix if missing
        cur.execute(f"SELECT source_id, epiweek, date FROM {TABLE} WHERE epiweek IS NULL OR epiweek = ''")
        to_fix = cur.fetchall()
        if to_fix:
            for source_id in to_fix:
                # source_id pattern: "<state>-<YYYYWW>"
                try:
                    epi = int(source_id.split("-")[-1])
                    new_date = _iso_monday_from_epiweek(epi)
                    cur.execute(
                        f"UPDATE {TABLE} SET epiweek=?, date=? WHERE source_id=?",
                        (epi, new_date, source_id),
                    )
                except Exception:
                    # if parsing fails, leave as is
                    pass
            conn.commit()

def save(df: pd.DataFrame) -> int:
    """
    Upsert the given dataframe into SQLite.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain columns: date, region, value, metric, source_id, epiweek.

    Returns
    -------
    int
        Number of rows inserted or updated (SQLite total_changes delta).
    """
    _ensure_db()
    if df is None or df.empty:
        return 0
    rows = [
        (
            pd.to_datetime(r["date"]).strftime("%Y-%m-%d"),
            str(r["region"]),
            float(r["value"]),
            str(r["metric"]),
            str(r["source_id"]),
            int(r["epiweek"]) if "epiweek" in r and pd.notna(r["epiweek"]) else None,
        )
        for r in df.to_dict(orient="records")
    ]
    with sqlite3.connect(DATA_PATH) as conn:
        before = conn.total_changes
        # SQLite UPSERT (requires UNIQUE/PK on source_id)
        conn.executemany(
            f"""
            INSERT INTO {TABLE} (date, region, value, metric, source_id, epiweek)
            VALUES (?,?,?,?,?,?)
            ON CONFLICT(source_id) DO UPDATE SET
                date=excluded.date,
                region=excluded.region,
                value=excluded.value,
                metric=excluded.metric,
                epiweek=excluded.epiweek
            """,
            rows,
        )
        inserted_or_updated = conn.total_changes - before
    return inserted_or_updated

def read_all() -> pd.DataFrame:
    """
    Read the entire observations table into a pandas DataFrame.

    Returns
    -------
    pd.DataFrame
        DataFrame with parsed dates. If the table is missing, returns an empty
        DF with the expected columns.
    """
    _ensure_db()
    with sqlite3.connect(DATA_PATH) as conn:
        try:
            return pd.read_sql_query(f"SELECT * FROM {TABLE}", conn, parse_dates=["date"])
        except Exception:
            return pd.DataFrame(columns=["date","region","value","metric","source_id","epiweek"])
