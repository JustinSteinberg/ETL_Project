
"""
transform.py
------------
Normalize raw Epidata (FluView) records into our internal schema and compute summary stats.

Key decisions:
- We derive a real `date` (ISO Monday) from `epiweek` so chart axes are intuitive.
- `source_id` = "<state-lower>-<YYYYWW>" gives a stable key for UPSERTs.
- We keep `metric="ili"` (weighted ILI percentage) so the table can support future metrics.
"""

import pandas as pd
from datetime import date as dt_date

COLUMNS = ["date", "region", "value", "metric", "source_id", "epiweek"]

def _epiweek_to_date(epi: int) -> str:
    s = str(int(epi))
    year, week = int(s[:4]), int(s[4:6])
    return pd.Timestamp(dt_date.fromisocalendar(year, week, 1)).strftime("%Y-%m-%d")

def transform(raw: list[dict]) -> pd.DataFrame:
    """
    Normalize raw Epidata records into the warehouse schema.

    Parameters
    ----------
    raw : list[dict]
        Raw records from `ingest.fetch`.

    Returns
    -------
    pd.DataFrame
        Columns: date, region, value, metric, source_id, epiweek
        - date     : ISO Monday of epiweek
        - region   : USPS state (uppercased)
        - value    : weighted ILI percentage (wili)
        - metric   : literal "ili"
        - source_id: "<state-lower>-<YYYYWW>"
        - epiweek  : integer YYYYWW
    """
    if not raw:
        return pd.DataFrame(columns=COLUMNS)

    df = pd.DataFrame(raw)

    # Normalize names/types
    df = df.rename(columns={"wili": "value"})
    df["region"] = df["region"].astype(str).str.upper()
    df["metric"] = "ili"

    # epiweek: be robust to bad/missing values
    df["epiweek"] = pd.to_numeric(df.get("epiweek"), errors="coerce").astype("Int64")
    df = df.dropna(subset=["epiweek"]).copy()
    df["epiweek"] = df["epiweek"].astype(int)

    # date from epiweek (ISO Monday)
    df["date"] = df["epiweek"].apply(_epiweek_to_date)

    # stable PK
    df["source_id"] = df["region"].str.lower() + "-" + df["epiweek"].astype(str)

    # numeric value
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    return df[["date", "region", "value", "metric", "source_id", "epiweek"]]


def summary_stats(df: pd.DataFrame) -> dict:
    """
    Compute lightweight summary statistics for a (possibly filtered) dataset.

    Parameters
    ----------
    df : pd.DataFrame
        Typically the result of reading SQLite and filtering by region and date.

    Returns
    -------
    dict
        {
          "count": int,          # number of rows
          "min": float | None,   # min ILI
          "max": float | None,   # max ILI
          "start": "YYYY-MM-DD" | None,  # min date
          "end":   "YYYY-MM-DD" | None,  # max date
          "regions": [str, ...]  # unique region list (sorted)
        }
    """
    if df is None or df.empty:
        return {"count": 0, "min": None, "max": None, "start": None, "end": None, "regions": []}

    dfx = df.copy()
    dfx["date"] = pd.to_datetime(dfx["date"])

    return {
        "count": int(len(dfx)),
        "min": float(dfx["value"].min()),
        "max": float(dfx["value"].max()),
        "start": dfx["date"].min().strftime("%Y-%m-%d"),
        "end": dfx["date"].max().strftime("%Y-%m-%d"),
        "regions": sorted(dfx["region"].unique().tolist()),
    }
