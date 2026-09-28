"""
router.py - Campus Landmark Routing Engine
Implements Haversine distance, Graph loading, and A* vs Dijkstra pathfinding algorithms.
"""

import heapq
import math
import time
from pathlib import Path
import networkx as nx
import osmnx as ox

# Constants
EARTH_RADIUS_METERS = 6371000.0  # Volumetric mean Earth radius
DEFAULT_CAMPUS_COORDS = (13.6288, 78.5024)  # MITS Campus Center (Lat, Lon)


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the straight-line (Great-Circle) distance between two GPS coordinates in meters."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * (math.sin(dlam / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - min(1.0, a)))
    return EARTH_RADIUS_METERS * c


def load_campus_graph(cache_file: str = "data/campus_network.graphml") -> nx.DiGraph:
    """
    Load the campus road and footpath network.
    Reads from the local cached file, or downloads via OSMnx if missing.
    Simplifies multiple parallel edges between vertices by keeping min(length).
    """
    cache_path = Path(cache_file)
    if cache_path.exists():
        raw_graph = ox.load_graphml(filepath=cache_path)
    else:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        raw_graph = ox.graph_from_point(DEFAULT_CAMPUS_COORDS, dist=1500, network_type="walk", simplify=True)
        ox.save_graphml(raw_graph, filepath=cache_path)

    # Convert MultiDiGraph to a clean, simple DiGraph with min(length)
    G = nx.DiGraph()
    for node, data in raw_graph.nodes(data=True):
        G.add_node(node, y=float(data.get("y", 0.0)), x=float(data.get("x", 0.0)))

    for u, v, data in raw_graph.edges(data=True):
        length = float(data.get("length", 1.0))
        if not G.has_edge(u, v) or length < G[u][v]["length"]:
            G.add_edge(u, v, length=length)

    return G


def snap_to_node(G: nx.DiGraph, lat: float, lon: float) -> tuple[int, float]:
    """
    Snap any GPS point to the nearest road/path intersection (vertex) in the graph.
    Returns (nearest_node_id, distance_in_meters).
    """
    best_node = None
    min_dist = float("inf")

    for node, data in G.nodes(data=True):
        dist = haversine(lat, lon, data["y"], data["x"])
        if dist < min_dist:
            min_dist = dist
            best_node = node

    return best_node, min_dist


def dijkstra(G: nx.DiGraph, start: int, goal: int):
    """
    Dijkstra's Algorithm (Uninformed Search, h = 0).
    Explores outwards uniformly based solely on distance traveled: g(n).
    Returns (total_distance, path, nodes_expanded, elapsed_ms).
    """
    t0 = time.perf_counter_ns()

    if start == goal:
        return 0.0, [start], 1, (time.perf_counter_ns() - t0) / 1e6

    # Priority queue: (cost, counter, current_node)
    counter = 0
    queue = [(0.0, counter, start)]
    g_score = {start: 0.0}
    came_from = {}
    visited = set()
    nodes_expanded = 0

    while queue:
        cost, _, current = heapq.heappop(queue)

        if current in visited or cost > g_score.get(current, float("inf")):
            continue

        visited.add(current)
        nodes_expanded += 1

        if current == goal:
            break

        for neighbor in G.successors(current):
            new_cost = cost + G[current][neighbor]["length"]
            if new_cost < g_score.get(neighbor, float("inf")):
                g_score[neighbor] = new_cost
                came_from[neighbor] = current
                counter += 1
                heapq.heappush(queue, (new_cost, counter, neighbor))

    elapsed_ms = (time.perf_counter_ns() - t0) / 1e6

    if goal not in came_from and start != goal:
        return None, [], nodes_expanded, elapsed_ms

    # Reconstruct path
    curr = goal
    path = [curr]
    while curr in came_from:
        curr = came_from[curr]
        path.append(curr)
    path.reverse()

    return g_score[goal], path, nodes_expanded, elapsed_ms


def astar(G: nx.DiGraph, start: int, goal: int):
    """
    A* Search Algorithm (Informed Search with Haversine Heuristic).
    Directs the search cone toward the destination using: f(n) = g(n) + h(n).
    Returns (total_distance, path, nodes_expanded, elapsed_ms).
    """
    t0 = time.perf_counter_ns()

    if start == goal:
        return 0.0, [start], 1, (time.perf_counter_ns() - t0) / 1e6

    goal_lat = G.nodes[goal]["y"]
    goal_lon = G.nodes[goal]["x"]

    def heuristic(node):
        return haversine(G.nodes[node]["y"], G.nodes[node]["x"], goal_lat, goal_lon)

    # Priority queue: (f_score, h_score, counter, current_node)
    # Breaking ties by h_score prioritizes nodes closer to the destination
    counter = 0
    start_h = heuristic(start)
    queue = [(start_h, start_h, counter, start)]
    g_score = {start: 0.0}
    came_from = {}
    visited = set()
    nodes_expanded = 0

    while queue:
        f, h, _, current = heapq.heappop(queue)

        if current in visited or f > g_score.get(current, float("inf")) + h + 1e-9:
            continue

        visited.add(current)
        nodes_expanded += 1

        if current == goal:
            break

        for neighbor in G.successors(current):
            new_g = g_score[current] + G[current][neighbor]["length"]
            if new_g < g_score.get(neighbor, float("inf")):
                g_score[neighbor] = new_g
                came_from[neighbor] = current
                nh = heuristic(neighbor)
                counter += 1
                heapq.heappush(queue, (new_g + nh, nh, counter, neighbor))

    elapsed_ms = (time.perf_counter_ns() - t0) / 1e6

    if goal not in came_from and start != goal:
        return None, [], nodes_expanded, elapsed_ms

    # Reconstruct path
    curr = goal
    path = [curr]
    while curr in came_from:
        curr = came_from[curr]
        path.append(curr)
    path.reverse()

    return g_score[goal], path, nodes_expanded, elapsed_ms
