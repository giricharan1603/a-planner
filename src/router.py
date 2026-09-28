"""Custom A* and Dijkstra search engines with Haversine heuristic (FR-3, FR-4)."""

import heapq
import math
import time
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple
import networkx as nx

from src.graph import EARTH_RADIUS_METERS


class PathNotFoundError(Exception):
    """Raised when no connected path exists between origin and destination."""
    pass


@dataclass
class SearchResult:
    """Benchmark and path results payload."""
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


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float, radius: float = EARTH_RADIUS_METERS) -> float:
    """Compute Great-Circle spherical distance in meters (FR-3.3)."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * (math.sin(dlam / 2.0)**2)
    return radius * 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - min(1.0, max(0.0, a))))


def make_haversine_heuristic(target_node: int, node_coords: Dict[int, Tuple[float, float]]) -> Callable[[int], float]:
    """Optimized closure computing h(n) against target coordinates."""
    t_lat, t_lon = node_coords[target_node]
    return lambda node: haversine_distance(node_coords[node][0], node_coords[node][1], t_lat, t_lon)


def search(
    G: nx.DiGraph,
    start_node: int,
    target_node: int,
    node_coords: Dict[int, Tuple[float, float]],
    heuristic_fn: Optional[Callable[[int], float]] = None,
    component_map: Optional[Dict[int, int]] = None,
    algorithm_name: str = "A_STAR",
) -> SearchResult:
    """Execute priority queue search (A* or Dijkstra) from base principles."""
    t_start = time.perf_counter_ns()

    # Pre-search connectivity fast-rejection (<10ms) (FR-3.6)
    if component_map is not None:
        c1, c2 = component_map.get(start_node), component_map.get(target_node)
        if c1 is None or c2 is None or c1 != c2:
            elapsed_ms = (time.perf_counter_ns() - t_start) / 1_000_000.0
            raise PathNotFoundError(f"Disconnected subcomponents ({c1} vs {c2}). Aborted in {elapsed_ms:.2f}ms.")

    # Identity route handling (TC-05)
    if start_node == target_node:
        elapsed_ms = (time.perf_counter_ns() - t_start) / 1_000_000.0
        coords = [{"lat": node_coords[start_node][0], "lon": node_coords[start_node][1]}]
        return SearchResult("SUCCESS", algorithm_name, start_node, target_node, 0.0, 1, 1, elapsed_ms, [start_node], coords)

    h_func = heuristic_fn if heuristic_fn else (lambda _: 0.0)

    # Priority queue min-heap: (f_score, h_score, counter, node_id)
    # Secondary sort by h_score channels search toward goal on f-score ties
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

        # Lazy deletion for stale heap records
        if f > g_score[current] + h + 1e-9 or current in closed_set:
            continue

        closed_set.add(current)
        nodes_expanded += 1

        if current == target_node:
            elapsed_ms = (time.perf_counter_ns() - t_start) / 1_000_000.0
            path = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            coords = [{"lat": node_coords[n][0], "lon": node_coords[n][1]} for n in path]
            return SearchResult("SUCCESS", algorithm_name, start_node, target_node, g_score[target_node], nodes_expanded, peak_frontier_size, elapsed_ms, path, coords)

        for neighbor in G.successors(current):
            if neighbor in closed_set:
                continue
            edge_len = G[current][neighbor].get("length", 1.0)
            tentative_g = g_score[current] + edge_len

            if tentative_g < g_score.get(neighbor, float("inf")):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                nh = h_func(neighbor)
                counter += 1
                heapq.heappush(open_heap, (tentative_g + nh, nh, counter, neighbor))

    elapsed_ms = (time.perf_counter_ns() - t_start) / 1_000_000.0
    raise PathNotFoundError(f"Unreachable target node {target_node}. Explored {nodes_expanded} nodes.")


def run_astar(G: nx.DiGraph, start_node: int, target_node: int, node_coords: Dict[int, Tuple[float, float]], component_map: Optional[Dict[int, int]] = None) -> SearchResult:
    """Run informed A* search with Haversine heuristic (FR-3.1 - FR-3.5)."""
    return search(G, start_node, target_node, node_coords, make_haversine_heuristic(target_node, node_coords), component_map, "A_STAR")


def run_dijkstra(G: nx.DiGraph, start_node: int, target_node: int, node_coords: Dict[int, Tuple[float, float]], component_map: Optional[Dict[int, int]] = None) -> SearchResult:
    """Run uninformed Dijkstra search baseline (h(n) = 0) (FR-4.1)."""
    return search(G, start_node, target_node, node_coords, None, component_map, "DIJKSTRA")
