CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS vehicles (
    vehicle_id INTEGER PRIMARY KEY,
    vehicle_name TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Available',
    location TEXT
);

CREATE TABLE IF NOT EXISTS trips (
    trip_id INTEGER PRIMARY KEY,
    origin TEXT NOT NULL,
    destination TEXT NOT NULL,
    priority INTEGER NOT NULL,
    vehicle_id INTEGER,
    status TEXT NOT NULL DEFAULT 'Assigned',
    FOREIGN KEY (vehicle_id)
        REFERENCES vehicles(vehicle_id)
);

CREATE TABLE IF NOT EXISTS status_history (
    history_id INTEGER PRIMARY KEY,
    trip_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (trip_id)
        REFERENCES trips(trip_id),
    FOREIGN KEY (user_id)
        REFERENCES users(user_id)
);
