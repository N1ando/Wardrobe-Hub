"""End-to-end measurement pipeline: bytes in, circumferences out."""

from __future__ import annotations

from app.config import Settings
from app.services.landmarks import locate_fractions
from app.services.measure import measure
from app.services.segmentation import extract_silhouette
from app.utils.imaging import decode_image, overlay_b64, resize_max


def run_measurement(
    front_bytes: bytes,
    side_bytes: bytes,
    height_value: float,
    settings: Settings,
    debug: bool = False,
) -> dict:
    """Estimate waist, lower-hip, and thigh circumferences.

    ``height_value`` is in whatever unit the caller uses; every returned
    circumference is in that same unit (the ratio is unit-agnostic).
    """
    # 1. Decode + normalize.
    front_img = resize_max(decode_image(front_bytes), settings.max_image_dim)
    side_img = resize_max(decode_image(side_bytes), settings.max_image_dim)

    # 2. Segment both views into clean binary masks.
    front_mask = extract_silhouette(front_img, settings)
    side_mask = extract_silhouette(side_img, settings)

    # 3. Locate landmarks (fractions) from the front view.
    fractions = locate_fractions(front_mask, settings)

    # 4. Measure widths -> circumferences.
    result = measure(front_mask, side_mask, fractions, height_value, settings)

    # 5. Optional debug overlays for visual verification.
    if debug:
        front_rows = result["diagnostics"]["front"]["rows"]
        side_rows = result["diagnostics"]["side"]["rows"]
        result["diagnostics"]["overlays"] = {
            "front": overlay_b64(front_img, front_mask, front_rows),
            "side": overlay_b64(side_img, side_mask, side_rows),
        }
    return result
