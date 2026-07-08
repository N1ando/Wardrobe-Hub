"""Locate body landmarks (as fractions of body height) from a front-view mask.

Per the paper, landmarks sit at fixed body proportions measured from the top of
the head: waist ~3/8, lower hip ~1/2, thigh ~5/8. We refine the waist and hip
within a band because a person's narrowest waist / widest hip rarely lands on the
exact proportion. The resulting fractions are applied to *both* the front and
side images so the two views measure the same anatomical level.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from app.config import Settings
from app.errors import NoPersonDetectedError
from app.utils.imaging import vertical_extent


@dataclass(frozen=True)
class BodyFractions:
    """Landmark positions as fractions of body height (0 = head, 1 = feet)."""

    waist: float
    hip: float
    thigh: float


def _row_widths(mask: np.ndarray, top: int, bottom: int) -> np.ndarray:
    """Foreground pixel count per row for rows ``top..bottom`` inclusive."""
    return np.count_nonzero(mask[top : bottom + 1] > 0, axis=1)


def locate_fractions(mask: np.ndarray, settings: Settings) -> BodyFractions:
    top, bottom = vertical_extent(mask)
    height_px = bottom - top
    if height_px < settings.min_person_height_px:
        raise NoPersonDetectedError("Subject too small in frame to measure.")

    widths = _row_widths(mask, top, bottom)  # index i -> row (top + i)

    waist_frac = _narrowest_fraction(
        widths, height_px, settings.waist_band_low, settings.waist_band_high,
        settings.waist_fraction, settings.flatness_eps,
    )
    hip_frac = _widest_fraction(
        widths, height_px, settings.hip_band_low, settings.hip_band_high,
        settings.hip_fraction,
    )
    return BodyFractions(waist=waist_frac, hip=hip_frac, thigh=settings.thigh_fraction)


def _narrowest_fraction(
    widths: np.ndarray, height_px: int, low: float, high: float,
    fallback: float, flatness_eps: float,
) -> float:
    lo, hi = int(low * height_px), int(high * height_px)
    band = widths[lo : hi + 1]
    if band.size == 0:
        return fallback
    band_max = int(band.max())
    if band_max == 0 or (band_max - int(band.min())) / band_max < flatness_eps:
        return fallback  # band is essentially flat -> trust the proportion
    return (lo + int(np.argmin(band))) / height_px


def _widest_fraction(
    widths: np.ndarray, height_px: int, low: float, high: float, fallback: float,
) -> float:
    lo, hi = int(low * height_px), int(high * height_px)
    band = widths[lo : hi + 1]
    if band.size == 0 or int(band.max()) == 0:
        return fallback
    return (lo + int(np.argmax(band))) / height_px
