"""Checkpoint 1: SQLite initialization and persistent trip round-trip."""
import sqlite3
import pytest
import database


@pytest.fixture
def temporary_database(tmp_path, monkeypatch):
    db_path = tmp_path / "checkpoint.db"
    monkeypatch.setattr(database, "DB_NAME", str(db_path))
    database.initialize_database()
    return db_path


def test_schema_tables_created(temporary_database):
    with sqlite3.connect(temporary_database) as conn:
        names = {row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )}
    assert {"users", "vehicles", "trips", "status_history"} <= names


def test_save_and_retrieve_trip_persists(temporary_database):
    trip_id = database.save_trip({
        "origin": "Stephenville",
        "destination": "Fort Worth",
        "priority": 1,
        "status": "Pending",
    })
    assert isinstance(trip_id, int)
    # Reinitialize (as happens on a later program launch); data must survive.
    database.initialize_database()
    saved = next(t for t in database.get_trips() if t["trip_id"] == trip_id)
    assert saved["origin"] == "Stephenville"
    assert saved["destination"] == "Fort Worth"
    assert saved["priority"] == 1
    assert saved["status"] == "Pending"
    assert saved["vehicle_id"] is None


def test_vehicle_foreign_key_enforced(temporary_database):
    with pytest.raises(sqlite3.IntegrityError):
        database.save_trip({
            "origin": "Dallas",
            "destination": "Waco",
            "priority": 3,
            "vehicle_id": 9999,
        })


def test_missing_required_fields_rejected(temporary_database):
    with pytest.raises(ValueError):
        database.save_trip({"origin": "Dallas"})
