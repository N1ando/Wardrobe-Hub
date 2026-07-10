"""FitOS deterministic size recommender.

Given a product (with a size chart and stretch percentage), a shopper's
body measurements, a fit preference, and optional review-sizing analysis,
:func:`recommend_size` scores every size in the chart and returns a
JSON-friendly recommendation dict.

Core business rules
-------------------
* ``raw_ease = garment - body``. Positive ease means room to spare.
* ``effective_ease = raw_ease + garment * stretch_pct * 0.5``: fabric
  stretch effectively adds room, but we only credit half the nominal
  stretch because garments are not comfortable at full extension.
* Stretch excuses tightness, never looseness: effective ease is used for
  scoring only when the raw ease falls below the ideal band. A baggy
  stretchy garment is exactly as baggy as a baggy rigid one.
* Review bias: if reviews clearly say "runs small" we add a +0.08 bonus
  to the next size up (mirrored for "runs large"), shifting borderline
  calls by at most one size and never inventing sizes off the chart.

Only the Python standard library is used. All inputs/outputs are plain
dicts/lists/strs/numbers so the backend can pass them straight to JSON.
"""

from __future__ import annotations

import json
import math
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal, TypedDict

from core.confidence import (
    calculate_confidence,
    calculate_review_agreement,
    confidence_level,
)

Category = Literal["tops", "pants", "dress"]
FitPref = Literal["slim", "regular", "relaxed"]
Verdict = Literal["ideal", "tight", "loose", "missing_data"]

# ---------------------------------------------------------------------------
# Category configuration
# ---------------------------------------------------------------------------

# Free-text category strings we accept, mapped to canonical categories.
_CATEGORY_ALIASES: dict[str, Category] = {
    "tops": "tops",
    "top": "tops",
    "shirt": "tops",
    "tshirt": "tops",
    "t-shirt": "tops",
    "blouse": "tops",
    "pants": "pants",
    "jeans": "pants",
    "trousers": "pants",
    "dress": "dress",
    "dresses": "dress",
}

# Relative importance of each dimension when combining per-dimension
# scores into a single size score. Weights are renormalized over the
# dimensions actually present so one missing field doesn't zero the size.
_DIMENSION_WEIGHTS: dict[Category, dict[str, float]] = {
    "pants": {"waist": 0.45, "hips": 0.35, "inseam": 0.20},
    "tops": {"chest": 0.55, "waist": 0.30, "sleeve": 0.15},
    "dress": {"bust": 0.40, "waist": 0.35, "hips": 0.25},
}

# Ideal ease bands in cm: (lower, upper) per category/dimension/fit_pref.
# Sleeve and inseam are length targets (garment should match body ±2cm),
# so their band is the same for every fit preference.
_EASE_BANDS: dict[Category, dict[str, dict[FitPref, tuple[float, float]]]] = {
    "tops": {
        "chest": {"slim": (4.0, 8.0), "regular": (8.0, 12.0), "relaxed": (12.0, 18.0)},
        "waist": {"slim": (4.0, 10.0), "regular": (8.0, 14.0), "relaxed": (12.0, 20.0)},
        "sleeve": {"slim": (-2.0, 2.0), "regular": (-2.0, 2.0), "relaxed": (-2.0, 2.0)},
    },
    "pants": {
        "waist": {"slim": (0.0, 2.0), "regular": (2.0, 4.0), "relaxed": (4.0, 6.0)},
        "hips": {"slim": (2.0, 5.0), "regular": (4.0, 8.0), "relaxed": (6.0, 12.0)},
        "inseam": {"slim": (-2.0, 2.0), "regular": (-2.0, 2.0), "relaxed": (-2.0, 2.0)},
    },
    "dress": {
        "bust": {"slim": (4.0, 7.0), "regular": (6.0, 10.0), "relaxed": (10.0, 14.0)},
        "waist": {"slim": (3.0, 6.0), "regular": (5.0, 9.0), "relaxed": (8.0, 14.0)},
        "hips": {"slim": (4.0, 8.0), "regular": (6.0, 10.0), "relaxed": (10.0, 15.0)},
    },
}

