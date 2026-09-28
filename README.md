# Campus Landmark A* Route Planner

**Mini-Project Reference:** S.No 12 (Course Code: 23CSE109 / 23CSE208 - Artificial Intelligence Laboratory)  
**Academic Requirement:** Comparative Benchmarking of Informed A* Search vs Uninformed Dijkstra Baseline on Campus Street Networks.

---

## 📌 Overview

This project provides a clean, easy-to-understand implementation of the **A\* Search Algorithm** compared against **Dijkstra's Algorithm** for navigating university campuses.

It loads the real street and pedestrian walkways of the campus from OpenStreetMap, snaps named buildings to road intersections, and finds the shortest path while benchmarking the efficiency of the heuristic.

---

## 📦 Simple Project Structure

```
ai-mini-pjt/
├── data/
│   ├── campus_network.graphml    # Campus road map (fast local loading)
│   └── landmarks.json            # Campus landmarks with GPS coordinates
├── router.py                     # All core logic (Haversine + Snapping + Dijkstra + A*)
├── main.py                       # Main script (runs routing, prints table, exports HTML map)
├── test_planner.py               # Simple verification tests (optimality, pruning, identity)
├── route_map.html                # Generated interactive route map (view in browser)
├── route_summary.json            # Generated route statistics in JSON
├── requirements.txt              # Required Python packages
├── README.md                     # Project documentation
└── .gitignore                    # Git ignore file
```

---

## 🚀 How to Run

### 1. Setup Virtual Environment & Dependencies
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Run the Route Planner
```powershell
python main.py
```
Or specify different campus landmarks:
```powershell
python main.py --start MITS_HOSTEL_B --target MITS_HOSTEL_G
```

### 3. Run the Automated Tests
```powershell
pytest test_planner.py -v
```

---

## 🗺️ View the Results

* **Interactive Web Map:** Open `route_map.html` in your browser (Chrome or Edge) to see the route polyline, start pin (green), and destination pin (red).
* **Summary JSON:** Open `route_summary.json` to see the distance and node statistics.

---

## 📊 Sample Benchmark Output

```
+------------------+------------------+------------------+----------------------+
| Metric           | Dijkstra (h=0)   | A* (Haversine)   | Advantage            |
+==================+==================+==================+======================+
| Total Distance   | 3301.38 m        | 3301.38 m        | 100% Match (Optimal) |
+------------------+------------------+------------------+----------------------+
| Nodes Explored   | 73               | 51               | +30.1% (Fewer nodes) |
+------------------+------------------+------------------+----------------------+
| Execution Time   | 0.27 ms          | 0.54 ms          | Sub-millisecond      |
+------------------+------------------+------------------+----------------------+
| Path Nodes Count | 20               | 20               | Identical Path       |
+------------------+------------------+------------------+----------------------+
```
