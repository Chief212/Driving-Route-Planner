"""
services.py -- the ONE place app.py talks to the rest of the project.

Each public function first tries the teammate's real module. If that module
is missing, the function isn't written yet (NotImplementedError), or it
doesn't exist in the module, the function falls back to a clearly labeled
in-memory DEMO implementation (the _stub_* functions below). Every page shows
a "demo data" banner listing which modules are still being simulated.

    routing.py   shortest_path
    database.py  get_trips, get_user_by_username (requested)
    trips.py     create_trip, assign_trip, update_status
    vehicles.py  get_vehicles, update_vehicle_location, get_vehicle_trips
    priority.py  add_trip

So each teammate's module switches over automatically as soon as it works;
app.py and the templates never change. Set DEMO_ONLY=1 (the tests do) to
force demo data everywhere.
"""
import heapq
import importlib
import logging
import os
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
def _stub_list_cities():
    """TODO: routing.py -- the eligible Texas cities."""
    return sorted(_GRAPH)


def _stub_shortest_route(origin, destination):
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
def _stub_get_user_by_username(username):
    """TODO: database.py -- dict with id, username, role, vehicle_id,
    password_hash (hashed; never plaintext) or None."""
    return _USERS.get(username)


# --------------------------------------------------- vehicles.py (Member 4)
def _stub_list_vehicles():
    """TODO: vehicles.py. Each vehicle dict also gets `queued`: how many
    open trips are waiting in its priority queue."""
    out = []
    for v in sorted(_VEHICLES.values(), key=lambda v: v["id"]):
        out.append(dict(v, queued=len([t for t in _TRIPS.values()
                                       if t["vehicle_id"] == v["id"]
                                       and t["status"] in OPEN_STATUSES])))
    return out


def _stub_get_vehicle(vehicle_id):
    """TODO: vehicles.py"""
    return _VEHICLES.get(vehicle_id)


def _stub_update_vehicle_location(vehicle_id, city):
    """TODO: vehicles.py -- record last reported (driver-reported) location."""
    v = _VEHICLES.get(vehicle_id)
    if v is None or city not in list_cities():
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


def _stub_create_trip(origin, destination, package, vehicle_id=None, priority=3):
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


def _stub_assign_trip(trip_id, vehicle_id, priority=None, user_id=None):
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


def _stub_list_trips():
    """TODO: trips.py -- newest first."""
    return sorted(_TRIPS.values(), key=lambda t: t["id"], reverse=True)


def _stub_list_trips_for_vehicle(vehicle_id):
    """TODO: priority.py -- the vehicle's queue: open trips by priority
    (1 first), then ties by creation order; delivered trips last."""
    return sorted((t for t in _TRIPS.values() if t["vehicle_id"] == vehicle_id),
                  key=_queue_key)


def _stub_get_trip(trip_id):
    """TODO: trips.py"""
    return _TRIPS.get(trip_id)


def _stub_update_trip_status(trip_id, status, user_id=None):
    """TODO: trips.py -- enforce Assigned -> Picked Up -> In Transit ->
    Delivered; record history; refresh the vehicle's status/location."""
    trip = _TRIPS.get(trip_id)
    if trip is None or ALLOWED_NEXT.get(trip["status"]) != status:
        return False
    trip["status"] = status
    _log(trip, status, user_id)
    if trip["vehicle_id"]:
        if status == "Delivered":
            _stub_update_vehicle_location(trip["vehicle_id"], trip["destination"])
        _refresh_vehicle_status(trip["vehicle_id"])
    return True


def seed_demo_trips(count=10):
    """Create `count` varied trips across the three vehicles (demo/tests)."""
    pairs = [("Dallas", "Houston"), ("Austin", "Fort Worth"),
             ("San Antonio", "Waco"), ("Waco", "Abilene"),
             ("Abilene", "Dallas")]
    made = []
    for i in range(count):
        o, d = pairs[i % len(pairs)]
        made.append(_stub_create_trip(o, d, f"Package {i + 1}",
                                vehicle_id=(i % 3) + 1, priority=(i % 5) + 1))
    return made


