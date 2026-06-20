"""Camera-based "visual GPS" — place recognition for global relocalization.

How it works (deliberately simple, runs on the ROCK 4C+ without a GPU):
  * During mapping, periodically grab a camera frame, compute ORB features,
    and store them as a "keyframe" tagged with the LiDAR pose.
  * To relocalize (startup, or after the robot is picked up and moved), match
    the current frame's ORB features against every keyframe; the best match
    gives a coarse global position that LiDAR SLAM then refines.

This is the realistic version of "GPS from the camera" — it complements LiDAR,
it does not replace it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import cv2  # type: ignore
import numpy as np

from shared.schemas import Pose2D


@dataclass
class Keyframe:
    pose: Pose2D
    descriptors: np.ndarray  # ORB descriptors (N x 32, uint8)


@dataclass
class VisualLocalizer:
    min_good_matches: int = 25
    _orb: cv2.ORB = field(default_factory=lambda: cv2.ORB_create(500))
    _matcher: cv2.BFMatcher = field(
        default_factory=lambda: cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    )
    _keyframes: list[Keyframe] = field(default_factory=list)

    def add_keyframe(self, frame_bgr: np.ndarray, pose: Pose2D) -> bool:
        """Store a keyframe if the frame has enough features. Returns success."""
        _kp, desc = self._orb.detectAndCompute(frame_bgr, None)
        if desc is None or len(desc) < self.min_good_matches:
            return False
        self._keyframes.append(Keyframe(pose=pose, descriptors=desc))
        return True

    def relocalize(self, frame_bgr: np.ndarray) -> Pose2D | None:
        """Return the pose of the best-matching keyframe, or None if unsure."""
        _kp, desc = self._orb.detectAndCompute(frame_bgr, None)
        if desc is None:
            return None

        best: tuple[int, Pose2D] | None = None
        for kf in self._keyframes:
            matches = self._matcher.match(desc, kf.descriptors)
            score = len(matches)
            if score >= self.min_good_matches and (best is None or score > best[0]):
                best = (score, kf.pose)
        return best[1] if best else None