# Length dimensions use a fixed 4cm tolerance; circumference dimensions
# use max(4, band width) so wide relaxed bands degrade more gently.
_LENGTH_DIMENSIONS = frozenset({"sleeve", "inseam"})

# Body-measurement fallbacks: shoppers often enter "chest" or "bust"
# interchangeably, so each maps to the other. We never invent
# measurements from height/weight.
_BODY_FALLBACKS: dict[str, str] = {"bust": "chest", "chest": "bust"}

# Keys accepted for the size label in chart entries, in priority order.
_LABEL_KEYS = ("size_label", "label", "size")

# Review bias thresholds: reviews must be both loud (>= 25% say small)
# and lopsided (>= 15 points more than the opposite camp) to shift sizes.
_REVIEW_MIN_PCT = 0.25
_REVIEW_MIN_GAP = 0.15
_REVIEW_BONUS = 0.08


class SizeScore(TypedDict):
    """Per-size scoring entry in the output JSON."""

    size: str
    base_score: float
    review_bonus: float
    adjusted_score: float


@dataclass(frozen=True)
class DimensionResult:
    """Internal, unrounded scoring result for one dimension of one size."""

    dim: str
    garment: float | None
    body: float | None
    raw_ease: float | None
    effective_ease: float | None
    scoring_ease: float | None
    ideal_band: tuple[float, float]
    verdict: Verdict
    score: float | None
    weight: float


def _as_float(value: Any) -> float | None:
    """Coerce ints, floats, and numeric strings ("83", "0.03") to float.

    Booleans, non-numeric strings, None, and non-finite values -> None.
    """
    if isinstance(value, bool):
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


def _normalize_category(raw: Any) -> Category:
    """Resolve category aliases; raise ValueError for unsupported ones."""
    if isinstance(raw, str):
        key = raw.strip().lower()
        if key in _CATEGORY_ALIASES:
            return _CATEGORY_ALIASES[key]
    raise ValueError(
        f"Unsupported product category: {raw!r}. "
        f"Supported categories/aliases: {sorted(_CATEGORY_ALIASES)}"
    )


def _normalize_fit_pref(raw: Any) -> FitPref:
    """Default to "regular" for missing or unknown fit preferences."""
    if isinstance(raw, str) and raw.strip().lower() in ("slim", "regular", "relaxed"):
        return raw.strip().lower()  # type: ignore[return-value]
    return "regular"


def _size_label(entry: Mapping[str, Any], index: int) -> str:
    """Pull the size label from a chart row, trying the accepted key names."""
    for key in _LABEL_KEYS:
        value = entry.get(key)
        if value is not None:
            return str(value)
    # Chart order is the size order, so a positional name is still usable.
    return f"size_{index}"


def _body_value(body: Mapping[str, Any], dim: str) -> float | None:
    """Look up a body measurement with chest<->bust fallback."""
    value = _as_float(body.get(dim))
    if value is None and dim in _BODY_FALLBACKS:
        value = _as_float(body.get(_BODY_FALLBACKS[dim]))
    return value


def _score_dimension(
    dim: str,
    garment: float | None,
    body: float | None,
    stretch_pct: float,
    band: tuple[float, float],
    weight: float,
) -> DimensionResult:
    """Score one dimension of one size against its ideal ease band.

    Inside the band scores 1.0; outside, the score decays linearly with
    distance from the band, hitting 0.0 at one tolerance away. Stretch is
    credited only when the garment is tight (raw ease below the band).
    """
    if garment is None or body is None:
        return DimensionResult(
            dim=dim, garment=garment, body=body, raw_ease=None,
            effective_ease=None, scoring_ease=None, ideal_band=band,
            verdict="missing_data", score=None, weight=weight,
        )

    lower, upper = band
    raw_ease = garment - body
    # Half the nominal stretch: garments are not comfy at full extension.
    effective_ease = raw_ease + garment * stretch_pct * 0.5

    # Stretch excuses tightness, never looseness.
    scoring_ease = effective_ease if raw_ease < lower else raw_ease

    if lower <= scoring_ease <= upper:
        score = 1.0
    else:
        distance = (lower - scoring_ease) if scoring_ease < lower else (scoring_ease - upper)
        if dim in _LENGTH_DIMENSIONS:
            tolerance = 4.0
        else:
            tolerance = max(4.0, upper - lower)
        score = 1.0 - min(1.0, abs(distance) / tolerance)

    # Verdict reflects the raw fit; stretch may soften the penalty but a
    # tight garment is still reported as tight.
    if raw_ease < lower:
        verdict: Verdict = "tight"
    elif raw_ease > upper:
        verdict = "loose"
    else:
        verdict = "ideal"

    return DimensionResult(
        dim=dim, garment=garment, body=body, raw_ease=raw_ease,
        effective_ease=effective_ease, scoring_ease=scoring_ease,
        ideal_band=band, verdict=verdict, score=score, weight=weight,
    )


