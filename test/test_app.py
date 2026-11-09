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
