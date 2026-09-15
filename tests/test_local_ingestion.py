import sqlite3

import pytest

from portfolio.ingest import ingest


def test_rerun_is_idempotent(tmp_path):
    db = tmp_path / "taxi.db"
    assert ingest("portfolio/sample.csv", db)["warehouse_rows"] == 2
    assert ingest("portfolio/sample.csv", db)["warehouse_rows"] == 2
    bad = tmp_path / "bad.csv"
    bad.write_text("trip_id,pickup_at,fare\na,2026-01-01T09:00:00,-1\n")
    with pytest.raises(ValueError):
        ingest(bad, db)
    with sqlite3.connect(db) as conn:
        assert conn.execute("SELECT COUNT(*) FROM trips").fetchone()[0] == 2
