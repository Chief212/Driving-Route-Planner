"""In-memory vehicle-specific delivery priority queues.

Smaller numeric priority values are served first. Equal priorities retain
insertion order using a monotonically increasing tiebreaker.
"""
import heapq
import itertools

queues = {1: [], 2: [], 3: []}
_tiebreak = itertools.count()


def add_trip(vehicle_id, trip):
    """Add a trip object with a numeric .priority to a vehicle queue."""
    heapq.heappush(queues[vehicle_id], (trip.priority, next(_tiebreak), trip))


def get_next_trip(vehicle_id):
    """Remove and return the highest-priority trip, or None if empty."""
    q = queues[vehicle_id]
    return heapq.heappop(q)[2] if q else None


def remove_trip(vehicle_id, trip_id):
    """Remove a queued trip by ID; return True if found, otherwise False.

    Supports Trips.tripID (the project's existing model), and trip_id.
    """
    q = queues[vehicle_id]
    for index, (_, _, trip) in enumerate(q):
        identifier = getattr(trip, "tripID", getattr(trip, "trip_id", None))
        if identifier == trip_id:
            q.pop(index)
            heapq.heapify(q)
            return True
    return False
