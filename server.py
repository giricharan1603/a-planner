"""Web server and REST API for Campus Route Planner."""

import json
import mimetypes
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from router import astar, dijkstra, load_campus_graph, build_coord_index, snap_to_node

BASE = Path(__file__).resolve().parent
PUBLIC = BASE / "public"

# --- Startup: load once ---
print("[*] Loading campus network...")
GRAPH = load_campus_graph()
COORDS = build_coord_index(GRAPH)
print(f"[+] {GRAPH.number_of_nodes()} nodes, {GRAPH.number_of_edges()} edges.")

with open(BASE / "data" / "landmarks.json", encoding="utf-8") as f:
    LANDMARKS_LIST = json.load(f)
LANDMARKS = {lm["landmark_id"]: lm for lm in LANDMARKS_LIST}

# Pre-snap all landmarks to graph nodes
SNAPPED = {}
for lid, lm in LANDMARKS.items():
    node, dist = snap_to_node(COORDS, lm["latitude"], lm["longitude"])
    SNAPPED[lid] = {"node": node, "snap_dist": round(dist, 1)}

# Pre-serialize network edges (sent once via GET /api/network)
NETWORK_EDGES = [[[COORDS[u][0], COORDS[u][1]], [COORDS[v][0], COORDS[v][1]]] for u, v in GRAPH.edges()]
NETWORK_JSON = json.dumps(NETWORK_EDGES).encode("utf-8")

def _read_file(path: Path) -> bytes:
    return path.read_bytes()


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(PUBLIC), **kw)

    def log_message(self, fmt, *args):
        pass  # Suppress per-request logging for performance

    def do_GET(self):
        p = urlparse(self.path).path
        if p in ("/", "/index.html"):
            self._file(PUBLIC / "index.html", "text/html")
        elif p in ("/privacy", "/privacy.html"):
            self._file(PUBLIC / "privacy.html", "text/html")
        elif p in ("/terms", "/terms.html"):
            self._file(PUBLIC / "terms.html", "text/html")
        elif p in ("/favicon.svg", "/favicon.ico"):
            self._file(PUBLIC / "favicon.svg", "image/svg+xml")
        elif p == "/api/landmarks":
            self._json_bytes(json.dumps(LANDMARKS_LIST).encode())
        elif p == "/api/network":
            self._json_bytes(NETWORK_JSON)
        else:
            target = PUBLIC / p.lstrip("/")
            if target.exists() and target.is_file():
                mime = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
                self._file(target, mime)
            else:
                self.send_error(404)

    def do_POST(self):
        if urlparse(self.path).path != "/api/route":
            self.send_error(404)
            return
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            sid = body.get("start", "MITS_MAIN_GATE")
            tid = body.get("target", "MITS_SPORTS")
            if sid not in LANDMARKS or tid not in LANDMARKS:
                self._json({"error": "Invalid landmark ID"}, 400)
                return

            sn, tn = SNAPPED[sid]["node"], SNAPPED[tid]["node"]
            dd, _, nd, td = dijkstra(GRAPH, sn, tn)
            da, pa, na, ta = astar(GRAPH, sn, tn, COORDS)
            pruning = ((nd - na) / nd * 100) if nd > 0 else 0

            start_lat = LANDMARKS[sid]["latitude"]
            start_lon = LANDMARKS[sid]["longitude"]
            dest_lat = LANDMARKS[tid]["latitude"]
            dest_lon = LANDMARKS[tid]["longitude"]

            path_pts = [[start_lat, start_lon]]
            path_pts.extend([[COORDS[n][0], COORDS[n][1]] for n in pa])
            path_pts.append([dest_lat, dest_lon])

            self._json({
                "status": "SUCCESS",
                "origin": {
                    "id": sid,
                    "name": LANDMARKS[sid]["name"],
                    "lat": start_lat,
                    "lon": start_lon,
                    "snap_dist": SNAPPED[sid]["snap_dist"],
                },
                "destination": {
                    "id": tid,
                    "name": LANDMARKS[tid]["name"],
                    "lat": dest_lat,
                    "lon": dest_lon,
                    "snap_dist": SNAPPED[tid]["snap_dist"],
                },
                "dijkstra": {"distance_meters": round(dd, 2), "nodes_expanded": nd, "elapsed_ms": round(td, 2)},
                "astar": {"distance_meters": round(da, 2), "nodes_expanded": na, "elapsed_ms": round(ta, 2)},
                "pruning_percentage": round(pruning, 2),
                "path_coordinates": path_pts,
            })
        except Exception as e:
            self._json({"error": str(e)}, 500)

    def _file(self, path: Path, ctype: str):
        try:
            data = _read_file(path)
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", len(data))
            self.end_headers()
            self.wfile.write(data)
        except Exception:
            self.send_error(500)

    def _json(self, obj, status=200):
        self._json_bytes(json.dumps(obj).encode(), status)

    def _json_bytes(self, body: bytes, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)


def run_server(port: int = 8000):
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"[+] http://127.0.0.1:{port}/")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Stopped.")
        srv.server_close()


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=8000)
    run_server(port=p.parse_args().port)
