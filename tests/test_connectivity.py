"""Unit tests for Fast-Failure Structural Connectivity Checklist (FR-3.6, TC-04, NFR)."""

import time
import pytest
from src.exceptions import PathNotFoundError
from src.router import run_astar, run_dijkstra


def test_tc04_disconnected_fast_failure(disconnected_graph_fixture):
    """TC-04: Confirm immediate <10 ms pre-queue rejection closures for disconnected locations."""
    G, node_coords, component_map, main_node, isolated_node = disconnected_graph_fixture

    # Test A* Fast Failure
    t0 = time.perf_counter()
    with pytest.raises(PathNotFoundError) as exc_info:
        run_astar(G, main_node, isolated_node, node_coords, component_map)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    assert elapsed_ms < 10.0, f"A* fast failure took {elapsed_ms:.2f}ms, exceeding 10ms limit!"
    assert "No connected path exists" in str(exc_info.value)

    # Test Dijkstra Fast Failure
    t0 = time.perf_counter()
    with pytest.raises(PathNotFoundError):
        run_dijkstra(G, main_node, isolated_node, node_coords, component_map)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    assert elapsed_ms < 10.0, f"Dijkstra fast failure took {elapsed_ms:.2f}ms, exceeding 10ms limit!"
