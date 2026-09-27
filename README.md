# Campus Landmark A* Route Planner

**Mini-Project Reference:** S.No 12 (Course Code: 23CSE109 / 23CSE208 - Artificial Intelligence Laboratory)  
**Curriculum Mapping:** Course Outcome CO2 (Unit II: Informed & Heuristic Search)  
**Academic Requirement:** Comparative Benchmarking of Informed A* Search vs Uninformed Dijkstra Baseline on Topological Real-World Networks.

---

## 📌 Executive Overview

The **Campus Landmark A* Route Planner** is a specialized geospatial routing and algorithmic benchmarking system. It extracts real-world street and walkway topological graphs from OpenStreetMap (OSM) via OSMnx, snaps campus landmarks using a 3D Cartesian KD-Tree, and runs an admissible and consistent A* search using the Great-Circle Haversine distance heuristic.

The system benchmarks A* against an uninformed uniform-cost Dijkstra baseline ($h(n) = 0$), quantifying search space pruning, peak queue size, and latency.

---

## 🚀 Key Performance Indicators (KPIs)

* **Optimality Parity:** 100% agreement with Dijkstra path distances down to $10^{-4}\text{ m}$ tolerance (TC-01).
* **Search Space Pruning:** $\ge 40\%$ reduction in nodes expanded by A* compared to Dijkstra for routes exceeding 500 meters (TC-03).
* **Instant Rejection:** $< 10\text{ ms}$ termination with `PathNotFoundError` for disconnected node pairs prior to priority queue execution (TC-04).
* **Snapping Safety Guard:** Warning logged if a landmark is $> 250\text{ m}$ from the nearest walkable graph vertex (FR-2.3).
* **Interface Schema Compliance:** Strict JSON schema conforming to PRD Section 8.2.

---

## 🛠️ System Architecture

```
[OpenStreetMap / Overpass API]
            │
            ▼ (Disk Cache: data/cache/*.graphml)
[OSMnx MultiDiGraph]
            │
            ▼ (Vectorized min(length) deduplication)
[Simplified networkx.DiGraph]
      /                     \
     v                       v
[Spatial Snapper KD-Tree]  [Structural Connectivity Check (<10ms)]
     \                       /
      v                     v
[Custom A* Engine (heapq)]  vs  [Dijkstra Baseline (h=0)]
      │
      ├───────────────────────┬───────────────────────┐
      ▼                       ▼                       ▼
[Tabular CLI Report]   [Folium HTML Map]      [Strict JSON Export]
```

---

## 📦 Directory Structure

```
ai-mini-pjt/
├── data/
│   ├── cache/                      # Cached .graphml files to prevent Overpass API limits
│   ├── landmarks.json              # Campus landmark catalog with coordinates
│   └── routes/                     # Exported JSON payloads and Folium HTML maps
├── src/
│   ├── config.py                   # Global constants (Earth radius, snapping thresholds)
│   ├── exceptions.py               # Custom exceptions (PathNotFoundError, etc.)
│   ├── graph_loader.py             # OSMnx ingestion, caching, and MultiDiGraph -> DiGraph simplifier
│   ├── spatial_index.py            # 3D ECEF KD-Tree coordinate snapping and threshold check
│   ├── heuristic.py                # Pure Haversine formula (admissible & consistent)
│   ├── router.py                   # Custom A* and Dijkstra solvers with heapq instrumentation
│   ├── visualizer.py               # Folium interactive HTML and Matplotlib static renderers
│   └── serializer.py               # Strict JSON schema builder conforming to PRD 8.2
├── tests/
│   ├── conftest.py                 # Graph fixtures and synthetic grid generators
│   ├── test_connectivity.py        # TC-04: Disconnected fast-failure validation (<10ms)
│   ├── test_heuristic.py           # TC-02: Admissibility and consistency checks
│   ├── test_router_optimality.py   # TC-01 & TC-05: Exact distance parity & zero-length identity
│   └── test_benchmarks.py          # TC-03: >= 40% node expansion reduction validation
├── requirements.txt                # Pinned production dependencies
├── main.py                         # CLI entry point for execution, benchmarking, and visualization
└── README.md
```

---

## 💻 Installation & Usage

### 1. Setup Virtual Environment
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run Route Planner & Benchmarking Engine
Route between default campus landmarks (Main Gate to Sports Complex):
```powershell
.\.venv\Scripts\python.exe main.py --start MITS_MAIN_GATE --target MITS_SPORTS
```

Specify custom landmarks:
```powershell
.\.venv\Scripts\python.exe main.py --start MITS_LIB --target MITS_HOSTEL_B --mode walk
```

### 3. Run Automated Pytest Suite (TC-01 through TC-05)
```powershell
.\.venv\Scripts\pytest.exe -v
```

---

## 📊 Sample Benchmark Output

```
================================================================================
📊 ALGORITHM BENCHMARKING REPORT
================================================================================
╒═══════════════════════════╤══════════════════╤══════════════════╤═══════════════════════════╕
│ Performance Metric        │ Dijkstra (h=0)   │ A* (Haversine)   │ Relative Difference       │
╞═══════════════════════════╪══════════════════╪══════════════════╪═══════════════════════════╡
│ Total Path Length         │ 1284.42 m        │ 1284.42 m        │ 0.00% (Identical Optimal) │
├───────────────────────────┼──────────────────┼──────────────────┼───────────────────────────┤
│ Nodes Expanded (Closed)   │ 384              │ 162              │ +57.81% (Pruned)          │
├───────────────────────────┼──────────────────┼──────────────────┼───────────────────────────┤
│ Peak Frontier Queue Size  │ 76               │ 34               │ +55.26%                   │
├───────────────────────────┼──────────────────┼──────────────────┼───────────────────────────┤
│ Wall-Clock Latency        │ 12.45 ms         │ 4.88 ms          │ +60.80%                   │
├───────────────────────────┼──────────────────┼──────────────────┼───────────────────────────┤
│ Optimality Verified       │ BASE             │ VERIFIED         │ PASSED                    │
╘═══════════════════════════╧══════════════════╧══════════════════╧═══════════════════════════╛
```

---

## 📄 License & Course Submission
Developed for AI Mini-Project S.No 12 (Course Code: 23CSE109 / 23CSE208).
All requirements of PRD v1.1.0 are fully implemented and verified.
