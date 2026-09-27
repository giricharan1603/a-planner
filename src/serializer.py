"""Data Interface Schema Serialization (PRD Section 8.2)."""

import json
from pathlib import Path
from typing import Any, Dict
from src.router import SearchResult


def serialize_search_result(result: SearchResult) -> Dict[str, Any]:
    """Serialize a SearchResult dataclass into the strict PRD Section 8.2 JSON schema."""
    return {
        "status": result.status,
        "algorithm": result.algorithm,
        "start_node_id": result.start_node_id,
        "target_node_id": result.target_node_id,
        "total_distance_meters": round(result.total_distance_meters, 2),
        "nodes_expanded": result.nodes_expanded,
        "execution_time_ms": round(result.execution_time_ms, 2),
        "path_coordinates": [
            {"lat": round(coord["lat"], 6), "lon": round(coord["lon"], 6)}
            for coord in result.path_coordinates
        ],
    }


def save_result_to_json(result: SearchResult, filepath: Path) -> Path:
    """Save the serialized search result payload to a JSON file."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    payload = serialize_search_result(result)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    return filepath
