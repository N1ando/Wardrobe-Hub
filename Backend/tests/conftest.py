"""Test fixtures: an isolated, seeded SQLite DB and a TestClient.

DATABASE_URL is pointed at a temp file BEFORE importing app.db so the module-level
engine binds to it. LLM calls stay offline: with no GEMMA_URL / FIREWORKS_API_KEY
set, the review miner uses its deterministic keyword fallback.
"""

from __future__ import annotations

import os
import tempfile

import pytest

_TMP_DB = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_TMP_DB.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP_DB.name}"
os.environ.pop("GEMMA_URL", None)
os.environ.pop("FIREWORKS_API_KEY", None)


@pytest.fixture(scope="session", autouse=True)
def _seeded_db():
    from scripts.seed import seed

    seed()

    from app.ai.batch_analysis import analyze_product_reviews
    from app.db import SessionLocal
    from app.models import Product

    db = SessionLocal()
    try:
        for product in db.query(Product).all():
            analyze_product_reviews(db, product.id)
    finally:
        db.close()
    yield
    os.unlink(_TMP_DB.name)


@pytest.fixture()
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    return TestClient(app)
