"""
Unit tests for Disease ETL pipeline.
Includes detailed logging for every test phase.
"""

import os
import json
import logging
import tempfile
from typing import Any, Dict, List

import pandas as pd
import pytest
from fastapi.testclient import TestClient

import app as backend_app
from etl.transform import transform, summary_stats
from etl.load import save, read_all
from etl import load as load_mod
from etl import ingest as ingest_mod


# ----------------------------------------------------------------------------
# Configure logging for test session
# ----------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
def temp_db(monkeypatch):
    """Redirect SQLite path to temporary DB for every test."""
    with tempfile.TemporaryDirectory() as td:
        tmp_path = os.path.join(td, "test.db")
        from pathlib import Path
        monkeypatch.setattr(load_mod, "DATA_PATH", Path(tmp_path))
        logger.info(f"🧪 Using temporary database at {tmp_path}")
        yield


@pytest.fixture()
def client():
    """Provide a FastAPI TestClient for API endpoint tests."""
    return TestClient(backend_app.app)


# ----------------------------------------------------------------------------
# Transform + Load Layer Tests
# ----------------------------------------------------------------------------

def test_transform_empty():
    """Empty input should yield empty DataFrame with correct schema."""
    logger.info("Running test_transform_empty...")
    df = transform([])
    logger.debug(f"Transform output columns: {df.columns.tolist()}")
    assert list(df.columns) == ["date", "region", "value", "metric", "source_id", "epiweek"]
    assert df.empty
    logger.info("✅ Empty transform returns empty DataFrame with schema intact.")


def test_transform_basic_row():
    """A valid FluView row normalizes fields correctly."""
    logger.info("Running test_transform_basic_row...")
    raw = [{"region": "ma", "epiweek": 202501, "wili": 1.23}]
    df = transform(raw)
    logger.debug(f"Transformed row: {df.iloc[0].to_dict()}")
    assert df.iloc[0]["region"] == "MA"
    assert df.iloc[0]["metric"] == "ili"
    assert df.iloc[0]["value"] == pytest.approx(1.23)
    assert "date" in df.columns and len(df.iloc[0]["date"]) == 10
    logger.info("Basic transform produces normalized row correctly.")


def test_save_and_read_upsert():
    """Saving twice with same key should update (not duplicate) rows."""
    logger.info("Running test_save_and_read_upsert...")
    df1 = transform([{"region": "ma", "epiweek": 202501, "wili": 1.0}])
    n1 = save(df1)
    logger.info(f"Inserted {n1} rows.")

    df2 = transform([{"region": "ma", "epiweek": 202501, "wili": 2.0}])
    n2 = save(df2)
    logger.info(f"Upserted {n2} rows (should replace previous).")

    out = read_all()
    logger.debug(f"DB contents after upsert: {out.to_dict(orient='records')}")
    assert len(out) == 1
    assert float(out.iloc[0]["value"]) == pytest.approx(2.0)
    logger.info("✅ Upsert works: only one row exists with updated value.")


def test_summary_stats():
    """summary_stats should compute correct min/max/count over a small frame."""
    logger.info("Running test_summary_stats...")
    df = transform([
        {"region": "ma", "epiweek": 202501, "wili": 1.0},
        {"region": "ma", "epiweek": 202502, "wili": 3.0}
    ])
    s = summary_stats(df)
    logger.info(f"Summary stats: {json.dumps(s, indent=2)}")
    assert s["count"] == 2
    assert s["min"] == pytest.approx(1.0)
    assert s["max"] == pytest.approx(3.0)
    logger.info("Summary stats computed correctly.")


def test_ingest_error_message(monkeypatch):
    """fetch() should raise a RuntimeError if API returns an error."""
    logger.info("Running test_ingest_error_message...")

    def fake_get(*a, **k):
        class R:
            def raise_for_status(self): pass
            def json(self):
                return {"result": -1, "message": "rate limited"}
        return R()

    monkeypatch.setattr(ingest_mod.requests, "get", fake_get)
    with pytest.raises(RuntimeError):
        ingest_mod.fetch("ma", "202501-202505")
    logger.info("Ingest properly raises RuntimeError on API failure.")


# ----------------------------------------------------------------------------
# API Route Tests
# ----------------------------------------------------------------------------

def _sample_raw(region: str, weeks: List[int], vals: List[float]):
    """Helper: build fake rows for mocked API fetch."""
    return [{"region": region, "epiweek": w, "wili": v} for w, v in zip(weeks, vals)]


def test_run_etl_endpoints(client, monkeypatch):
    """Run ETL, stats, and data endpoints with mocked fetch."""
    logger.info("Running test_run_etl_endpoints...")

    def fake_fetch(region: str, epiweeks: str | None = None):
        if region == "ma":
            return _sample_raw("ma", [202501, 202502], [1.0, 3.0])
        if region == "ny":
            return _sample_raw("ny", [202501, 202502], [2.0, 4.0])
        return []

    monkeypatch.setattr(ingest_mod, "fetch", fake_fetch)
    logger.info("🔧 Mocked fetch() to avoid network requests.")

    r = client.post("/etl/run", params={"region": "all", "start_date": "2025-01-01", "end_date": "2025-01-14"})
    logger.info(f"/etl/run response: {r.status_code} {r.json()}")
    assert r.status_code == 200
    assert r.json()["rows_loaded"] == 150

    stats = client.get("/stats", params={"region": "MA", "start_date": "2025-01-01", "end_date": "2025-01-31"}).json()
    logger.info(f"/stats output: {stats}")
    assert stats["count"] == 3

    data = client.get("/data", params={"region": "MA", "start_date": "2025-01-01", "end_date": "2025-01-31"}).json()
    logger.info(f"/data output rows: {len(data['rows'])}")
    assert len(data["rows"]) == 3

    mapr = client.get("/map", params={"start_date": "2025-01-01", "end_date": "2025-01-31"})
    logger.info(f"/map output: {mapr.json()}")
    assert mapr.status_code == 200

    csv = client.get("/download.csv", params={"start_date": "2025-01-01", "end_date": "2025-01-31"})
    logger.info(f"/download.csv headers: {csv.headers}")
    assert csv.status_code == 200
    assert "text/csv" in csv.headers["content-type"]
    logger.info("✅ Full ETL and retrieval path works end-to-end.")


def test_run_etl_bad_dates(client):
    """Start > end should trigger 400 Bad Request."""
    logger.info("Running test_run_etl_bad_dates...")
    r = client.post("/etl/run", params={"region": "MA", "start_date": "2025-02-01", "end_date": "2025-01-01"})
    logger.info(f"Response: {r.status_code} {r.json()}")
    assert r.status_code == 400
    assert "start_date must be" in r.json().get("error", "")
    logger.info("Properly rejects invalid date range.")
