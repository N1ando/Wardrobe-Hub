"""Chart-field requirements per garment category.

Used by the seller analytics for completeness / missing-field checks. The
scoring itself lives in the shared repo-root engine (``core/``); this module
only maps categories to the DB chart columns. Note: dress bust is stored in
the ``chest`` column (no bust column) — the recommend router adapter surfaces
it to the engine under ``bust``.
"""

from __future__ import annotations

_CATEGORY_FIELDS = {
    "tops": ["chest", "waist", "sleeve"],
    "pants": ["waist", "hips", "inseam"],
    "dress": ["chest", "waist", "hips"],  # chest column holds bust for dresses
}

_ALIASES = {
    "shirt": "tops", "top": "tops", "tops": "tops", "tshirt": "tops",
    "t-shirt": "tops", "blouse": "tops",
    "jacket": "tops", "coat": "tops", "blazer": "tops",
    "pants": "pants", "jeans": "pants", "trousers": "pants", "shorts": "pants",
    "dress": "dress", "dresses": "dress", "gown": "dress",
}


def chart_fields_for_category(category: str) -> list[str]:
    """DB chart columns this garment needs (drives completeness checks)."""
    canonical = _ALIASES.get((category or "").strip().lower(), "tops")
    return list(_CATEGORY_FIELDS[canonical])
