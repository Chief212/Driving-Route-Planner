
import math
import unittest

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from routing import WeightedGraph, build_sample_graph


class TestShortestPath(unittest.TestCase):

    def setUp(self):
        """Create a fresh sample graph before each test."""
        self.graph = build_sample_graph()

    def test_known_shortest_route(self):
        """Test that Dijkstra finds the expected shortest route."""
        route, distance = self.graph.shortest_path(
            "Dallas", "San Antonio"
        )

        self.assertEqual(
            route,
            ["Dallas", "Waco", "Austin", "San Antonio"]
        )

        self.assertEqual(distance, 277.0)

    def test_same_start_and_end(self):
        """Test a route where the starting city is the destination."""
        route, distance = self.graph.shortest_path(
            "Austin", "Austin"
        )

        self.assertEqual(route, ["Austin"])
        self.assertEqual(distance, 0.0)

    def test_unreachable_destination(self):
        """Test what happens when no route exists."""
        route, distance = self.graph.shortest_path(
            "Dallas", "El Paso"
        )

        self.assertIsNone(route)
        self.assertTrue(math.isinf(distance))

    def test_invalid_start_city(self):
        """Test an invalid starting city."""
        with self.assertRaises(ValueError):
            self.graph.shortest_path("Atlantis", "Austin")

    def test_invalid_end_city(self):
        """Test an invalid destination city."""
        with self.assertRaises(ValueError):
            self.graph.shortest_path("Austin", "Atlantis")

    def test_graph_uses_two_way_roads(self):
        """Test that roads can be traveled in both directions."""
        route, distance = self.graph.shortest_path(
            "San Antonio", "Dallas"
        )

        self.assertEqual(
            route,
            ["San Antonio", "Austin", "Waco", "Dallas"]
        )

        self.assertEqual(distance, 277.0)

    def test_rejects_negative_distance(self):
        """Test that negative road distances are rejected."""
        graph = WeightedGraph()

        with self.assertRaises(ValueError):
            graph.add_road("A", "B", -5)


if __name__ == "__main__":
    unittest.main()
