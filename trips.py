# For trip IDs
import itertools # Needed for generating unique trip IDs.
tripIDCounter = itertools.count(0) # Counter for generating unique trip IDs.
trips = {} # Dictionary to store trips with trip_id as the key and trip object as the value.

# Code for stuff related to trips, such as creating, assigning, and updating delivery trips.

# Class for trip-related variables.
class Trips: # Constructor for reusable variables.
    def __init__ (self, trip_id, origin, destination, priority):
        self.tripID = trip_id
        self.origin = origin
        self.destination = destination
        self.priority = priority
        # Above are what inputs are for this part.
        self.status = None # Default status for a new trip.
        self.route = [] # Placeholder for the route, which will be written later.
        self.vehicle_id = None # Assign the trip to a vehicle.


# Creating new route via simple function.
def create_trip(origin, destination, priority):
    return Trips(next(tripIDCounter), origin, destination, priority)
#    raise NotImplementedError("Trip creation not implemented yet")

def assign_trip(trip_id, vehicle_id): # Adding the new route for the vehicle.
    raise NotImplementedError("Trip assignment not implemented yet")

def update_status(trip_id, status, user_id): # Updates status of a trip, with user_id for validation.
    """Validate and update a delivery's status."""
    raise NotImplementedError("Status update not implemented yet")

def get_trip_status(trip_id): # Retrieves the current status of a trip.
    """Retrieve the current status of a delivery."""
    raise NotImplementedError("Status retrieval not implemented yet")
