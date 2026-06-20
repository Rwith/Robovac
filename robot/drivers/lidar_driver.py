"""RPLidar A1 driver wrapper.

Wraps the `rplidar` Python package and yields one full 360-degree scan at a
time as (angle_deg, distance_mm) pairs, which is exactly what BreezySLAM wants.

Install:  pip install rplidar        (or rplidar-roboticia, a maintained fork)

Milestone M1: run this file standalone to confirm the LiDAR is alive.
"""

from __future__ import annotations

from collections.abc import Iterator

from robot.config import CONFIG

try:
    from rplidar import RPLidar  # type: ignore
except ImportError:  # keep the module importable on a dev PC without the lib
    RPLidar = None  # type: ignore


class Lidar:
    def __init__(self, port: str | None = None) -> None:
        if RPLidar is None:
            raise RuntimeError("rplidar package not installed (pip install rplidar)")
        self._lidar = RPLidar(port or CONFIG.lidar_port)

    def scans(self) -> Iterator[list[tuple[float, float]]]:
        """Yield successive scans as lists of (angle_deg, distance_mm)."""
        for scan in self._lidar.iter_scans():
            # scan items are (quality, angle, distance); drop quality.
            yield [(angle, dist) for (_q, angle, dist) in scan]

    def stop(self) -> None:
        self._lidar.stop()
        self._lidar.stop_motor()
        self._lidar.disconnect()


def _demo() -> None:
    """Print a few scans so you can confirm the sensor works (M1)."""
    lidar = Lidar()
    try:
        for i, scan in enumerate(lidar.scans()):
            print(f"scan {i}: {len(scan)} points, "
                  f"nearest={min(d for _a, d in scan):.0f} mm")
            if i >= 5:
                break
    finally:
        lidar.stop()


if __name__ == "__main__":
    _demo()