def _score_size(
    entry: Mapping[str, Any],
    body: Mapping[str, Any],
    category: Category,
    fit_pref: FitPref,
    stretch_pct: float,
) -> tuple[float, list[DimensionResult]]:
    """Score one chart row: weighted per-dimension scores, renormalized
    over the dimensions that actually have data."""
    results: list[DimensionResult] = []
    for dim, weight in _DIMENSION_WEIGHTS[category].items():
        band = _EASE_BANDS[category][dim][fit_pref]
        results.append(
            _score_dimension(
                dim=dim,
                garment=_as_float(entry.get(dim)),
                body=_body_value(body, dim),
                stretch_pct=stretch_pct,
                band=band,
                weight=weight,
            )
        )

    scored = [r for r in results if r.score is not None]
    total_weight = sum(r.weight for r in scored)
    if total_weight <= 0.0:
        # No usable dimension at all; the size is unrankable.
        return 0.0, results
    base_score = sum(r.score * r.weight for r in scored if r.score is not None)
    return base_score / total_weight, results


def _review_bias(review_analysis: Mapping[str, Any] | None) -> tuple[str, str | None]:
    """Classify review sizing bias.

    Returns (direction, caveat) where direction is "up" (runs small, so
    nudge toward the next size up), "down" (runs large), or "none".
    """
    if review_analysis is None:
        return "none", None

    pct_small = _as_float(review_analysis.get("pct_small")) or 0.0
    pct_large = _as_float(review_analysis.get("pct_large")) or 0.0
    caveat = review_analysis.get("caveat")
    caveat = caveat if isinstance(caveat, str) else None

    if pct_small >= _REVIEW_MIN_PCT and (pct_small - pct_large) >= _REVIEW_MIN_GAP:
        return "up", caveat or "Reviews suggest this item runs small; consider sizing up."
    if pct_large >= _REVIEW_MIN_PCT and (pct_large - pct_small) >= _REVIEW_MIN_GAP:
        return "down", caveat or "Reviews suggest this item runs large; consider sizing down."
    return "none", None


def _material_note(stretch_pct: float, material: Any) -> str:
    """Human-readable note on how stretch was (or wasn't) used."""
    if stretch_pct <= 0.0:
        return "Rigid fabric (no stretch); ease was scored as measured."
    pct_text = f"{stretch_pct * 100:g}%"
    kind = "knit/jersey" if stretch_pct >= 0.15 else "stretch fabric"
    note = (
        f"{pct_text} stretch detected ({kind}); stretch was only used to "
        "reduce tightness penalties, not looseness."
    )
    if isinstance(material, str) and material.strip():
        note = f"Material: {material.strip()}. {note}"
    return note


