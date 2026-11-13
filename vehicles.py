def get_vehicles():
    """Retrieve all vehicles in the fleet."""
    raise NotImplementedError("Get vehicles not implemented yet")

# Gonna assume deliveries are hub-to-hub to keep it simple.
def get_vehicle_status(vehicle_id):
    """Retrieve the current status of a vehicle."""
    # 0 for Inactive Vehicle (maintenance, unavailable, etc.)
    # 1 for Idle Vehicle (awaiting trips)
    # 2 for Active Vehicle at origin (picking up package) 
    # 3 for Active Vehicle en route (delivering package)
    # 4 for Active Vehicle at destination (delivered package)
    # 5 for Active Vehicle returning to origin (returning to hub)
    # 6 for Active Vehicle in delays (traffic, weather, etc.)
    # 7 for Active Vehicle in emergency (accident, breakdown, etc.)
    raise NotImplementedError("Vehicle status not implemented yet")


def update_vehicle_location(vehicle_id, location):
    """Update a vehicle's last reported location."""
    raise NotImplementedError("Location update not implemented yet")


def get_vehicle_trips(vehicle_id):
    """Retrieve trips assigned to a vehicle."""
    raise NotImplementedError("Vehicle trips not implemented yet")
