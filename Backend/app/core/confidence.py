"""Confidence scoring (plan Section 4).

confidence = 100 * (0.45*best_size_score
                  + 0.20*margin              # best - second_best, capped
                  + 0.20*data_completeness    # fraction of needed fields present
                  + 0.15*review_agreement)    # 1 - entropy of small/tts/large
Floored at 35, capped at 96.
"""

from __future__ import annotations

import math

FLOOR = 35
CAP = 96
_MARGIN_CAP = 0.25  # a 0.25 gap between best and runner-up counts as "max margin"


def review_agreement(pct_small: float, pct_tts: float, pct_large: float) -> float:
    """1 - normalised Shannon entropy of the small/tts/large distribution.

    1.0 => reviewers fully agree; 0.0 => evenly split three ways.
    """
    parts = [p for p in (pct_small, pct_tts, pct_large) if p > 0]
    total = sum(parts)
    if total <= 0 or len(parts) <= 1:
        return 1.0
    probs = [p / total for p in parts]
    entropy = -sum(p * math.log(p) for p in probs)
    max_entropy = math.log(3)  # three possible outcomes
    return max(0.0, 1.0 - entropy / max_entropy)


def compute_confidence(
    best_score: float,
    second_score: float,
    data_completeness: float,
    review_agreement_value: float = 1.0,
) -> int:
    margin = min(1.0, max(0.0, best_score - second_score) / _MARGIN_CAP)
    raw = (
        0.45 * best_score
        + 0.20 * margin
        + 0.20 * data_completeness
        + 0.15 * review_agreement_value
    )
    value = round(100 * raw)
    return max(FLOOR, min(CAP, value))
