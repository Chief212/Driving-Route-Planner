"""Tests for app.py (Member 5). Run from the project root:  pytest tests/test_app.py"""
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import services
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    services.DEMO_ONLY = True          # test the frontend in isolation
    services.reset_stub_data()
    with app.test_client() as c:
        yield c


def token(client, path="/login"):
    html = client.get(path).get_data(as_text=True)
    return re.search(r'name="_csrf" value="([^"]+)"', html).group(1)


def login(client, username, password):
    return client.post("/login", data={"username": username, "password": password,
                                       "_csrf": token(client)})


def post(client, path, page, **data):
    data["_csrf"] = token(client, page)
    return client.post(path, data=data, follow_redirects=True)


def new_trip(client, vehicle_id="1", priority="3", origin="Dallas", dest="Austin", pkg="Box"):
    return post(client, "/operator/trips/new", "/operator", origin=origin,
                destination=dest, package=pkg, priority=priority, vehicle_id=vehicle_id)


# ------------------------------------------------------------------ auth
def test_index_for_anonymous(client):
    r = client.get("/")
    assert r.status_code == 200 and b"Driving Route Planner" in r.data


def test_redirects_to_login_when_anonymous(client):
    r = client.get("/operator")
    assert r.status_code == 302 and "/login" in r.headers["Location"]


def test_bad_password_rejected(client):
    r = login(client, "operator", "wrong")
    assert b"Invalid username or password" in r.data


def test_operator_login(client):
    assert login(client, "operator", "operator123").headers["Location"].endswith("/operator")


@pytest.mark.parametrize("u", ["driver1", "driver2", "driver3"])
def test_three_drivers_login(client, u):
    assert login(client, u, "driver123").headers["Location"].endswith("/driver")


def test_post_without_csrf_rejected(client):
    login(client, "operator", "operator123")
    assert client.post("/operator/trips/new", data={}).status_code == 400


def test_driver_blocked_from_operator_pages(client):
    login(client, "driver1", "driver123")
    assert client.get("/operator").status_code == 403
    r = post(client, "/operator/trips/1/assign", "/driver", vehicle_id="1")
    assert r.status_code == 403


# ------------------------------------------------------------- priorities
def test_create_trip_with_priority(client):
    login(client, "operator", "operator123")
    new_trip(client, priority="1")
    assert services.list_trips()[0]["priority"] == 1


def test_invalid_priority_rejected(client):
    login(client, "operator", "operator123")
    new_trip(client, priority="9")
    assert services.list_trips() == []


def test_driver_queue_ordered_by_priority(client):
    login(client, "operator", "operator123")
    new_trip(client, priority="5", pkg="low")
    new_trip(client, priority="1", pkg="high")
    new_trip(client, priority="3", pkg="mid")
    client.post("/logout", data={"_csrf": token(client, "/operator")})
    login(client, "driver1", "driver123")
    html = client.get("/driver").get_data(as_text=True)
    assert html.index("high") < html.index("mid") < html.index("low")
    assert "Next up" in html


def test_operator_assign_and_reprioritize(client):
    login(client, "operator", "operator123")
    new_trip(client, vehicle_id="", priority="3")
    tid = services.list_trips()[0]["id"]
    post(client, f"/operator/trips/{tid}/assign", "/operator", vehicle_id="2", priority="1")
    t = services.get_trip(tid)
    assert t["vehicle_id"] == 2 and t["priority"] == 1 and t["status"] == "Assigned"


def test_cannot_reassign_after_pickup(client):
    login(client, "operator", "operator123")
    new_trip(client, vehicle_id="1")
    tid = services.list_trips()[0]["id"]
    services.update_trip_status(tid, "Picked Up")
    post(client, f"/operator/trips/{tid}/assign", "/operator", vehicle_id="2", priority="1")
    assert services.get_trip(tid)["vehicle_id"] == 1


