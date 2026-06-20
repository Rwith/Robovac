"""Camera capture wrapper (OpenCV).

Starts with a USB webcam (simplest for a beginner). Switch `camera_index`
in config.py once you move to a MIPI-CSI camera.
"""

from __future__ import annotations

import cv2  # type: ignore

from robot.config import CONFIG


class Camera:
    def __init__(self, index: int | None = None) -> None:
        self._cap = cv2.VideoCapture(index if index is not None else CONFIG.camera_index)
        if not self._cap.isOpened():
            raise RuntimeError("could not open camera")

    def frame(self):
        """Return the latest BGR frame, or None if capture failed."""
        ok, img = self._cap.read()
        return img if ok else None

    def release(self) -> None:
        self._cap.release()
