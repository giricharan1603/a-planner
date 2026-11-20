"""CLI runner: benchmark A* vs Dijkstra and export route map."""

import argparse
import json
import sys
from pathlib import Path

from router import astar, dijkstra, load_campus_graph, build_coord_index, snap_to_node


def load_landmarks(path: str = "data/landmarks.json") -> dict:
    with open(path, encoding="utf-8") as f:
        return {lm["landmark_id"]: lm for lm in json.load(f)}


def generate_map(G, coords, path, sl, tl, out="route_map.html"):
    """Generate Folium HTML map with single multi-polyline for background."""
    import folium

    pts = [(sl["latitude"], sl["longitude"])]
    pts.extend([(coords[n][0], coords[n][1]) for n in path])
    pts.append((tl["latitude"], tl["longitude"]))

    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    m = folium.Map(location=[cx, cy], zoom_start=17, tiles="OpenStreetMap")

    # Single multi-polyline for all background roads
    bg = [[(coords[u][0], coords[u][1]), (coords[v][0], coords[v][1])] for u, v in G.edges()]
    for seg in bg:
        folium.PolyLine(seg, color="#CCC", weight=1.5, opacity=0.6).add_to(m)

    folium.PolyLine(pts, color="#1E88E5", weight=5, opacity=0.9).add_to(m)
    folium.Marker(
        (sl["latitude"], sl["longitude"]),
        popup=f"Start: {sl['name']}<br>GPS: {sl['latitude']:.5f}, {sl['longitude']:.5f}",
        icon=folium.Icon(color="green", icon="play", prefix="fa"),
    ).add_to(m)
    folium.Marker(
        (tl["latitude"], tl["longitude"]),
        popup=f"Dest: {tl['name']}<br>GPS: {tl['latitude']:.5f}, {tl['longitude']:.5f}",
        icon=folium.Icon(color="red", icon="flag", prefix="fa"),
    ).add_to(m)
    m.save(out)
    print(f"[+] Map saved: {out}")


def main():
    if sys.stdout.encoding != "utf-8":
        try: sys.stdout.reconfigure(encoding="utf-8")
        except Exception: pass

    ap = argparse.ArgumentParser(description="Campus Route Planner (A* vs Dijkstra)")
    ap.add_argument("--start", default="MITS_MAIN_GATE")
    ap.add_argument("--target", default="MITS_SPORTS")
    ap.add_argument("--all", action="store_true", help="Benchmark all campus landmark pairs")
    ap.add_argument("--serve", action="store_true", help="Start web dashboard server")
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()

    if args.serve:
        from server import run_server
        run_server(port=args.port)
        return

    landmarks = load_landmarks()

    if args.all:
        import math
        from tabulate import tabulate
        G = load_campus_graph()
        coords = build_coord_index(G)
        lids = list(landmarks.keys())
        rows = []
        for i in range(len(lids) - 1):
            sid, tid = lids[i], lids[i + 1]
            sn, _ = snap_to_node(coords, landmarks[sid]["latitude"], landmarks[sid]["longitude"])
            tn, _ = snap_to_node(coords, landmarks[tid]["latitude"], landmarks[tid]["longitude"])
            dd, _, nd, _ = dijkstra(G, sn, tn)
            da, _, na, _ = astar(G, sn, tn, coords)
            prune = ((nd - na) / nd * 100) if nd > 0 else 0.0
            opt = "100% (Pass)" if math.isclose(dd, da, rel_tol=1e-3) else "Mismatch"
            rows.append([f"{sid} -> {tid}", f"{da:.1f} m", nd, na, f"{prune:+.1f}%", opt])
        print("\n" + tabulate(rows, headers=["Route Pair", "Distance", "Dijkstra Nodes", "A* Nodes", "Pruning", "Optimality"], tablefmt="grid"))
        return
    if args.start not in landmarks or args.target not in landmarks:
        print(f"Error: Invalid IDs. Available: {list(landmarks.keys())}")
        return

    sl, tl = landmarks[args.start], landmarks[args.target]
    print(f"Origin:      {sl['name']} (GPS: {sl['latitude']:.5f}, {sl['longitude']:.5f})")
    print(f"Destination: {tl['name']} (GPS: {tl['latitude']:.5f}, {tl['longitude']:.5f})")

    G = load_campus_graph()
    coords = build_coord_index(G)
    print(f"Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    sn, d1 = snap_to_node(coords, sl["latitude"], sl["longitude"])
    tn, d2 = snap_to_node(coords, tl["latitude"], tl["longitude"])
    print(f"Snapped: start={sn} ({d1:.0f}m), dest={tn} ({d2:.0f}m)")

    dd, pd, nd, td = dijkstra(G, sn, tn)
    da, pa, na, ta = astar(G, sn, tn, coords)
    prune = ((nd - na) / nd * 100) if nd > 0 else 0

    from tabulate import tabulate
    print("\n" + tabulate([
        ["Distance", f"{dd:.2f} m", f"{da:.2f} m"],
        ["Nodes Expanded", nd, na],
        ["Time", f"{td:.2f} ms", f"{ta:.2f} ms"],
        ["Path Nodes", len(pd), len(pa)],
        ["Pruning", "", f"{prune:.1f}%"],
    ], headers=["Metric", "Dijkstra", "A*"], tablefmt="grid"))

    generate_map(G, coords, pa, sl, tl)

    with open("route_summary.json", "w", encoding="utf-8") as f:
        json.dump({"start": args.start, "target": args.target,
                   "distance_m": round(da, 2), "nodes_astar": na,
                   "nodes_dijkstra": nd, "pruning_pct": round(prune, 2)}, f, indent=2)
    print("[+] Summary: route_summary.json")


if __name__ == "__main__":
    main()
