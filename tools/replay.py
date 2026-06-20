"""Replay a recorded JSONL log through SLAM and save the resulting map.

Run on any PC (no hardware needed):
    python -m tools.replay out.jsonl map.png
"""

from __future__ import annotations

import json
import sys

from robot.perception.slam import SlamEngine


def main(log_path: str, _map_out: str) -> None:
    slam = SlamEngine()
    with open(log_path, encoding="utf-8") as f:
        for line in f:
            scan = json.loads(line)["scan"]
            distances = [dist for _angle, dist in scan]
            pose = slam.update(distances)
    print("final pose:", pose)
    # TODO: write slam.occupancy_grid() to a PNG via Pillow.


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "map.png")
