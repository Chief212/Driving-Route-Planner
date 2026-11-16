"""Checkpoint 1: one-vehicle queue behavior and three-vehicle isolation."""
from types import SimpleNamespace
import pytest
import priority


@pytest.fixture(autouse=True)
def clear_queues():
    for queue in priority.queues.values():
        queue.clear()
    yield
    for queue in priority.queues.values():
        queue.clear()


def trip(identifier, value):
    return SimpleNamespace(tripID=identifier, priority=value)


def test_one_vehicle_priority_order():
    priority.add_trip(1, trip(1, 4))
    priority.add_trip(1, trip(2, 1))
    priority.add_trip(1, trip(3, 3))
    assert [priority.get_next_trip(1).tripID for _ in range(3)] == [2, 3, 1]
    assert priority.get_next_trip(1) is None


def test_equal_priority_is_stable():
    priority.add_trip(1, trip(10, 2))
    priority.add_trip(1, trip(11, 2))
    assert priority.get_next_trip(1).tripID == 10
    assert priority.get_next_trip(1).tripID == 11


def test_remove_trip_keeps_heap_valid():
    for identifier, value in [(1, 3), (2, 1), (3, 2)]:
        priority.add_trip(1, trip(identifier, value))
    assert priority.remove_trip(1, 2) is True
    assert priority.remove_trip(1, 999) is False
    assert [priority.get_next_trip(1).tripID for _ in range(2)] == [3, 1]


def test_vehicle_queues_are_independent():
    priority.add_trip(1, trip(1, 1))
    priority.add_trip(2, trip(2, 1))
    assert priority.get_next_trip(1).tripID == 1
    assert priority.get_next_trip(1) is None
    assert priority.get_next_trip(2).tripID == 2
