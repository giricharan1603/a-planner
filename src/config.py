from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CACHE_DIR = DATA_DIR / "cache"
ROUTES_DIR = DATA_DIR / "routes"
LANDMARKS_FILE = DATA_DIR / "landmarks.json"

# Physics / Geodesy Constants
EARTH_RADIUS_METERS = 6371000.0  # As specified in PRD FR-3.3

# Snapping & Quality Thresholds
SNAPPING_THRESHOLD_METERS = 250.0  # As specified in PRD FR-2.3

# Routing Network Defaults
DEFAULT_NETWORK_MODE = "walk"  # 'walk' or 'drive' as specified in PRD FR-1.2
DEFAULT_CAMPUS_LOCATION = "Madanapalle, Andhra Pradesh, India"
DEFAULT_CAMPUS_COORDS = (13.6288, 78.5024)
DEFAULT_CAMPUS_RADIUS_METERS = 1500
DEFAULT_CACHE_FILENAME = "campus_network.graphml"
