"""
Texas City Shortest-Path Prototype

A weighted, undirected graph implemented with an adjacency list.
Dijkstra's algorithm finds the minimum-distance route between cities.
"""

import heapq
import math


class WeightedGraph:
    """Weighted undirected graph using an adjacency list."""

    def __init__(self):
        self.adjacency = {}

    def add_city(self, city):
        """Add a city if it does not already exist."""
        if not isinstance(city, str) or not city.strip():
            raise ValueError("City name must be a non-empty string.")

        city = city.strip()
        self.adjacency.setdefault(city, {})

    def add_road(self, city_a, city_b, distance):
        """Add a two-way road with a non-negative distance."""

        if not isinstance(city_a, str) or not city_a.strip():
            raise ValueError("Invalid first city name.")

        if not isinstance(city_b, str) or not city_b.strip():
            raise ValueError("Invalid second city name.")

        if city_a == city_b:
            raise ValueError("A road must connect two different cities.")

        if not isinstance(distance, (int, float)) or isinstance(distance, bool):
            raise ValueError("Distance must be a number.")

        if not math.isfinite(distance) or distance < 0:
            raise ValueError("Distance must be finite and non-negative.")

        self.add_city(city_a)
        self.add_city(city_b)

        self.adjacency[city_a][city_b] = float(distance)
        self.adjacency[city_b][city_a] = float(distance)

    def shortest_path(self, start, end):
        """
        Find the shortest path using Dijkstra's algorithm.

        Returns:
            (route, total_distance)

        Unknown cities raise ValueError.
        Unreachable cities return (None, infinity).
        """

        if not isinstance(start, str) or not start.strip():
            raise ValueError("Invalid starting city.")

        if not isinstance(end, str) or not end.strip():
            raise ValueError("Invalid destination city.")

        start = start.strip()
        end = end.strip()

        if start not in self.adjacency:
            raise ValueError(f"Unknown starting city: {start}")

        if end not in self.adjacency:
            raise ValueError(f"Unknown destination city: {end}")

        # Store the shortest known distance to each city.
        distances = {
            city: math.inf for city in self.adjacency
        }

        # Store the previous city in the shortest route.
        previous = {
            city: None for city in self.adjacency
        }

        distances[start] = 0.0

        # Priority queue stores (distance, city).
        priority_queue = [(0.0, start)]

        while priority_queue:

            current_distance, current_city = heapq.heappop(
                priority_queue
            )

            # Ignore outdated queue entries.
            if current_distance > distances[current_city]:
                continue

            # Destination has been reached.
            if current_city == end:
                break

            # Examine all neighboring cities.
            for neighbor, road_distance in self.adjacency[current_city].items():

                new_distance = current_distance + road_distance

                # Check whether this route is shorter.
                if new_distance < distances[neighbor]:

                    distances[neighbor] = new_distance
                    previous[neighbor] = current_city

                    heapq.heappush(
                        priority_queue,
                        (new_distance, neighbor)
                    )

        # No route exists.
        if math.isinf(distances[end]):
            return None, math.inf

        # Reconstruct the route by working backward.
        route = []
        current = end

        while current is not None:
            route.append(current)
            current = previous[current]

        # Reverse so the route starts at the starting city.
        route.reverse()

        return route, distances[end]


def build_sample_graph():
    """Create a sample Texas road network for testing."""

    graph = WeightedGraph()

    sample_roads = [
        ("Dallas", "Fort Worth", 32),
        ("Dallas", "Waco", 95),
        ("Fort Worth", "Waco", 90),
        ("Waco", "Austin", 102),
        ("Austin", "San Antonio", 80),
        ("Waco", "Houston", 185),
        ("Austin", "Houston", 165),
        ("San Antonio", "Houston", 197),
        ("Dallas", "Houston", 240),
        ("Fort Worth", "Abilene", 150),
        ("Abilene", "Austin", 185),
    ]

    for city_a, city_b, distance in sample_roads:
        graph.add_road(city_a, city_b, distance)

    # Add an isolated city to test unreachable destinations.
    graph.add_city("El Paso")

    return graph


if __name__ == "__main__":

    texas_graph = build_sample_graph()

    start_city = "Dallas"
    end_city = "San Antonio"

    route, distance = texas_graph.shortest_path(
        start_city, end_city
    )

    if route is None:
        print("No route found.")
    else:
        print("Shortest route:", " -> ".join(route))
        print("Total distance:", distance, "sample miles")

    print("\nUnreachable example:")

    route, distance = texas_graph.shortest_path(
        "Dallas", "El Paso"
    )

    print("Route:", route)
    print("Distance:", distance)
