Here is the complete guide on **how to set up requirements from scratch** and **how to run the project**.

---

## Part 1: How to Setup the Requirements

If you are setting this up on a new machine or re-installing:

### Step 1: Open PowerShell or Terminal in the Project Folder
```powershell
cd c:\Users\giric\Desktop\project\ai-mini-pjt
```

### Step 2: Create a Python Virtual Environment
*(Use Python 3.10, 3.11, 3.12, or 3.13)*
```powershell
python -m venv .venv
```
> **Note:** If `python` is not in your system PATH, use the full path to your installed Python executable:
> ```powershell
> & "C:\Users\giric\AppData\Local\Programs\Python\Python313\python.exe" -m venv .venv
> ```

### Step 3: Activate the Virtual Environment
* On **Windows PowerShell**:
  ```powershell
  .\.venv\Scripts\Activate.ps1
  ```
  *(If you get an execution policy error, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` and then run the activate command again).*

* On **Windows Command Prompt (cmd)**:
  ```cmd
  .venv\Scripts\activate.bat
  ```

* On **macOS / Linux**:
  ```bash
  source .venv/bin/activate
  ```

### Step 4: Install Dependencies from `requirements.txt`
With the environment activated, run:
```powershell
pip install -r requirements.txt
```
*(Or without activating, directly execute: `.\.venv\Scripts\pip.exe install -r requirements.txt`)*

The [`requirements.txt`](file:///c:/Users/giric/Desktop/project/ai-mini-pjt/requirements.txt) includes:
* `osmnx>=1.9.0` (OpenStreetMap graph extraction)
* `networkx>=3.0` (Graph data structures)
* `scipy>=1.10.0` (KD-Tree spatial indexing)
* `matplotlib>=3.7.0` (Static map plotting)
* `folium>=0.14.0` (Interactive Leaflet HTML maps)
* `tabulate>=0.9.0` (Formatted console benchmark tables)
* `pytest>=7.0.0` (Automated testing suite)

---

## Part 2: How to Run the Project

Once the requirements are installed, running the project takes just one command.

### 1. Run the Main Route Planner
```powershell
.\.venv\Scripts\python.exe main.py
```
This automatically:
1. Loads the campus road/walkway network.
2. Snaps start and target landmarks to the nearest road vertices.
3. Computes the optimal route using **$A^*$** and **Dijkstra**.
4. Prints the side-by-side performance table.
5. Saves the route map and data files.

---

### 2. Route Between Specific Campus Buildings
You can specify `--start` and `--target` using landmark IDs:
```powershell
.\.venv\Scripts\python.exe main.py --start MITS_HOSTEL_B --target MITS_HOSTEL_G
```

Other available landmarks in [`data/landmarks.json`](file:///c:/Users/giric/Desktop/project/ai-mini-pjt/data/landmarks.json):
* `MITS_MAIN_GATE` (Campus Main Entrance Gate)
* `MITS_LIB` (Central Library)
* `MITS_ADMIN` (Administrative Headquarters)
* `MITS_CSE` (Computer Science & Engineering Block)
* `MITS_ECE` (Electronics & Electrical Engineering Block)
* `MITS_HOSTEL_B` (Boys Hostel Complex)
* `MITS_HOSTEL_G` (Girls Hostel Complex)
* `MITS_SPORTS` (Sports Ground & Athletics Field)
* `MITS_CANTEEN` (Campus Cafeteria & Student Center)
* `MITS_AUDITORIUM` (University Auditorium)

---

### 3. Switch Network Mode (Walk vs Drive)
* **Pedestrian walkway mode (default):**
  ```powershell
  .\.venv\Scripts\python.exe main.py --start MITS_MAIN_GATE --target MITS_LIB --mode walk
  ```
* **Drive road network:**
  ```powershell
  .\.venv\Scripts\python.exe main.py --start MITS_MAIN_GATE --target MITS_CSE --mode drive
  ```

---

### 4. View the Generated Maps
After running `main.py`, open the output files in your browser:
* **Interactive Web Map:**
  ```powershell
  Start-Process data\routes\campus_route.html
  ```
* **Static High-Resolution Plot:**
  ```powershell
  Start-Process data\routes\campus_route.png
  ```
* **JSON Output (PRD Section 8.2):**
  ```powershell
  Get-Content data\routes\campus_route.json
  ```

---

### 5. Run the Automated Tests (TC-01 to TC-05)
To verify algorithm correctness, heuristic admissibility, and search space pruning:
```powershell
.\.venv\Scripts\pytest.exe -v
```