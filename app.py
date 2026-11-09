"""
app.py -- Flask front end for the Driving Route Planner (Member 5).

Handles login/authentication, role-based access (operator vs driver),
the two dashboards, and trip/vehicle updates. All data access goes
through services.py so the other members' modules plug in in one place.

Run:  python app.py        (then open http://127.0.0.1:5000)
Dev logins (stub data):  operator / operator123,  driver1-3 / driver123
DEMO_DATA=1 python app.py   seeds 10 sample trips
"""
import os
import secrets
from functools import wraps

from flask import (Flask, abort, flash, redirect, render_template, request,
                   session, url_for)
from werkzeug.security import check_password_hash

import services

app = Flask(__name__)
# Set SECRET_KEY in the environment for real deployments; the fallback is dev-only.
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-me")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


# ------------------------------------------------------------- security
def csrf_token():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_hex(16)
    return session["_csrf"]


app.jinja_env.globals["csrf_token"] = csrf_token


@app.before_request
def check_csrf():
    if request.method == "POST":
        sent = request.form.get("_csrf", "")
        if not sent or not secrets.compare_digest(sent, session.get("_csrf", "")):
            abort(400, "Invalid or missing CSRF token.")


def current_user():
    username = session.get("username")
    return services.get_user_by_username(username) if username else None


@app.context_processor
def inject_user():
    return {"user": current_user()}


def login_required(role=None):
    """Require a logged-in user, optionally with a specific role."""
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            user = current_user()
            if user is None:
                return redirect(url_for("login"))
            if role and user["role"] != role:
                abort(403)
            return view(*args, **kwargs)
        return wrapped
    return decorator


def parse_priority(raw, default=None):
    """Return an int 1-5, `default` if blank, or None if invalid."""
    raw = (raw or "").strip()
    if not raw:
        return default
    return int(raw) if raw.isdigit() and int(raw) in services.PRIORITIES else None


def home_for(user):
    return url_for("operator_dashboard" if user["role"] == "operator"
                   else "driver_dashboard")


# ------------------------------------------------------------ auth routes
@app.route("/")
def index():
    user = current_user()
    if user:
        return redirect(home_for(user))
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = services.get_user_by_username(
            request.form.get("username", "").strip())
        if user and check_password_hash(user["password_hash"],
                                        request.form.get("password", "")):
            session.clear()           # fresh session on login
            session["username"] = user["username"]
            return redirect(home_for(user))
        flash("Invalid username or password.", "error")
    return render_template("login.html")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))


# -------------------------------------------------------------- operator
@app.route("/operator")
@login_required("operator")
def operator_dashboard():
    return render_template("operator.html",
                           vehicles=services.list_vehicles(),
                           trips=services.list_trips(),
                           cities=services.list_cities(),
                           priorities=list(services.PRIORITIES))


@app.route("/operator/trips/new", methods=["POST"])
@login_required("operator")
def create_trip():
    origin = request.form.get("origin", "")
    destination = request.form.get("destination", "")
    package = request.form.get("package", "").strip()
    vehicle_raw = request.form.get("vehicle_id", "")
    vehicle_id = int(vehicle_raw) if vehicle_raw.isdigit() else None
    priority = parse_priority(request.form.get("priority"), default=3)

    if not package:
        flash("Please describe the package.", "error")
    elif origin == destination:
        flash("Origin and destination must be different cities.", "error")
    elif priority is None:
        flash("Priority must be a number from 1 (highest) to 5.", "error")
    elif vehicle_id and services.get_vehicle(vehicle_id) is None:
        flash("Unknown vehicle.", "error")
    else:
        trip = services.create_trip(origin, destination, package,
                                    vehicle_id, priority)
        if trip is None:
            flash(f"No route found between {origin} and {destination}.", "error")
        else:
            flash(f"Trip #{trip['id']} created ({trip['miles']} miles).", "success")
            return redirect(url_for("trip_detail", trip_id=trip["id"]))
    return redirect(url_for("operator_dashboard"))


@app.route("/operator/trips/<int:trip_id>/assign", methods=["POST"])
@login_required("operator")
def assign_trip(trip_id):
    """Operator-only: (re)assign a trip to a vehicle queue / change priority."""
    vehicle_raw = request.form.get("vehicle_id", "")
    vehicle_id = int(vehicle_raw) if vehicle_raw.isdigit() else None
    priority = parse_priority(request.form.get("priority"))
    if priority is None:
        flash("Priority must be a number from 1 (highest) to 5.", "error")
    elif services.get_trip(trip_id) is None:
        abort(404)
    elif services.assign_trip(trip_id, vehicle_id, priority,
                              user_id=current_user()["id"]):
        flash(f"Trip #{trip_id} updated.", "success")
    else:
        flash("That trip can't be changed (already picked up, or unknown vehicle).",
              "error")
    return redirect(url_for("operator_dashboard"))


# ---------------------------------------------------------------- driver
@app.route("/driver")
@login_required("driver")
def driver_dashboard():
    user = current_user()
    vehicle = services.get_vehicle(user["vehicle_id"])
    return render_template("driver.html", vehicle=vehicle,
                           trips=services.list_trips_for_vehicle(user["vehicle_id"]),
                           cities=services.list_cities())


# Allowed driver status moves: Assigned -> Picked Up -> In Transit -> Delivered
NEXT_STATUS = services.ALLOWED_NEXT
app.jinja_env.globals["next_status"] = NEXT_STATUS.get


@app.route("/trips/<int:trip_id>/status", methods=["POST"])
@login_required("driver")
def update_status(trip_id):
    user = current_user()
    trip = services.get_trip(trip_id)
    if trip is None or trip["vehicle_id"] != user["vehicle_id"]:
        abort(404)                    # drivers only see their own trips
    new = NEXT_STATUS.get(trip["status"])
    if request.form.get("status") != new:
        flash("That status change isn't allowed.", "error")
    else:
        if services.update_trip_status(trip_id, new, user_id=user["id"]):
            flash(f"Trip #{trip_id} marked {new}.", "success")
        else:
            flash("The trip could not be updated.", "error")
    return redirect(url_for("driver_dashboard"))


@app.route("/vehicle/location", methods=["POST"])
@login_required("driver")
def report_location():
    user = current_user()
    city = request.form.get("city", "")
    if services.update_vehicle_location(user["vehicle_id"], city):
        flash(f"Location updated to {city}.", "success")
    else:
        flash("Unknown city.", "error")
    return redirect(url_for("driver_dashboard"))


# ----------------------------------------------------------- shared views
@app.route("/trips/<int:trip_id>")
@login_required()
def trip_detail(trip_id):
    user = current_user()
    trip = services.get_trip(trip_id)
    if trip is None:
        abort(404)
    if user["role"] == "driver" and trip["vehicle_id"] != user["vehicle_id"]:
        abort(404)
    return render_template("trip_detail.html", trip=trip,
                           vehicle=services.get_vehicle(trip["vehicle_id"]))


@app.errorhandler(403)
@app.errorhandler(404)
@app.errorhandler(400)
def error_page(err):
    return render_template("error.html", err=err), err.code


if __name__ == "__main__":
    if os.environ.get("DEMO_DATA") == "1":      # e.g.  DEMO_DATA=1 python app.py
        services.seed_demo_trips(10)
    app.run(debug=True)
