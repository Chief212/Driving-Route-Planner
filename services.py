"""
services.py -- the ONE place app.py talks to the rest of the project.

Right now every function here is backed by a small in-memory stub so the
Flask app runs on its own. When the other members' modules are merged,
replace the body of each function with a call into the real module
(the TODO on each function says which one). app.py never has to change.

    routing.py   (Member 2)  -> list_cities, shortest_route
    database.py  (Member 3)  -> get_user_by_username
    trips.py     (Member 4)  -> list_trips, list_trips_for_vehicle, get_trip,
    priority.py  (Member 4)     create_trip, assign_trip, update_trip_status
    vehicles.py  (Member 4)  -> list_vehicles, get_vehicle,
                                update_vehicle_location, update_vehicle_status
"""
import heapq
from datetime import datetime

from werkzeug.security import generate_password_hash

TRIP_STATUSES = ["Pending", "Assigned", "Picked Up", "In Transit", "Delivered"]
# Permitted driver moves (arrival does NOT imply Delivered; the driver confirms it)
ALLOWED_NEXT = {"Assigned": "Picked Up", "Picked Up": "In Transit",
                "In Transit": "Delivered"}
PRIORITIES = range(1, 6)          # 1 = highest priority, 5 = lowest
OPEN_STATUSES = ("Pending", "Assigned", "Picked Up", "In Transit")

# ---------------------------------------------------------------- stub data
_ROADS = {  # approximate driving miles between neighboring Texas cities
    ("Dallas", "Fort Worth"): 32, ("Dallas", "Waco"): 97,
    ("Dallas", "Tyler"): 100, ("Fort Worth", "Abilene"): 150,
    ("Waco", "Austin"): 102, ("Waco", "Houston"): 185,
    ("Austin", "San Antonio"): 80, ("Austin", "Houston"): 165,
    ("San Antonio", "Houston"): 197, ("Tyler", "Houston"): 210,
    ("Abilene", "Waco"): 180,
}
_GRAPH = {}
for (a, b), miles in _ROADS.items():
    _GRAPH.setdefault(a, {})[b] = miles
    _GRAPH.setdefault(b, {})[a] = miles

_USERS = {
    "operator": {"id": 1, "username": "operator", "role": "operator",
                 "vehicle_id": None,
                 "password_hash": generate_password_hash("operator123")},
    "driver1": {"id": 2, "username": "driver1", "role": "driver",
                "vehicle_id": 1,
                "password_hash": generate_password_hash("driver123")},
    "driver2": {"id": 3, "username": "driver2", "role": "driver",
                "vehicle_id": 2,
                "password_hash": generate_password_hash("driver123")},
    "driver3": {"id": 4, "username": "driver3", "role": "driver",
                "vehicle_id": 3,
                "password_hash": generate_password_hash("driver123")},
}
_VEHICLES = {
    1: {"id": 1, "name": "Truck 101", "status": "Available",
        "location": "Dallas", "updated": "-"},
    2: {"id": 2, "name": "Van 202", "status": "Available",
        "location": "Austin", "updated": "-"},
    3: {"id": 3, "name": "Truck 303", "status": "Available",
        "location": "San Antonio", "updated": "-"},
}
_TRIPS = {}
_next_trip_id = 1


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M")


# ------------------------------------------------- routing.py (Member 2)
def list_cities():
    """TODO: routing.py -- the eligible Texas cities."""
    return sorted(_GRAPH)


def shortest_route(origin, destination):
    """TODO: routing.py -- Dijkstra. Return (path_list, miles) or None."""
    if origin not in _GRAPH or destination not in _GRAPH:
        return None
    dist, prev, heap = {origin: 0}, {}, [(0, origin)]
    while heap:
        d, city = heapq.heappop(heap)
        if city == destination:
            break
        if d > dist.get(city, float("inf")):
            continue
        for nxt, miles in _GRAPH[city].items():
            nd = d + miles
            if nd < dist.get(nxt, float("inf")):
                dist[nxt], prev[nxt] = nd, city
                heapq.heappush(heap, (nd, nxt))
    if destination not in dist:
        return None
    path = [destination]
    while path[-1] != origin:
        path.append(prev[path[-1]])
    return path[::-1], dist[destination]


# -------------------------------------------------- database.py (Member 3)
def get_user_by_username(username):
    """TODO: database.py -- dict with id, username, role, vehicle_id,
    password_hash (hashed; never plaintext) or None."""
    return _USERS.get(username)


# --------------------------------------------------- vehicles.py (Member 4)
def list_vehicles():
    """TODO: vehicles.py. Each vehicle dict also gets `queued`: how many
    open trips are waiting in its priority queue."""
    out = []
    for v in sorted(_VEHICLES.values(), key=lambda v: v["id"]):
        out.append(dict(v, queued=len([t for t in _TRIPS.values()
                                       if t["vehicle_id"] == v["id"]
                                       and t["status"] in OPEN_STATUSES])))
    return out