def reset_stub_data():
    """Test helper: clear trips and restore vehicles."""
    global _next_trip_id
    _TRIPS.clear()
    _next_trip_id = 1
    for vid, city in ((1, "Dallas"), (2, "Austin"), (3, "San Antonio")):
        _VEHICLES[vid].update(status="Available", location=city, updated="-")


# =====================================================================
#  Public API used by app.py: real module first, demo data as fallback
# =====================================================================
from types import SimpleNamespace

DEMO_ONLY = os.environ.get("DEMO_ONLY") == "1"
_NOT_READY = object()
_errored = set()             # modules that raised unexpected errors at runtime
_db_initialized = False
_graph_cache = None


def _implemented(module, *names):
    """True if `module` imports and each function exists and is not a
    placeholder (a body that still raises NotImplementedError)."""
    if DEMO_ONLY:
        return False
    try:
        mod = importlib.import_module(module)
    except ImportError:
        return False
    for name in names:
        fn = getattr(mod, name, None)
        code = getattr(fn, "__code__", None)
        if code is None or "NotImplementedError" in code.co_names:
            return False
    return True


# Trips, vehicles and the database must all be real together, otherwise
# records would be split between the real database and demo memory.
_STORE_NEEDS = (
    ("database", ("get_trips", "save_trip")),
    ("trips", ("create_trip", "assign_trip", "update_status")),
    ("vehicles", ("get_vehicles", "get_vehicle_trips", "update_vehicle_location")),
)


def _store_real():
    if not all(_implemented(m, *names) for m, names in _STORE_NEEDS):
        return False
    global _db_initialized
    if not _db_initialized:
        _db_initialized = True
        try:
            importlib.import_module("database").initialize_database()
        except Exception as exc:
            logging.warning("database.initialize_database failed: %r", exc)
            _errored.add("database.py")
    return True


def demo_modules():
    """Backend modules currently on demo data (shown in the page banner)."""
    out = set(_errored)
    if not (_implemented("routing", "build_sample_graph")
            or _implemented("routing", "shortest_path")):
        out.add("routing.py")
    if not _implemented("database", "get_trips", "save_trip",
                        "get_user_by_username"):
        out.add("database.py")
    if not _implemented("trips", "create_trip", "assign_trip", "update_status"):
        out.add("trips.py")
    if not _implemented("vehicles", "get_vehicles", "get_vehicle_trips",
                        "update_vehicle_location"):
        out.add("vehicles.py")
    if not _implemented("priority", "add_trip", "remove_trip"):
        out.add("priority.py")
    return sorted(out)


def _call_real(module, func, *args):
    """Call module.func(*args); _NOT_READY if it can't be used right now."""
    label = module + ".py"
    if DEMO_ONLY:
        return _NOT_READY
    try:
        fn = getattr(importlib.import_module(module), func)
    except (ImportError, AttributeError):
        return _NOT_READY
    try:
        return fn(*args)
    except NotImplementedError:
        return _NOT_READY
    except (ValueError, PermissionError):
        raise                      # real validation errors: callers handle
    except Exception as exc:       # half-written module: don't crash the site
        logging.warning("%s.%s failed (%r); using demo data", module, func, exc)
        _errored.add(label)
        return _NOT_READY


def _as_dict(row):
    if row is None:
        return None
    if isinstance(row, dict):
        return row
    try:
        return dict(row)            # sqlite3.Row etc.
    except (TypeError, ValueError):
        pass
    if hasattr(row, "__dict__"):    # plain objects such as trips.Trips
        return dict(vars(row))
    return None


def _norm_user(row):
    r = _as_dict(row)
    if r is None:
        return None
    return {"id": r.get("user_id", r.get("id")), "username": r.get("username"),
            "role": r.get("role"), "vehicle_id": r.get("vehicle_id"),
            "password_hash": r.get("password_hash")}


