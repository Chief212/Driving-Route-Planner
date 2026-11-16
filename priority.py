import heapq
import itertools

# Code for dealing with priority queues for delivery trips.
queues = {1: [], 2: [], 3: []}
# This makes sure two trips with equal priority don't crash the system.
_tiebreak = itertools.count()

# Adds trips to a vehicle's priority queue.
def add_trip(vehicle_id, trip):
    heapq.heappush(queues[vehicle_id], (trip.priority, next(_tiebreak), trip))

# Retrieves the highest-priority trip for a vehicle.
def get_next_trip(vehicle_id):
    q = queues[vehicle_id]
    if not q:
        return None
    return heapq.heappop(q)[2]

# Removes a trip from a vehicle's priority queue when finished or canceled.
def remove_trip(vehicle_id, trip_id):
    """Remove a delivery trip from a vehicle's queue."""
    raise NotImplementedError("Remove trip not implemented yet")
