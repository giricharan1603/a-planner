"""Custom domain exceptions and warnings for Campus Landmark A* Route Planner."""

class CampusRouterError(Exception):
    """Base exception for routing engine errors."""
    pass

class PathNotFoundError(CampusRouterError):
    """Raised when no connected path exists between origin and destination."""
    pass

class LandmarkNotFoundError(CampusRouterError):
    """Raised when a requested landmark identifier is missing in the database."""
    pass

class DisconnectedGraphError(CampusRouterError):
    """Raised when graph component connectivity checklist detects disjoint components."""
    pass

class SnappingThresholdWarning(UserWarning):
    """Warning emitted when coordinate snapping distance exceeds configured safety threshold (FR-2.3)."""
    pass