# ------------------------------------------------------------ status flow
def test_full_status_flow_and_history(client):
    login(client, "operator", "operator123")
    new_trip(client, vehicle_id="1")
    tid = services.list_trips()[0]["id"]
    client.post("/logout", data={"_csrf": token(client, "/operator")})
    login(client, "driver1", "driver123")
    for s in ["Picked Up", "In Transit", "Delivered"]:
        post(client, f"/trips/{tid}/status", "/driver", status=s)
        assert services.get_trip(tid)["status"] == s
    assert len(services.get_trip(tid)["history"]) >= 4
    assert services.get_vehicle(1)["location"] == "Austin"


def test_cannot_skip_statuses(client):
    login(client, "operator", "operator123")
    new_trip(client, vehicle_id="1")
    tid = services.list_trips()[0]["id"]
    client.post("/logout", data={"_csrf": token(client, "/operator")})
    login(client, "driver1", "driver123")
    post(client, f"/trips/{tid}/status", "/driver", status="Delivered")
    assert services.get_trip(tid)["status"] == "Assigned"


def test_driver_cannot_touch_other_vehicle_trip(client):
    login(client, "operator", "operator123")
    new_trip(client, vehicle_id="2")
    tid = services.list_trips()[0]["id"]
    client.post("/logout", data={"_csrf": token(client, "/operator")})
    login(client, "driver1", "driver123")
    r = post(client, f"/trips/{tid}/status", "/driver", status="Picked Up")
    assert r.status_code == 404
    assert services.get_trip(tid)["status"] == "Assigned"


def test_location_report_does_not_change_status(client):
    login(client, "operator", "operator123")
    new_trip(client, vehicle_id="1", dest="Austin")
    tid = services.list_trips()[0]["id"]
    client.post("/logout", data={"_csrf": token(client, "/operator")})
    login(client, "driver1", "driver123")
    post(client, "/vehicle/location", "/driver", city="Austin")
    assert services.get_trip(tid)["status"] == "Assigned"


# ---------------------------------------------------------------- volume
def test_twelve_trips_render(client):
    services.seed_demo_trips(12)
    login(client, "operator", "operator123")
    r = client.get("/operator")
    assert r.status_code == 200 and len(services.list_trips()) >= 12
    assert r.get_data(as_text=True).count("<tr") >= 13


# ------------------------------------------------- optional package / banner
def test_package_is_optional(client):
    login(client, "operator", "operator123")
    new_trip(client, pkg="")
    assert len(services.list_trips()) == 1


def test_demo_banner_shown(client):
    login(client, "operator", "operator123")
    assert b"Demo data" in client.get("/operator").data


# ----------------------------------------- real-module integration/fallback
def _fake_module(monkeypatch, name, **funcs):
    import types
    mod = types.ModuleType(name)
    for k, v in funcs.items():
        setattr(mod, k, v)
    monkeypatch.setitem(sys.modules, name, mod)


def test_falls_back_when_real_module_not_implemented(client, monkeypatch):
    def nope():
        raise NotImplementedError
    _fake_module(monkeypatch, "vehicles", get_vehicles=nope)
    monkeypatch.setattr(services, "DEMO_ONLY", False)
    assert len(services.list_vehicles()) == 3
    assert "vehicles.py" in services.demo_modules()


def test_uses_real_module_and_maps_schema_columns(client, monkeypatch):
    rows = [{"vehicle_id": 7, "vehicle_name": "Real Truck", "status": "Available",
             "location": "Waco"}]
    _fake_module(monkeypatch, "vehicles", get_vehicles=lambda: rows,
                 get_vehicle_trips=lambda v: [], update_vehicle_location=lambda v, c: True)
    _fake_module(monkeypatch, "trips", create_trip=lambda o, d, p: None,
                 assign_trip=lambda t, v: True, update_status=lambda t, s, u: True)
    _fake_module(monkeypatch, "database", save_trip=lambda t: 1,
                 initialize_database=lambda: None, get_trips=lambda: [
        {"trip_id": 5, "origin": "Dallas", "destination": "Waco",
         "priority": 2, "vehicle_id": 7, "status": "Assigned"}])
    monkeypatch.setattr(services, "DEMO_ONLY", False)
    v = services.list_vehicles()[0]
    assert v["id"] == 7 and v["name"] == "Real Truck" and v["queued"] == 1
    t = services.get_trip(5)
    assert t["id"] == 5 and t["miles"] > 0 and t["package"] == ""
    assert "vehicles.py" not in services.demo_modules()


