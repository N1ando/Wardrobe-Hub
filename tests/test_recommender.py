"""Regression tests for the FitOS deterministic size recommender.

All products here are seeded dummy data; every assertion is deterministic
because the engine uses no randomness and no external calls.
"""

from __future__ import annotations

from typing import Any

import pytest

from core.confidence import calculate_review_agreement
from core.recommender import recommend_size

# ---------------------------------------------------------------------------
# Seeded dummy products
# ---------------------------------------------------------------------------

TOP: dict[str, Any] = {
    "id": "top_001",
    "name": "Classic Oxford Shirt",
    "category": "shirt",  # alias for "tops"
    "material": "rigid cotton",
    "stretch_pct": 0.0,
    "size_chart": [
        {"size_label": "S", "chest": 96, "waist": 90, "sleeve": 60},
        {"size_label": "M", "chest": 102, "waist": 96, "sleeve": 62},
        {"size_label": "L", "chest": 108, "waist": 102, "sleeve": 64},
    ],
}

PANTS: dict[str, Any] = {
    "id": "jeans_001",
    "name": "Rigid Selvedge Jeans",
    "category": "jeans",  # alias for "pants"
    "material": "100% cotton denim",
    "stretch_pct": 0.0,
    "size_chart": [
        {"size_label": "30", "waist": 80, "hips": 96, "inseam": 78},
        {"size_label": "31", "waist": 83, "hips": 99, "inseam": 79},
        {"size_label": "32", "waist": 86, "hips": 102, "inseam": 80},
        {"size_label": "33", "waist": 89, "hips": 105, "inseam": 81},
    ],
}

DRESS: dict[str, Any] = {
    "id": "dress_001",
    "name": "A-Line Midi Dress",
    "category": "dresses",  # alias for "dress"
    "material": "polyester blend",
    "stretch_pct": 0.0,
    "size_chart": [
        {"size_label": "S", "bust": 88, "waist": 70, "hips": 94},
        {"size_label": "M", "bust": 94, "waist": 76, "hips": 100},
        {"size_label": "L", "bust": 100, "waist": 82, "hips": 106},
    ],
}

# Body that fits PANTS size 31 perfectly at "regular" fit.
PANTS_BODY = {"waist": 80.0, "hips": 93.0, "inseam": 79.0}

REQUIRED_OUTPUT_KEYS = {
    "recommended_size", "confidence", "confidence_level", "runner_up",
    "size_scores", "fit_breakdown", "review_signal", "material_note",
    "missing_fields", "debug",
}


def _score_entry(result: dict[str, Any], size: str) -> dict[str, Any]:
    return next(s for s in result["size_scores"] if s["size"] == size)


def _dim_entry(result: dict[str, Any], dim: str) -> dict[str, Any]:
    return next(d for d in result["fit_breakdown"] if d["dim"] == dim)


# 1. Pants regular fit recommends the expected middle size.
def test_pants_regular_recommends_middle_size():
    result = recommend_size(PANTS, PANTS_BODY, "regular")
    assert result["recommended_size"] == "31"
    assert _score_entry(result, "31")["adjusted_score"] == 1.0
    assert REQUIRED_OUTPUT_KEYS <= set(result)


# 2. Relaxed fit shifts the recommendation one size up versus regular.
def test_pants_relaxed_recommends_one_size_up():
    regular = recommend_size(PANTS, PANTS_BODY, "regular")
    relaxed = recommend_size(PANTS, PANTS_BODY, "relaxed")
    assert regular["recommended_size"] == "31"
    assert relaxed["recommended_size"] == "32"


