"""Visualization and JSON serialization engine (FR-5, Section 8.2)."""

import json
from pathlib import Path
from typing import Dict, Tuple
import folium
import matplotlib.pyplot as plt
import networkx as nx

from src.router import SearchResult


def save_result_to_json(result: SearchResult, filepath: Path) -> Path:
    """Save result payload strictly conforming to PRD Section 8.2 JSON schema."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "status": result.status,
        "algorithm": result.algorithm,
        "start_node_id": result.start_node_id,
        "target_node_id": result.target_node_id,
        "total_distance_meters": round(result.total_distance_meters, 2),
        "nodes_expanded": result.nodes_expanded,
        "execution_time_ms": round(result.execution_time_ms, 2),
        "path_coordinates": [
            {"lat": round(c["lat"], 6), "lon": round(c["lon"], 6)}
            for c in result.path_coordinates
        ],
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return filepath


def render_folium_map(
    G: nx.DiGraph,
    result: SearchResult,
    node_coords: Dict[int, Tuple[float, float]],
    output_html_path: Path,
    start_label: str = "Origin",
    target_label: str = "Destination",
) -> Path:
    """Render and export interactive Leaflet web map with route overlay (FR-5.2)."""
    output_html_path.parent.mkdir(parents=True, exist_ok=True)
    coords = [(c["lat"], c["lon"]) for c in result.path_coordinates]
    center = (sum(c[0] for c in coords) / len(coords), sum(c[1] for c in coords) / len(coords)) if coords else list(node_coords.values())[0]

    fmap = folium.Map(location=center, zoom_start=17, tiles="OpenStreetMap")

    # Background street network
    for u, v in G.edges():
        folium.PolyLine(
            locations=[node_coords[u], node_coords[v]],
            color="#CCCCCC",
            weight=1.5,
            opacity=0.6,
        ).add_to(fmap)

    # Optimal route polyline
    folium.PolyLine(locations=coords, color="#1E88E5", weight=5.5, opacity=0.9, tooltip=f"Route: {result.total_distance_meters:.1f}m").add_to(fmap)

    if coords:
        folium.Marker(coords[0], popup=f"<b>Start:</b> {start_label}", icon=folium.Icon(color="green", icon="play", prefix="fa")).add_to(fmap)
        folium.Marker(coords[-1], popup=f"<b>Target:</b> {target_label}<br>Dist: {result.total_distance_meters:.1f}m", icon=folium.Icon(color="red", icon="flag", prefix="fa")).add_to(fmap)

    fmap.save(str(output_html_path))
    return output_html_path


def render_matplotlib_plot(
    G: nx.DiGraph,
    result: SearchResult,
    node_coords: Dict[int, Tuple[float, float]],
    output_png_path: Path,
    title: str = "Campus A* Route Path",
) -> Path:
    """Render and export static high-resolution route map (FR-5.1)."""
    output_png_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(9, 7), dpi=200)

    for u, v in G.edges():
        ax.plot([node_coords[u][1], node_coords[v][1]], [node_coords[u][0], node_coords[v][0]], color="#B0BEC5", linewidth=0.8, alpha=0.7)

    if result.path_coordinates:
        lons = [c["lon"] for c in result.path_coordinates]
        lats = [c["lat"] for c in result.path_coordinates]
        ax.plot(lons, lats, color="#0D47A1", linewidth=3.0, label=f"Path ({result.total_distance_meters:.1f}m)")
        ax.scatter([lons[0]], [lats[0]], color="#2E7D32", s=100, zorder=5, label="Start")
        ax.scatter([lons[-1]], [lats[-1]], color="#C62828", s=100, zorder=5, label="Target")

    ax.set_title(f"{title} - Dist: {result.total_distance_meters:.1f}m | Nodes: {result.nodes_expanded}")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.legend(loc="upper left")
    plt.tight_layout()
    plt.savefig(str(output_png_path))
    plt.close(fig)
    return output_png_path
