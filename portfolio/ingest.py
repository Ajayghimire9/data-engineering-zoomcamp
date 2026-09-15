"""Idempotent local taxi ingestion; original course examples remain independent."""

import argparse
import csv
import hashlib
import json
import sqlite3
from pathlib import Path


def ingest(source, database):
    source, database = Path(source), Path(database)
    with source.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    required = {"trip_id", "pickup_at", "fare"}
    if not rows or not required.issubset(rows[0]):
        raise ValueError("Expected trip_id, pickup_at and fare columns")
    values = []
    import math
    from datetime import datetime

    for row in rows:
        fare = float(row["fare"])
        if not row["trip_id"] or not math.isfinite(fare) or fare < 0:
            raise ValueError("Invalid trip identifier or fare")
        datetime.fromisoformat(row["pickup_at"])
        values.append((row["trip_id"], row["pickup_at"], fare))
    database.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(database) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS trips (trip_id TEXT PRIMARY KEY, pickup_at TEXT NOT NULL, fare REAL NOT NULL CHECK(fare>=0))"
        )
        conn.executemany(
            "INSERT INTO trips VALUES (?,?,?) ON CONFLICT(trip_id) DO UPDATE SET pickup_at=excluded.pickup_at, fare=excluded.fare",
            values,
        )
        count = conn.execute("SELECT COUNT(*) FROM trips").fetchone()[0]
    return {
        "input_rows": len(values),
        "warehouse_rows": count,
        "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    parser.add_argument("--database", default="artifacts/taxi.db")
    args = parser.parse_args()
    print(json.dumps(ingest(args.source, args.database), indent=2))
