"""Confidence scoring for FitOS size recommendations.

Business rules implemented here:

* ``review_agreement`` measures how much reviewers agree with each other
  about an item's sizing. It is ``1 - normalized_entropy`` over the
  (pct_small, pct_tts, pct_large) distribution: if everyone says
  "true to size" agreement is ~1.0; if opinions are split three ways
  agreement approaches 0.0. Missing/all-zero review data yields a
  neutral 0.5 so absent reviews neither help nor hurt confidence.

* ``calculate_confidence`` blends four signals into a 0-100 integer:
  how well the best size fits (45%), how clearly it beats the runner-up
  (20%), how complete the size-chart/body data was (20%), and reviewer
  agreement (15%). Confidence is floored at 35 (we never claim total
  ignorance to shoppers) and capped at 96 (sizing is never a guarantee).

Only the Python standard library is used.
"""

from __future__ import annotations

import math
from typing import Any, Mapping

# Business floor/cap: never tell a shopper 0% or 100% certainty.
CONFIDENCE_FLOOR = 35
CONFIDENCE_CAP = 96

# Used when review data is missing or degenerate (all zeros).
NEUTRAL_REVIEW_AGREEMENT = 0.5

_REVIEW_PCT_KEYS = ("pct_small", "pct_tts", "pct_large")


def _as_float(value: Any) -> float | None:
    """Coerce ints, floats, and numeric strings ("83", "0.03") to float.

    Booleans, non-numeric strings, None, and non-finite values -> None.
    """
    if isinstance(value, bool):  # bool is an int subclass; reject explicitly
        return None
    if isinstance(value, (int, float)):
        result = float(value)
    elif isinstance(value, str):
        try:
            result = float(value.strip())
        except ValueError:
            return None
    else:
        return None
    return result if math.isfinite(result) else None


def calculate_review_agreement(review_analysis: Mapping[str, Any] | None) -> float:
    """Return reviewer agreement in [0, 1] as 1 - normalized entropy.

    Uses only the positive probabilities among pct_small/pct_tts/pct_large,
    normalizing them if they do not sum to 1. A single dominant opinion
    (e.g. pct_tts=1.0) gives agreement 1.0; a uniform three-way split gives
    0.0. Missing or all-zero data returns the neutral 0.5.
    """
    if review_analysis is None:
        return NEUTRAL_REVIEW_AGREEMENT

    probs = []
    for key in _REVIEW_PCT_KEYS:
        value = _as_float(review_analysis.get(key))
        if value is not None and value > 0.0:
            probs.append(value)

    if not probs:
        return NEUTRAL_REVIEW_AGREEMENT

    total = sum(probs)
    if total <= 0.0:
        return NEUTRAL_REVIEW_AGREEMENT
    probs = [p / total for p in probs]

    if len(probs) == 1:
        # One voice only: perfect agreement (entropy is 0, log(1) undefined).
        return 1.0

    entropy = -sum(p * math.log(p) for p in probs) / math.log(len(probs))
    return max(0.0, min(1.0, 1.0 - entropy))


def calculate_confidence(
    best_size_score: float,
    second_best_score: float | None,
    data_completeness: float,
    review_analysis: Mapping[str, Any] | None,
) -> int:
    """Blend fit quality, margin, data completeness, and review agreement.

    ``second_best_score`` is None when the chart has a single size; the
    margin term is then 1.0 because there is no competing alternative.
    Result is an int in [CONFIDENCE_FLOOR, CONFIDENCE_CAP].
    """
    if second_best_score is None:
        margin = 1.0
    else:
        margin = min(1.0, max(0.0, best_size_score - second_best_score))

    review_agreement = calculate_review_agreement(review_analysis)

    confidence = 100.0 * (
        0.45 * best_size_score
        + 0.20 * margin
        + 0.20 * data_completeness
        + 0.15 * review_agreement
    )
    confidence = max(float(CONFIDENCE_FLOOR), min(float(CONFIDENCE_CAP), confidence))
    return round(confidence)


def confidence_level(confidence: int, data_completeness: float) -> str:
    """Map numeric confidence to "low" / "medium" / "high".

    Incomplete data (< 50% of required chart fields) always reads "low",
    no matter how good the numeric score looks — we refuse to sound sure
    when we barely saw the size chart.
    """
    if confidence < 60 or data_completeness < 0.5:
        return "low"
    if confidence < 80:
        return "medium"
    return "high"