# 3. Top scoring returns a fit breakdown for chest, waist, and sleeve.
def test_top_scoring_and_breakdown():
    body = {"chest": 92.0, "waist": 84.0, "sleeve": 61.0}
    result = recommend_size(TOP, body, "regular")
    assert result["recommended_size"] == "M"
    assert {d["dim"] for d in result["fit_breakdown"]} == {"chest", "waist", "sleeve"}
    # M is a perfect regular fit: chest ease 10, waist ease 12, sleeve ease 1.
    for dim in ("chest", "waist", "sleeve"):
        assert _dim_entry(result, dim)["verdict"] == "ideal"
    # Sanity: score ordering S < M and L < M.
    scores = {s["size"]: s["adjusted_score"] for s in result["size_scores"]}
    assert scores["M"] > scores["S"] and scores["M"] > scores["L"]


# 4. Dress accepts "chest" as a fallback body key for bust.
def test_dress_chest_fallback_for_bust():
    body = {"chest": 86.0, "waist": 69.0, "hips": 92.0}  # no "bust" key
    result = recommend_size(DRESS, body, "regular")
    assert result["recommended_size"] == "M"
    bust = _dim_entry(result, "bust")
    assert bust["body"] == 86.0
    assert bust["verdict"] == "ideal"
    assert "bust" not in result["missing_fields"]


# 5. Stretch improves a tight waist score versus rigid fabric.
def test_stretch_improves_tight_waist_score():
    chart = [{"size_label": "M", "waist": 82, "hips": 100, "inseam": 78}]
    body = {"waist": 81.0, "hips": 94.0, "inseam": 78.0}  # waist raw ease = 1 (tight)
    rigid = dict(PANTS, size_chart=chart, stretch_pct=0.0)
    stretchy = dict(PANTS, size_chart=chart, stretch_pct=0.05)

    rigid_waist = _dim_entry(recommend_size(rigid, body), "waist")
    stretch_waist = _dim_entry(recommend_size(stretchy, body), "waist")

    assert rigid_waist["verdict"] == "tight"
    assert stretch_waist["score"] > rigid_waist["score"]
    # Stretch scoring used effective ease, which exceeds raw ease.
    assert stretch_waist["scoring_ease"] > stretch_waist["raw_ease"]


# 6. Stretch never excuses looseness: a loose size stays equally penalized.
def test_stretch_does_not_excuse_looseness():
    chart = [{"size_label": "M", "waist": 82, "hips": 100, "inseam": 78}]
    body = {"waist": 75.0, "hips": 94.0, "inseam": 78.0}  # waist raw ease = 7 (loose)
    rigid = dict(PANTS, size_chart=chart, stretch_pct=0.0)
    stretchy = dict(PANTS, size_chart=chart, stretch_pct=0.20)

    rigid_waist = _dim_entry(recommend_size(rigid, body), "waist")
    stretch_waist = _dim_entry(recommend_size(stretchy, body), "waist")

    assert rigid_waist["verdict"] == "loose"
    assert stretch_waist["verdict"] == "loose"
    assert stretch_waist["score"] == rigid_waist["score"] < 1.0
    # Looseness scored on raw ease even for a knit.
    assert stretch_waist["scoring_ease"] == stretch_waist["raw_ease"]


# 7. Runs-small reviews add +0.08 to the next size up and attach a caveat.
def test_runs_small_review_bias():
    reviews = {"pct_small": 0.40, "pct_large": 0.10, "pct_tts": 0.50}
    result = recommend_size(PANTS, PANTS_BODY, "regular", reviews)
    # Best base size is 31, so the bonus lands on 32.
    assert _score_entry(result, "32")["review_bonus"] == 0.08
    assert _score_entry(result, "31")["review_bonus"] == 0.0
    assert result["review_signal"]["bias_direction"] == "up"
    assert result["review_signal"]["applied_shift_bias"] is True
    assert result["review_signal"]["caveat"]


# 8. Runs-large reviews add +0.08 to the previous size and attach a caveat.
def test_runs_large_review_bias():
    reviews = {"pct_small": 0.05, "pct_large": 0.45, "pct_tts": 0.50,
               "caveat": "Runs large per reviews."}
    result = recommend_size(PANTS, PANTS_BODY, "regular", reviews)
    assert _score_entry(result, "30")["review_bonus"] == 0.08
    assert result["review_signal"]["bias_direction"] == "down"
    assert result["review_signal"]["applied_shift_bias"] is True
    assert result["review_signal"]["caveat"] == "Runs large per reviews."


