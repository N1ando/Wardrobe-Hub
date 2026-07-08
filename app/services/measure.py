"""Convert masks + landmark fractions into body circumferences.

Method (from the paper):
  * Pixel-to-unit ratio per image: ratio = known_height / person_height_px (Eq. 2).
    Front and side photos each get their own ratio (different scales).
  * At each landmark, the front width gives the ellipse's long axis and the side
    width (body depth) gives the short axis.
  * Circumference via the RMS ellipse-perimeter approximation (Eq. 9):
        C = 2*pi*sqrt((a^2 + b^2) / 2),  a = front_width/2, b = side_width/2.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from app.config import Settings
from app.services.landmarks import BodyFractions
from app.utils.imaging import (
    single_leg_width_px,
    torso_width_px,
    vertical_extent,
)


@dataclass(frozen=True)
class ImageScale:
    ratio: float  # units per pixel
    top: int
    height_px: int

    @property
    def bottom(self) -> int:
        return self.top + self.height_px


def image_scale(mask: np.ndarray, height_units: float) -> ImageScale:
    top, bottom = vertical_extent(mask)
    height_px = bottom - top
    return ImageScale(ratio=height_units / height_px, top=top, height_px=height_px)


def circumference(front_width: float, side_width: float) -> float:
    """Ellipse perimeter (Eq. 9) from front width and side depth, in units."""
    a = front_width / 2.0
    b = side_width / 2.0
    return 2.0 * math.pi * math.sqrt((a * a + b * b) / 2.0)


def _row_at(scale: ImageScale, frac: float) -> int:
    row = int(round(scale.top + frac * scale.height_px))
    return min(max(row, scale.top), scale.bottom)


def measure(
    front_mask: np.ndarray,
    side_mask: np.ndarray,
    fractions: BodyFractions,
    height_units: float,
    settings: Settings,
) -> dict:
    """Return circumferences (in the height's unit) plus diagnostics."""
    front = image_scale(front_mask, height_units)
    side = image_scale(side_mask, height_units)

    # Waist & lower hip: solid torso -> full row width on both views.
    waist_rows = (_row_at(front, fractions.waist), _row_at(side, fractions.waist))
    hip_rows = (_row_at(front, fractions.hip), _row_at(side, fractions.hip))

    waist_fw = torso_width_px(front_mask, waist_rows[0]) * front.ratio
    waist_sw = torso_width_px(side_mask, waist_rows[1]) * side.ratio
    hip_fw = torso_width_px(front_mask, hip_rows[0]) * front.ratio
    hip_sw = torso_width_px(side_mask, hip_rows[1]) * side.ratio

    # Thigh: in the front view legs are side by side -> single-leg width.
    # In the side view the legs overlap into one run -> that run is a leg's depth.
    thigh_rows = (_row_at(front, fractions.thigh), _row_at(side, fractions.thigh))
    thigh_fw = single_leg_width_px(front_mask, thigh_rows[0]) * front.ratio
    thigh_sw = torso_width_px(side_mask, thigh_rows[1]) * side.ratio

    measurements = {
        "waist": circumference(waist_fw, waist_sw),
        "low_hip": circumference(hip_fw, hip_sw),
        "thigh": circumference(thigh_fw, thigh_sw),
    }
    diagnostics = {
        "fractions": {
            "waist": fractions.waist,
            "low_hip": fractions.hip,
            "thigh": fractions.thigh,
        },
        "front": {
            "ratio": front.ratio,
            "top": front.top,
            "height_px": front.height_px,
            "rows": {
                "waist": waist_rows[0],
                "low_hip": hip_rows[0],
                "thigh": thigh_rows[0],
            },
            "widths_units": {"waist": waist_fw, "low_hip": hip_fw, "thigh": thigh_fw},
        },
        "side": {
            "ratio": side.ratio,
            "top": side.top,
            "height_px": side.height_px,
            "rows": {
                "waist": waist_rows[1],
                "low_hip": hip_rows[1],
                "thigh": thigh_rows[1],
            },
            "widths_units": {"waist": waist_sw, "low_hip": hip_sw, "thigh": thigh_sw},
        },
    }
    return {"measurements": measurements, "diagnostics": diagnostics}
