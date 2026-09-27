"""Static Matplotlib and Interactive Folium Web Map Renderers (FR-5.1, FR-5.2)."""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
import folium
import matplotlib.pyplot as plt
import networkx as nx

from src.router import SearchResult


def render_folium_map(
    G: nx.DiGraph,
    result: SearchResult,
    node_coords: Dict[int, Tuple[float, float]],
    output_html_path: Path,
    start_label: str = "Origin",
    target_label: str = "Destination",
) -> Path:
    """Render and export an interactive Folium web map.

    Features:
        - Light network overlay for context.
        - High-contrast route polyline (#1E88E5).
        - Green Marker for Origin.
        - Red Marker for Destination.
        - Popups with distance and runtime statistics.

    Args:
        G: Simplified networkx.DiGraph.
        result: SearchResult from A* or Dijkstra.
        node_coords: Mapping of node_id -> (lat, lon).
        output_html_path: Output HTML file path.
        start_label: Landmark or label for start point.
        target_label: Landmark or label for target point.

    Returns:
        Path to the saved HTML file.
    """
    output_html_path.parent.mkdir(parents=True, exist_ok=True)

    path_coords = [(c["lat"], c["lon"]) for c in result.path_coordinates]

    if path_coords:
        center_lat = sum(c[0] for c in path_coords) / len(path_coords)
        center_lon = sum(c[1] for c in path_coords) / len(path_coords)
    else:
        # Default fallback
        first_node = list(node_coords.values())[0]
        center_lat, center_lon = first_node

    fmap = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=17,
        tiles="OpenStreetMap",
    )

    # Subtle background network paths
    for u, v in G.edges():
        u_lat, u_lon = node_coords[u]
        v_lat, v_lon = node_coords[v]
        folium.PolyLine(
            locations=[(u_lat, u_lon), (v_lat, v_lon)],
            color="#CCCCCC",
            weight=1.5,
            opacity=0.6,
        ).add_to(fmap)

    # High-contrast optimal route polyline
    folium.PolyLine(
        locations=path_coords,
        color="#1E88E5",
        weight=5.5,
        opacity=0.9,
        tooltip=f"{result.algorithm} Route: {result.total_distance_meters:.1f} m",
    ).add_to(fmap)

    # Origin marker (Green Pin)
    if path_coords:
        start_lat, start_lon = path_coords[0]
        folium.Marker(
            location=[start_lat, start_lon],
            popup=f"<b>Start:</b> {start_label}<br>Node: {result.start_node_id}",
            icon=folium.Icon(color="green", icon="play", prefix="fa"),
        ).add_to(fmap)

        # Destination marker (Red Pin)
        target_lat, target_lon = path_coords[-1]
        folium.Marker(
            location=[target_lat, target_lon],
            popup=(
                f"<b>Destination:</b> {target_label}<br>"
                f"Node: {result.target_node_id}<br>"
                f"Distance: {result.total_distance_meters:.1f}m<br>"
                f"Nodes Expanded: {result.nodes_expanded}<br>"
                f"Time: {result.execution_time_ms:.2f}ms"
            ),
            icon=folium.Icon(color="red", icon="flag", prefix="fa"),
        ).add_to(fmap)

    fmap.save(str(output_html_path))
    return output_html_path


def render_matplotlib_plot(
    G: nx.DiGraph,
    result: SearchResult,
    node_coords: Dict[int, Tuple[float, float]],
    output_png_path: Path,
    title: str = "Campus A* Route Path",
) -> Path:
    """Render static high-resolution plot using Matplotlib (FR-5.1)."""
    output_png_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 8), dpi=200)

    # Draw all graph edges in light gray
    for u, v in G.edges():
        u_lat, u_lon = node_coords[u]
        v_lat, v_lon = node_coords[v]
        ax.plot([u_lon, v_lon], [u_lat, v_lat], color="#B0BEC5", linewidth=0.8, alpha=0.7)

    # Highlight optimal route in bold blue
    if result.path_coordinates:
        path_lons = [c["lon"] for c in result.path_coordinates]
        path_lats = [c["lat"] for c in result.path_coordinates]
        ax.plot(path_lons, path_lats, color="#0D47A1", linewidth=3.0, label=f"Path ({result.total_distance_meters:.1f}m)")

        # Start and Target Markers
        ax.scatter([path_lons[0]], [path_lats[0]], color="#2E7D32", s=100, zorder=5, label="Start")
        ax.scatter([path_lons[-1]], [path_lats[-1]], color="#C62828", s=100, zorder=5, label="Destination")

    ax.set_title(f"{title} - Distance: {result.total_distance_meters:.1f}m (Nodes: {result.nodes_expanded})")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.legend(loc="upper left")
    plt.tight_layout()

    plt.savefig(str(output_png_path))
    plt.close(fig)
    return output_png_path
