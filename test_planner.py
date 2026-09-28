"""
test_planner.py - Simple automated verification tests for the Route Planner.
Verifies algorithm optimality, search pruning, and Haversine calculations.
"""

import math
import pytest
from router import astar, dijkstra, haversine, load_campus_graph, snap_to_node


def test_haversine_formula():
    """Verify that Haversine distance is 0 for identical points and accurate for real locations."""
    # Identical coordinates
    assert math.isclose(haversine(13.6288, 78.5024, 13.6288, 78.5024), 0.0, abs_tol=1e-5)

    # Bangalore to Chennai is approximately 290 km
    dist = haversine(12.9716, 77.5946, 13.0827, 80.2707)
    assert 280_000 < dist < 300_000


def test_optimality_astar_vs_dijkstra():
    """Verify that A* and Dijkstra find the exact same optimal path distance."""
    G = load_campus_graph()
    nodes = list(G.nodes())
    start = nodes[0]
    goal = nodes[len(nodes) // 2]

    dist_dijkstra, path_d, _, _ = dijkstra(G, start, goal)
    dist_astar, path_a, _, _ = astar(G, start, goal)

    assert dist_dijkstra is not None
    assert dist_astar is not None
    # Distance must match down to small float tolerance
    assert math.isclose(dist_dijkstra, dist_astar, rel_tol=1e-3)


def test_astar_search_pruning():
    """Verify that A* expands fewer or equal nodes compared to uninformed Dijkstra."""
    G = load_campus_graph()
    nodes = list(G.nodes())
    start = nodes[0]
    goal = nodes[-1]

    _, _, nodes_d, _ = dijkstra(G, start, goal)
    _, _, nodes_a, _ = astar(G, start, goal)

    assert nodes_a <= nodes_d, f"A* expanded {nodes_a} which is greater than Dijkstra {nodes_d}"


def test_identity_route():
    """Routing from a node to itself must immediately return 0 distance and 1 node."""
    G = load_campus_graph()
    sample_node = list(G.nodes())[0]

    dist, path, nodes_count, _ = astar(G, sample_node, sample_node)
    assert dist == 0.0
    assert path == [sample_node]
    assert nodes_count == 1