def _norm_trip(row):
    r = _as_dict(row)
    if r is None:
        return None
    tid = next((r[k] for k in ("trip_id", "id", "tripID") if k in r), None)
    t = {"id": tid, "origin": r.get("origin", r.get("start_location")),
         "destination": r.get("destination", r.get("end_location")),
         "package": r.get("package") or "",
         "priority": r.get("priority", 3), "vehicle_id": r.get("vehicle_id"),
         "status": r.get("status") or ("Assigned" if r.get("vehicle_id") else "Pending"),
         "history": r.get("history") or [], "created": r.get("created", "")}
    miles = r.get("miles")
    if miles is None:
        route = shortest_route(t["origin"], t["destination"])
        miles = route[1] if route else "-"
    t["miles"] = miles
    return t


def _norm_vehicle(row):
    r = _as_dict(row)
    if r is None:
        return None
    return {"id": r.get("vehicle_id", r.get("id")),
            "name": r.get("vehicle_name", r.get("name")),
            "status": r.get("status", "Available"),
            "location": r.get("location") or "Unknown",
            "updated": r.get("location_updated", r.get("updated", "-"))}


def _sync_queue(trip, old_vehicle=None):
    """Mirror a trip's vehicle/priority into priority.py's heap queues."""
    if old_vehicle:
        _call_real("priority", "remove_trip", old_vehicle, trip["id"])
    if trip["vehicle_id"]:
        item = SimpleNamespace(tripID=trip["id"], trip_id=trip["id"],
                               priority=trip["priority"])
        _call_real("priority", "add_trip", trip["vehicle_id"], item)


# -- routing ----------------------------------------------------------
def _graph():
    """routing.py's WeightedGraph (built once), or None if unavailable."""
    global _graph_cache
    if not _implemented("routing", "build_sample_graph"):
        return None
    if _graph_cache is None:
        try:
            _graph_cache = importlib.import_module("routing").build_sample_graph()
        except Exception as exc:
            logging.warning("routing.build_sample_graph failed: %r", exc)
            _errored.add("routing.py")
            return None
    return _graph_cache


def list_cities():
    g = _graph()
    return sorted(g.adjacency) if g else _stub_list_cities()


def shortest_route(origin, destination):
    """Return (path_list, miles) or None when there is no route."""
    g = _graph()
    if g is None:
        return _stub_shortest_route(origin, destination)
    try:
        path, miles = g.shortest_path(origin, destination)
    except ValueError:               # unknown city
        return None
    if path is None:                 # unreachable (e.g. El Paso)
        return None
    return path, (int(miles) if float(miles).is_integer() else round(miles, 1))


# -- users ------------------------------------------------------------
def get_user_by_username(username):
    if not _implemented("database", "get_user_by_username"):
        return _stub_get_user_by_username(username)
    res = _call_real("database", "get_user_by_username", username)
    return _stub_get_user_by_username(username) if res is _NOT_READY else _norm_user(res)


# -- vehicles ---------------------------------------------------------
def list_vehicles():
    if not _store_real():
        return _stub_list_vehicles()
    res = _call_real("vehicles", "get_vehicles")
    if res is _NOT_READY:
        return _stub_list_vehicles()
    vehicles = [v for v in map(_norm_vehicle, res or []) if v]
    open_trips = [t for t in list_trips() if t["status"] in OPEN_STATUSES]
    for v in vehicles:
        v["queued"] = len([t for t in open_trips if t["vehicle_id"] == v["id"]])
    return sorted(vehicles, key=lambda v: v["id"])


def get_vehicle(vehicle_id):
    return next((v for v in list_vehicles() if v["id"] == vehicle_id), None)


def update_vehicle_location(vehicle_id, city):
    if city not in list_cities():
        return False
    if not _store_real():
        return _stub_update_vehicle_location(vehicle_id, city)
    res = _call_real("vehicles", "update_vehicle_location", vehicle_id, city)
    if res is _NOT_READY:
        return _stub_update_vehicle_location(vehicle_id, city)
    return res is not False


