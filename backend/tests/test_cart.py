"""Cart endpoint contract tests against the seeded DB."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _empty_cart(client):
    """Each test starts and ends with an empty cart (shared demo cart)."""
    yield
    for item in client.get("/api/cart").json()["items"]:
        client.delete(f"/api/cart/items/{item['id']}")


def test_cart_starts_empty(client):
    r = client.get("/api/cart")
    assert r.status_code == 200
    assert r.json() == {"items": [], "total": 0.0}


def test_add_item_returns_cart_with_product_details(client):
    r = client.post("/api/cart/items", json={"product_id": 1, "size": "M", "quantity": 2})
    assert r.status_code == 200
    body = r.json()
    assert len(body["items"]) == 1
    item = body["items"][0]
    assert item["name"] == "Classic Oxford Shirt"
    assert item["size"] == "M"
    assert item["quantity"] == 2
    assert body["total"] == round(item["price"] * 2, 2)


def test_same_product_and_size_merges_lines(client):
    client.post("/api/cart/items", json={"product_id": 2, "size": "32", "quantity": 1})
    r = client.post("/api/cart/items", json={"product_id": 2, "size": "32", "quantity": 1})
    body = r.json()
    assert len(body["items"]) == 1
    assert body["items"][0]["quantity"] == 2


def test_remove_item(client):
    added = client.post(
        "/api/cart/items", json={"product_id": 3, "size": "L", "quantity": 1}
    ).json()
    item_id = added["items"][0]["id"]
    r = client.delete(f"/api/cart/items/{item_id}")
    assert r.status_code == 200
    assert r.json()["items"] == []


def test_add_unknown_product_404(client):
    r = client.post("/api/cart/items", json={"product_id": 999, "size": "M", "quantity": 1})
    assert r.status_code == 404


def test_add_invalid_size_400(client):
    r = client.post("/api/cart/items", json={"product_id": 1, "size": "XXXL", "quantity": 1})
    assert r.status_code == 400
    assert "not available" in r.json()["detail"]


def test_remove_missing_item_404(client):
    assert client.delete("/api/cart/items/99999").status_code == 404


def test_zero_quantity_rejected(client):
    r = client.post("/api/cart/items", json={"product_id": 1, "size": "M", "quantity": 0})
    assert r.status_code == 422
