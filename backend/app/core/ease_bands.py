"""Ease bands and per-garment scoring configuration (plan Section 4).

Pure data + tiny helpers, no framework deps. Ease bands are in centimetres and
are the *starting* values from the plan; tune against the persona suite.
"""

from __future__ import annotations

from dataclasses import dataclass

# Fit preferences
FITS = ("slim", "regular", "relaxed")


@dataclass(frozen=True)
class DimSpec:
    """One scored dimension of a garment.

    body_key:  which measurement in the user's body dict feeds this dimension
               (falls back to `body_alt` if the primary is missing).
    chart_key: the size-chart column.
    weight:    relative importance within the garment (weights re-normalise if a
               dimension can't be scored).
    bands:     {fit: (low_cm, high_cm)} ideal ease window. None => target-based
               (used for inseam, where the target is the body measurement itself).
    tolerance: cm over which the score decays from 1.0 to 0.0 outside the band.
    """

    dim: str
    chart_key: str
    body_key: str
    weight: float
    bands: dict[str, tuple[float, float]] | None
    tolerance: float
    body_alt: str | None = None
    target_based: bool = False  # inseam: ideal when garment ~= body value


# Ease bands transcribed from the plan's table.
_TOP = [
    DimSpec("chest", "chest", "chest", 0.55,
            {"slim": (4, 8), "regular": (8, 12), "relaxed": (12, 18)}, tolerance=6),
    DimSpec("waist", "waist", "waist", 0.30,
            {"slim": (4, 10), "regular": (8, 14), "relaxed": (12, 20)}, tolerance=7),
    DimSpec("sleeve", "sleeve", "sleeve", 0.15, None, tolerance=4),  # usually unscored
]

_PANTS = [
    DimSpec("waist", "waist", "waist", 0.45,
            {"slim": (0, 2), "regular": (2, 4), "relaxed": (4, 6)}, tolerance=3),
    DimSpec("hips", "hips", "hips", 0.35,
            {"slim": (2, 5), "regular": (4, 8), "relaxed": (6, 12)}, tolerance=5),
    DimSpec("inseam", "inseam", "inseam", 0.20, None, tolerance=4, target_based=True),
]

_JACKET = [
    DimSpec("chest", "chest", "chest", 0.60,
            {"slim": (8, 12), "regular": (12, 16), "relaxed": (16, 22)}, tolerance=6),
    DimSpec("waist", "waist", "waist", 0.25,
            {"slim": (6, 12), "regular": (10, 16), "relaxed": (14, 22)}, tolerance=7),
    DimSpec("sleeve", "sleeve", "sleeve", 0.15, None, tolerance=4),
]

_DRESS = [
    DimSpec("bust", "chest", "bust", 0.40,
            {"slim": (4, 7), "regular": (6, 10), "relaxed": (10, 14)},
            tolerance=6, body_alt="chest"),
    DimSpec("waist", "waist", "waist", 0.35,
            {"slim": (3, 6), "regular": (5, 9), "relaxed": (8, 14)}, tolerance=6),
    DimSpec("hips", "hips", "hips", 0.25,
            {"slim": (4, 8), "regular": (6, 10), "relaxed": (10, 15)}, tolerance=5),
]

# Normalise loose category strings to a spec.
_CATEGORY_ALIASES = {
    "shirt": _TOP, "top": _TOP, "tshirt": _TOP, "t-shirt": _TOP, "blouse": _TOP,
    "pants": _PANTS, "jeans": _PANTS, "trousers": _PANTS, "shorts": _PANTS,
    "jacket": _JACKET, "coat": _JACKET, "blazer": _JACKET,
    "dress": _DRESS, "gown": _DRESS,
}


def spec_for_category(category: str) -> list[DimSpec]:
    """Return the dimension specs for a product category (defaults to tops)."""
    return _CATEGORY_ALIASES.get((category or "").strip().lower(), _TOP)


def chart_fields_for_category(category: str) -> list[str]:
    """Chart columns this garment needs (used for data-completeness / missing)."""
    return [s.chart_key for s in spec_for_category(category)]
