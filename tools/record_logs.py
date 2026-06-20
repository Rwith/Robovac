"""Record LiDAR + odometry to a JSONL file for offline SLAM/nav testing.

Letting you replay real sensor data on your dev PC means you don't have to
drive the hardware every time you tweak SLAM or path planning.

Run on the robot:  python -m tools.record_logs out.jsonl
"""

from __future__ import annotations

import json
import sys
import time

from robot.drivers.lidar_driver import Lidar


def main(path: str) -> None:
    lidar = Lidar()
    with open(path, "w", encoding="utf-8") as f:
        try:
            for scan in lidar.scans():
                f.write(json.dumps({"t": time.time(), "scan": scan}) + "\n")
        except KeyboardInterrupt:
            pass
        finally:
            lidar.stop()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "out.jsonl")
