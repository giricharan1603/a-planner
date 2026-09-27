"""Heuristic calculations for A* pathfinding.

Calculates Great-Circle distance using the Haversine formula (PRD FR-3.3).
Guaranteed to be strictly admissible (h(n) <= h*(n)) and consistent (h(n) <= c(n, a, n') + h(n')).
"""

import math
from typing import Dict, Tuple
from src.config import EARTH_RADIUS_METERS


def haversine_distance(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
    radius: float = EARTH_RADIUS_METERS,
) -> float:
    """Calculate the Great-Circle distance between two points on Earth in meters.

    Args:
        lat1: Latitude of point 1 in decimal degrees.
        lon1: Longitude of point 1 in decimal degrees.
        lat2: Latitude of point 2 in decimal degrees.
        lon2: Longitude of point 2 in decimal degrees.
        radius: Earth radius constant in meters (default: 6,371,000m).

    Returns:
        Great-Circle distance in meters.
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2)
    )
    # Clamp to avoid numerical floating-point errors outside [-1, 1]
    a = min(1.0, max(0.0, a))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    return radius * c


def make_haversine_heuristic(
    target_node: int,
    node_coords: Dict[int, Tuple[float, float]],
    radius: float = EARTH_RADIUS_METERS,
):
    """Factory creating an optimized closure for computing h(n) against a target node.

    Pre-extracts target coordinates to minimize dictionary lookups in the A* inner loop.

    Args:
        target_node: Target graph vertex ID.
        node_coords: Mapping of node_id -> (lat, lon) in decimal degrees.
        radius: Earth radius in meters.

    Returns:
        Callable taking node_id and returning estimated distance in meters.
    """
    target_lat, target_lon = node_coords[target_node]

    def heuristic(node: int) -> float:
        curr_lat, curr_lon = node_coords[node]
        return haversine_distance(curr_lat, curr_lon, target_lat, target_lon, radius)

    return heuristic
