"""
server.py - Web Server & REST API for Campus Landmark A* Route Planner
Lightweight, zero-dependency server using Python's standard library.
Serves the institutional dashboard, Leaflet map client, privacy/terms pages, and route APIs.
"""

import json
import mimetypes
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from router import astar, dijkstra, load_campus_graph, snap_to_node

BASE_DIR = Path(__file__).resolve().parent
PUBLIC_DIR = BASE_DIR / "public"
LANDMARKS_FILE = BASE_DIR / "data" / "landmarks.json"

# Load graph and landmarks once at startup
print("[*] Initializing Campus Network Graph...")
CAMPUS_GRAPH = load_campus_graph()
print(f"[+] Loaded {CAMPUS_GRAPH.number_of_nodes()} intersections and {CAMPUS_GRAPH.number_of_edges()} paths.")

with open(LANDMARKS_FILE, "r", encoding="utf-8") as f:
    LANDMARKS_DATA = json.load(f)
LANDMARKS_DICT = {item["landmark_id"]: item for item in LANDMARKS_DATA}

# Pre-extract road network edge coordinates for background map rendering
NETWORK_EDGES = [
    [
        [CAMPUS_GRAPH.nodes[u]["y"], CAMPUS_GRAPH.nodes[u]["x"]],
        [CAMPUS_GRAPH.nodes[v]["y"], CAMPUS_GRAPH.nodes[v]["x"]],
    ]
    for u, v in CAMPUS_GRAPH.edges()
]


class RouteAppHandler(SimpleHTTPRequestHandler):
    """Handles static files, HTML pages, and JSON API routes."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(PUBLIC_DIR), **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path in ("/", "/index.html"):
            self._serve_file(PUBLIC_DIR / "index.html", "text/html")
        elif path in ("/privacy", "/privacy.html"):
            self._serve_file(PUBLIC_DIR / "privacy.html", "text/html")
        elif path in ("/terms", "/terms.html"):
            self._serve_file(PUBLIC_DIR / "terms.html", "text/html")
        elif path in ("/favicon.svg", "/favicon.ico"):
            self._serve_file(PUBLIC_DIR / "favicon.svg", "image/svg+xml")
        elif path == "/api/landmarks":
            self._send_json(LANDMARKS_DATA)
        else:
            # Fallback to standard static file serving from public/
            target = PUBLIC_DIR / path.lstrip("/")
            if target.exists() and target.is_file():
                mime, _ = mimetypes.guess_type(str(target))
                self._serve_file(target, mime or "application/octet-stream")
            else:
                self.send_error(404, "Page Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/route":
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length).decode("utf-8")
                payload = json.loads(body)

                start_id = payload.get("start", "MITS_MAIN_GATE")
                target_id = payload.get("target", "MITS_SPORTS")

                if start_id not in LANDMARKS_DICT or target_id not in LANDMARKS_DICT:
                    self._send_json({"error": "Invalid landmark ID"}, status=400)
                    return

                start_lm = LANDMARKS_DICT[start_id]
                target_lm = LANDMARKS_DICT[target_id]

                start_node, d1 = snap_to_node(CAMPUS_GRAPH, start_lm["latitude"], start_lm["longitude"])
                target_node, d2 = snap_to_node(CAMPUS_GRAPH, target_lm["latitude"], target_lm["longitude"])

                # Run both algorithms
                dist_d, path_d, nodes_d, time_d = dijkstra(CAMPUS_GRAPH, start_node, target_node)
                dist_a, path_a, nodes_a, time_a = astar(CAMPUS_GRAPH, start_node, target_node)

                pruning_pct = ((nodes_d - nodes_a) / nodes_d * 100.0) if nodes_d > 0 else 0.0

                path_coords = [
                    [CAMPUS_GRAPH.nodes[n]["y"], CAMPUS_GRAPH.nodes[n]["x"]]
                    for n in path_a
                ]

                response_data = {
                    "status": "SUCCESS",
                    "origin": {
                        "id": start_id,
                        "name": start_lm["name"],
                        "lat": start_lm["latitude"],
                        "lon": start_lm["longitude"],
                        "node_id": start_node,
                        "snap_dist": round(d1, 1),
                    },
                    "destination": {
                        "id": target_id,
                        "name": target_lm["name"],
                        "lat": target_lm["latitude"],
                        "lon": target_lm["longitude"],
                        "node_id": target_node,
                        "snap_dist": round(d2, 1),
                    },
                    "dijkstra": {
                        "distance_meters": round(dist_d, 2),
                        "nodes_expanded": nodes_d,
                        "elapsed_ms": round(time_d, 2),
                    },
                    "astar": {
                        "distance_meters": round(dist_a, 2),
                        "nodes_expanded": nodes_a,
                        "elapsed_ms": round(time_a, 2),
                    },
                    "pruning_percentage": round(pruning_pct, 2),
                    "path_coordinates": path_coords,
                    "network_edges": NETWORK_EDGES,
                }

                self._send_json(response_data)
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)
        else:
            self.send_error(404, "Endpoint Not Found")

    def _serve_file(self, filepath: Path, content_type: str):
        try:
            with open(filepath, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(content)
        except Exception:
            self.send_error(500, "Error reading file")

    def _send_json(self, data: dict, status: int = 200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)


def run_server(port: int = 8000):
    server = ThreadingHTTPServer(("127.0.0.1", port), RouteAppHandler)
    print("=" * 75)
    print(f"[*] Campus Landmark Route Planner Web Application")
    print(f"[+] Server running at: http://127.0.0.1:{port}/")
    print(f"[+] Dashboard:         http://127.0.0.1:{port}/")
    print(f"[+] Privacy Policy:    http://127.0.0.1:{port}/privacy")
    print(f"[+] Terms of Service:  http://127.0.0.1:{port}/terms")
    print("=" * 75)
    print("Press Ctrl+C to stop the server.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Server shutdown cleanly.")
        server.server_close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run Campus Landmark Route Planner Web Server")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind server (default: 8000)")
    args = parser.parse_args()
    run_server(port=args.port)
