# Campus Landmark A* Route Planner

**Mini-Project Reference:** S.No 12 (Course Code: 23CSE109 / 23CSE208 - Artificial Intelligence Laboratory)  
**Academic Requirement:** Comparative Benchmarking of Informed A* Search vs Uninformed Dijkstra Baseline on OpenStreetMap Campus Street Networks.

---

## 1. Overview

The **Campus Landmark A* Route Planner** is a specialized geospatial routing and algorithmic benchmarking system. It models campus pedestrian and street topologies from OpenStreetMap (OSM) via OSMnx, snaps campus landmarks using spherical Haversine distance metrics, and executes an admissible A* search using the Great-Circle Haversine distance heuristic.

The system benchmarks A* against an uninformed uniform-cost Dijkstra baseline ($h(n) = 0$), quantifying search space pruning, nodes expanded, and execution latency.

---

## 2. Project Structure

```
ai-mini-pjt/
├── data/
│   ├── campus_network.graphml    # Campus walkway & road network graph
│   └── landmarks.json            # Campus landmarks with GPS coordinates
├── public/                       # Web application frontend assets
│   ├── index.html                # Interactive dashboard with coordinate displays
│   ├── privacy.html              # Privacy Policy page
│   ├── terms.html                # Terms of Service page
│   ├── style.css                 # Clean institutional stylesheet
│   ├── app.js                    # Client Leaflet map controller & route solver
│   └── favicon.svg               # Custom vector icon
├── router.py                     # Algorithmic core (Haversine, Snapping, Dijkstra, A*)
├── main.py                       # Regular CLI driver & benchmark runner
├── server.py                     # Zero-dependency local web server & REST API
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
* **Interactive Map & Accurate Coordinates:** Live Leaflet map displaying OpenStreetMap tiles, campus footpaths, all campus facility pins with exact GPS coordinates (Latitude, Longitude), live cursor GPS tracking, and route polyline with real-time metric benchmarks.
* **Manual Execution:** Route computation triggers strictly when the user clicks "Compute Route" (no automatic execution on page load).
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
*Or using main.py:*
```powershell
python main.py --serve
```
Then open **[http://localhost:8000](http://localhost:8000)** in your browser:
- Inspect all campus facilities and their coordinates directly on the map.
- Select Origin and Destination landmarks to view their exact GPS coordinates.
- Click **Compute Route** to calculate and visualize the optimal path.

### Option B: Run Command-Line Benchmark
Run default benchmark:
```powershell
python main.py
```
Or specify origin and destination landmarks:
```powershell
python main.py --start MITS_MAIN_GATE --target MITS_SPORTS
```

### Option C: Benchmark All Landmark Pairs
Run validation across all campus landmark pairs:
```powershell
python main.py --all
```

---

## 5. Sample Benchmark Output

```
+----------------+------------+----------+
| Metric         | Dijkstra   | A*       |
+================+============+==========+
| Distance       | 585.83 m   | 585.83 m |
+----------------+------------+----------+
| Nodes Expanded | 24         | 10       |
+----------------+------------+----------+
| Time           | 0.17 ms    | 0.15 ms  |
+----------------+------------+----------+
| Path Nodes     | 8          | 8        |
+----------------+------------+----------+
| Pruning        |            | 58.3%    |
+----------------+------------+----------+
```