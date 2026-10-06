/**
 * Campus Route Planner - Client Controller & Leaflet Map
 */

let map, routeLayer, bgLayer, markerLayer, landmarksLayer;
let networkLoaded = false;
let landmarksList = [];
let landmarksMap = {};

// Cache DOM references once
const $ = (id) => document.getElementById(id);

document.addEventListener("DOMContentLoaded", () => {
  initMap();
  loadLandmarks();

  // Listen for selection changes to update GPS coordinate displays
  $("origin-select").addEventListener("change", updateCoordinateDisplays);
  $("dest-select").addEventListener("change", updateCoordinateDisplays);

  // Manual compute triggered ONLY on form submit (no auto-run)
  $("route-form").addEventListener("submit", (e) => {
    e.preventDefault();
    computeRoute();
  });
});

function initMap() {
  const campusCenter = [13.6288, 78.5024];
  map = L.map("map-container").setView(campusCenter, 16);

  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  }).addTo(map);

  bgLayer = L.layerGroup().addTo(map);
  landmarksLayer = L.layerGroup().addTo(map);
  routeLayer = L.layerGroup().addTo(map);
  markerLayer = L.layerGroup().addTo(map);

  // Display live GPS coordinates on mouse movement and map click
  map.on("mousemove", (e) => {
    const status = $("map-status");
    if (status && !status.dataset.locked) {
      status.textContent = `Cursor: ${e.latlng.lat.toFixed(5)}, ${e.latlng.lng.toFixed(5)}`;
    }
  });

  map.on("click", (e) => {
    const status = $("map-status");
    if (status) {
      status.textContent = `Selected: ${e.latlng.lat.toFixed(5)}, ${e.latlng.lng.toFixed(5)}`;
      status.dataset.locked = "true";
      setTimeout(() => { delete status.dataset.locked; }, 3000);
    }
  });
}

async function loadLandmarks() {
  try {
    const res = await fetch("/api/landmarks");
    landmarksList = await res.json();
    landmarksMap = {};

    const orig = $("origin-select");
    const dest = $("dest-select");

    // Populate dropdowns and lookup map
    const opts = landmarksList.map((l) => {
      landmarksMap[l.landmark_id] = l;
      return `<option value="${l.landmark_id}">${l.name} (${l.category})</option>`;
    }).join("");

    orig.innerHTML = opts;
    dest.innerHTML = opts;

    // Default landmark selections
    orig.value = "MITS_MAIN_GATE";
    dest.value = "MITS_SPORTS";

    updateCoordinateDisplays();
    renderAllLandmarkMarkers();

    // Fetch background street network once
    loadNetwork();

    // NOTE: Manual execution only. computeRoute() is NOT called automatically.
  } catch (e) {
    console.error("Landmarks load failed:", e);
    $("map-status").textContent = "Failed to load landmarks catalog.";
  }
}

function updateCoordinateDisplays() {
  const origId = $("origin-select").value;
  const destId = $("dest-select").value;

  const origLm = landmarksMap[origId];
  const destLm = landmarksMap[destId];

  if (origLm) {
    $("origin-coords").textContent = `GPS: Lat ${origLm.latitude.toFixed(5)}, Lon ${origLm.longitude.toFixed(5)}`;
  }
  if (destLm) {
    $("dest-coords").textContent = `GPS: Lat ${destLm.latitude.toFixed(5)}, Lon ${destLm.longitude.toFixed(5)}`;
  }
}

function renderAllLandmarkMarkers() {
  landmarksLayer.clearLayers();

  landmarksList.forEach((lm) => {
    const dot = L.circleMarker([lm.latitude, lm.longitude], {
      radius: 6,
      fillColor: "#475569",
      color: "#ffffff",
      weight: 1.5,
      opacity: 1,
      fillOpacity: 0.85,
    });

    const popupHtml = `
      <div style="font-family: var(--font); font-size: 12px; line-height: 1.4;">
        <b>${lm.name}</b><br>
        <span style="color: #64748b;">${lm.category}</span><br>
        <code>Lat: ${lm.latitude.toFixed(5)}, Lon: ${lm.longitude.toFixed(5)}</code>
        <div style="margin-top: 6px; display: flex; gap: 4px;">
          <button style="padding: 2px 6px; font-size: 11px; cursor: pointer;" onclick="setAsOrigin('${lm.landmark_id}')">Set Origin</button>
          <button style="padding: 2px 6px; font-size: 11px; cursor: pointer;" onclick="setAsDest('${lm.landmark_id}')">Set Dest</button>
        </div>
      </div>
    `;

    dot.bindPopup(popupHtml);
    dot.addTo(landmarksLayer);
  });
}

