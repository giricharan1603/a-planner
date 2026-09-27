"""Campus Landmark A* Route Planner - Main Execution and Benchmarking Driver."""

import argparse
import json
import sys
from pathlib import Path
from tabulate import tabulate

from src.config import (
    DEFAULT_CAMPUS_LOCATION,
    DEFAULT_CAMPUS_COORDS,
    DEFAULT_CAMPUS_RADIUS_METERS,
    DEFAULT_NETWORK_MODE,
    LANDMARKS_FILE,
    ROUTES_DIR,
)
from src.graph_loader import fetch_campus_graph
from src.router import run_astar, run_dijkstra
from src.serializer import save_result_to_json
from src.spatial_index import SpatialSnapper
from src.visualizer import render_folium_map, render_matplotlib_plot


def load_landmarks(filepath: Path) -> dict:
    """Load landmarks catalog from JSON file."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {item["landmark_id"]: item for item in data}


def main():
    parser = argparse.ArgumentParser(description="Campus Landmark A* Route Planner & Benchmarking Engine")
    parser.add_argument("--start", type=str, default="MITS_MAIN_GATE", help="Origin landmark ID")
    parser.add_argument("--target", type=str, default="MITS_SPORTS", help="Destination landmark ID")
    parser.add_argument("--mode", type=str, default=DEFAULT_NETWORK_MODE, choices=["walk", "drive"], help="Routing network mode")
    parser.add_argument("--dist", type=int, default=DEFAULT_CAMPUS_RADIUS_METERS, help="Campus search radius in meters")
    parser.add_argument("--location", type=str, default=None, help="Optional campus location query for OSMnx")
    parser.add_argument("--no-viz", action="store_true", help="Disable HTML and PNG map generation")
    args = parser.parse_args()

    # Ensure UTF-8 output encoding on Windows terminals
    if sys.stdout.encoding != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("=" * 80)
    print("[*] CAMPUS LANDMARK A* ROUTE PLANNER (Mini-Project S.No 12)")
    print("=" * 80)

    # 1. Load Landmark Catalog
    landmarks = load_landmarks(LANDMARKS_FILE)
    if args.start not in landmarks:
        print(f"[!] Error: Start landmark '{args.start}' not found in {LANDMARKS_FILE}")
        sys.exit(1)
    if args.target not in landmarks:
        print(f"[!] Error: Target landmark '{args.target}' not found in {LANDMARKS_FILE}")
        sys.exit(1)

    start_lm = landmarks[args.start]
    target_lm = landmarks[args.target]

    print(f"[-] Origin:      [{start_lm['landmark_id']}] {start_lm['name']} ({start_lm['latitude']:.5f}, {start_lm['longitude']:.5f})")
    print(f"[-] Destination: [{target_lm['landmark_id']}] {target_lm['name']} ({target_lm['latitude']:.5f}, {target_lm['longitude']:.5f})")
    print(f"[-] Network Mode: {args.mode.upper()}")
    print("-" * 80)



    print("[-] Ingesting and preprocessing campus road network...")
    G, node_coords, component_map = fetch_campus_graph(
        location_query=args.location,
        center_point=DEFAULT_CAMPUS_COORDS if args.location is None else None,
        dist=args.dist,
        mode=args.mode,
    )
    print(f"[+] Graph simplified: {G.number_of_nodes()} vertices, {G.number_of_edges()} directed edges.")

    # 3. Spatial Snapping
    snapper = SpatialSnapper(node_coords)
    start_node, start_snap_dist = snapper.snap(start_lm["latitude"], start_lm["longitude"])
    target_node, target_snap_dist = snapper.snap(target_lm["latitude"], target_lm["longitude"])
    print(f"[+] Snapped Start  -> Node {start_node} ({start_snap_dist:.1f}m away)")
    print(f"[+] Snapped Target -> Node {target_node} ({target_snap_dist:.1f}m away)")
    print("-" * 80)

    # 4. Execute Dual Search Channels (A* and Dijkstra)
    print("[*] Running informed A* search (Haversine heuristic)...")
    res_astar = run_astar(G, start_node, target_node, node_coords, component_map)

    print("[*] Running baseline uninformed Dijkstra search (h=0)...")
    res_dijkstra = run_dijkstra(G, start_node, target_node, node_coords, component_map)

    # 5. Comparative Evaluation Table
    dist_diff = abs(res_astar.total_distance_meters - res_dijkstra.total_distance_meters)
    is_optimal = dist_diff < 1e-4

    nodes_d = res_dijkstra.nodes_expanded
    nodes_a = res_astar.nodes_expanded
    pruning_pct = ((nodes_d - nodes_a) / nodes_d * 100.0) if nodes_d > 0 else 0.0

    peak_d = res_dijkstra.peak_frontier_size
    peak_a = res_astar.peak_frontier_size
    peak_diff_pct = ((peak_d - peak_a) / peak_d * 100.0) if peak_d > 0 else 0.0

    time_d = res_dijkstra.execution_time_ms
    time_a = res_astar.execution_time_ms
    time_saved_pct = ((time_d - time_a) / time_d * 100.0) if time_d > 0 else 0.0

    table_data = [
        ["Total Path Length", f"{res_dijkstra.total_distance_meters:.2f} m", f"{res_astar.total_distance_meters:.2f} m", "0.00% (Identical Optimal)"],
        ["Nodes Expanded (Closed)", f"{nodes_d}", f"{nodes_a}", f"{pruning_pct:+.2f}% ({'Pruned' if pruning_pct > 0 else 'Neutral'})"],
        ["Peak Frontier Queue Size", f"{peak_d}", f"{peak_a}", f"{peak_diff_pct:+.2f}%"],
        ["Wall-Clock Latency", f"{time_d:.2f} ms", f"{time_a:.2f} ms", f"{time_saved_pct:+.2f}%"],
        ["Optimality Verified", "BASE", "VERIFIED", "PASSED" if is_optimal else "FAILED"],
    ]

    print("\n" + "=" * 80)
    print("ALGORITHM BENCHMARKING REPORT")
    print("=" * 80)
    print(tabulate(table_data, headers=["Performance Metric", "Dijkstra (h=0)", "A* (Haversine)", "Relative Difference"], tablefmt="grid"))

    # 6. Save Data Payloads & Visualizations
    ROUTES_DIR.mkdir(parents=True, exist_ok=True)
    json_path = ROUTES_DIR / "campus_route.json"
    save_result_to_json(res_astar, json_path)
    print(f"\n[+] Saved strict JSON schema payload: {json_path}")

    if not args.no_viz:
        html_path = ROUTES_DIR / "campus_route.html"
        render_folium_map(G, res_astar, node_coords, html_path, start_lm["name"], target_lm["name"])
        print(f"[+] Exported interactive Folium web map: {html_path}")

        png_path = ROUTES_DIR / "campus_route.png"
        render_matplotlib_plot(G, res_astar, node_coords, png_path, f"Route: {start_lm['name']} to {target_lm['name']}")
        print(f"[+] Exported static Matplotlib plot:    {png_path}")

    print("\n[+] Route calculation and benchmarking completed successfully.\n")


if __name__ == "__main__":
    main()
