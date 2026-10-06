"""
manual_test.py - Manual Verification & Testing Utility for Campus Route Planner.
Run manually on demand: python manual_test.py [--start ID] [--target ID] [--all]
"""

import argparse
import json
import math
import sys
from tabulate import tabulate

from router import astar, build_coord_index, dijkstra, haversine, load_campus_graph, snap_to_node


def load_landmarks(path: str = "data/landmarks.json") -> dict:
    with open(path, encoding="utf-8") as f:
        return {lm["landmark_id"]: lm for lm in json.load(f)}


def run_manual_test(start_id: str, target_id: str, G, coords, landmarks):
    if start_id not in landmarks or target_id not in landmarks:
        print(f"[-] Invalid landmark ID. Available: {list(landmarks.keys())}")
        return

    orig = landmarks[start_id]
    dest = landmarks[target_id]

    print("\n" + "=" * 70)
    print(f"MANUAL TEST: {orig['name']} -> {dest['name']}")
    print("=" * 70)
    print(f"Origin:      {orig['name']} ({start_id})")
    print(f"             GPS: Lat {orig['latitude']:.5f}, Lon {orig['longitude']:.5f}")
    print(f"Destination: {dest['name']} ({target_id})")
    print(f"             GPS: Lat {dest['latitude']:.5f}, Lon {dest['longitude']:.5f}")
    print("-" * 70)

    sn, d1 = snap_to_node(coords, orig["latitude"], orig["longitude"])
    tn, d2 = snap_to_node(coords, dest["latitude"], dest["longitude"])
    print(f"Snapped Origin:      Node {sn} ({d1:.1f} m from landmark)")
    print(f"Snapped Destination: Node {tn} ({d2:.1f} m from landmark)")
    print("-" * 70)

    dd, pd, nd, td = dijkstra(G, sn, tn)
    da, pa, na, ta = astar(G, sn, tn, coords)
    prune = ((nd - na) / nd * 100) if nd > 0 else 0.0
    match = math.isclose(dd, da, rel_tol=1e-3)

    table = [
        ["Total Distance", f"{dd:.2f} m", f"{da:.2f} m", "100% Match" if match else "MISMATCH"],
        ["Nodes Expanded", f"{nd}", f"{na}", f"{prune:+.1f}% fewer"],
        ["Execution Time", f"{td:.2f} ms", f"{ta:.2f} ms", f"{td - ta:+.2f} ms"],
        ["Path Waypoints", f"{len(pd)}", f"{len(pa)}", "Identical" if len(pd) == len(pa) else "Different"],
    ]
    print(tabulate(table, headers=["Metric", "Dijkstra (h=0)", "A* (Haversine)", "Status"], tablefmt="grid"))
    print("=" * 70 + "\n")


def run_all_manual_checks(G, coords, landmarks):
    print("\n" + "=" * 70)
    print("RUNNING MANUAL ROUTING VALIDATION ACROSS LANDMARK PAIRS")
    print("=" * 70)
    lids = list(landmarks.keys())
    results = []

    for i in range(len(lids) - 1):
        sid = lids[i]
        tid = lids[i + 1]
        sn, _ = snap_to_node(coords, landmarks[sid]["latitude"], landmarks[sid]["longitude"])
        tn, _ = snap_to_node(coords, landmarks[tid]["latitude"], landmarks[tid]["longitude"])
        dd, _, nd, td = dijkstra(G, sn, tn)
        da, _, na, ta = astar(G, sn, tn, coords)
        prune = ((nd - na) / nd * 100) if nd > 0 else 0.0
        is_opt = math.isclose(dd, da, rel_tol=1e-3)
        results.append([f"{sid} -> {tid}", f"{da:.1f}m", f"{nd}", f"{na}", f"{prune:+.1f}%", "PASS" if is_opt else "FAIL"])

    print(tabulate(results, headers=["Route Pair", "Distance", "Dijkstra Nodes", "A* Nodes", "Pruning", "Optimality"], tablefmt="grid"))
    print("=" * 70 + "\n")


def main():
    if sys.stdout.encoding != "utf-8":
        try: sys.stdout.reconfigure(encoding="utf-8")
        except Exception: pass

    parser = argparse.ArgumentParser(description="Manual Route Planner Test Utility")
    parser.add_argument("--start", default="MITS_MAIN_GATE", help="Start landmark ID")
    parser.add_argument("--target", default="MITS_SPORTS", help="Destination landmark ID")
    parser.add_argument("--all", action="store_true", help="Run validation across multiple landmark pairs")
    args = parser.parse_args()

    landmarks = load_landmarks()
    print("[*] Loading campus graph...")
    G = load_campus_graph()
    coords = build_coord_index(G)
    print(f"[+] Loaded {G.number_of_nodes()} intersections, {G.number_of_edges()} paths.")

    if args.all:
        run_all_manual_checks(G, coords, landmarks)
    else:
        run_manual_test(args.start, args.target, G, coords, landmarks)


if __name__ == "__main__":
    main()
