"""Unit tests for the Haversine Heuristic Engine (FR-3.3, FR-3.4, TC-02)."""

import math
from src.heuristic import haversine_distance, make_haversine_heuristic


def test_haversine_known_coordinates():
    """Verify Haversine against known geographical distance."""
    # Bangalore (12.9716, 77.5946) to Chennai (13.0827, 80.2707) is approx 290-295 km
    dist = haversine_distance(12.9716, 77.5946, 13.0827, 80.2707)
    assert 285_000 < dist < 300_000, f"Unexpected distance: {dist}m"


def test_haversine_zero_distance():
    """Haversine distance between identical points must be exactly zero."""
    dist = haversine_distance(13.6288, 78.5024, 13.6288, 78.5024)
    assert math.isclose(dist, 0.0, abs_tol=1e-6)


def test_heuristic_consistency(synthetic_grid_graph):
    """Verify heuristic consistency (triangle inequality): h(u) <= c(u, v) + h(v) for all edges."""
    G, node_coords, _ = synthetic_grid_graph
    target_node = 224  # Bottom-right corner of 15x15 grid
    h_func = make_haversine_heuristic(target_node, node_coords)

    violations = 0
    for u, v, data in G.edges(data=True):
        edge_cost = data["length"]
        h_u = h_func(u)
        h_v = h_func(v)
        # Consistent if h(u) <= edge_cost + h(v) + numerical_epsilon
        if h_u > edge_cost + h_v + 1e-6:
            violations += 1

    assert violations == 0, f"Found {violations} consistency violations in graph edges."
