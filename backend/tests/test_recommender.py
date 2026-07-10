"""Persona regression suite through the shared engine (repo-root ``core/``).

The backend serves ``core.recommender.recommend_size`` via a thin adapter
(routers/recommend.py). These tests pin the adapter's chart mapping (dress
bust lives in the DB's chest column) and the demo persona outcomes against
the seeded charts, so seed edits can't silently break a rehearsed moment.
Engine internals (confidence math, stretch rules, coercion) are covered by
the repo-root test suite.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.recommender import recommend_size

from app.routers.recommend import _caveat

SEED = Path(__file__).resolve().parent.parent / "data" / "seed"


def _charts() -> dict[int, list[dict]]:
    charts: dict[int, list[dict]] = {}
    for row in json.loads((SEED / "size_charts.json").read_text()):
        charts.setdefault(row["product_id"], []).append(row)
    for rows in charts.values():
        rows.sort(key=lambda r: r.get("order_index", 0))
    return charts


CHARTS = _charts()
META = {1: ("shirt", 0.0, "Cotton poplin"),
        2: ("jeans", 0.01, "Denim"),
        3: ("dress", 0.03, "Cotton")}

DRESS_RUNS_SMALL = {"pct_small": 0.857, "pct_large": 0.0, "pct_tts": 0.143}


def _product(pid: int) -> dict:
    """Mirror the router adapter: engine product dict from seeded chart rows."""
    cat, stretch, material = META[pid]
    rows = [dict(r) for r in CHARTS[pid]]
    if cat == "dress":
        for r in rows:  # DB stores dress bust in the chest column
            r["bust"] = r.get("chest")
    return {"id": pid, "category": cat, "size_chart": rows,
            "stretch_pct": stretch, "material": material}


def _rec(pid: int, measurements: dict, fit: str = "regular", review_analysis=None) -> dict:
    return recommend_size(_product(pid), measurements, fit, review_analysis)


# (name, product_id, measurements, fit_pref, expected_size)
PERSONAS = [
    ("slim-fit shirt wearer", 1, {"chest": 96, "waist": 82}, "regular", "M"),
    ("broad shirt wearer", 1, {"chest": 112, "waist": 104}, "regular", "XL"),
    ("small shirt wearer", 1, {"chest": 90, "waist": 78}, "regular", "S"),
    # Mid-band on every size-32 dimension (waist ease 3, hips 6, inseam 1) so
    # the pick is decisive, not a borderline coin flip between 32 and 33.
    ("mid jeans regular", 2, {"waist": 79, "hips": 92, "inseam": 85}, "regular", "32"),
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
    assert result["confidence_level"] in ("low", "medium", "high")


def test_shirt_reports_missing_sleeve():
    result = _rec(1, {"chest": 100, "waist": 90, "sleeve": 62})
    assert "sleeve" in result["missing_fields"]


def test_dress_reports_missing_hips():
    result = _rec(3, {"bust": 90, "waist": 72, "hips": 96})
    assert "hips" in result["missing_fields"]


def test_dress_runs_small_reviews_attach_signal():
    result = _rec(3, {"bust": 90, "waist": 72}, review_analysis=DRESS_RUNS_SMALL)
    signal = result["review_signal"]
    assert signal["bias_direction"] == "up"
    assert signal["pct_small"] == pytest.approx(0.857)


def test_material_note_mentions_stretch_handling():
    stretchy = _rec(3, {"bust": 90, "waist": 72})
    rigid = _rec(1, {"chest": 100, "waist": 90})
    assert "stretch" in stretchy["material_note"].lower()
    assert "rigid" in rigid["material_note"].lower()


def test_runs_small_shift_bias_bumps_one_size_up():
    """Borderline body: the +0.08 review bonus flips the pick one size up.

    Note the engine caps adjusted scores at 1.0, so a PERFECT fit can never be
    displaced by reviews — the flip only happens on genuinely borderline calls.
    """
    chart = [
        {"size_label": "30", "waist": 80, "hips": 96, "inseam": 78},
        {"size_label": "31", "waist": 83, "hips": 99, "inseam": 79},
        {"size_label": "32", "waist": 86, "hips": 102, "inseam": 80},
    ]
    product = {"id": 99, "category": "jeans", "size_chart": chart,
               "stretch_pct": 0.03, "material": "stretch denim"}
    body = {"waist": 82.6, "hips": 93.0, "inseam": 79.5}  # 31 barely beats 32

    plain = recommend_size(product, body)
    assert plain["recommended_size"] == "31"

    biased = recommend_size(product, body, "regular",
                            {"pct_small": 0.55, "pct_large": 0.05, "pct_tts": 0.40})
    assert biased["recommended_size"] == "32"
    assert biased["review_signal"]["applied_shift_bias"] is True
    assert "small" in (biased["review_signal"]["caveat"] or "")


def test_empty_chart_raises_value_error():
    # Engine error contract: bad product data -> ValueError (router maps to 422).
    with pytest.raises(ValueError, match="size_chart"):
        recommend_size({"id": 1, "category": "shirt", "size_chart": []},
                       {"chest": 95})


def test_empty_measurements_read_as_low_confidence():
    result = _rec(2, {})
    assert result["confidence_level"] == "low"
    assert result["confidence"] <= 60


def test_adapter_caveat_only_fires_with_engine_thresholds():
    assert "runs small in the waist" in _caveat(0.857, 0.0, [{"area": "waist"}])
    assert "sizing down" in _caveat(0.05, 0.45, [])
    assert _caveat(0.2, 0.1, [{"area": "bust"}]) is None  # below trigger
    assert _caveat(0.3, 0.25, []) is None  # gap below margin
