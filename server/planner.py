"""Server-side cleaning planner.

Turns a stored map (and an optional room selection) into an ordered list of
waypoints for the robot to execute. This runs off the robot because choosing a
whole-house route is not latency-critical — the robot just follows the result.

For v1 this reuses the same coverage strategy as the robot's local planner;
later it can add room segmentation, no-go zones, and multi-room ordering.
"""

from __future__ import annotations

import numpy as np

from robot.navigation.planner import coverage_path
from shared.schemas import CoveragePlan, OccupancyGridMeta, Waypoint


def plan_coverage(grid: np.ndarray, meta: OccupancyGridMeta) -> CoveragePlan:
    """Generate a coverage plan in world (meter) coordinates."""
    cells = coverage_path(grid)
    res = meta.resolution
    waypoints = [
        Waypoint(
            x=meta.origin.x + c * res,
            y=meta.origin.y + r * res,
        )
        for (r, c) in cells
    ]
    return CoveragePlan(waypoints=waypoints)
