"""Quickly view a stored occupancy-grid PNG (sanity check for M3/M5).

    python -m tools.map_viewer server/store/maps/house.png
"""

from __future__ import annotations

import sys

import cv2  # type: ignore


def main(path: str) -> None:
    img = cv2.imread(path)
    if img is None:
        raise SystemExit(f"could not read {path}")
    cv2.imshow("robovac map", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main(sys.argv[1])
