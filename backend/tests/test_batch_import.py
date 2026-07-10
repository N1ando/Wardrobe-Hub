"""Offline batch-analysis import: adapter correctness + endpoint compatibility.

These tests exercise the explicit AMD-batch import path (app/ai/batch_import)
against the shared seeded test DB. Every mutating test re-runs the runtime
miner afterwards so the other test modules keep seeing the seeded baseline.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
# The canonical captured evidence (data/processed/ holds regenerable runtime
# outputs only; the frozen AMD run lives in docs/amd_proof/).
AMD_BATCH_FILE = REPO_ROOT / "docs" / "amd_proof" / "review_analysis_amd_240.json"


def _session():
    from app.db import SessionLocal

    return SessionLocal()


def _get_analysis(product_id: int):
    from app.models import ReviewAnalysis

    db = _session()
    try:
        return db.get(ReviewAnalysis, product_id)
    finally:
        db.close()


@pytest.fixture()
def restore_runtime_analysis():
    """Re-mine every product after the test so imports don't leak state."""
    yield
    from app.ai.batch_analysis import analyze_product_reviews
    from app.models import Product

    db = _session()
    try:
        for product in db.query(Product).order_by(Product.id).all():
            analyze_product_reviews(db, product.id)
    finally:
        db.close()


def _amd_row(product_id: str, total: int = 10, **overrides) -> dict:
    row = {
        "product_id": product_id,
        "total_reviews": total,
        "pct_small": 0.2,
        "pct_large": 0.1,
        "pct_tts": 0.5,
        "top_issues_json": [{"area": "waist", "count": 3}],
        "classified_reviews": [{"backend": "amd-vllm", "fit_verdict": "small"}],
        "analysis_mode": "amd-vllm",
        "updated_at": "2026-07-09T18:30:22+00:00",
    }
    row.update(overrides)
    return row


_SENTINEL = {
    "product_id": "__benchmark__",
    "analysis_mode": "amd-vllm",
    "total_reviews": 240,
    "elapsed_seconds": 40.0,
    "updated_at": "2026-07-09T18:30:22+00:00",
}


# ---- Real benchmark output --------------------------------------------------


def test_real_amd_batch_file_imports_into_review_analysis(restore_runtime_analysis):
    if not AMD_BATCH_FILE.exists():
        pytest.skip(f"benchmark proof file not present: {AMD_BATCH_FILE}")
    from app.ai.batch_import import import_review_analysis

    data = json.loads(AMD_BATCH_FILE.read_text(encoding="utf-8"))
    db = _session()
    try:
        report = import_review_analysis(db, data)
    finally:
        db.close()

    # Slugs jeans_001 / shirt_001 / dress_001 resolve via category prefix.
    assert set(report.imported) == {1, 2, 3}
    assert report.skipped == []
    assert report.source == "amd-vllm"
    assert report.run_total_reviews == 240
    assert report.run_elapsed_seconds == pytest.approx(39.9668)

    jeans = _get_analysis(2)  # jeans_001 in the benchmark file
    assert jeans.reviews_analyzed == 104
    # Counted from the complete classified_reviews list: 2 small, 0 large.
    assert jeans.complaint_count == 2
    assert jeans.pct_small == pytest.approx(0.0192)
    assert jeans.analysis_source == "amd-vllm"
    assert jeans.analysis_mode == "batch"
    assert jeans.elapsed_seconds == pytest.approx(39.9668)
    assert "AMD vLLM batch: 240 reviews" in jeans.throughput_note


# ---- Validation and safe skipping -------------------------------------------


