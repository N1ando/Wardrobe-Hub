"""Deterministic size-recommendation engine (plan Section 4).

Pure Python, zero framework/DB deps: it consumes plain dicts and returns a plain
dict shaped like `schemas.RecommendResponse`. The LLM never picks a size here;
it only explains the output elsewhere. This module is what the persona test
suite pins down.
"""

from __future__ import annotations

from typing import Optional

from app.core.confidence import compute_confidence, review_agreement
from app.core.ease_bands import DimSpec, chart_fields_for_category, spec_for_category

SHIFT_BONUS = 0.08
SMALL_TRIGGER = 0.25
SMALL_MARGIN = 0.15


def _body_value(spec: DimSpec, measurements: dict) -> Optional[float]:
    val = measurements.get(spec.body_key)
    if val is None and spec.body_alt:
        val = measurements.get(spec.body_alt)
    return val


def _score_dimension(
    spec: DimSpec, garment: Optional[float], body: Optional[float], stretch_pct: float, fit_pref: str
) -> dict:
    """Return a fit-breakdown item. `score` is None when the dim can't be scored."""
    item = {"dim": spec.dim, "garment": garment, "body": body, "ease": None,
            "verdict": "missing_data", "score": None}

    if garment is None or body is None:
        return item

    raw_ease = round(garment - body, 1)
    item["ease"] = raw_ease

    # Target-based dimension (inseam): ideal when garment length ~= body length.
    if spec.target_based:
        distance = max(0.0, abs(raw_ease) - 2.0)
        score = 1.0 - min(1.0, distance / spec.tolerance)
        item["score"] = round(score, 3)
        item["verdict"] = "ideal" if distance == 0 else ("tight" if raw_ease < 0 else "loose")
        return item

    # No band (e.g. sleeve) => informational only, unscored.
    if spec.bands is None:
        item["verdict"] = "info"
        return item

    low, high = spec.bands.get(fit_pref, spec.bands["regular"])
    # Stretch can excuse tightness, never looseness.
    eff_ease = raw_ease + garment * stretch_pct * 0.5
    lower_val = eff_ease
    upper_val = raw_ease

    if lower_val < low:
        distance = low - lower_val
        verdict = "tight"
    elif upper_val > high:
        distance = upper_val - high
        verdict = "loose"
    else:
        item["score"] = 1.0
        item["verdict"] = "ideal"
        return item

    penalty = min(1.0, distance / spec.tolerance)
    item["score"] = round(1.0 - penalty, 3)
    item["verdict"] = verdict
    return item


def _score_size(
    specs: list[DimSpec], row: dict, measurements: dict, stretch_pct: float, fit_pref: str
) -> tuple[float, list[dict]]:
    breakdown: list[dict] = []
    weighted_sum = 0.0
    weight_total = 0.0
    for spec in specs:
        item = _score_dimension(
            spec, row.get(spec.chart_key), _body_value(spec, measurements), stretch_pct, fit_pref
        )
        breakdown.append(item)
        if item["score"] is not None:
            weighted_sum += spec.weight * item["score"]
            weight_total += spec.weight
    size_score = weighted_sum / weight_total if weight_total else 0.0
    return round(size_score, 4), breakdown


def _data_completeness(specs: list[DimSpec], rows: list[dict]) -> tuple[float, list[str]]:
    """Return (completeness, missing_fields).

    Completeness is the fraction of *scored* fields present (drives confidence).
    missing_fields lists every garment field absent from the chart, including
    unscored ones like sleeve, so the buyer/seller UI can surface them.
    """
    scored = [s for s in specs if s.bands is not None or s.target_based]
    scored_present = 0
    missing: list[str] = []
    for spec in specs:
        has_any = any(r.get(spec.chart_key) is not None for r in rows)
        if has_any:
            if spec in scored:
                scored_present += 1
        else:
            missing.append(spec.chart_key)
    completeness = scored_present / len(scored) if scored else 1.0
    return completeness, missing


