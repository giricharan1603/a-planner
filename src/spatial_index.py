"""Spatial Indexing and Coordinate Snapping Engine (FR-2.1, FR-2.2, FR-2.3)."""

import math
import warnings
from typing import Dict, List, Tuple
import numpy as np
from scipy.spatial import KDTree

from src.config import SNAPPING_THRESHOLD_METERS
from src.exceptions import SnappingThresholdWarning
from src.heuristic import haversine_distance


class SpatialSnapper:
    """Snaps arbitrary geographical coordinates to the nearest graph node via 3D ECEF KD-Tree.

    Converts (lat, lon) to 3D Cartesian coordinates (x, y, z) on a unit sphere to ensure
    Euclidean KD-Tree queries are strictly monotonic with Great-Circle spherical distance.
    """

    def __init__(self, node_coords: Dict[int, Tuple[float, float]]):
        """Initialize the spatial index.

        Args:
            node_coords: Mapping of node_id -> (lat, lon) in decimal degrees.
        """
        self.node_ids: List[int] = list(node_coords.keys())
        self.node_coords = node_coords

        # Convert spherical (lat, lon) to 3D Cartesian (x, y, z) on unit sphere
        cartesian_points = []
        for nid in self.node_ids:
            lat, lon = node_coords[nid]
            phi = math.radians(lat)
            theta = math.radians(lon)
            x = math.cos(phi) * math.cos(theta)
            y = math.cos(phi) * math.sin(theta)
            z = math.sin(phi)
            cartesian_points.append((x, y, z))

        self.tree = KDTree(np.array(cartesian_points))

    def snap(self, lat: float, lon: float, threshold_meters: float = SNAPPING_THRESHOLD_METERS) -> Tuple[int, float]:
        """Snap an input coordinate to the nearest valid graph node.

        Args:
            lat: Input latitude in decimal degrees.
            lon: Input longitude in decimal degrees.
            threshold_meters: Warning threshold in meters (default 250m).

        Returns:
            Tuple of (snapped_node_id, snap_distance_in_meters).
        """
        phi = math.radians(lat)
        theta = math.radians(lon)
        target_xyz = np.array([
            math.cos(phi) * math.cos(theta),
            math.cos(phi) * math.sin(theta),
            math.sin(phi)
        ])

        _, idx = self.tree.query(target_xyz, k=1)
        nearest_node = self.node_ids[idx]
        node_lat, node_lon = self.node_coords[nearest_node]

        distance_meters = haversine_distance(lat, lon, node_lat, node_lon)

        if distance_meters > threshold_meters:
            warnings.warn(
                f"Resolved node {nearest_node} is {distance_meters:.1f}m away from ({lat:.5f}, {lon:.5f}), "
                f"exceeding the safety threshold of {threshold_meters}m.",
                category=SnappingThresholdWarning,
                stacklevel=2,
            )

        return nearest_node, distance_meters
