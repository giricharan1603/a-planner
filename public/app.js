/**
 * Campus Landmark Route Planner
 * Client-Side Controller & Leaflet Map Renderer
 */

let mapInstance = null;
let routeLayer = null;
let backgroundLayer = null;
let markersLayer = null;

// Initialize on DOM load
document.addEventListener("DOMContentLoaded", () => {
  initMap();
  loadLandmarks();

  const form = document.getElementById("route-form");
  if (form) {
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      calculateRoute();
    });
  }
});

function initMap() {
  // Center around MITS campus coordinates
  const campusCenter = [13.6288, 78.5024];

  mapInstance = L.map("map-container", {
    zoomControl: true,
    attributionControl: true,
  }).setView(campusCenter, 16);

  // Clean OpenStreetMap base layer
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  }).addTo(mapInstance);

  backgroundLayer = L.layerGroup().addTo(mapInstance);
  routeLayer = L.layerGroup().addTo(mapInstance);
  markersLayer = L.layerGroup().addTo(mapInstance);
}

async function loadLandmarks() {
  const originSelect = document.getElementById("origin-select");
  const destSelect = document.getElementById("dest-select");

  try {
    const res = await fetch("/api/landmarks");
    const landmarks = await res.json();

    originSelect.innerHTML = "";
    destSelect.innerHTML = "";

    landmarks.forEach((item, index) => {
      const opt1 = new Option(`${item.name} (${item.category})`, item.landmark_id);
      const opt2 = new Option(`${item.name} (${item.category})`, item.landmark_id);

      originSelect.add(opt1);
      destSelect.add(opt2);
    });

    // Default selection: Hostel B to Hostel G, or Main Gate to Sports
    if (landmarks.length >= 2) {
      originSelect.value = "MITS_MAIN_GATE";
      destSelect.value = "MITS_SPORTS";
    }

    // Trigger initial calculation
    calculateRoute();
  } catch (err) {
    console.error("Failed to load landmarks catalog:", err);
  }
}

async function calculateRoute() {
  const originId = document.getElementById("origin-select").value;
  const destId = document.getElementById("dest-select").value;
  const statusEl = document.getElementById("map-status");

  setLoadingState(true);
  statusEl.textContent = "Computing optimal paths...";

  try {
    const response = await fetch("/api/route", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ start: originId, target: destId }),
    });

    if (!response.ok) {
      throw new Error(`Routing request failed with status: ${response.status}`);
    }

    const data = await response.json();
    renderRoute(data);
    updateMetrics(data);
    statusEl.textContent = `Path resolved in ${data.astar.elapsed_ms.toFixed(2)} ms`;
  } catch (error) {
    console.error("Route calculation error:", error);
    statusEl.textContent = "Pathfinding failed for selected vertices.";
  } finally {
    setLoadingState(false);
  }
}

function renderRoute(data) {
  // Clear previous traces
  routeLayer.clearLayers();
  markersLayer.clearLayers();

  const coords = data.path_coordinates;
  if (!coords || coords.length === 0) return;

  // Background street network (render once if not populated)
  if (data.network_edges && backgroundLayer.getLayers().length === 0) {
    data.network_edges.forEach((segment) => {
      L.polyline(segment, {
        color: "#94a3b8",
        weight: 1.5,
        opacity: 0.55,
      }).addTo(backgroundLayer);
    });
  }

  // Draw active path
  const polyline = L.polyline(coords, {
    color: "#1e40af",
    weight: 5,
    opacity: 0.95,
  }).addTo(routeLayer);

  // Custom Origin Marker (Solid Green)
  const originIcon = L.divIcon({
    className: "custom-pin origin-pin",
    html: `<div style="background-color:#15803d;color:#ffffff;font-size:11px;font-weight:700;padding:3px 7px;border-radius:4px;border:1px solid #ffffff;box-shadow:0 1px 3px rgba(0,0,0,0.3);white-space:nowrap;">Origin</div>`,
    iconSize: [50, 20],
    iconAnchor: [25, 10],
  });

  // Custom Destination Marker (Solid Red)
  const destIcon = L.divIcon({
    className: "custom-pin dest-pin",
    html: `<div style="background-color:#b91c1c;color:#ffffff;font-size:11px;font-weight:700;padding:3px 7px;border-radius:4px;border:1px solid #ffffff;box-shadow:0 1px 3px rgba(0,0,0,0.3);white-space:nowrap;">Destination</div>`,
    iconSize: [75, 20],
    iconAnchor: [37, 10],
  });

  const startCoord = coords[0];
  const targetCoord = coords[coords.length - 1];

  L.marker(startCoord, { icon: originIcon })
    .bindPopup(`<strong>Origin:</strong> ${data.origin.name}<br>Snap Distance: ${data.origin.snap_dist.toFixed(1)} m`)
    .addTo(markersLayer);

  L.marker(targetCoord, { icon: destIcon })
    .bindPopup(`<strong>Destination:</strong> ${data.destination.name}<br>Snap Distance: ${data.destination.snap_dist.toFixed(1)} m`)
    .addTo(markersLayer);

  mapInstance.fitBounds(polyline.getBounds(), { padding: [40, 40] });
}

function updateMetrics(data) {
  document.getElementById("val-dist-dijkstra").textContent = `${data.dijkstra.distance_meters.toFixed(2)} m`;
  document.getElementById("val-dist-astar").textContent = `${data.astar.distance_meters.toFixed(2)} m`;

  document.getElementById("val-nodes-dijkstra").textContent = data.dijkstra.nodes_expanded;
  document.getElementById("val-nodes-astar").textContent = data.astar.nodes_expanded;

  document.getElementById("val-time-dijkstra").textContent = `${data.dijkstra.elapsed_ms.toFixed(2)} ms`;
  document.getElementById("val-time-astar").textContent = `${data.astar.elapsed_ms.toFixed(2)} ms`;

  const tagPruning = document.getElementById("tag-pruning");
  tagPruning.textContent = `${data.pruning_percentage.toFixed(1)}% reduction`;
  tagPruning.className = "metric-tag " + (data.pruning_percentage > 0 ? "gain" : "match");

  const tagOptimality = document.getElementById("tag-optimality");
  const isMatch = Math.abs(data.dijkstra.distance_meters - data.astar.distance_meters) < 0.01;
  tagOptimality.textContent = isMatch ? "Identical (100%)" : "Discrepancy";
  tagOptimality.className = "metric-tag " + (isMatch ? "match" : "gain");
}

function setLoadingState(isLoading) {
  const elements = [
    document.getElementById("val-dist-dijkstra"),
    document.getElementById("val-dist-astar"),
    document.getElementById("val-nodes-dijkstra"),
    document.getElementById("val-nodes-astar"),
    document.getElementById("val-time-dijkstra"),
    document.getElementById("val-time-astar"),
  ];

  elements.forEach((el) => {
    if (el) {
      if (isLoading) el.classList.add("skeleton");
      else el.classList.remove("skeleton");
    }
  });
}
