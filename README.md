# Campus Landmark A* Route Planner

**Mini-Project Reference:** S.No 12 (Course Code: 23CSE109 / 23CSE208 - Artificial Intelligence Laboratory)  
**Academic Requirement:** Comparative Benchmarking of Informed A* Search vs Uninformed Dijkstra Baseline on OpenStreetMap Campus Street Networks.

---

## 1. Overview

The **Campus Landmark A* Route Planner** is a specialized geospatial routing and algorithmic benchmarking system. It extracts real-world pedestrian and street topologies from OpenStreetMap (OSM) via OSMnx, snaps campus landmarks using Euclidean and spherical distance metrics, and executes an admissible A* search using the Great-Circle Haversine distance heuristic.

The system benchmarks A* against an uninformed uniform-cost Dijkstra baseline ($h(n) = 0$), quantifying search space pruning, nodes expanded, and execution latency.

---

## 2. Project Structure

```
ai-mini-pjt/
├── data/
│   ├── campus_network.graphml    # Cached campus street network
│   └── landmarks.json            # Campus landmarks with GPS coordinates
├── public/                       # Web application frontend assets
│   ├── index.html                # Main interactive dashboard with coordinate displays
│   ├── privacy.html              # Privacy Policy page
│   ├── terms.html                # Terms of Service page
│   ├── style.css                 # Clean institutional stylesheet
│   ├── app.js                    # Client Leaflet map controller & manual route solver
│   └── favicon.svg               # Custom vector icon
├── router.py                     # Algorithmic core (Haversine, Graph Snapping, Dijkstra, A*)
├── main.py                       # CLI driver (prints benchmark table & exports route_map.html)
├── server.py                     # Zero-dependency local web server & REST API
├── manual_test.py                # Manual testing & validation utility (on-demand execution)
├── requirements.txt              # Pinned Python packages
├── README.md                     # Project documentation
└── .gitignore                    # Version control ignore rules
```

---

## 3. Design Standards & Anti-Pattern Compliance

The web interface is built in strict accordance with professional engineering standards:
* **Custom Branding & Favicon:** Custom vector SVG favicon; zero "Made with AI" tags or badges.
* **Palette:** Grounded daylight palette using slate neutrals (`#f8fafc` canvas, `#ffffff` panels, `#0f172a` text, `#1e40af` primary blue). No purple gradients or rainbow accents.
* **Sharp Geometry:** Clean 6px border radii; zero pill-shaped buttons.
* **Real Interactive Demo & Coordinate Display:** Live Leaflet map displaying real OpenStreetMap tiles, actual footpaths, all campus facility pins with exact GPS coordinates (Latitude, Longitude), live cursor GPS tracking, and route polyline with real-time metric benchmarks.
* **Manual Execution:** Route computation triggers strictly when the user clicks "Compute Route" (no unwanted auto-running).
* **No Marketing Gimmicks:** Zero fake reviews, zero fake counters, zero sparkle icons, and zero em dashes.
* **Legal Transparency:** Dedicated [Privacy Policy](public/privacy.html) and [Terms of Service](public/terms.html) pages included.

---

## 4. How to Run

### Setup Environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Option A: Launch Interactive Web Application
```powershell
python server.py
```
*Or via main CLI:*
```powershell
python main.py --serve
```
Then open **[http://localhost:8000](http://localhost:8000)** in your browser:
- View all campus landmarks and their GPS coordinates directly on the map.
- Select Origin and Destination landmarks to see their coordinates.
- Click **Compute Route** to manually calculate and visualize the optimal path.

### Option B: Run Command-Line Benchmark
```powershell
python main.py
```
Or specify origin and destination landmarks:
```powershell
python main.py --start MITS_HOSTEL_B --target MITS_HOSTEL_G
```

### Option C: Run Manual Verification & Testing
Test a specific pair manually:
```powershell
python manual_test.py --start MITS_MAIN_GATE --target MITS_SPORTS
```
Or run validation across all consecutive campus landmark pairs:
```powershell
python manual_test.py --all
```

---

## 5. Sample Benchmark Output

```
+----------------+------------+-----------+
| Metric         | Dijkstra   | A*        |
+================+============+===========+
| Distance       | 3301.38 m  | 3301.38 m |
+----------------+------------+-----------+
| Nodes Expanded | 76         | 64        |
+----------------+------------+-----------+
| Time           | 0.26 ms    | 0.42 ms   |
+----------------+------------+-----------+
| Path Nodes     | 20         | 20        |
+----------------+------------+-----------+
| Pruning        |            | 15.8%     |
+----------------+------------+-----------+
```