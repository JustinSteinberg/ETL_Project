# etl/ingest.py
import os
import requests
from dotenv import load_dotenv

# Load the .env file once
load_dotenv()

BASE = "https://api.delphi.cmu.edu/epidata/fluview/"
API_KEY = os.getenv("DELPHI_API_KEY")

def fetch(region: str, epiweeks: str | None = None) -> list[dict]:
    """
    Fetch FluView data for a given state and epiweek range.

    Parameters
    ----------
    region : str
        Two-letter USPS state code. Case-insensitive; we send lowercase
        because FluView accepts region names that way (e.g., "ma").
    epiweeks : str | None
        Range string "YYYYWW-YYYYWW". If None, we use a broad default window
        so the caller always gets something when exploring.

    Returns
    -------
    list[dict]
        Raw Epidata records (each a dict). We intentionally return the raw
        structure here; the transform step will normalize into our schema.
    """
    region = region.lower()
    params = {
        "regions": region,
        "epiweeks": epiweeks or "201401-202552",
        "api_key": API_KEY, 
    }

    r = requests.get(BASE, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()

    if data.get("result") == 1:
        return data.get("epidata", [])

    msg = (data.get("message") or "").lower()
    if "no results" in msg or "no data" in msg:
        return []

    raise RuntimeError(f"FluView error: {data.get('message')}")
