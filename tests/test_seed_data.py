"""Pins the seeded demo data to the demo script.

The demo data is load-bearing: each product/persona pair is tuned to a
rehearsed on-stage moment (the size-31 jeans, the review-driven M->L dress
flip, the fit-pref S->M shirt shift, the missing-sleeve chart). These tests
fail if an edit to data/seed/*.json silently breaks one of those moments.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from core import recommend_size

_SEED_DIR = Path(__file__).resolve().parent.parent / "data" / "seed"


def _load(name: str) -> Any:
    return json.loads((_SEED_DIR / name).read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def products() -> dict[str, dict[str, Any]]:
    return {p["id"]: p for p in _load("products.json")}


@pytest.fixture(scope="module")
def personas() -> dict[str, dict[str, Any]]:
    return _load("personas.json")


def test_any_persona_on_any_product_is_json_safe(products, personas):
    for product in products.values():
        for persona in personas.values():
            result = recommend_size(
                product,
                persona["measurements"],
                persona["fit_pref"],
                product.get("review_analysis"),
            )
            json.dumps(result)  # must never raise
            assert result["recommended_size"]


def test_jordan_jeans_regular_is_31(products, personas):
    jeans = products["jeans_001"]
    result = recommend_size(
        jeans, personas["jordan"]["measurements"], "regular", jeans["review_analysis"]
    )
    assert result["recommended_size"] == "31"
    # The jeans' review signal is deliberately below the bias thresholds.
    assert result["review_signal"]["applied_shift_bias"] is False


def test_riley_dress_flips_m_to_l_on_runs_small_reviews(products, personas):
    dress = products["dress_001"]
    body = personas["riley"]["measurements"]
    without_reviews = recommend_size(dress, body, "regular", None)
    with_reviews = recommend_size(dress, body, "regular", dress["review_analysis"])
    assert without_reviews["recommended_size"] == "M"
    assert with_reviews["recommended_size"] == "L"
    assert with_reviews["review_signal"]["applied_shift_bias"] is True
    assert "runs small" in with_reviews["review_signal"]["caveat"]


def test_sam_shirt_fit_pref_shifts_s_to_m(products, personas):
    shirt = products["shirt_001"]
    body = personas["sam"]["measurements"]
    assert recommend_size(shirt, body, "regular")["recommended_size"] == "S"
    assert recommend_size(shirt, body, "relaxed")["recommended_size"] == "M"


def test_shirt_chart_missing_sleeve_is_surfaced(products, personas):
    result = recommend_size(
        products["shirt_001"], personas["sam"]["measurements"], "relaxed"
    )
    assert result["missing_fields"] == ["sleeve"]


def test_dress_review_signal_crosses_bias_thresholds(products):
    analysis = products["dress_001"]["review_analysis"]
    assert analysis["pct_small"] >= 0.25
    assert analysis["pct_small"] - analysis["pct_large"] >= 0.15
