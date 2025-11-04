"""
FastAPI backend for the Disease ETL (Extract-Transform-Load) dashboard.

This service ingests influenza-like illness (ILI) data from the Carnegie Mellon
Delphi FluView API, transforms it into a clean tabular format, saves it locally
to SQLite, and exposes multiple endpoints for visualization and download.

Frontend consumers (e.g., SvelteKit app) can:
  - Run ETL jobs for specific states or all states (/etl/run)
  - Query stored data (/data)
  - Retrieve summary statistics (/stats)
  - Generate map-ready aggregated data (/map)
  - Download full datasets as CSV (/download.csv)
"""

import logging
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse, StreamingResponse
from datetime import date as dt_date
import pandas as pd
from io import StringIO

from etl.ingest import fetch
from etl.transform import transform, summary_stats
from etl.load import save, read_all

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Disease ETL API")

STATES = ['AL','AK','AZ','AR','CA','CO','CT','DE','DC','FL','GA','HI','ID','IL','IN','IA','KS','KY','LA','ME','MD','MA','MI','MN','MS','MO','MT','NE','NV','NH','NJ','NM','NY','NC','ND','OH','OK','OR','PA','RI','SC','SD','TN','TX','UT','VT','VA','WA','WV','WI','WY']

def _date_to_epiweek(d: dt_date) -> int:
    """
    Convert a standard date (YYYY-MM-DD) into an integer epiweek (YYYYWW).
    Epiweeks are standardized by the CDC and align with ISO weeks.
    Example: 2025-01-07 → 202501
    """
    y, w, _ = d.isocalendar()
    return int(f"{y:04d}{w:02d}")

def _epiweek_to_monday(epi: int) -> str:
    """
    Convert an epiweek integer (YYYYWW) to its Monday start date (YYYY-MM-DD).
    Used for visual labels and time range summaries.
    Example: 202501 → '2024-12-30'
    """
    s = str(int(epi)); y, w = int(s[:4]), int(s[4:6])
    return pd.Timestamp(dt_date.fromisocalendar(y, w, 1)).strftime("%Y-%m-%d")

@app.post("/etl/run")
def run_etl(
    region: str = "ma",
    start_date: str | None = Query(None, description="YYYY-MM-DD"),
    end_date: str | None = Query(None, description="YYYY-MM-DD"),
):
    """
    Execute a complete ETL cycle for a given region and date range.

    Steps:
    1. Convert the start and end dates into epiweek format.
    2. Fetch raw ILI data for the selected regions from the Delphi API.
    3. Transform and normalize the results into tabular structure.
    4. Save all rows into SQLite (UPSERT behavior on source_id).
    5. Return a summary (rows loaded, first/last epiweek covered).

    Supports:
        - region='MA' for a single state
        - region='all' or '*' for all U.S. states
    """
    logger.info(f"ETL job started - region: {region}, start_date: {start_date}, end_date: {end_date}")
    
    try:
        epi = None
        if start_date and end_date:
            sd, ed = dt_date.fromisoformat(start_date), dt_date.fromisoformat(end_date)
            if sd > ed:
                logger.warning(f"Invalid date range: {start_date} > {end_date}")
                return JSONResponse(status_code=400, content={"error": "start_date must be <= end_date"})
            epi = f"{_date_to_epiweek(sd)}-{_date_to_epiweek(ed)}"
            logger.info(f"Date range converted to epiweek range: {epi}")

        regions = STATES if region.lower() in ("all", "*") else [region.upper()]
        logger.info(f"Processing {len(regions)} region(s)")
        
        all_dfs = []
        total_rows = 0

        for r in regions:
            logger.info(f"Fetching data for region: {r}")
            raw = fetch(r.lower(), epiweeks=epi)
            
            df = transform(raw)
            if not df.empty:
                rows_count = len(df)
                total_rows += int(rows_count)
                logger.info(f"Transformed {rows_count} rows for {r}")
                
                save(df)
                logger.info(f"Saved {rows_count} rows for {r} to database")
                all_dfs.append(df)
            else:
                logger.warning(f"No data returned for region: {r}")

        if not all_dfs:
            logger.warning("ETL completed with no data loaded")
            return {"rows_loaded": 0, "first_week": None, "last_week": None}

        big = pd.concat(all_dfs, ignore_index=True)
        first_epi = int(big["epiweek"].min())
        last_epi  = int(big["epiweek"].max())
        
        result = {
            "rows_loaded": int(total_rows),
            "first_week": _epiweek_to_monday(first_epi),
            "last_week":  _epiweek_to_monday(last_epi)
        }
        
        logger.info(f"ETL completed successfully: {result}")
        return result
        
    except Exception as e:
        logger.error(f"ETL job failed: {str(e)}", exc_info=True)
        return JSONResponse(status_code=400, content={"error": str(e)})

