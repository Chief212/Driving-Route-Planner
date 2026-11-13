import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
# Above imports help test case run with files from main folder.
# Debug solution assistance sourced from Gemini, 11/10/2026.

# Will not run normally when ran. For whatever reason, you will have to run this in terminal.
# First, type: PYTHONPATH=. python3 test/test_trips-1.py
# Then, type: python3 test/test_trips-1.py

# This will run the test. If it outputs nothing, it passed. If it outputs an error, it failed.

# Test case for trips.py, as of 2026-11-10 (Milestone 1).

# Import from other files.
from priority import add_trip, get_next_trip
from trips import Trips, create_trip

# Defining small test cases for code.
def trip_priority_list():
    # Creates a trip with varying priority.
    trip0 = create_trip("Austin", "Houston", 1) 
    trip1 = create_trip("Dallas", "San Antonio", 3) 
    trip2 = create_trip("Austin", "El Paso", 2)
    trip3 = create_trip("Fort Worth", "Lubbock", 4)
    
    # Assign them all randomly to a vehicle,
    # then see if the system can sort them properly.
    add_trip(1, trip1)
    add_trip(1, trip3)
    add_trip(1, trip0)
    add_trip(1, trip2)

    # This should show the lowest priority trip first.
    # Helps ensure that the program is actually sorting it.
    assert get_next_trip(1) is trip0   # Priority 1
    assert get_next_trip(1) is trip2   # Priority 2
    assert get_next_trip(1) is trip1   # Priority 3
    assert get_next_trip(1) is trip3   # Priority 4
    assert get_next_trip(1) is None    # Queue is now empty

# No outputs should be made if it passes. If it fails, it will output an error.