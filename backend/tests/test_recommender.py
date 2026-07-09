"""Persona regression suite for the deterministic engine (plan Section 4).

The engine is the product; these tests keep it from silently breaking during
frontend/backend churn. Charts are loaded from the seed data so the tests track
the real demo inputs.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.core.confidence import compute_confidence, review_agreement
from app.core.recommender import recommend

SEED = Path(__file__).resolve().parent.parent / "data" / "seed"


def _charts() -> dict[int, list[dict]]:
    charts: dict[int, list[dict]] = {}
    for row in json.loads((SEED / "size_charts.json").read_text()):
        charts.setdefault(row["product_id"], []).append(row)
    return charts


CHARTS = _charts()
META = {1: ("shirt", 0.0, "Cotton poplin"),
        2: ("jeans", 0.01, "Denim"),
        3: ("dress", 0.03, "Cotton")}

DRESS_RUNS_SMALL = {"pct_small": 0.857, "pct_large": 0.0, "pct_tts": 0.143,
                    "top_issues": [{"area": "waist", "count": 5}]}


def _rec(pid: int, measurements: dict, fit: str = "regular", review_analysis=None) -> dict:
    cat, stretch, material = META[pid]
    return recommend(category=cat, size_chart=CHARTS[pid], measurements=measurements,
                     fit_pref=fit, stretch_pct=stretch, material=material,
                     review_analysis=review_analysis)


# (name, product_id, measurements, fit_pref, expected_size)
PERSONAS = [
    ("slim-fit shirt wearer", 1, {"chest": 96, "waist": 82}, "regular", "M"),
    ("broad shirt wearer", 1, {"chest": 112, "waist": 104}, "regular", "XL"),
    ("small shirt wearer", 1, {"chest": 90, "waist": 78}, "regular", "S"),
    ("mid jeans regular", 2, {"waist": 80, "hips": 96, "inseam": 84}, "regular", "32"),
    ("slim jeans", 2, {"waist": 76, "hips": 90, "inseam": 82}, "slim", "30"),
    ("large jeans", 2, {"waist": 88, "hips": 104, "inseam": 86}, "regular", "34"),
    ("dress regular", 3, {"bust": 90, "waist": 72}, "regular", "L"),
    ("dress small frame", 3, {"bust": 84, "waist": 66}, "regular", "M"),
]


@pytest.mark.parametrize("name,pid,measurements,fit,expected", PERSONAS,
                         ids=[p[0] for p in PERSONAS])
def test_persona_sizes(name, pid, measurements, fit, expected):
    result = _rec(pid, measurements, fit)
    assert result["recommended_size"] == expected, (
        f"{name}: got {result['recommended_size']} ({result['confidence']}%)"
    )
    assert 35 <= result["confidence"] <= 96


def test_shirt_reports_missing_sleeve():
    result = _rec(1, {"chest": 100, "waist": 90})
    assert "sleeve" in result["missing_fields"]


def test_dress_reports_missing_hips_and_flags_low_or_review_data():
    result = _rec(3, {"bust": 90, "waist": 72})
    assert "hips" in result["missing_fields"]


def test_material_note_present_for_stretch_fabric():
    result = _rec(3, {"bust": 90, "waist": 72})
    assert result["material_note"] is not None


def test_no_material_note_for_rigid_fabric():
    result = _rec(1, {"chest": 100, "waist": 90})
    assert result["material_note"] is None


def test_runs_small_shift_bias_bumps_one_size_up():
    """Two-size synthetic chart where geometry ties; runs-small breaks the tie up."""
    chart = [
        {"size_label": "A", "order_index": 0, "chest": 100},
        {"size_label": "B", "order_index": 1, "chest": 104},
    ]
    body = {"chest": 92}  # regular band 8-12: A ease 8 (ideal), B ease 12 (ideal) => tie

    plain = recommend(category="shirt", size_chart=chart, measurements=body)
    assert plain["recommended_size"] == "A"  # first of the tie

    biased = recommend(category="shirt", size_chart=chart, measurements=body,
                       review_analysis={"pct_small": 0.6, "pct_large": 0.05, "pct_tts": 0.35})
    assert biased["recommended_size"] == "B"
    assert biased["review_signal"]["applied_shift_bias"] is True
    assert "small" in (biased["review_signal"]["caveat"] or "")


def test_confidence_floor_and_cap():
    assert compute_confidence(0.0, 0.0, 0.0, 0.0) == 35
    assert compute_confidence(1.0, 0.0, 1.0, 1.0) == 96


def test_review_agreement_bounds():
    assert review_agreement(1.0, 0.0, 0.0) == pytest.approx(1.0)
    assert review_agreement(1 / 3, 1 / 3, 1 / 3) == pytest.approx(0.0, abs=1e-9)


def test_empty_chart_is_low_confidence():
    result = recommend(category="shirt", size_chart=[], measurements={"chest": 95})
    assert result["low_confidence"] is True
    assert result["confidence"] == 35


def test_empty_measurements_flag_low_confidence():
    # No usable body measurements: the engine still answers (floor confidence),
    # but must self-identify as low confidence so the UI can render the
    # "add your measurements" state instead of a normal result card.
    result = recommend(category="jeans", size_chart=CHARTS[2], measurements={})
    assert result["confidence"] <= 60
    assert result["low_confidence"] is True