# 8b. No size beyond the best one: caveat kept, but no bonus applied.
def test_review_bias_at_chart_edge_reports_caveat_without_bonus():
    body = {"waist": 86.0, "hips": 99.0, "inseam": 81.0}  # fits size 33 best
    reviews = {"pct_small": 0.40, "pct_large": 0.10, "pct_tts": 0.50}
    result = recommend_size(PANTS, body, "regular", reviews)
    assert result["recommended_size"] == "33"
    assert all(s["review_bonus"] == 0.0 for s in result["size_scores"])
    assert result["review_signal"]["applied_shift_bias"] is False
    assert result["review_signal"]["bias_direction"] == "up"
    assert result["review_signal"]["caveat"]


# 9. Missing chart fields are reported and drop confidence_level to low.
def test_missing_fields_reduce_confidence_level():
    sparse = dict(
        PANTS,
        size_chart=[
            {"size_label": "31", "waist": 83},  # hips + inseam missing
            {"size_label": "32", "waist": 86},
        ],
    )
    result = recommend_size(sparse, PANTS_BODY, "regular")
    assert set(result["missing_fields"]) == {"hips", "inseam"}
    assert result["debug"]["data_completeness"] == pytest.approx(1 / 3, abs=1e-3)
    assert result["confidence_level"] == "low"


# 10a. Confidence never drops below the floor of 35.
def test_confidence_floor():
    awful = dict(
        PANTS,
        size_chart=[
            {"size_label": "30", "waist": 80},
            {"size_label": "31", "waist": 81},
        ],
    )
    body = {"waist": 120.0}  # hopelessly tight in every size, most data missing
    result = recommend_size(awful, body, "regular")
    assert result["confidence"] == 35
    assert result["confidence_level"] == "low"


# 10b. Confidence never exceeds the cap of 96.
def test_confidence_cap():
    single = dict(
        PANTS,
        size_chart=[{"size_label": "31", "waist": 83, "hips": 99, "inseam": 79}],
    )
    reviews = {"pct_small": 0.0, "pct_large": 0.0, "pct_tts": 1.0}
    result = recommend_size(single, PANTS_BODY, "regular", reviews)
    # Perfect fit, single size (margin 1.0), full data, unanimous reviews.
    assert result["confidence"] == 96
    assert result["confidence_level"] == "high"
    assert result["runner_up"] is None


# 11. Unsupported category raises ValueError.
def test_unsupported_category_raises():
    bad = dict(PANTS, category="shoes")
    with pytest.raises(ValueError, match="[Uu]nsupported"):
        recommend_size(bad, PANTS_BODY)


# 12. Missing/empty size_chart raises ValueError.
def test_missing_size_chart_raises():
    with pytest.raises(ValueError, match="size_chart"):
        recommend_size(dict(PANTS, size_chart=[]), PANTS_BODY)
    no_chart = {k: v for k, v in PANTS.items() if k != "size_chart"}
    with pytest.raises(ValueError, match="size_chart"):
        recommend_size(no_chart, PANTS_BODY)


# 13. Non-mapping product / body_measurements raise ValueError, not
# AttributeError, so the backend's single ValueError handler catches them.
def test_non_mapping_inputs_raise_value_error():
    with pytest.raises(ValueError, match="product"):
        recommend_size(None, PANTS_BODY)
    with pytest.raises(ValueError, match="body_measurements"):
        recommend_size(PANTS, None)


# 14. Non-object rows inside size_chart raise ValueError with the row index.
# This is the path the LLM size-chart parser feeds, so it must never leak
# an AttributeError.
def test_malformed_size_chart_rows_raise():
    bad_charts = (
        ["S", "M"],
        [None],
        [42],
        [{"size_label": "30", "waist": 80}, "M"],  # one good row, one junk
    )
    for chart in bad_charts:
        with pytest.raises(ValueError, match="size_chart"):
            recommend_size(dict(PANTS, size_chart=chart), PANTS_BODY)


