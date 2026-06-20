"""Pydantic models exchanged between the robot and the server.

These are intentionally small and JSON-friendly so they can travel over
HTTP (map upload / commands) and MQTT (realtime telemetry).
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Pose2D(BaseModel):
    """Robot pose on the map, in meters and radians."""

    x: float
    y: float
    theta: float  # heading, radians, 0 = +x axis


class OccupancyGridMeta(BaseModel):
    """Describes how grid pixels map to real-world meters.

    Mirrors the ROS map_server convention so the format is familiar.
    """

    resolution: float  # meters per cell
    width: int  # cells
    height: int  # cells
    origin: Pose2D  # world coords of cell (0, 0)


class MapUpload(BaseModel):
    """A finished map the robot sends to the server for storage."""

    robot_id: str
    name: str = "house"
    meta: OccupancyGridMeta
    # Occupancy grid encoded as a base64 PNG (0=free, 100=occupied, -1=unknown
    # flattened to 0/127/255 for the image). Image bytes travel separately as a
    # multipart upload; this field carries the metadata + checksum.
    image_sha256: str


class RobotState(str, Enum):
    IDLE = "idle"
    MAPPING = "mapping"
    CLEANING = "cleaning"
    RELOCALIZING = "relocalizing"
    RETURNING = "returning"
    ERROR = "error"


class RobotStatus(BaseModel):
    """Realtime telemetry published to the server (MQTT)."""

    robot_id: str
    state: RobotState
    pose: Pose2D
    battery_pct: Optional[float] = None
    coverage_pct: Optional[float] = None
    message: Optional[str] = None


class Waypoint(BaseModel):
    x: float
    y: float


class CommandType(str, Enum):
    START_MAPPING = "start_mapping"
    START_CLEANING = "start_cleaning"
    CLEAN_ROOM = "clean_room"
    GO_TO = "go_to"
    STOP = "stop"
    RETURN_TO_DOCK = "return_to_dock"


class Command(BaseModel):
    """A high-level instruction from the server/dashboard to the robot."""

    type: CommandType
    room: Optional[str] = None
    target: Optional[Waypoint] = None


class CoveragePlan(BaseModel):
    """An ordered list of waypoints the robot should drive to cover an area."""

    waypoints: list[Waypoint] = Field(default_factory=list)
