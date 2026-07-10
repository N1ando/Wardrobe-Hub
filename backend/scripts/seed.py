"""Load seed products, size charts, and reviews into SQLite.

    python -m scripts.seed          # from the backend/ directory

Idempotent: drops and recreates FitOS tables, then loads data/seed/*.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Allow running as a script from backend/ without installing the package.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings  # noqa: E402
from app.db import Base, SessionLocal, engine, init_db  # noqa: E402
from app.models import Product, Review, SizeChart  # noqa: E402


def _load(name: str) -> list[dict]:
    path = get_settings().seed_dir / name
    return json.loads(path.read_text())


def seed() -> None:
    Base.metadata.drop_all(bind=engine)
    init_db()

    db = SessionLocal()
    try:
        for p in _load("products.json"):
            db.add(Product(**p))
        for c in _load("size_charts.json"):
            db.add(SizeChart(**c))
        for r in _load("reviews.json"):
            db.add(Review(**r))
        db.commit()

        n_products = db.query(Product).count()
        n_charts = db.query(SizeChart).count()
        n_reviews = db.query(Review).count()
        print(f"Seeded {n_products} products, {n_charts} size rows, {n_reviews} reviews.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
