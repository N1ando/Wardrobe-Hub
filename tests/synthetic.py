"""Generate synthetic dark-on-white silhouettes for deterministic tests.

The figures are drawn dark on a white background so the Otsu ``threshold``
backend segments them without needing any ML model.
"""

from __future__ import annotations

import cv2
import numpy as np

_DARK = (30, 30, 30)
_WHITE = 255


def front_array() -> np.ndarray:
    """A standing figure, front view: hourglass torso + two spread legs."""
    h, w = 800, 400
    img = np.full((h, w, 3), _WHITE, dtype=np.uint8)
    cx = w // 2

    # Head (top ~= y=30) + neck bridging head to torso (single component).
    cv2.circle(img, (cx, 70), 40, _DARK, -1)
    cv2.rectangle(img, (cx - 18, 100), (cx + 18, 130), _DARK, -1)

    # Hourglass torso: shoulders wide, waist narrow (~y=300), hips wide (~y=430).
    # Points ordered clockwise: left shoulder, right shoulder, right waist,
    # right hip, left hip, left waist.
    torso = np.array(
        [
            [cx - 80, 120], [cx + 80, 120],
            [cx + 40, 300], [cx + 80, 430],
            [cx - 80, 430], [cx - 40, 300],
        ],
        dtype=np.int32,
    )
    cv2.fillPoly(img, [torso], _DARK)

    # Two legs with a central gap (bottom ~= y=780).
    cv2.rectangle(img, (cx - 70, 430), (cx - 15, 780), _DARK, -1)
    cv2.rectangle(img, (cx + 15, 430), (cx + 70, 780), _DARK, -1)
    return img


def side_array() -> np.ndarray:
    """A standing figure, side view: single depth column, overlapping legs."""
    h, w = 800, 300
    img = np.full((h, w, 3), _WHITE, dtype=np.uint8)
    cx = w // 2

    cv2.circle(img, (cx, 70), 40, _DARK, -1)
    cv2.rectangle(img, (cx - 18, 100), (cx + 18, 130), _DARK, -1)  # neck
    # Torso with a slight belly bulge toward the front.
    torso = np.array(
        [
            [cx - 45, 120], [cx + 45, 120],
            [cx + 55, 300], [cx + 50, 430],
            [cx - 50, 430], [cx - 45, 300],
        ],
        dtype=np.int32,
    )
    cv2.fillPoly(img, [torso], _DARK)
    # Legs overlap into one run in profile.
    cv2.rectangle(img, (cx - 40, 430), (cx + 40, 780), _DARK, -1)
    return img


def to_png(arr: np.ndarray) -> bytes:
    ok, buf = cv2.imencode(".png", cv2.cvtColor(arr, cv2.COLOR_RGB2BGR))
    assert ok
    return buf.tobytes()
