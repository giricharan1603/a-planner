"""Routing engine: Haversine, graph loading, Dijkstra, A* pathfinding."""

import heapq
import math
import time
from pathlib import Path

import networkx as nx
import osmnx as ox

EARTH_RADIUS = 6371000.0
CAMPUS_CENTER = (13.6288, 78.5024)


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in meters between two GPS coordinates."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return EARTH_RADIUS * 2 * math.atan2(math.sqrt(a), math.sqrt(max(0, 1 - a)))


def load_campus_graph(cache_file: str = "data/campus_network.graphml") -> nx.DiGraph:
    """Load campus walk network from cache or OSMnx, return simplified DiGraph."""
    cache = Path(cache_file)
    if cache.exists():
        raw = ox.load_graphml(filepath=cache)
    else:
        cache.parent.mkdir(parents=True, exist_ok=True)
        raw = ox.graph_from_point(CAMPUS_CENTER, dist=1500, network_type="walk", simplify=True)
        ox.save_graphml(raw, filepath=cache)

    G = nx.DiGraph()
    for n, d in raw.nodes(data=True):
        G.add_node(n, y=float(d.get("y", 0)), x=float(d.get("x", 0)))
    for u, v, d in raw.edges(data=True):
        w = float(d.get("length", 1))
        if not G.has_edge(u, v) or w < G[u][v]["length"]:
            G.add_edge(u, v, length=w)
    return G


def build_coord_index(G: nx.DiGraph) -> dict:
    """Pre-extract node coordinates as {node: (lat, lon)} for fast lookup."""
    return {n: (d["y"], d["x"]) for n, d in G.nodes(data=True)}


def snap_to_node(coords: dict, lat: float, lon: float) -> tuple:
    """Snap GPS point to nearest graph node using pre-built coordinate index. O(N) scan."""
    best, best_d = None, float("inf")
    for n, (ny, nx_) in coords.items():
        d = haversine(lat, lon, ny, nx_)
        if d < best_d:
            best, best_d = n, d
    return best, best_d


def _reconstruct(came_from: dict, goal: int) -> list:
    """Trace back the path from goal to start."""
    path = [goal]
    while goal in came_from:
        goal = came_from[goal]
        path.append(goal)
    path.reverse()
    return path


def dijkstra(G: nx.DiGraph, start: int, goal: int) -> tuple:
    """Dijkstra (h=0). Returns (distance, path, nodes_expanded, elapsed_ms)."""
    t0 = time.perf_counter_ns()
    if start == goal:
        return 0.0, [start], 1, (time.perf_counter_ns() - t0) / 1e6

    cnt = 0
    heap = [(0.0, cnt, start)]
    g = {start: 0.0}
    prev = {}
    closed = set()
    expanded = 0

    while heap:
        cost, _, u = heapq.heappop(heap)
        if u in closed:
            continue
        closed.add(u)
        expanded += 1
        if u == goal:
            break
        for v in G.successors(u):
            nc = cost + G[u][v]["length"]
            if nc < g.get(v, float("inf")):
                g[v] = nc
                prev[v] = u
                cnt += 1
                heapq.heappush(heap, (nc, cnt, v))

    ms = (time.perf_counter_ns() - t0) / 1e6
    if goal not in prev and start != goal:
        return None, [], expanded, ms
    return g[goal], _reconstruct(prev, goal), expanded, ms


def astar(G: nx.DiGraph, start: int, goal: int, coords: dict = None) -> tuple:
    """A* with Haversine heuristic. Returns (distance, path, nodes_expanded, elapsed_ms)."""
    t0 = time.perf_counter_ns()
    if start == goal:
        return 0.0, [start], 1, (time.perf_counter_ns() - t0) / 1e6

    if coords is None:
        coords = build_coord_index(G)
    gy, gx = coords[goal]

    h_cache = {}
    def h(n):
        if n not in h_cache:
            ny, nx_ = coords[n]
            h_cache[n] = haversine(ny, nx_, gy, gx)
        return h_cache[n]

    cnt = 0
    sh = h(start)
    heap = [(sh, sh, cnt, start)]
    g = {start: 0.0}
    prev = {}
    closed = set()
    expanded = 0

    while heap:
        f, _, _, u = heapq.heappop(heap)
        if u in closed:
            continue
        closed.add(u)
        expanded += 1
        if u == goal:
            break
        gu = g[u]
        for v in G.successors(u):
            ng = gu + G[u][v]["length"]
            if ng < g.get(v, float("inf")):
                g[v] = ng
                prev[v] = u
                hv = h(v)
                cnt += 1
                heapq.heappush(heap, (ng + hv, hv, cnt, v))

    ms = (time.perf_counter_ns() - t0) / 1e6
    if goal not in prev and start != goal:
        return None, [], expanded, ms
    return g[goal], _reconstruct(prev, goal), expanded, ms
