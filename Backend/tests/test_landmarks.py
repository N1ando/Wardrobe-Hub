"""Tests for body-proportion landmark location."""

import numpy as np

from app.services.landmarks import locate_fractions


def _build_mask(settings) -> np.ndarray:
    """Symmetric silhouette: narrowest near 0.375, widest near ~0.52."""
    h, w = 800, 400
    mask = np.zeros((h, w), dtype=np.uint8)
    top, bottom = 50, 750
    cx = w // 2
    span = bottom - top
    for r in range(top, bottom + 1):
        f = (r - top) / span
        if 0.30 <= f <= 0.45:
            width = 40 + int(400 * abs(f - 0.375))   # min (=40) at 0.375
        elif 0.45 < f <= 0.60:
            width = 120 - int(400 * abs(f - 0.525))   # max (=120) at 0.525
        else:
            width = 100
        half = max(1, width // 2)
        mask[r, cx - half : cx + half] = 255
    return mask


def test_waist_and_hip_fractions(settings):
    mask = _build_mask(settings)
    fr = locate_fractions(mask, settings)
    assert 0.35 <= fr.waist <= 0.40      # narrowest ~ 3/8
    assert 0.47 <= fr.hip <= 0.58        # widest in hip band
    assert fr.hip > fr.waist
    assert fr.thigh == settings.thigh_fraction


def test_flat_band_falls_back_to_proportion(settings):
    # Uniform-width column -> no meaningful "narrowest" -> fall back to 3/8.
    h, w = 800, 400
    mask = np.zeros((h, w), dtype=np.uint8)
    mask[50:750, 150:250] = 255
    fr = locate_fractions(mask, settings)
    assert fr.waist == settings.waist_fraction
