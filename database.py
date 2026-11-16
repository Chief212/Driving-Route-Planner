"""SQLite persistence for the Driving Route Planner.

The table definitions live in schema.sql. Keep that file as the single source
of truth so the Python implementation cannot silently diverge from the schema.
"""
from pathlib import Path
import sqlite3

DB_NAME = "route_planner.db"
SCHEMA_PATH = Path(__file__).resolve().with_name("schema.sql")


def _connect():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_database():
    """Create the users, vehicles, trips and status_history tables."""
    with _connect() as conn:
        conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))


def save_trip(trip):
    """Save a trip using schema.sql column names; return its new trip_id.

    Required keys: origin, destination, priority.
    Optional keys: vehicle_id, status (defaults to 'Assigned').
    A supplied vehicle_id must already exist in vehicles.
    """
    if not isinstance(trip, dict):
        raise TypeError("trip must be a dictionary")
    required = ("origin", "destination", "priority")
    missing = [key for key in required if trip.get(key) is None]
    if missing:
        raise ValueError("Missing required trip fields: " + ", ".join(missing))
    with _connect() as conn:
        cursor = conn.execute(
            """INSERT INTO trips
               (origin, destination, priority, vehicle_id, status)
               VALUES (?, ?, ?, ?, ?)""",
            (
                trip["origin"],
                trip["destination"],
                trip["priority"],
                trip.get("vehicle_id"),
                trip.get("status", "Assigned"),
            ),
        )
        return cursor.lastrowid


def get_trips():
    """Retrieve saved trips as dictionaries, ordered by trip_id."""
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM trips ORDER BY trip_id").fetchall()
    return [dict(row) for row in rows]


if __name__ == "__main__":
    initialize_database()
    # Demo uses an unassigned trip so no vehicle record is required.
    sample = {
        "origin": "Stephenville",
        "destination": "Fort Worth",
        "priority": 2,
        "status": "Pending",
    }
    trip_id = save_trip(sample)
    print(f"Saved trip ID: {trip_id}")
    print("Retrieved trip:", next(t for t in get_trips() if t["trip_id"] == trip_id))
