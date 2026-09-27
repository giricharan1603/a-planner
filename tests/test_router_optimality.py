"""Unit tests for Search Optimality and Admissibility (TC-01, TC-02, TC-05)."""

import math
import random
from src.router import run_astar, run_dijkstra
from src.heuristic import haversine_distance


def test_tc05_identity_route(synthetic_grid_graph):
    """TC-05: Validate zero-distance output handling when origin and destination coordinates are identical."""
    G, node_coords, component_map = synthetic_grid_graph
    sample_node = 42

    res_astar = run_astar(G, sample_node, sample_node, node_coords, component_map)
    assert res_astar.status == "SUCCESS"
    assert res_astar.total_distance_meters == 0.0
    assert len(res_astar.path) == 1
    assert res_astar.path[0] == sample_node

    res_dijkstra = run_dijkstra(G, sample_node, sample_node, node_coords, component_map)
    assert res_dijkstra.status == "SUCCESS"
    assert res_dijkstra.total_distance_meters == 0.0
    assert len(res_dijkstra.path) == 1


def test_tc01_tc02_optimality_and_admissibility_100_pairs(synthetic_grid_graph):
    """TC-01 & TC-02: Assert A* distance equals Dijkstra distance (<1e-4) and h(u) <= actual_dist across 100 pairs."""
    G, node_coords, component_map = synthetic_grid_graph
    all_nodes = list(G.nodes())

    random.seed(42)
    sample_pairs = []
    for _ in range(100):
        u, v = random.sample(all_nodes, 2)
        sample_pairs.append((u, v))

    admissibility_violations = 0
    optimality_violations = 0

    for u, v in sample_pairs:
        res_a = run_astar(G, u, v, node_coords, component_map)
        res_d = run_dijkstra(G, u, v, node_coords, component_map)

        # TC-01: 100% path length agreement down to 10^-4 precision
        if not math.isclose(res_a.total_distance_meters, res_d.total_distance_meters, rel_tol=1e-4):
            optimality_violations += 1

        # TC-02: Admissibility condition: h(u, v) <= actual_shortest_path(u, v)
        u_lat, u_lon = node_coords[u]
        v_lat, v_lon = node_coords[v]
        h_val = haversine_distance(u_lat, u_lon, v_lat, v_lon)

        if h_val > res_a.total_distance_meters + 1e-6:
            admissibility_violations += 1

    assert optimality_violations == 0, f"Found {optimality_violations} optimality violations between A* and Dijkstra."
    assert admissibility_violations == 0, f"Found {admissibility_violations} admissibility violations in heuristic."
