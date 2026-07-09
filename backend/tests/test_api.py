"""Endpoint contract tests against a seeded DB (plan Section 3)."""

from __future__ import annotations


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["gemma_backend"] in ("amd-vllm", "fireworks", "cache", "template")


def test_list_products(client):
    r = client.get("/api/products")
    assert r.status_code == 200
    products = r.json()
    assert len(products) == 3
    assert {p["category"] for p in products} == {"shirt", "jeans", "dress"}


def test_product_detail_has_chart_and_reviews(client):
    r = client.get("/api/products/3")
    assert r.status_code == 200
    detail = r.json()
    assert detail["name"] == "Floral Wrap Dress"
    assert len(detail["size_chart"]) == 4
    assert detail["review_summary"]["reviews_analyzed"] == 8
    assert detail["review_summary"]["pct_small"] > 0.5  # planted runs-small cluster


def test_product_detail_404(client):
    assert client.get("/api/products/999").status_code == 404


def test_recommend_jeans(client):
    r = client.post("/api/recommend", json={
        "product_id": 2, "fit_pref": "regular",
        "measurements": {"waist": 80, "hips": 96, "inseam": 84},
    })
    assert r.status_code == 200
    body = r.json()
    assert body["recommended_size"] == "32"
    assert 35 <= body["confidence"] <= 96
    assert body["fit_breakdown"]


def test_recommend_dress_applies_review_signal(client):
    r = client.post("/api/recommend", json={
        "product_id": 3, "fit_pref": "regular",
        "measurements": {"bust": 90, "waist": 72},
    })
    body = r.json()
    assert body["review_signal"]["pct_small"] > 0.5
    assert "hips" in body["missing_fields"]


def test_recommend_404(client):
    r = client.post("/api/recommend", json={
        "product_id": 999, "fit_pref": "regular", "measurements": {"chest": 95},
    })
    assert r.status_code == 404


def test_explain_returns_text_and_source(client):
    rec = client.post("/api/recommend", json={
        "product_id": 1, "fit_pref": "regular",
        "measurements": {"chest": 100, "waist": 90},
    }).json()
    r = client.post("/api/explain", json={"recommendation": rec, "product_name": "Classic Oxford Shirt"})
    assert r.status_code == 200
    body = r.json()
    assert body["explanation"]
    assert body["source"] in ("amd-vllm", "fireworks", "cache", "template")


def test_seller_overview(client):
    r = client.get("/api/seller/overview")
    assert r.status_code == 200
    rows = r.json()["products"]
    assert len(rows) == 3
    dress = next(p for p in rows if p["product_id"] == 3)
    # The seeded dress is the flagship risk product: the demo script shows it
    # as HIGH (planted runs-small cluster + missing hips).
    assert dress["risk_level"] == "high"
    assert "hips" in dress["missing_fields"]


def test_seller_overview_rows_carry_dashboard_fields(client):
    rows = client.get("/api/seller/overview").json()["products"]
    for row in rows:
        assert 0.0 <= row["chart_completeness"] <= 1.0
        assert row["review_count"] >= row["complaint_count"] >= 0
        dist = row["fit_distribution"]
        assert set(dist) == {"pct_small", "pct_tts", "pct_large"}
    dress = next(p for p in rows if p["product_id"] == 3)
    assert dress["review_count"] == 8
    assert dress["fit_distribution"]["pct_small"] > 0.5
    assert dress["image_url"]


def test_seller_product_risk_has_suggestions(client):
    r = client.get("/api/seller/products/3/risk")
    assert r.status_code == 200
    body = r.json()
    assert body["suggestions"]
    assert body["complaint_clusters"]


def test_seller_risk_returns_stable_mined_quotes(client):
    first = client.get("/api/seller/products/3/risk").json()["quotes"]
    second = client.get("/api/seller/products/3/risk").json()["quotes"]
    assert 1 <= len(first) <= 4
    # Quotes are real mined reviews with verdicts; dominant complaint first.
    assert all(q["text"] and q["verdict"] in ("small", "large", "tts") for q in first)
    assert first[0]["verdict"] == "small"  # the dress's planted cluster
    assert first == second  # deterministic ordering: the demo can't wobble


def test_analyze_reviews_endpoint(client):
    r = client.post("/api/ai/analyze-reviews", json={"product_id": 3})
    assert r.status_code == 200
    analyzed = r.json()["analyzed"]
    assert analyzed[0]["reviews_analyzed"] == 8
