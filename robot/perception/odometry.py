"""Differential-drive odometry from wheel encoders + IMU yaw.

Converts encoder tick deltas into how far the robot moved, fusing the IMU
heading (which drifts far less than integrated wheel rotation) for theta.

This output feeds BreezySLAM as a `pose_change` hint to fight drift (M3).
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class WheelGeometry:
    wheel_radius_m: float = 0.034
    wheel_base_m: float = 0.20  # distance between the two driven wheels
    ticks_per_rev: int = 1440  # encoder counts per wheel revolution


class Odometry:
    def __init__(self, geom: WheelGeometry | None = None) -> None:
        self.geom = geom or WheelGeometry()
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        self._last_enc_l: int | None = None
        self._last_enc_r: int | None = None

    def _dist(self, dticks: int) -> float:
        rev = dticks / self.geom.ticks_per_rev
        return rev * 2 * math.pi * self.geom.wheel_radius_m

    def update(self, enc_l: int, enc_r: int, yaw_rad: float | None = None):
        """Update pose from absolute encoder counts; return (dxy_mm, dtheta_deg, _).

        The returned tuple is in BreezySLAM's `pose_change` format.
        """
        if self._last_enc_l is None:
            self._last_enc_l, self._last_enc_r = enc_l, enc_r
            return (0.0, 0.0, 0.0)

        d_l = self._dist(enc_l - self._last_enc_l)
        d_r = self._dist(enc_r - self._last_enc_r)
        self._last_enc_l, self._last_enc_r = enc_l, enc_r

        d_center = (d_l + d_r) / 2.0
        if yaw_rad is not None:
            d_theta = yaw_rad - self.theta  # trust the IMU for heading
            self.theta = yaw_rad
        else:
            d_theta = (d_r - d_l) / self.geom.wheel_base_m
            self.theta += d_theta

        self.x += d_center * math.cos(self.theta)
        self.y += d_center * math.sin(self.theta)

        return (d_center * 1000.0, math.degrees(d_theta), 0.0)