def get_vehicle(vehicle_id):
    """TODO: vehicles.py"""
    return _VEHICLES.get(vehicle_id)


def update_vehicle_location(vehicle_id, city):
    """TODO: vehicles.py -- record last reported (driver-reported) location."""
    v = _VEHICLES.get(vehicle_id)
    if v is None or city not in _GRAPH:
        return False
    v["location"], v["updated"] = city, _now()
    return True


def _refresh_vehicle_status(vehicle_id):
    """A vehicle is On Trip only while a trip is Picked Up / In Transit."""
    if vehicle_id in _VEHICLES:
        busy = any(t["vehicle_id"] == vehicle_id
                   and t["status"] in ("Picked Up", "In Transit")
                   for t in _TRIPS.values())
        _VEHICLES[vehicle_id]["status"] = "On Trip" if busy else "Available"


# ------------------------------------------------------ trips.py (Member 4)
def _log(trip, status, user_id):
    trip["history"].append({"status": status, "at": _now(), "by": user_id})


def create_trip(origin, destination, package, vehicle_id=None, priority=3):
    """TODO: trips.py / priority.py. Returns the new trip dict, or None if
    no route exists between the cities."""
    global _next_trip_id
    route = shortest_route(origin, destination)
    if route is None or priority not in PRIORITIES:
        return None
    path, miles = route
    trip = {"id": _next_trip_id, "origin": origin, "destination": destination,
            "package": package, "vehicle_id": vehicle_id, "priority": priority,
            "path": path, "miles": miles, "created": _now(), "history": [],
            "status": "Assigned" if vehicle_id else "Pending"}
    _log(trip, trip["status"], None)
    _TRIPS[trip["id"]] = trip
    _next_trip_id += 1
    return trip


def assign_trip(trip_id, vehicle_id, priority=None, user_id=None):
    """TODO: priority.py -- (re)assign a trip to a vehicle's queue and/or
    change its priority. Only allowed before pickup. vehicle_id=None
    un-assigns the trip."""
    trip = _TRIPS.get(trip_id)
    if trip is None or trip["status"] not in ("Pending", "Assigned"):
        return False
    if vehicle_id is not None and vehicle_id not in _VEHICLES:
        return False
    if priority is not None:
        if priority not in PRIORITIES:
            return False
        trip["priority"] = priority
    trip["vehicle_id"] = vehicle_id
    new_status = "Assigned" if vehicle_id else "Pending"
    if new_status != trip["status"]:
        trip["status"] = new_status
        _log(trip, new_status, user_id)
    return True


def _queue_key(t):
    return (t["status"] == "Delivered", t["priority"], t["id"])


def list_trips():
    """TODO: trips.py -- newest first."""
    return sorted(_TRIPS.values(), key=lambda t: t["id"], reverse=True)


def list_trips_for_vehicle(vehicle_id):
    """TODO: priority.py -- the vehicle's queue: open trips by priority
    (1 first), then ties by creation order; delivered trips last."""
    return sorted((t for t in _TRIPS.values() if t["vehicle_id"] == vehicle_id),
                  key=_queue_key)


def get_trip(trip_id):
    """TODO: trips.py"""
    return _TRIPS.get(trip_id)


def update_trip_status(trip_id, status, user_id=None):
    """TODO: trips.py -- enforce Assigned -> Picked Up -> In Transit ->
    Delivered; record history; refresh the vehicle's status/location."""
    trip = _TRIPS.get(trip_id)
    if trip is None or ALLOWED_NEXT.get(trip["status"]) != status:
        return False
    trip["status"] = status
    _log(trip, status, user_id)
    if trip["vehicle_id"]:
        if status == "Delivered":
            update_vehicle_location(trip["vehicle_id"], trip["destination"])
        _refresh_vehicle_status(trip["vehicle_id"])
    return True


def seed_demo_trips(count=10):
    """Create `count` varied trips across the three vehicles (demo/tests)."""
    pairs = [("Dallas", "Houston"), ("Austin", "Fort Worth"),
             ("San Antonio", "Waco"), ("Tyler", "Austin"),
             ("Abilene", "Dallas")]
    made = []
    for i in range(count):
        o, d = pairs[i % len(pairs)]
        made.append(create_trip(o, d, f"Package {i + 1}",
                                vehicle_id=(i % 3) + 1, priority=(i % 5) + 1))
    return made


def reset_stub_data():
    """Test helper: clear trips and restore vehicles."""
    global _next_trip_id
    _TRIPS.clear()
    _next_trip_id = 1
    for vid, city in ((1, "Dallas"), (2, "Austin"), (3, "San Antonio")):
        _VEHICLES[vid].update(status="Available", location=city, updated="-")
