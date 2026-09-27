"""Unit tests for Search Space Pruning Benchmarking (FR-4.2, TC-03)."""

from src.router import run_astar, run_dijkstra


def test_tc03_search_space_pruning_gt_500m(synthetic_grid_graph):
    """TC-03: Verify a minimum 40% node expansion reduction via A* on paths spanning distances >500 meters."""
    G, node_coords, component_map = synthetic_grid_graph

    # Select representative origin-destination pairs spanning > 500 meters
    # Center node is 12 * 25 + 12 = 312
    center = 312
    test_pairs = [
        (center, 0),    # Center to Top-Left Corner (~1800m)
        (center, 24),   # Center to Top-Right Corner (~1800m)
        (center, 600),  # Center to Bottom-Left Corner (~1800m)
        (center, 624),  # Center to Bottom-Right Corner (~1800m)
        (center, 12),   # Center to Top-Mid (~920m)
        (center, 612),  # Center to Bottom-Mid (~920m)
    ]

    pruning_ratios = []

    for u, v in test_pairs:
        res_a = run_astar(G, u, v, node_coords, component_map)
        res_d = run_dijkstra(G, u, v, node_coords, component_map)

        assert res_d.total_distance_meters > 500.0, (
            f"Test pair ({u}, {v}) distance is only {res_d.total_distance_meters:.1f}m <= 500m."
        )

        nodes_d = res_d.nodes_expanded
        nodes_a = res_a.nodes_expanded
        reduction = (nodes_d - nodes_a) / nodes_d
        pruning_ratios.append(reduction)

        # Each path > 500m must achieve significant pruning
        assert reduction >= 0.40, (
            f"Pair ({u}, {v}) achieved only {reduction:.1%} reduction (Dijkstra: {nodes_d}, A*: {nodes_a}), "
            f"below the required 40% threshold."
        )

    avg_reduction = sum(pruning_ratios) / len(pruning_ratios)
    print(f"\nAverage search space pruning across >500m paths: {avg_reduction:.2%}")
    assert avg_reduction >= 0.40