# 15. review_analysis is optional enrichment: a malformed (non-mapping)
# value degrades to "no review data" instead of failing the recommendation.
def test_malformed_review_analysis_treated_as_absent():
    baseline = recommend_size(PANTS, PANTS_BODY, "regular", None)
    for junk in ([], "runs small", 0.4):
        result = recommend_size(PANTS, PANTS_BODY, "regular", junk)
        assert result == baseline
        assert result["review_signal"] is None


# Extra guards: review agreement math and invalid fit_pref defaulting.
def test_review_agreement_neutral_and_unanimous():
    assert calculate_review_agreement(None) == 0.5
    assert calculate_review_agreement(["not", "a", "mapping"]) == 0.5
    assert calculate_review_agreement({"pct_small": 0, "pct_large": 0, "pct_tts": 0}) == 0.5
    assert calculate_review_agreement({"pct_tts": 1.0}) == 1.0
    split = calculate_review_agreement(
        {"pct_small": 1 / 3, "pct_large": 1 / 3, "pct_tts": 1 / 3}
    )
    assert split == pytest.approx(0.0, abs=1e-9)


def test_invalid_fit_pref_defaults_to_regular():
    result = recommend_size(PANTS, PANTS_BODY, "super-skinny")
    assert result["debug"]["fit_pref"] == "regular"
    assert result["recommended_size"] == "31"


# Numeric strings in charts/body measurements are accepted; junk is not.
def test_numeric_string_measurements_accepted():
    string_pants = dict(
        PANTS,
        size_chart=[
            {"size_label": "30", "waist": "80", "hips": "96", "inseam": "78"},
            {"size_label": "31", "waist": "83", "hips": "99.0", "inseam": "79"},
            {"size_label": "32", "waist": "86", "hips": "102", "inseam": "80"},
            {"size_label": "33", "waist": "89", "hips": "105", "inseam": "81"},
        ],
    )
    string_body = {"waist": "80", "hips": "93.0", "inseam": "79"}
    result = recommend_size(string_pants, string_body, "regular")
    baseline = recommend_size(PANTS, PANTS_BODY, "regular")
    assert result["recommended_size"] == baseline["recommended_size"] == "31"
    assert result["size_scores"] == baseline["size_scores"]
    assert result["missing_fields"] == []


def test_non_numeric_values_treated_as_missing():
    body = {"waist": "eighty", "hips": True, "inseam": 79.0}  # only inseam valid
    result = recommend_size(PANTS, body, "regular")
    assert set(result["missing_fields"]) == {"waist", "hips"}
    verdicts = {d["dim"]: d["verdict"] for d in result["fit_breakdown"]}
    assert verdicts["waist"] == verdicts["hips"] == "missing_data"
    assert result["confidence_level"] == "low"


# stretch_pct given as a whole percentage (3) is normalized to 0.03.
def test_stretch_pct_percentage_normalization():
    chart = [{"size_label": "M", "waist": 82, "hips": 100, "inseam": 78}]
    body = {"waist": 81.0, "hips": 94.0, "inseam": 78.0}  # waist raw ease = 1 (tight)
    fraction = dict(PANTS, size_chart=chart, stretch_pct=0.03)
    whole_pct = dict(PANTS, size_chart=chart, stretch_pct=3)
    rigid = dict(PANTS, size_chart=chart, stretch_pct=0.0)

    fraction_waist = _dim_entry(recommend_size(fraction, body), "waist")
    whole_pct_waist = _dim_entry(recommend_size(whole_pct, body), "waist")
    rigid_waist = _dim_entry(recommend_size(rigid, body), "waist")

    # 3 and 0.03 must behave identically, and both beat rigid when tight.
    assert whole_pct_waist == fraction_waist
    assert whole_pct_waist["score"] > rigid_waist["score"]
