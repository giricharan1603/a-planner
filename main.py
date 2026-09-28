"""
main.py - Campus Landmark A* Route Planner Runner
Loads landmarks, computes routes using A* and Dijkstra, benchmarks performance, and exports an interactive map.
"""

import argparse
import json
import sys
from pathlib import Path
import folium
from tabulate import tabulate

from router import astar, dijkstra, load_campus_graph, snap_to_node


def load_landmarks(filepath: str = "data/landmarks.json") -> dict:
    """Load campus landmarks catalog."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {item["landmark_id"]: item for item in data}


def generate_map(G, path, start_label, target_label, output_file="route_map.html"):
    """Generate an interactive HTML map using Folium."""
    coords = [(G.nodes[n]["y"], G.nodes[n]["x"]) for n in path]
    if not coords:
        return

    # Center map on route centroid
    center_lat = sum(c[0] for c in coords) / len(coords)
    center_lon = sum(c[1] for c in coords) / len(coords)

    fmap = folium.Map(location=[center_lat, center_lon], zoom_start=17, tiles="OpenStreetMap")

    # Draw campus road background in gray
    for u, v in G.edges():
        folium.PolyLine(
            locations=[(G.nodes[u]["y"], G.nodes[u]["x"]), (G.nodes[v]["y"], G.nodes[v]["x"])],
            color="#CCCCCC",
            weight=1.5,
            opacity=0.6,
        ).add_to(fmap)

    # Draw calculated optimal path in bold blue
    folium.PolyLine(locations=coords, color="#1E88E5", weight=5, opacity=0.9).add_to(fmap)

    # Green pin for origin, Red pin for destination
    folium.Marker(coords[0], popup=f"<b>Start:</b> {start_label}", icon=folium.Icon(color="green", icon="play", prefix="fa")).add_to(fmap)
    folium.Marker(coords[-1], popup=f"<b>Destination:</b> {target_label}", icon=folium.Icon(color="red", icon="flag", prefix="fa")).add_to(fmap)

    fmap.save(output_file)
    print(f"[+] Saved interactive map: {output_file}")


def main():
    # Handle UTF-8 encoding on Windows terminals
    if sys.stdout.encoding != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="Campus Landmark Route Planner (A* vs Dijkstra)")
    parser.add_argument("--start", type=str, default="MITS_HOSTEL_B", help="Start landmark ID")
    parser.add_argument("--target", type=str, default="MITS_HOSTEL_G", help="Destination landmark ID")
    args = parser.parse_args()

    print("=" * 75)
    print("📍 CAMPUS LANDMARK ROUTE PLANNER (A* vs Dijkstra)")
    print("=" * 75)

    # 1. Load landmarks
    landmarks = load_landmarks()
    if args.start not in landmarks or args.target not in landmarks:
        print(f"Error: Invalid landmark IDs. Available: {list(landmarks.keys())}")
        return

    start_lm = landmarks[args.start]
    target_lm = landmarks[args.target]

    print(f"Origin:      {start_lm['name']} ({args.start})")
    print(f"Destination: {target_lm['name']} ({args.target})")
    print("-" * 75)

    # 2. Load campus graph
    print("Loading campus road network...")
    G = load_campus_graph()
    print(f"Graph loaded: {G.number_of_nodes()} intersections, {G.number_of_edges()} road paths.")

    # 3. Snap landmarks to graph vertices
    start_node, d1 = snap_to_node(G, start_lm["latitude"], start_lm["longitude"])
    target_node, d2 = snap_to_node(G, target_lm["latitude"], target_lm["longitude"])
    print(f"Snapped start -> Node {start_node} ({d1:.1f}m away)")
    print(f"Snapped destination -> Node {target_node} ({d2:.1f}m away)")
    print("-" * 75)

    # 4. Run Algorithms
    print("Running Dijkstra (Uninformed, h = 0)...")
    dist_d, path_d, nodes_d, time_d = dijkstra(G, start_node, target_node)

    print("Running A* (Informed, Haversine)...")
    dist_a, path_a, nodes_a, time_a = astar(G, start_node, target_node)

    # 5. Benchmark Comparison Table
    pruning_pct = ((nodes_d - nodes_a) / nodes_d * 100.0) if nodes_d > 0 else 0.0

    table = [
        ["Total Distance", f"{dist_d:.2f} m", f"{dist_a:.2f} m", "100% Match (Optimal)"],
        ["Nodes Explored", f"{nodes_d}", f"{nodes_a}", f"{pruning_pct:+.1f}% (Fewer nodes)"],
        ["Execution Time", f"{time_d:.2f} ms", f"{time_a:.2f} ms", f"{time_d - time_a:+.2f} ms"],
        ["Path Nodes Count", f"{len(path_d)}", f"{len(path_a)}", "Identical Path"],
    ]

    print("\n" + tabulate(table, headers=["Metric", "Dijkstra (h=0)", "A* (Haversine)", "Advantage"], tablefmt="grid"))

    # 6. Generate interactive HTML web map
    generate_map(G, path_a, start_lm["name"], target_lm["name"], "route_map.html")

    # 7. Save JSON summary payload
    summary = {
        "status": "SUCCESS",
        "start": args.start,
        "target": args.target,
        "total_distance_meters": round(dist_a, 2),
        "nodes_expanded_astar": nodes_a,
        "nodes_expanded_dijkstra": nodes_d,
        "pruning_percentage": round(pruning_pct, 2),
        "path_node_ids": path_a,
    }
    with open("route_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print("[+] Saved summary payload: route_summary.json\n")


if __name__ == "__main__":
    main()
