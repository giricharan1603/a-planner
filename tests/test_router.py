"""Comprehensive test suite for Campus Landmark A* Route Planner (TC-01 through TC-05)."""

import math
import random
import time
import pytest
import networkx as nx

from src.router import PathNotFoundError, haversine_distance, make_haversine_heuristic, run_astar, run_dijkstra


@pytest.fixture
def synthetic_campus_graph():
    """Create a 25x25 topological road grid with realistic campus coordinates."""
    G = nx.DiGraph()
    node_coords = {}
    component_map = {}
    base_lat, base_lon = 13.6288, 78.5024
    step = 0.0006  # ~66 meters between vertices
    grid_size = 25

    for i in range(grid_size):
        for j in range(grid_size):
            node_id = i * grid_size + j
            lat = base_lat + (i - grid_size // 2) * step
            lon = base_lon + (j - grid_size // 2) * step
            G.add_node(node_id, y=lat, x=lon)
            node_coords[node_id] = (lat, lon)
            component_map[node_id] = 0

    for i in range(grid_size):
        for j in range(grid_size):
            u = i * grid_size + j
            for ni, nj in [(i + 1, j), (i, j + 1)]:
                if ni < grid_size and nj < grid_size:
                    v = ni * grid_size + nj
                    d = haversine_distance(node_coords[u][0], node_coords[u][1], node_coords[v][0], node_coords[v][1]) * 1.15
                    G.add_edge(u, v, length=d, oneway=False)
                    G.add_edge(v, u, length=d, oneway=False)

    return G, node_coords, component_map


def test_haversine_metric():
    """Verify Haversine formula distance and zero identity."""
    assert math.isclose(haversine_distance(13.6288, 78.5024, 13.6288, 78.5024), 0.0, abs_tol=1e-6)
    dist = haversine_distance(12.9716, 77.5946, 13.0827, 80.2707)  # Bangalore to Chennai
    assert 285_000 < dist < 300_000


def test_tc01_tc02_optimality_and_admissibility(synthetic_campus_graph):
    """TC-01 & TC-02: Assert A* distance equals Dijkstra distance (<1e-4) and h(u) <= actual_dist."""
    G, node_coords, component_map = synthetic_campus_graph
    random.seed(42)
    all_nodes = list(G.nodes())

    for _ in range(100):
        u, v = random.sample(all_nodes, 2)
        res_a = run_astar(G, u, v, node_coords, component_map)
        res_d = run_dijkstra(G, u, v, node_coords, component_map)

        # TC-01: Exact distance parity down to 10^-4 tolerance
        assert math.isclose(res_a.total_distance_meters, res_d.total_distance_meters, rel_tol=1e-4)

        # TC-02: Admissibility condition: h(start) <= actual_distance
        h_val = haversine_distance(node_coords[u][0], node_coords[u][1], node_coords[v][0], node_coords[v][1])
        assert h_val <= res_a.total_distance_meters + 1e-6


def test_tc03_search_space_pruning_gt_500m(synthetic_campus_graph):
    """TC-03: Verify at least 40% node expansion reduction via A* on paths > 500 meters."""
    G, node_coords, component_map = synthetic_campus_graph
    center = 312  # Center of 25x25 grid
    test_pairs = [(center, 0), (center, 24), (center, 600), (center, 624), (center, 12), (center, 612)]

    for u, v in test_pairs:
        res_a = run_astar(G, u, v, node_coords, component_map)
        res_d = run_dijkstra(G, u, v, node_coords, component_map)
        assert res_d.total_distance_meters > 500.0

        pruning = (res_d.nodes_expanded - res_a.nodes_expanded) / res_d.nodes_expanded
        assert pruning >= 0.40, f"Pair ({u}, {v}) achieved only {pruning:.1%} reduction."


def test_tc04_disconnected_fast_failure(synthetic_campus_graph):
    """TC-04: Confirm immediate < 10ms pre-queue rejection closures for disconnected locations."""
    G, node_coords, component_map = synthetic_campus_graph
    isolated_node = 999999
    G.add_node(isolated_node, y=13.650, x=78.550)
    node_coords[isolated_node] = (13.650, 78.550)
    component_map[isolated_node] = 1

    t0 = time.perf_counter()
    with pytest.raises(PathNotFoundError):
        run_astar(G, 0, isolated_node, node_coords, component_map)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    assert elapsed_ms < 10.0, f"Fast rejection took {elapsed_ms:.2f}ms >= 10ms limit."


def test_tc05_identity_route(synthetic_campus_graph):
    """TC-05: Validate zero-distance output handling when origin and destination are identical."""
    G, node_coords, component_map = synthetic_campus_graph
    res = run_astar(G, 42, 42, node_coords, component_map)
    assert res.total_distance_meters == 0.0
    assert res.path == [42]
    assert res.nodes_expanded == 1
