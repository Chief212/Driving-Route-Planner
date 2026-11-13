# Driving Route Planner — Datasets

This directory contains the datasets used by the
Driving Route Planner proof-of-concept.

## Dataset Files

### texas_cities.csv
Texas cities with estimated populations of at
least 5,000.

Source: U.S. Census Bureau
Population estimate year: 2025

### texas_nodes.csv
Road-network node identifiers and geographic
coordinates (latitude and longitude).

Source: OpenStreetMap
Extract date: November 12, 2026

### texas_roads.csv
Directed road-network connections containing:
- Starting node
- Ending node
- Distance in meters
- OpenStreetMap way identifier

Source: OpenStreetMap
Extract date: November 12, 2026

## Storage

texas_cities.csv is stored in this repository.

texas_nodes.csv and texas_roads.csv are stored
externally because they exceed GitHub's regular
file-size limit.

Shared download location: TO BE ADDED

## Routing

The routing module will use the road-network
data to construct a weighted directed graph
and calculate shortest paths using Dijkstra's
algorithm.

City locations must be mapped to appropriate
road-network nodes before routing.

## Data Limitations

The road network has not yet been fully validated
for connectivity, vehicle access restrictions,
or turn restrictions.

## Attribution

Road data: OpenStreetMap contributors.
OpenStreetMap data is licensed under the ODbL.
https://www.openstreetmap.org/copyright

Population data: U.S. Census Bureau.