// Global helpers for popup buttons
window.setAsOrigin = function(id) {
  $("origin-select").value = id;
  updateCoordinateDisplays();
  map.closePopup();
};

window.setAsDest = function(id) {
  $("dest-select").value = id;
  updateCoordinateDisplays();
  map.closePopup();
};

async function loadNetwork() {
  if (networkLoaded) return;
  try {
    const res = await fetch("/api/network");
    const edges = await res.json();
    L.polyline(edges, { color: "#94a3b8", weight: 1.5, opacity: 0.5 }).addTo(bgLayer);
    networkLoaded = true;
  } catch (e) {
    console.error("Network load failed:", e);
  }
}

async function computeRoute() {
  const status = $("map-status");
  setLoading(true);
  status.textContent = "Computing optimal route...";

  const startId = $("origin-select").value;
  const targetId = $("dest-select").value;

  try {
    const res = await fetch("/api/route", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ start: startId, target: targetId }),
    });

    if (!res.ok) throw new Error(`Server returned HTTP ${res.status}`);
    const d = await res.json();

    renderPath(d);
    updateMetrics(d);
    status.textContent = `A* Path resolved in ${d.astar.elapsed_ms.toFixed(2)} ms (${d.astar.distance_meters.toFixed(1)} m)`;
  } catch (e) {
    console.error("Routing error:", e);
    status.textContent = "Pathfinding failed for selected landmarks.";
  } finally {
    setLoading(false);
  }
}

function renderPath(d) {
  routeLayer.clearLayers();
  markerLayer.clearLayers();

  const pts = d.path_coordinates;
  if (!pts || !pts.length) return;

  const line = L.polyline(pts, {
    color: "#1e40af",
    weight: 5,
    opacity: 0.95,
  }).addTo(routeLayer);

  const pin = (label, color) => L.divIcon({
    className: "",
    html: `<div style="background:${color};color:#fff;font-size:11px;font-weight:700;padding:3px 7px;border-radius:4px;border:1px solid #fff;box-shadow:0 1px 3px rgba(0,0,0,.3);white-space:nowrap">${label}</div>`,
    iconAnchor: [30, 10],
  });

  const origCoord = [d.origin.lat, d.origin.lon];
  const destCoord = [d.destination.lat, d.destination.lon];

  L.marker(origCoord, { icon: pin("Origin", "#15803d") })
    .bindPopup(`<b>Origin:</b> ${d.origin.name}<br><b>GPS:</b> Lat ${d.origin.lat.toFixed(5)}, Lon ${d.origin.lon.toFixed(5)}<br>Road snap: ${d.origin.snap_dist} m`)
    .addTo(markerLayer);

  L.marker(destCoord, { icon: pin("Destination", "#b91c1c") })
    .bindPopup(`<b>Destination:</b> ${d.destination.name}<br><b>GPS:</b> Lat ${d.destination.lat.toFixed(5)}, Lon ${d.destination.lon.toFixed(5)}<br>Road snap: ${d.destination.snap_dist} m`)
    .addTo(markerLayer);

  map.fitBounds(line.getBounds(), { padding: [40, 40] });
}

function updateMetrics(d) {
  $("val-dist-dijkstra").textContent = `${d.dijkstra.distance_meters.toFixed(2)} m`;
  $("val-dist-astar").textContent = `${d.astar.distance_meters.toFixed(2)} m`;
  $("val-nodes-dijkstra").textContent = d.dijkstra.nodes_expanded;
  $("val-nodes-astar").textContent = d.astar.nodes_expanded;
  $("val-time-dijkstra").textContent = `${d.dijkstra.elapsed_ms.toFixed(2)} ms`;
  $("val-time-astar").textContent = `${d.astar.elapsed_ms.toFixed(2)} ms`;

  const tp = $("tag-pruning");
  tp.textContent = `${d.pruning_percentage.toFixed(1)}% reduction`;
  tp.className = `metric-tag ${d.pruning_percentage > 0 ? "gain" : "match"}`;

  const to = $("tag-optimality");
  const match = Math.abs(d.dijkstra.distance_meters - d.astar.distance_meters) < 0.01;
  to.textContent = match ? "Identical (100%)" : "Discrepancy";
  to.className = `metric-tag ${match ? "match" : "gain"}`;
}

function setLoading(on) {
  ["val-dist-dijkstra", "val-dist-astar", "val-nodes-dijkstra", "val-nodes-astar", "val-time-dijkstra", "val-time-astar"]
    .forEach((id) => $(id)?.classList.toggle("skeleton", on));
}
