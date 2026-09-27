"""Custom A* and Dijkstra Search Engines with Base Principles (FR-3.1 - FR-3.6, FR-4.1 - FR-4.2)."""

import heapq
import time
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple
import networkx as nx

from src.exceptions import PathNotFoundError
from src.heuristic import make_haversine_heuristic


@dataclass
class SearchResult:
    """Structured pathfinding and benchmark result payload."""
    status: str
    algorithm: str
    start_node_id: int
    target_node_id: int
    total_distance_meters: float
    nodes_expanded: int
    peak_frontier_size: int
    execution_time_ms: float
    path: List[int]
    path_coordinates: List[Dict[str, float]]


def _reconstruct_path(
    came_from: Dict[int, int],
    current: int,
    node_coords: Dict[int, Tuple[float, float]],
) -> Tuple[List[int], List[Dict[str, float]]]:
    """Reconstruct path from start to target using came_from predecessor map."""
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    path.reverse()

    coords = [
        {"lat": node_coords[nid][0], "lon": node_coords[nid][1]}
        for nid in path
    ]
    return path, coords


def search(
    G: nx.DiGraph,
    start_node: int,
    target_node: int,
    node_coords: Dict[int, Tuple[float, float]],
    heuristic_fn: Optional[Callable[[int], float]] = None,
    component_map: Optional[Dict[int, int]] = None,
    algorithm_name: str = "A_STAR",
) -> SearchResult:
    """Execute heuristic-guided search (A* or Dijkstra) from base principles using heapq.

    Args:
        G: Simplified networkx.DiGraph.
        start_node: Origin vertex ID.
        target_node: Destination vertex ID.
        node_coords: Mapping of node_id -> (lat, lon).
        heuristic_fn: Callable returning h(node). If None or returns 0, acts as Dijkstra.
        component_map: Optional mapping of node_id -> component_id for fast-failure checks.
        algorithm_name: Label ('A_STAR' or 'DIJKSTRA').

    Returns:
        SearchResult containing path, distances, and execution benchmarks.

    Raises:
        PathNotFoundError: If disconnected or unreachable.
    """
    t_start = time.perf_counter_ns()

    # FR-3.6 & NFR: Instant structural connectivity validation (<10 ms)
    if component_map is not None:
        start_comp = component_map.get(start_node)
        target_comp = component_map.get(target_node)
        if start_comp is None or target_comp is None or start_comp != target_comp:
            t_end = time.perf_counter_ns()
            elapsed_ms = (t_end - t_start) / 1_000_000.0
            raise PathNotFoundError(
                f"No connected path exists between {start_node} and {target_node} "
                f"(components {start_comp} vs {target_comp}). Terminated in {elapsed_ms:.2f}ms."
            )

    # TC-05: Identity route check
    if start_node == target_node:
        t_end = time.perf_counter_ns()
        elapsed_ms = (t_end - t_start) / 1_000_000.0
        coords = [{"lat": node_coords[start_node][0], "lon": node_coords[start_node][1]}]
        return SearchResult(
            status="SUCCESS",
            algorithm=algorithm_name,
            start_node_id=start_node,
            target_node_id=target_node,
            total_distance_meters=0.0,
            nodes_expanded=1,
            peak_frontier_size=1,
            execution_time_ms=elapsed_ms,
            path=[start_node],
            path_coordinates=coords,
        )

    # Fallback to zero heuristic for uninformed Dijkstra
    if heuristic_fn is None:
        h_func = lambda _: 0.0
    else:
        h_func = heuristic_fn

    # Priority queue min-heap: (f_score, h_score, tie_breaker_counter, node_id)
    # Breaking ties by smaller h_score channels exploration towards the goal.
    counter = 0
    start_h = h_func(start_node)
    open_heap = [(start_h, start_h, counter, start_node)]
    
    g_score: Dict[int, float] = {start_node: 0.0}
    came_from: Dict[int, int] = {}
    closed_set: set = set()

    nodes_expanded = 0
    peak_frontier_size = 1

    while open_heap:
        peak_frontier_size = max(peak_frontier_size, len(open_heap))
        f, h, _, current = heapq.heappop(open_heap)

        # Lazy deletion: discard stale heap entries
        current_g = g_score[current]
        if f > current_g + h + 1e-9:
            continue

        if current in closed_set:
            continue

        closed_set.add(current)
        nodes_expanded += 1

        # Goal check
        if current == target_node:
            t_end = time.perf_counter_ns()
            elapsed_ms = (t_end - t_start) / 1_000_000.0
            path, coords = _reconstruct_path(came_from, current, node_coords)
            return SearchResult(
                status="SUCCESS",
                algorithm=algorithm_name,
                start_node_id=start_node,
                target_node_id=target_node,
                total_distance_meters=g_score[target_node],
                nodes_expanded=nodes_expanded,
                peak_frontier_size=peak_frontier_size,
                execution_time_ms=elapsed_ms,
                path=path,
                path_coordinates=coords,
            )

        # Relax outward edges
        for neighbor in G.successors(current):
            if neighbor in closed_set:
                continue

            edge_len = G[current][neighbor].get("length", 1.0)
            tentative_g = current_g + edge_len

            if tentative_g < g_score.get(neighbor, float("inf")):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                neighbor_h = h_func(neighbor)
                neighbor_f = tentative_g + neighbor_h
                counter += 1
                heapq.heappush(open_heap, (neighbor_f, neighbor_h, counter, neighbor))

    t_end = time.perf_counter_ns()
    elapsed_ms = (t_end - t_start) / 1_000_000.0
    raise PathNotFoundError(
        f"Search space exhausted without reaching target node {target_node}. "
        f"Explored {nodes_expanded} nodes in {elapsed_ms:.2f}ms."
    )


def run_astar(
    G: nx.DiGraph,
    start_node: int,
    target_node: int,
    node_coords: Dict[int, Tuple[float, float]],
    component_map: Optional[Dict[int, int]] = None,
) -> SearchResult:
    """Run informed A* search with the Haversine Great-Circle heuristic (FR-3.1 - FR-3.5)."""
    h_func = make_haversine_heuristic(target_node, node_coords)
    return search(
        G=G,
        start_node=start_node,
        target_node=target_node,
        node_coords=node_coords,
        heuristic_fn=h_func,
        component_map=component_map,
        algorithm_name="A_STAR",
    )


def run_dijkstra(
    G: nx.DiGraph,
    start_node: int,
    target_node: int,
    node_coords: Dict[int, Tuple[float, float]],
    component_map: Optional[Dict[int, int]] = None,
) -> SearchResult:
    """Run baseline uninformed uniform-cost Dijkstra search (h(n) = 0) (FR-4.1)."""
    return search(
        G=G,
        start_node=start_node,
        target_node=target_node,
        node_coords=node_coords,
        heuristic_fn=None,
        component_map=component_map,
        algorithm_name="DIJKSTRA",
    )
