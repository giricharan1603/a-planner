"""Geospatial graph acquisition, simplification, caching, and spatial indexing."""

import math
import warnings
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import networkx as nx
import numpy as np
import osmnx as ox
from scipy.spatial import KDTree

# Default Campus & Routing Constants
EARTH_RADIUS_METERS = 6371000.0
SNAPPING_THRESHOLD_METERS = 250.0
DEFAULT_CAMPUS_COORDS = (13.6288, 78.5024)  # MITS Campus Center
DEFAULT_CAMPUS_RADIUS_METERS = 1500

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CACHE_DIR = DATA_DIR / "cache"
ROUTES_DIR = DATA_DIR / "routes"
LANDMARKS_FILE = DATA_DIR / "landmarks.json"


class SnappingThresholdWarning(UserWarning):
    """Warning emitted when snapping distance exceeds the configured threshold (FR-2.3)."""
    pass


def simplify_multigraph_to_digraph(multi_g: nx.MultiDiGraph) -> nx.DiGraph:
    """Convert MultiDiGraph to DiGraph, retaining min(length) for parallel edges (FR-1.5)."""
    di_g = nx.DiGraph()

    for node, data in multi_g.nodes(data=True):
        di_g.add_node(node, y=float(data.get("y", 0.0)), x=float(data.get("x", 0.0)))

    edge_dict = {}
    for u, v, k, data in multi_g.edges(keys=True, data=True):
        length = float(data.get("length", 1.0))
        pair = (u, v)
        if pair not in edge_dict or length < edge_dict[pair]["length"]:
            edge_dict[pair] = {
                "length": length,
                "name": data.get("name", ""),
                "oneway": data.get("oneway", False),
            }

    for (u, v), attrs in edge_dict.items():
        di_g.add_edge(u, v, **attrs)

    return di_g


def fetch_campus_graph(
    center_point: Tuple[float, float] = DEFAULT_CAMPUS_COORDS,
    dist: int = DEFAULT_CAMPUS_RADIUS_METERS,
    mode: str = "walk",
    force_reload: bool = False,
) -> Tuple[nx.DiGraph, Dict[int, Tuple[float, float]], Dict[int, int]]:
    """Fetch street network with local disk caching and DiGraph simplification (FR-1.1, FR-1.4)."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE_DIR / f"{mode}_campus_network.graphml"

    raw_multi_g = None
    if not force_reload and cache_path.exists():
        try:
            raw_multi_g = ox.load_graphml(filepath=cache_path)
        except Exception:
            raw_multi_g = None

    if raw_multi_g is None:
        ox.settings.use_cache = True
        ox.settings.log_console = False
        raw_multi_g = ox.graph_from_point(center_point, dist=dist, network_type=mode, simplify=True)
        ox.save_graphml(raw_multi_g, filepath=cache_path)

    simplified_g = simplify_multigraph_to_digraph(raw_multi_g)
    node_coords = {
        node: (float(data["y"]), float(data["x"]))
        for node, data in simplified_g.nodes(data=True)
    }

    component_map = {}
    for cid, comp in enumerate(nx.weakly_connected_components(simplified_g)):
        for node in comp:
            component_map[node] = cid

    return simplified_g, node_coords, component_map


class SpatialSnapper:
    """Snaps GPS coordinates to nearest graph vertex via 3D Cartesian KD-Tree (FR-2.2)."""

    def __init__(self, node_coords: Dict[int, Tuple[float, float]]):
        self.node_ids: List[int] = list(node_coords.keys())
        self.node_coords = node_coords

        points = []
        for nid in self.node_ids:
            lat, lon = node_coords[nid]
            phi, theta = math.radians(lat), math.radians(lon)
            points.append((math.cos(phi) * math.cos(theta), math.cos(phi) * math.sin(theta), math.sin(phi)))
        self.tree = KDTree(np.array(points))

    def snap(self, lat: float, lon: float, threshold_meters: float = SNAPPING_THRESHOLD_METERS) -> Tuple[int, float]:
        phi, theta = math.radians(lat), math.radians(lon)
        target = np.array([math.cos(phi) * math.cos(theta), math.cos(phi) * math.sin(theta), math.sin(phi)])

        _, idx = self.tree.query(target, k=1)
        nearest_node = self.node_ids[idx]
        n_lat, n_lon = self.node_coords[nearest_node]

        # Great-Circle distance to snapped node
        dphi = math.radians(n_lat - lat)
        dlam = math.radians(n_lon - lon)
        a = math.sin(dphi / 2)**2 + math.cos(math.radians(lat)) * math.cos(math.radians(n_lat)) * math.sin(dlam / 2)**2
        dist = EARTH_RADIUS_METERS * 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - min(1.0, a)))

        if dist > threshold_meters:
            warnings.warn(
                f"Resolved node {nearest_node} is {dist:.1f}m away, exceeding safety threshold of {threshold_meters}m.",
                category=SnappingThresholdWarning,
                stacklevel=2,
            )
        return nearest_node, dist