def recommend(
    *,
    category: str,
    size_chart: list[dict],
    measurements: dict,
    fit_pref: str = "regular",
    stretch_pct: float = 0.0,
    material: Optional[str] = None,
    review_analysis: Optional[dict] = None,
) -> dict:
    """Core entry point. See module docstring for contract."""
    specs = spec_for_category(category)

    rows = sorted(size_chart, key=lambda r: r.get("order_index", 0))
    if not rows:
        return {
            "recommended_size": "?", "confidence": 35, "runner_up": None,
            "fit_breakdown": [], "review_signal": None, "material_note": None,
            "missing_fields": chart_fields_for_category(category), "low_confidence": True,
        }

    scored = []  # (index, size_label, score, breakdown)
    for i, row in enumerate(rows):
        score, breakdown = _score_size(specs, row, measurements, stretch_pct, fit_pref)
        scored.append({"index": i, "size": row["size_label"], "score": score,
                       "breakdown": breakdown})

    # --- Review shift bias (never more than one size) ---
    review_signal = None
    applied_shift = False
    pre_best = max(scored, key=lambda s: s["score"])
    if review_analysis:
        pct_small = review_analysis.get("pct_small", 0.0)
        pct_large = review_analysis.get("pct_large", 0.0)
        pct_tts = review_analysis.get("pct_tts", 0.0)
        caveat = None
        top_issues = review_analysis.get("top_issues") or []
        top_area = top_issues[0]["area"] if top_issues and "area" in top_issues[0] else None

        if pct_small >= SMALL_TRIGGER and (pct_small - pct_large) >= SMALL_MARGIN:
            nxt = pre_best["index"] + 1
            if nxt < len(scored):
                scored[nxt]["score"] = round(scored[nxt]["score"] + SHIFT_BONUS, 4)
                applied_shift = True
            caveat = f"runs small{f' in {top_area}' if top_area else ''}"
        elif pct_large >= SMALL_TRIGGER and (pct_large - pct_small) >= SMALL_MARGIN:
            prv = pre_best["index"] - 1
            if prv >= 0:
                scored[prv]["score"] = round(scored[prv]["score"] + SHIFT_BONUS, 4)
                applied_shift = True
            caveat = f"runs large{f' in {top_area}' if top_area else ''}"

        review_signal = {
            "pct_small": round(pct_small, 2), "pct_tts": round(pct_tts, 2),
            "pct_large": round(pct_large, 2), "caveat": caveat,
            "applied_shift_bias": applied_shift,
        }

    ranked = sorted(scored, key=lambda s: s["score"], reverse=True)
    best = ranked[0]
    second = ranked[1] if len(ranked) > 1 else None

    completeness, missing = _data_completeness(specs, rows)
    agreement = 1.0
    if review_analysis:
        agreement = review_agreement(
            review_analysis.get("pct_small", 0.0),
            review_analysis.get("pct_tts", 0.0),
            review_analysis.get("pct_large", 0.0),
        )

    confidence = compute_confidence(
        best_score=min(best["score"], 1.0),
        second_score=second["score"] if second else 0.0,
        data_completeness=completeness,
        review_agreement_value=agreement,
    )

    material_note = None
    if stretch_pct >= 0.03 and material:
        pct = round(stretch_pct * 100)
        material_note = f"{material} (~{pct}% stretch) tolerates a little less ease"

    return {
        "recommended_size": best["size"],
        "confidence": confidence,
        "runner_up": ({"size": second["size"], "score": round(second["score"], 2)}
                      if second else None),
        "fit_breakdown": best["breakdown"],
        "review_signal": review_signal,
        "material_note": material_note,
        "missing_fields": missing,
        # Low both when the chart is too sparse AND when the overall confidence
        # is weak (e.g. the shopper supplied no usable measurements): a floor-35
        # answer must never render as a normal, trustworthy-looking result.
        "low_confidence": completeness < 0.5 or confidence < 60,
    }