@app.get("/stats")
def get_stats(region: str | None = None, start_date: str | None = None, end_date: str | None = None):
    logger.info(f"Stats request - region: {region}, start_date: {start_date}, end_date: {end_date}")
    
    try:
        df = read_all()
        initial_count = len(df)
        logger.debug(f"Read {initial_count} total rows from database")
        
        if region: 
            df = df[df["region"] == region.upper()]
            logger.debug(f"Filtered to region {region}: {len(df)} rows")
            
        if start_date: 
            df = df[df["epiweek"] >= _date_to_epiweek(dt_date.fromisoformat(start_date))]
            logger.debug(f"Filtered by start_date: {len(df)} rows remain")
            
        if end_date:   
            df = df[df["epiweek"] <= _date_to_epiweek(dt_date.fromisoformat(end_date))]
            logger.debug(f"Filtered by end_date: {len(df)} rows remain")
        
        stats = summary_stats(df)
        logger.info(f"Returning stats for {len(df)} rows")
        return stats
        
    except Exception as e:
        logger.error(f"Error generating stats: {str(e)}", exc_info=True)
        raise

@app.get("/data")
def get_data(
    limit: int = 50,
    offset: int = 0,
    region: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
):
    """
    Return raw observation rows for table or chart visualization.

    Pagination is supported via `limit` and `offset`.
    The frontend uses this endpoint to populate the "Explore" tab.

    Returns:
        {
            "total": <int>,
            "rows": [ {date, region, value, metric, source_id, epiweek}, ... ]
        }
    """
    logger.info(f"Data request - limit: {limit}, offset: {offset}, region: {region}, "
                f"start_date: {start_date}, end_date: {end_date}")
    
    try:
        df = read_all()
        if region: df = df[df["region"] == region.upper()]
        if start_date: df = df[df["epiweek"] >= _date_to_epiweek(dt_date.fromisoformat(start_date))]
        if end_date:   df = df[df["epiweek"] <= _date_to_epiweek(dt_date.fromisoformat(end_date))]
        
        total = int(len(df))
        page = df.sort_values("date").iloc[offset:offset+limit].copy()
        page["date"] = pd.to_datetime(page["date"]).dt.strftime("%Y-%m-%d")
        
        logger.info(f"Returning {len(page)} rows out of {total} total")
        return {"total": total, "rows": page.to_dict(orient="records")}
        
    except Exception as e:
        logger.error(f"Error retrieving data: {str(e)}", exc_info=True)
        raise

@app.get("/map")
def map_data(start_date: str, end_date: str, metric: str = "ili"):
    """
    Aggregate mean ILI (%) values for all states within a date range.

    Used by the frontend's U.S. choropleth map to color each state based
    on its average ILI percentage.

    Returns a dictionary:
        { 'MA': 1.23, 'NY': 0.94, 'TX': 2.05, ... }
    """
    logger.info(f"Map data request - start_date: {start_date}, end_date: {end_date}, metric: {metric}")
    
    try:
        df = read_all()
        sd = _date_to_epiweek(dt_date.fromisoformat(start_date))
        ed = _date_to_epiweek(dt_date.fromisoformat(end_date))
        df = df[(df["metric"] == metric) & (df["epiweek"] >= sd) & (df["epiweek"] <= ed)]
        
        if df.empty:
            logger.warning(f"No data found for map with given parameters")
            return {}
        
        gp = df.groupby("region")["value"].mean().round(6)
        result_dict = gp.to_dict()
        
        logger.info(f"Returning map data for {len(result_dict)} regions")
        return result_dict
        
    except Exception as e:
        logger.error(f"Error generating map data: {str(e)}", exc_info=True)
        raise

@app.get("/download.csv")
def download_csv(region: str | None = None, start_date: str | None = None, end_date: str | None = None):
    """
    Stream the full (filtered) dataset as a CSV file.

    Allows analysts or users to download the processed data directly
    from the UI for further use in Excel, R, or Python notebooks.
    """
    logger.info(f"CSV download request - region: {region}, start_date: {start_date}, end_date: {end_date}")
    
    try:
        df = read_all()
        if region: df = df[df["region"] == region.upper()]
        if start_date: df = df[df["epiweek"] >= _date_to_epiweek(dt_date.fromisoformat(start_date))]
        if end_date:   df = df[df["epiweek"] <= _date_to_epiweek(dt_date.fromisoformat(end_date))]
        
        logger.info(f"Generating CSV with {len(df)} rows")
        
        csv_buf = StringIO()
        df.sort_values(["region","date"]).to_csv(csv_buf, index=False)
        csv_buf.seek(0)
        
        logger.info("CSV download started")
        return StreamingResponse(csv_buf, media_type="text/csv",
            headers={"Content-Disposition": 'attachment; filename="cleaned.csv"'})
            
    except Exception as e:
        logger.error(f"Error generating CSV: {str(e)}", exc_info=True)
        raise