# -- trips ------------------------------------------------------------
def list_trips():
    if not _store_real():
        return _stub_list_trips()
    res = _call_real("database", "get_trips")
    if res is _NOT_READY:
        return _stub_list_trips()
    trips = [t for t in map(_norm_trip, res or []) if t]
    return sorted(trips, key=lambda t: t["id"], reverse=True)


def get_trip(trip_id):
    return next((t for t in list_trips() if t["id"] == trip_id), None)


def list_trips_for_vehicle(vehicle_id):
    if not _store_real():
        return _stub_list_trips_for_vehicle(vehicle_id)
    res = _call_real("vehicles", "get_vehicle_trips", vehicle_id)
    if res is _NOT_READY:
        return _stub_list_trips_for_vehicle(vehicle_id)
    trips = [t for t in map(_norm_trip, res or []) if t]
    return sorted(trips, key=_queue_key)


def create_trip(origin, destination, package="", vehicle_id=None, priority=3):
    """Returns the new trip dict, or None if there is no route / bad input.
    `package` is optional; the trips table has no package column."""
    if priority not in PRIORITIES or shortest_route(origin, destination) is None:
        return None
    if not _store_real():
        trip = _stub_create_trip(origin, destination, package, vehicle_id, priority)
    else:
        trip = _create_trip_real(origin, destination, package, vehicle_id, priority)
    if trip:
        _sync_queue(trip)
    return trip


def _create_trip_real(origin, destination, package, vehicle_id, priority):
    res = _call_real("trips", "create_trip", origin, destination, priority)
    if res is _NOT_READY:
        return _stub_create_trip(origin, destination, package, vehicle_id, priority)
    created = _norm_trip(res) if _as_dict(res) is not None else get_trip(res)
    # trips.create_trip may only build an object; make sure it is stored.
    if created is None or get_trip(created["id"]) is None:
        new_id = _call_real("database", "save_trip", {
            "origin": origin, "destination": destination, "priority": priority,
            "vehicle_id": vehicle_id,
            "status": "Assigned" if vehicle_id else "Pending"})
        if new_id is _NOT_READY:
            return _stub_create_trip(origin, destination, package, vehicle_id, priority)
        created = get_trip(new_id)
    elif vehicle_id:
        assign_trip(created["id"], vehicle_id)
        created = get_trip(created["id"])
    if created:
        created["package"] = package
    return created


def assign_trip(trip_id, vehicle_id, priority=None, user_id=None):
    """(Re)assign a trip to a vehicle queue / change its priority.
    NOTE: the real modules have no 'change priority' function yet, so in real
    mode only the vehicle assignment is persisted."""
    if priority is not None and priority not in PRIORITIES:
        return False
    before = get_trip(trip_id)
    old_vehicle = before["vehicle_id"] if before else None
    if vehicle_id is None or not _store_real():
        ok = _stub_assign_trip(trip_id, vehicle_id, priority, user_id) \
            if not _store_real() else False
    else:
        res = _call_real("trips", "assign_trip", trip_id, vehicle_id)
        ok = (res is not False) if res is not _NOT_READY else \
            _stub_assign_trip(trip_id, vehicle_id, priority, user_id)
    if ok:
        after = get_trip(trip_id)
        if after:
            _sync_queue(after, old_vehicle)
    return ok


def update_trip_status(trip_id, status, user_id=None):
    if not _store_real():
        return _stub_update_trip_status(trip_id, status, user_id)
    try:
        res = _call_real("trips", "update_status", trip_id, status, user_id)
    except (ValueError, PermissionError):
        return False
    if res is _NOT_READY:
        return _stub_update_trip_status(trip_id, status, user_id)
    if res is False:
        return False
    trip = get_trip(trip_id)
    if status == "Delivered" and trip and trip["vehicle_id"]:
        update_vehicle_location(trip["vehicle_id"], trip["destination"])
        _call_real("priority", "remove_trip", trip["vehicle_id"], trip_id)
    return True