def recommend_size(
    product: Mapping[str, Any],
    body_measurements: Mapping[str, float],
    fit_pref: str = "regular",
    review_analysis: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Recommend a size from the product's chart for the given body.

    Deterministic: same inputs always give the same output. The returned
    dict is fully JSON-serializable.

    Error contract — ValueError is the ONLY exception raised for bad
    input, so the backend can map it to a single HTTP error response:
    * product or body_measurements is not a mapping
    * unsupported/missing product category
    * size_chart missing, empty, or containing non-object rows
    review_analysis is optional enrichment: if it has the wrong shape it
    is treated as absent (no review signal) rather than raising.
    """
    if not isinstance(product, Mapping):
        raise ValueError(
            f"product must be a mapping, got {type(product).__name__}"
        )
    if not isinstance(body_measurements, Mapping):
        raise ValueError(
            f"body_measurements must be a mapping, got {type(body_measurements).__name__}"
        )
    if review_analysis is not None and not isinstance(review_analysis, Mapping):
        review_analysis = None

    category = _normalize_category(product.get("category"))
    pref = _normalize_fit_pref(fit_pref)

    size_chart = product.get("size_chart")
    if not isinstance(size_chart, (list, tuple)) or len(size_chart) == 0:
        raise ValueError(
            f"Product {product.get('id')!r} has no size_chart; "
            "expected a non-empty list of size entries."
        )

    stretch_pct = _as_float(product.get("stretch_pct")) or 0.0
    if stretch_pct > 1.0:
        # Sellers sometimes enter whole percentages (3 meaning 3%);
        # anything above 1.0 can't be a fraction, so rescale it.
        stretch_pct /= 100.0
    stretch_pct = max(0.0, stretch_pct)

    # ------------------------------------------------------------------
    # Base scores per size (chart order defines size order).
    # ------------------------------------------------------------------
    labels: list[str] = []
    base_scores: list[float] = []
    breakdowns: list[list[DimensionResult]] = []
    for index, entry in enumerate(size_chart):
        if not isinstance(entry, Mapping):
            raise ValueError(
                f"size_chart entry {index} for product {product.get('id')!r} "
                f"is not an object: {entry!r}"
            )
        labels.append(_size_label(entry, index))
        score, dims = _score_size(entry, body_measurements, category, pref, stretch_pct)
        base_scores.append(score)
        breakdowns.append(dims)

    # ------------------------------------------------------------------
    # Review bias: nudge one adjacent size by +0.08 when reviews clearly
    # say the item runs small ("up") or large ("down"). We find the best
    # base-score size first, then bonus its neighbor, so the shift is at
    # most one size off the pure-measurement pick.
    # ------------------------------------------------------------------
    bias_direction, caveat = _review_bias(review_analysis)
    bonuses = [0.0] * len(labels)
    applied_shift = False
    best_base_index = min(range(len(labels)), key=lambda i: (-base_scores[i], i))
    if bias_direction == "up" and best_base_index + 1 < len(labels):
        bonuses[best_base_index + 1] = _REVIEW_BONUS
        applied_shift = True
    elif bias_direction == "down" and best_base_index - 1 >= 0:
        bonuses[best_base_index - 1] = _REVIEW_BONUS
        applied_shift = True

    adjusted_scores = [min(1.0, b + bonus) for b, bonus in zip(base_scores, bonuses)]

    # Highest adjusted score wins; ties go to the smaller size so we
    # never over-recommend larger sizes.
    best_index = min(range(len(labels)), key=lambda i: (-adjusted_scores[i], i))

    # Runner-up = best adjusted score among the other sizes.
    runner_up: dict[str, Any] | None = None
    second_best_score: float | None = None
    other_indices = [i for i in range(len(labels)) if i != best_index]
    if other_indices:
        second_index = min(other_indices, key=lambda i: (-adjusted_scores[i], i))
        second_best_score = adjusted_scores[second_index]
        runner_up = {"size": labels[second_index], "score": round(second_best_score, 3)}

    # ------------------------------------------------------------------
    # Data completeness: fraction of required fields present in BOTH the
    # recommended size's chart row and the body measurements.
    # ------------------------------------------------------------------
    required = list(_DIMENSION_WEIGHTS[category])
    best_entry = size_chart[best_index]
    missing_fields: list[str] = []
    for dim in required:
        if _as_float(best_entry.get(dim)) is None or _body_value(body_measurements, dim) is None:
            missing_fields.append(dim)
    data_completeness = (len(required) - len(missing_fields)) / len(required)

    confidence = calculate_confidence(
        best_size_score=adjusted_scores[best_index],
        second_best_score=second_best_score,
        data_completeness=data_completeness,
        review_analysis=review_analysis,
    )
    level = confidence_level(confidence, data_completeness)

    # ------------------------------------------------------------------
    # JSON-friendly output (scores to 3 decimals, ease to 2 decimals).
    # ------------------------------------------------------------------
    size_scores: list[SizeScore] = [
        {
            "size": labels[i],
            "base_score": round(base_scores[i], 3),
            "review_bonus": round(bonuses[i], 3),
            "adjusted_score": round(adjusted_scores[i], 3),
        }
        for i in range(len(labels))
    ]

    fit_breakdown: list[dict[str, Any]] = []
    for r in breakdowns[best_index]:
        fit_breakdown.append(
            {
                "dim": r.dim,
                "garment": r.garment,
                "body": r.body,
                "raw_ease": None if r.raw_ease is None else round(r.raw_ease, 2),
                "effective_ease": None if r.effective_ease is None else round(r.effective_ease, 2),
                "scoring_ease": None if r.scoring_ease is None else round(r.scoring_ease, 2),
                "ideal_band": [r.ideal_band[0], r.ideal_band[1]],
                "verdict": r.verdict,
                "score": None if r.score is None else round(r.score, 3),
                "weight": r.weight,
            }
        )

    review_signal: dict[str, Any] | None = None
    if review_analysis is not None:
        review_signal = {
            "pct_small": _as_float(review_analysis.get("pct_small")),
            "pct_large": _as_float(review_analysis.get("pct_large")),
            "pct_tts": _as_float(review_analysis.get("pct_tts")),
            "bias_direction": bias_direction,
            "applied_shift_bias": applied_shift,
            "caveat": caveat,
        }

    margin = 1.0 if second_best_score is None else max(
        0.0, min(1.0, adjusted_scores[best_index] - second_best_score)
    )

    return {
        "recommended_size": labels[best_index],
        "confidence": confidence,
        "confidence_level": level,
        "runner_up": runner_up,
        "size_scores": size_scores,
        "fit_breakdown": fit_breakdown,
        "review_signal": review_signal,
        "material_note": _material_note(stretch_pct, product.get("material")),
        "missing_fields": missing_fields,
        "debug": {
            "category": category,
            "fit_pref": pref,
            "data_completeness": round(data_completeness, 3),
            "review_agreement": round(calculate_review_agreement(review_analysis), 3),
            "margin": round(margin, 3),
        },
    }


if __name__ == "__main__":
    # Smoke demo: python -m core.recommender
    # Prints one JSON document with three scenarios:
    #   1. A clean fit with agreeing reviews -> high confidence.
    #   2. A borderline body without reviews -> size 31 wins narrowly.
    #   3. The same borderline body with runs-small reviews -> the +0.08
    #      bonus flips the recommendation to size 32.
    # stretch_pct is deliberately given as 3 (whole percent) to show the
    # percentage normalization: it is treated as 0.03.
    demo_product = {
        "id": "jeans_001",
        "name": "Stretch Denim Jeans",
        "category": "pants",
        "material": "denim with 3% elastane",
        "stretch_pct": 3,
        "size_chart": [
            {"size_label": "30", "waist": 80, "hips": 96, "inseam": 78},
            {"size_label": "31", "waist": 83, "hips": 99, "inseam": 79},
            {"size_label": "32", "waist": 86, "hips": 102, "inseam": 80},
        ],
    }

    clean_fit_body = {"waist": 80.0, "hips": 95.0, "inseam": 79.0}
    agreeing_reviews = {"pct_small": 0.03, "pct_large": 0.03, "pct_tts": 0.94}

    borderline_body = {"waist": 82.6, "hips": 93.0, "inseam": 79.5}
    runs_small_reviews = {
        "pct_small": 0.55,
        "pct_large": 0.05,
        "pct_tts": 0.40,
        "top_issues": ["tight waistband"],
        "caveat": "Reviews suggest this item runs small.",
    }

    demo = {
        "1_clean_fit_high_confidence": recommend_size(
            demo_product, clean_fit_body, "regular", agreeing_reviews
        ),
        "2_borderline_body_no_reviews": recommend_size(
            demo_product, borderline_body, "regular"
        ),
        "3_borderline_body_runs_small_reviews": recommend_size(
            demo_product, borderline_body, "regular", runs_small_reviews
        ),
    }
    print(json.dumps(demo, indent=2))
