"""Motion controller: drive the robot toward a waypoint.

A simple proportional "go-to-goal" controller for a differential drive base.
It converts the error between the current pose and the target into left/right
wheel speeds, and refuses to move if the LiDAR sees an obstacle dead ahead.

Obstacle avoidance is LiDAR-first (M4): the same scan that maps the room is
checked here for anything close in the direction of travel.
"""

from __future__ import annotations

import math

from robot.drivers.serial_link import SerialLink
from shared.schemas import Pose2D, Waypoint


class Controller:
    def __init__(
        self,
        link: SerialLink,
        cruise_mps: float = 0.20,
        reach_tol_m: float = 0.05,
        stop_distance_m: float = 0.25,
    ) -> None:
        self.link = link
        self.cruise = cruise_mps
        self.tol = reach_tol_m
        self.stop_distance = stop_distance_m

    def at_goal(self, pose: Pose2D, wp: Waypoint) -> bool:
        return math.hypot(wp.x - pose.x, wp.y - pose.y) <= self.tol

    def obstacle_ahead(self, scan: list[tuple[float, float]]) -> bool:
        """True if any LiDAR point within +/-20 deg of front is too close."""
        for angle, dist_mm in scan:
            a = angle % 360
            if (a < 20 or a > 340) and 0 < dist_mm / 1000.0 < self.stop_distance:
                return True
        return False

    def step(
        self,
        pose: Pose2D,
        wp: Waypoint,
        scan: list[tuple[float, float]] | None = None,
    ) -> None:
        """Issue one control command toward the waypoint."""
        if scan and self.obstacle_ahead(scan):
            self.link.stop()
            return

        heading_to_goal = math.atan2(wp.y - pose.y, wp.x - pose.x)
        err = math.atan2(
            math.sin(heading_to_goal - pose.theta),
            math.cos(heading_to_goal - pose.theta),
        )
        # Proportional turn: bias wheel speeds by the heading error.
        turn = max(-1.0, min(1.0, err)) * self.cruise
        self.link.set_wheel_speeds(self.cruise - turn, self.cruise + turn)