def test_real_user_lookup_maps_user_id(client, monkeypatch):
    _fake_module(monkeypatch, "database", get_user_by_username=lambda u: {
        "user_id": 9, "username": u, "password_hash": "x", "role": "driver",
        "vehicle_id": 2})
    monkeypatch.setattr(services, "DEMO_ONLY", False)
    u = services.get_user_by_username("someone")
    assert u["id"] == 9 and u["vehicle_id"] == 2


def test_partly_finished_backend_keeps_demo_store(client, monkeypatch):
    """database ready but trips/vehicles still stubs -> one consistent demo store."""
    _fake_module(monkeypatch, "database", get_trips=lambda: [], save_trip=lambda t: 1,
                 initialize_database=lambda: None)
    monkeypatch.setattr(services, "DEMO_ONLY", False)
    trip = services.create_trip("Dallas", "Waco", "", 1, 2)
    assert trip is not None and services.get_trip(trip["id"]) is not None
    assert "trips.py" in services.demo_modules()


def test_unsaved_trip_object_is_persisted(client, monkeypatch):
    saved = []
    class Trips:
        def __init__(self):
            self.tripID, self.origin, self.destination = 0, "Dallas", "Waco"
            self.priority, self.status, self.vehicle_id = 2, None, None
    def save(t):
        saved.append(t); return 11
    def rows():
        return [dict(trip_id=11, origin="Dallas", destination="Waco", priority=2,
                     vehicle_id=None, status="Pending")] if saved else []
    _fake_module(monkeypatch, "trips", create_trip=lambda o, d, p: Trips(),
                 assign_trip=lambda t, v: True, update_status=lambda t, s, u: True)
    _fake_module(monkeypatch, "database", get_trips=rows, save_trip=save,
                 initialize_database=lambda: None)
    _fake_module(monkeypatch, "vehicles", get_vehicles=lambda: [],
                 get_vehicle_trips=lambda v: [], update_vehicle_location=lambda v, c: True)
    monkeypatch.setattr(services, "DEMO_ONLY", False)
    trip = services.create_trip("Dallas", "Waco", "", None, 2)
    assert trip["id"] == 11 and saved[0]["status"] == "Pending"


def test_broken_real_module_does_not_crash_site(client, monkeypatch):
    def boom(*a):
        raise TypeError("half-written")
    _fake_module(monkeypatch, "database", get_trips=boom, save_trip=boom,
                 initialize_database=lambda: None)
    _fake_module(monkeypatch, "trips", create_trip=boom, assign_trip=boom, update_status=boom)
    _fake_module(monkeypatch, "vehicles", get_vehicles=boom, get_vehicle_trips=boom,
                 update_vehicle_location=boom)
    monkeypatch.setattr(services, "DEMO_ONLY", False)
    login(client, "operator", "operator123")
    assert client.get("/operator").status_code == 200


def test_real_routing_graph_used(client, monkeypatch):
    import types
    class G:
        adjacency = {"A": {}, "B": {}}
        def shortest_path(self, a, b):
            if "Z" in (a, b):
                raise ValueError("unknown")
            return ["A", "B"], 12.0
    _fake_module(monkeypatch, "routing", build_sample_graph=lambda: G())
    monkeypatch.setattr(services, "_graph_cache", None)
    monkeypatch.setattr(services, "DEMO_ONLY", False)
    assert services.list_cities() == ["A", "B"]
    assert services.shortest_route("A", "B") == (["A", "B"], 12)
    assert services.shortest_route("A", "Z") is None
    monkeypatch.setattr(services, "_graph_cache", None)


def test_priority_queue_mirrors_assignment(client, monkeypatch):
    calls = []
    _fake_module(monkeypatch, "priority",
                 add_trip=lambda v, t: calls.append(("add", v, t.tripID, t.priority)),
                 remove_trip=lambda v, i: calls.append(("remove", v, i)))
    monkeypatch.setattr(services, "DEMO_ONLY", False)
    trip = services.create_trip("Dallas", "Waco", "", 1, 2)
    assert ("add", 1, trip["id"], 2) in calls
