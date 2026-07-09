"""Pre-run the Gemma review-mining batch and cache results in SQLite.

    python -m scripts.ingest_analysis        # from the backend/ directory

Run this before the demo so the seller dashboard + review shift bias are warm
without any live LLM calls. Uses the AMD vLLM / Fireworks / keyword fallback
ladder defined in app/ai/gemma_client.py, so it also works fully offline.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ai.batch_analysis import analyze_product_reviews  # noqa: E402
from app.db import SessionLocal, init_db  # noqa: E402
from app.models import Product  # noqa: E402


def ingest() -> None:
    init_db()
    db = SessionLocal()
    try:
        products = db.query(Product).order_by(Product.id).all()
        if not products:
            print("No products found. Run `python -m scripts.seed` first.")
            return
        for product in products:
            analysis = analyze_product_reviews(db, product.id)
            print(
                f"[{product.id}] {product.name}: "
                f"small={analysis.pct_small} tts={analysis.pct_tts} large={analysis.pct_large} "
                f"| {analysis.throughput_note} | issues={analysis.top_issues}"
            )
    finally:
        db.close()


if __name__ == "__main__":
    ingest()
