"""FitOS deterministic sizing recommendation engine.

Pure standard-library package. The backend imports :func:`recommend_size`
and the confidence helpers; everything accepts and returns plain
dict/list/str/float/int values so results are JSON-serializable as-is.

Re-exports are lazy (PEP 562) so ``python -m core.recommender`` runs its
demo without a double-import RuntimeWarning. Both import styles work:

    from core import recommend_size
    from core.recommender import recommend_size
"""

from typing import Any

__all__ = [
    "recommend_size",
    "calculate_confidence",
    "calculate_review_agreement",
    "confidence_level",
]

_EXPORTS = {
    "recommend_size": "core.recommender",
    "calculate_confidence": "core.confidence",
    "calculate_review_agreement": "core.confidence",
    "confidence_level": "core.confidence",
}


def __getattr__(name: str) -> Any:
    if name in _EXPORTS:
        import importlib

        return getattr(importlib.import_module(_EXPORTS[name]), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
