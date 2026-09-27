"""Pytest fixtures for Campus Landmark A* Route Planner."""

import pytest
import networkx as nx
from src.heuristic import haversine_distance


@pytest.fixture
def synthetic_grid_graph():
    """Create a 15x15 topological road grid with realistic campus coordinates.

    Nodes: grid of (i, j) points centered around MITS campus (13.6288, 78.5024).
    Edges: horizontal and vertical connections with edge lengths set to actual
    Haversine distance * 1.15 (simulating realistic pedestrian street curvature).
    """
    G = nx.DiGraph()
    node_coords = {}
    component_map = {}

    base_lat = 13.6288
    base_lon = 78.5024
    step = 0.0006  # ~66 meters between grid points

    grid_size = 25
    for i in range(grid_size):
        for j in range(grid_size):
            node_id = i * grid_size + j
            lat = base_lat + (i - grid_size // 2) * step
            lon = base_lon + (j - grid_size // 2) * step
            G.add_node(node_id, y=lat, x=lon)
            node_coords[node_id] = (lat, lon)
            component_map[node_id] = 0

    # Add bidirectional edges
    for i in range(grid_size):
        for j in range(grid_size):
            u = i * grid_size + j
            neighbors = []
            if i + 1 < grid_size:
                neighbors.append((i + 1) * grid_size + j)
            if j + 1 < grid_size:
                neighbors.append(i * grid_size + (j + 1))

            for v in neighbors:
                u_lat, u_lon = node_coords[u]
                v_lat, v_lon = node_coords[v]
                direct_dist = haversine_distance(u_lat, u_lon, v_lat, v_lon)
                road_length = direct_dist * 1.15  # road distance >= straight-line distance

                G.add_edge(u, v, length=road_length, oneway=False)
                G.add_edge(v, u, length=road_length, oneway=False)

    return G, node_coords, component_map


@pytest.fixture
def disconnected_graph_fixture(synthetic_grid_graph):
    """Fixture containing a main grid and an isolated node with distinct component ID (TC-04)."""
    G, node_coords, component_map = synthetic_grid_graph
    
    isolated_node = 999999
    iso_lat = 13.6500
    iso_lon = 78.5500
    G.add_node(isolated_node, y=iso_lat, x=iso_lon)
    node_coords[isolated_node] = (iso_lat, iso_lon)
    component_map[isolated_node] = 1  # Distinct disconnected component

    main_node = 0
    return G, node_coords, component_map, main_node, isolated_node
