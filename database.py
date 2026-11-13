import sqlite3

DB_NAME = "route_planner.db"

def initialize_database():
    """Create and initialize the project database with users, vehicles, trips, and delivery status history tables."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Enable foreign key support in SQLite
    cursor.execute("PRAGMA foreign_keys = ON;")

    # 1. Users Table
    cursor.execute()

    # 2. Vehicles Table
    cursor.execute()

    # 3. Trips Table
    cursor.execute()

    # 4. Delivery Status History Table
    cursor.execute()

    conn.commit()
    conn.close()

def save_trip(trip):
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute( (
        trip.get("user_id"),
        trip.get("vehicle_id"),
        trip.get("status", "planned"),
        trip.get("start_location"),
        trip.get("end_location"),
        trip.get("scheduled_start")
    ))
    
    trip_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return trip_id

def get_trips():
    """Retrieve all saved delivery trips as a list of dictionaries."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Allows fetching rows as dictionaries
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM trips")
    rows = cursor.fetchall()
    
    trips = [dict(row) for row in rows]
    conn.close()
    return trips

if __name__ == "__main__":
    # 1. Initialize DB & tables
    initialize_database()
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 2. Insert a prerequisite user and vehicle for foreign key constraints
    cursor.execute("INSERT OR IGNORE INTO users (id, username, email) VALUES (1, 'johndoe', 'john@example.com')")
    cursor.execute("INSERT OR IGNORE INTO vehicles (id, license_plate, model, capacity) VALUES (1, 'XYZ-123', 'Toyota Prius', 4)")
    conn.commit()
    conn.close()

    # 3. Test saving a trip
    sample_trip = {
        "user_id": 1,
        "vehicle_id": 1,
        "status": "planned",
        "start_location": "HQ Warehouse",
        "end_location": "123 Main St",
        "scheduled_start": "2026-11-12 09:00:00"
    }
    
    trip_id = save_trip(sample_trip)
    print(f"Successfully saved trip with ID: {trip_id}")

    # 4. Test retrieving trips
    retrieved_trips = get_trips()
    print("Retrieved Trips from DB:")
    for t in retrieved_trips:
        print(t)