def test_invalid_rows_are_skipped_with_reasons_and_leave_db_unchanged(restore_runtime_analysis):
    from app.ai.batch_import import import_review_analysis

    before_dress = _get_analysis(3)
    baseline = (before_dress.pct_small, before_dress.reviews_analyzed)

    payload = [
        _amd_row("jeans_001"),  # valid: unique category prefix
        _amd_row("1", total=7),  # valid: numeric string id
        _amd_row("hat_999"),  # no product in category "hat"
        _amd_row(""),  # missing product id
        _amd_row("dress_001", pct_small=1.5),  # pct out of range
        _amd_row("dress_001", total=-4),  # negative review count
        _amd_row("dress_001", top_issues_json="waist"),  # wrong type
        "not-an-object",
        _SENTINEL,
    ]
    db = _session()
    try:
        report = import_review_analysis(db, payload)
    finally:
        db.close()

    assert sorted(report.imported) == [1, 2]
    assert len(report.skipped) == 6
    assert any("hat_999" in reason for reason in report.skipped)
    assert any("missing product_id" in reason for reason in report.skipped)

    # _amd_row ships 1 classified review against total=10, so complaint_count
    # falls back to the producer-pct derivation: round((0.2 + 0.1) * 10) = 3.
    assert _get_analysis(2).complaint_count == 3

    # Every dress row was invalid: its runtime analysis must be untouched.
    after_dress = _get_analysis(3)
    assert (after_dress.pct_small, after_dress.reviews_analyzed) == baseline


def test_non_list_payload_fails_clearly():
    from app.ai.batch_import import import_review_analysis

    db = _session()
    try:
        with pytest.raises(ValueError, match="JSON array"):
            import_review_analysis(db, {"product_id": "jeans_001"})
    finally:
        db.close()


def test_sentinel_only_payload_imports_nothing():
    from app.ai.batch_import import import_review_analysis

    db = _session()
    try:
        report = import_review_analysis(db, [_SENTINEL])
    finally:
        db.close()
    assert report.imported == []
    assert report.skipped == []


def test_local_mode_results_are_not_labelled_amd(restore_runtime_analysis):
    from app.ai.batch_import import import_review_analysis

    payload = [
        _amd_row(
            "jeans_001",
            classified_reviews=[{"backend": "local", "fit_verdict": "tts"}],
            analysis_mode="local",
        )
    ]
    db = _session()
    try:
        report = import_review_analysis(db, payload)
    finally:
        db.close()

    assert report.imported == [2]
    jeans = _get_analysis(2)
    assert jeans.analysis_source == "keyword"
    assert "AMD" not in jeans.throughput_note


# ---- Endpoint compatibility --------------------------------------------------


def test_seller_endpoints_stay_compatible_and_expose_import_metadata(
    client, restore_runtime_analysis
):
    from app.ai.batch_import import import_review_analysis

    db = _session()
    try:
        # shirt_001 included because the overview note comes from the first
        # product (by id) that has one.
        import_review_analysis(
            db, [_amd_row("shirt_001"), _amd_row("jeans_001", total=104), _SENTINEL]
        )
    finally:
        db.close()

    risk = client.get("/api/seller/products/2/risk")
    assert risk.status_code == 200
    body = risk.json()
    # Pre-existing contract fields are all still present.
    for field in (
        "risk_level", "risk_score", "missing_fields", "complaint_clusters",
        "review_summary", "suggestions", "review_count", "complaint_count",
        "chart_completeness", "fit_distribution", "quotes",
    ):
        assert field in body
    summary = body["review_summary"]
    assert summary["analysis_source"] == "amd-vllm"
    assert summary["analysis_mode"] == "batch"
    assert summary["reviews_analyzed"] == 104
    assert summary["elapsed_seconds"] == pytest.approx(40.0)

    detail = client.get("/api/products/2").json()
    assert detail["review_summary"]["analysis_source"] == "amd-vllm"

    overview = client.get("/api/seller/overview").json()
    assert len(overview["products"]) == 3
    assert "AMD vLLM batch: 240 reviews" in overview["throughput_note"]


def test_runtime_analysis_reports_its_own_provenance(client):
    # The session fixture mined with no LLM configured, so provenance must
    # say so — keyword fallback, never a false amd-vllm claim. ("cache" can
    # appear on dev machines with a warm LLM cache.)
    summary = client.get("/api/seller/products/3/risk").json()["review_summary"]
    assert summary["analysis_source"] in ("keyword", "cache")
    assert summary["analysis_mode"] in ("fallback", "live", "batch")
    assert summary["analysis_source"] != "amd-vllm"
