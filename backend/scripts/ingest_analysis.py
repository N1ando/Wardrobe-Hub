"""Pre-run the Gemma review-mining batch and cache results in SQLite.

    python -m scripts.ingest_analysis                     # from the backend/ directory
    python -m scripts.ingest_analysis --from-json PATH    # import offline batch results

Run this before the demo so the seller dashboard + review shift bias are warm
without any live LLM calls. The default mode uses the AMD vLLM / Fireworks /
keyword fallback ladder defined in app/ai/gemma_client.py, so it also works
fully offline. `--from-json` instead imports an offline batch-analysis file
(the tools/amd_benchmark output format) into the same review_analysis table.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ai.batch_analysis import analyze_product_reviews  # noqa: E402
from app.ai.batch_import import import_review_analysis  # noqa: E402
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
            analysis = analyze_product_reviews(db, product.id, mode="batch")
            print(
                f"[{product.id}] {product.name}: "
                f"small={analysis.pct_small} tts={analysis.pct_tts} large={analysis.pct_large} "
                f"| {analysis.throughput_note} | issues={analysis.top_issues}"
            )
    finally:
        db.close()


def ingest_from_json(path: Path) -> None:
    init_db()
    data = json.loads(path.read_text(encoding="utf-8"))
    db = SessionLocal()
    try:
        report = import_review_analysis(db, data)
        print(f"Imported {len(report.imported)} product analyses from {path}")
        print(f"Source: {report.source or 'n/a'} | "
              f"run total reviews: {report.run_total_reviews or 'n/a'} | "
              f"run elapsed: {report.run_elapsed_seconds or 'n/a'}s")
        for reason in report.skipped:
            print(f"Skipped {reason}")
        if not report.imported:
            print("Nothing imported; database left unchanged.")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--from-json",
        type=Path,
        default=None,
        metavar="PATH",
        help="Import an offline batch-analysis JSON file (tools/amd_benchmark "
             "output format) instead of running the live review miner.",
    )
    args = parser.parse_args()
    if args.from_json is not None:
        ingest_from_json(args.from_json)
    else:
        ingest()
