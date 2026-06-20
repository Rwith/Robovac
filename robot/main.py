"""Robot orchestrator — wires the pieces together into a state machine.

This is the entry point that runs on the ROCK 4C+. It is intentionally a
skeleton: each milestone (M3 SLAM, M4 motion, M5 server, M6 coverage,
M7 visual GPS) fills in one more branch.

Run:  python -m robot.main
"""

from __future__ import annotations

import time

from robot.comms.server_client import ServerClient
from robot.config import CONFIG
from robot.drivers.lidar_driver import Lidar
from robot.drivers.serial_link import SerialLink
from robot.navigation.controller import Controller
from robot.perception.odometry import Odometry
from robot.perception.slam import SlamEngine
from shared.schemas import Command, CommandType, Pose2D, RobotState, RobotStatus


class RobotApp:
    def __init__(self) -> None:
        self.state = RobotState.IDLE
        self.pose = Pose2D(x=0.0, y=0.0, theta=0.0)
        # Hardware/services are created lazily per milestone so the skeleton
        # imports cleanly on a dev PC without sensors attached.
        self.lidar: Lidar | None = None
        self.slam: SlamEngine | None = None
        self.odom = Odometry()
        self.link: SerialLink | None = None
        self.controller: Controller | None = None
        self.server: ServerClient | None = None

    def handle_command(self, cmd: Command) -> None:
        if cmd.type == CommandType.START_MAPPING:
            self.state = RobotState.MAPPING
        elif cmd.type == CommandType.START_CLEANING:
            self.state = RobotState.CLEANING
        elif cmd.type == CommandType.STOP:
            self.state = RobotState.IDLE
            if self.link:
                self.link.stop()

    def run(self) -> None:
        # TODO(M3): init Lidar() + SlamEngine(), feed scans, build the map.
        # TODO(M4): init SerialLink() + Controller(), drive to waypoints.
        # TODO(M5): init ServerClient(), publish status + upload finished map.
        # TODO(M7): init VisualLocalizer(), relocalize on startup/pickup.
        print(f"[{CONFIG.robot_id}] starting in state={self.state}")
        try:
            while True:
                if self.server:
                    self.server.publish_status(
                        RobotStatus(
                            robot_id=CONFIG.robot_id,
                            state=self.state,
                            pose=self.pose,
                        )
                    )
                time.sleep(0.1)
        except KeyboardInterrupt:
            if self.link:
                self.link.stop()
            print("\nstopped.")


if __name__ == "__main__":
    RobotApp().run()
