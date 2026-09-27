"""Geospatial Graph Acquisition, Disk Caching, and Preprocessing (FR-1.1 - FR-1.5, FR-3.6)."""

import os
from pathlib import Path
from typing import Dict, Optional, Tuple, Set
import networkx as nx
import osmnx as ox

from src.config import (
    CACHE_DIR,
    DEFAULT_NETWORK_MODE,
    DEFAULT_CACHE_FILENAME,
    DEFAULT_CAMPUS_RADIUS_METERS,
    DEFAULT_CAMPUS_COORDS,
)


def simplify_multigraph_to_digraph(multi_g: nx.MultiDiGraph) -> nx.DiGraph:
    """Convert an OSMnx MultiDiGraph to a simplified standard networkx.DiGraph (FR-1.5).

    Resolves multiple parallel edges between identical vertices u and v by retaining
    only the single edge containing the minimum length attribute value.
    Preserves node coordinates ('x', 'y') and directional attributes.

    Args:
        multi_g: Raw osmnx MultiDiGraph.

    Returns:
        Simplified networkx.DiGraph with O(1) edge lookups.
    """
    di_g = nx.DiGraph()

    # Copy all nodes with spatial coordinates and attributes
    for node, data in multi_g.nodes(data=True):
        lat = float(data.get("y", 0.0))
        lon = float(data.get("x", 0.0))
        di_g.add_node(node, y=lat, x=lon, osmid=data.get("osmid", node))

    # Iterate through all multi-edges and keep the min(length) edge for each (u, v)
    edge_dict = {}
    for u, v, k, data in multi_g.edges(keys=True, data=True):
        length = float(data.get("length", 1.0))
        pair = (u, v)
        if pair not in edge_dict or length < edge_dict[pair]["length"]:
            edge_dict[pair] = {
                "length": length,
                "name": data.get("name", ""),
                "highway": data.get("highway", ""),
                "oneway": data.get("oneway", False),
                "geometry": data.get("geometry", None),
            }

    for (u, v), attrs in edge_dict.items():
        di_g.add_edge(u, v, **attrs)

    return di_g


def fetch_campus_graph(
    location_query: Optional[str] = None,
    center_point: Optional[Tuple[float, float]] = None,
    dist: int = DEFAULT_CAMPUS_RADIUS_METERS,
    bbox: Optional[Tuple[float, float, float, float]] = None,
    mode: str = DEFAULT_NETWORK_MODE,
    cache_path: Optional[Path] = None,
    force_reload: bool = False,
) -> Tuple[nx.DiGraph, Dict[int, Tuple[float, float]], Dict[int, int]]:
    """Fetch and preprocess campus street network with disk caching (FR-1.1, FR-1.4).

    Attempts to load a cached .graphml from disk first. If missing or force_reload is True,
    queries OpenStreetMap via OSMnx, simplifies the graph, and persists to disk.

    Args:
        location_query: Bounding place query (e.g. 'Madanapalle, Andhra Pradesh, India').
        center_point: Optional (latitude, longitude) center coordinate.
        dist: Search radius in meters around center_point.
        bbox: Bounding box tuple (north, south, east, west).
        mode: Network routing mode ('walk' or 'drive').
        cache_path: File path for caching graphml.
        force_reload: Force re-download even if cache exists.

    Returns:
        Tuple of:
            - Simplified networkx.DiGraph
            - node_coords: Dict[node_id, (lat, lon)]
            - component_map: Dict[node_id, component_id] (Weakly Connected Component)
    """
    if cache_path is None:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_path = CACHE_DIR / f"{mode}_{DEFAULT_CACHE_FILENAME}"

    raw_multi_g = None

    if not force_reload and cache_path.exists():
        try:
            raw_multi_g = ox.load_graphml(filepath=cache_path)
        except Exception:
            raw_multi_g = None

    if raw_multi_g is None:
        # Configure osmnx settings
        ox.settings.use_cache = True
        ox.settings.log_console = False

        if bbox is not None:
            north, south, east, west = bbox
            raw_multi_g = ox.graph_from_bbox(
                bbox=(north, south, east, west),
                network_type=mode,
                simplify=True,
            )
        elif center_point is not None:
            raw_multi_g = ox.graph_from_point(
                center_point,
                dist=dist,
                network_type=mode,
                simplify=True,
            )
        elif location_query is not None:
            try:
                raw_multi_g = ox.graph_from_place(
                    location_query,
                    network_type=mode,
                    simplify=True,
                )
            except Exception:
                # Fallback to campus center point if place polygon resolution fails
                from src.config import DEFAULT_CAMPUS_COORDS
                raw_multi_g = ox.graph_from_point(
                    DEFAULT_CAMPUS_COORDS,
                    dist=dist,
                    network_type=mode,
                    simplify=True,
                )
        else:
            from src.config import DEFAULT_CAMPUS_COORDS
            raw_multi_g = ox.graph_from_point(
                DEFAULT_CAMPUS_COORDS,
                dist=dist,
                network_type=mode,
                simplify=True,
            )

        # Persist raw graph to disk cache
        ox.save_graphml(raw_multi_g, filepath=cache_path)

    # Simplify MultiDiGraph to DiGraph with min(length) deduplication
    simplified_g = simplify_multigraph_to_digraph(raw_multi_g)

    # Pre-extract coordinate lookup map: node_id -> (lat, lon)
    node_coords = {
        node: (float(data["y"]), float(data["x"]))
        for node, data in simplified_g.nodes(data=True)
    }

    # Precompute Weakly Connected Components for instant connectivity pre-checking (FR-3.6)
    component_map = {}
    for cid, comp in enumerate(nx.weakly_connected_components(simplified_g)):
        for node in comp:
            component_map[node] = cid

    return simplified_g, node_coords, component_map
