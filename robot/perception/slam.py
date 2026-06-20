"""2D LiDAR SLAM wrapper around BreezySLAM.

BreezySLAM does the heavy lifting (scan matching + occupancy grid). We feed it
LiDAR scans (optionally with odometry to reduce drift) and read back the pose
and map.

Install BreezySLAM from source (it is not always on PyPI for ARM):
    git clone https://github.com/simondlevy/BreezySLAM
    cd BreezySLAM/python && python setup.py install

Milestone M3: push the robot around by hand and watch the map build.
"""

from __future__ import annotations

from robot.config import CONFIG
from shared.schemas import OccupancyGridMeta, Pose2D

try:
    from breezyslam.algorithms import RMHC_SLAM  # type: ignore
    from breezyslam.sensors import RPLidarA1  # type: ignore
except ImportError:
    RMHC_SLAM = None  # type: ignore
    RPLidarA1 = None  # type: ignore


class SlamEngine:
    def __init__(self) -> None:
        if RMHC_SLAM is None:
            raise RuntimeError("BreezySLAM not installed (see module docstring)")
        self._slam = RMHC_SLAM(
            RPLidarA1(),
            CONFIG.map_size_pixels,
            CONFIG.map_size_meters,
        )
        self._mapbytes = bytearray(CONFIG.map_size_pixels * CONFIG.map_size_pixels)

    def update(
        self,
        distances_mm: list[float],
        odometry: tuple[float, float, float] | None = None,
    ) -> Pose2D:
        """Feed one scan; return the updated pose.

        `odometry` is (dxy_mm, dtheta_deg, dt_seconds) since the last update.
        """
        self._slam.update(distances_mm, pose_change=odometry)
        x_mm, y_mm, theta_deg = self._slam.getpos()
        from math import radians

        return Pose2D(x=x_mm / 1000.0, y=y_mm / 1000.0, theta=radians(theta_deg))

    def occupancy_grid(self) -> bytes:
        """Return the current map as a row-major byte array (0..255)."""
        self._slam.getmap(self._mapbytes)
        return bytes(self._mapbytes)

    def meta(self, pose: Pose2D) -> OccupancyGridMeta:
        px = CONFIG.map_size_pixels
        return OccupancyGridMeta(
            resolution=CONFIG.map_resolution,
            width=px,
            height=px,
            origin=Pose2D(x=0.0, y=0.0, theta=0.0),
        )
