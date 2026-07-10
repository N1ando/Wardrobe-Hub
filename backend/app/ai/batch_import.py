"""Adapter: import offline batch review-analysis JSON into ReviewAnalysis.

The offline producer (tools/amd_benchmark/batch_analysis.py) speaks a
different dialect than the runtime: products are keyed by string slugs like
"jeans_001", aggregates are named total_reviews / top_issues_json, and
run-level metadata (mode, elapsed) travels in a "__benchmark__" sentinel row.
This module translates that dialect into the backend's canonical
review_analysis table; it does not re-implement the benchmark, and it never
touches Review rows (mined quotes stay owned by the runtime pipeline).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models import Product, ReviewAnalysis

BENCHMARK_SENTINEL = "__benchmark__"

# Producer labels -> the backend's analysis_source vocabulary.
_SOURCE_ALIASES = {"local": "keyword", "template": "keyword"}
_KNOWN_SOURCES = ("amd-vllm", "fireworks", "keyword", "cache")
_PCT_FIELDS = ("pct_small", "pct_large", "pct_tts")


@dataclass
class ImportReport:
    imported: list[int] = field(default_factory=list)  # product ids upserted
    skipped: list[str] = field(default_factory=list)  # one reason per skipped row
    source: str | None = None  # dominant analysis_source of imported rows
    run_total_reviews: int | None = None  # from the sentinel row, when present
    run_elapsed_seconds: float | None = None


def _as_number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _resolve_product(db: Session, raw_id: object) -> Product | None:
    """Map a producer product id onto a backend Product.

    Accepts the backend's integer ids (or numeric strings) directly; slugs
    like "jeans_001" resolve through their category prefix, but only when
    exactly one product has that category — ambiguity is a skip, not a guess.
    """
    if isinstance(raw_id, bool):
        return None
    if isinstance(raw_id, int):
        return db.get(Product, raw_id)
    if isinstance(raw_id, str):
        if raw_id.isdigit():
            return db.get(Product, int(raw_id))
        if "_" in raw_id:
            category = raw_id.rsplit("_", 1)[0]
            matches = db.query(Product).filter(Product.category == category).all()
            if len(matches) == 1:
                return matches[0]
    return None


def _row_source(item: dict) -> str | None:
    """The source that actually produced the row's verdicts.

    Per-review `backend` labels are ground truth (the producer falls back
    per-review), so the majority label wins; the row-level analysis_mode is
    only trusted when no per-review labels exist. Unknown labels return None
    so the row is skipped rather than mislabelled — in particular a row is
    never marked amd-vllm unless the data says so.
    """
    backends = Counter(
        str(r["backend"])
        for r in item.get("classified_reviews", [])
        if isinstance(r, dict) and r.get("backend")
    )
    label = backends.most_common(1)[0][0] if backends else item.get("analysis_mode")
    if not isinstance(label, str):
        return None
    label = _SOURCE_ALIASES.get(label, label)
    return label if label in _KNOWN_SOURCES else None


def _throughput_note(source: str, run_total: int | None, run_elapsed: float | None) -> str:
    label = "AMD vLLM batch" if source == "amd-vllm" else f"Offline batch ({source})"
    if run_total and run_elapsed:
        return (
            f"{label}: {run_total} reviews in {run_elapsed:.1f}s "
            f"({run_total / run_elapsed:.1f} rev/s)"
        )
    return f"{label} import"


def _parse_updated_at(value: object) -> datetime:
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            pass
    return datetime.now(timezone.utc)


def import_review_analysis(db: Session, data: object) -> ImportReport:
    """Upsert offline batch aggregates into review_analysis.

    Invalid rows are skipped with a recorded reason; a payload that is not a
    list at all fails loudly. Commits once at the end.
    """
    if not isinstance(data, list):
        raise ValueError("Batch analysis payload must be a JSON array of per-product rows")

    report = ImportReport()

    # The sentinel carries run-level metadata that per-product rows lack.
    for item in data:
        if isinstance(item, dict) and item.get("product_id") == BENCHMARK_SENTINEL:
            report.run_elapsed_seconds = _as_number(item.get("elapsed_seconds"))
            total = _as_number(item.get("total_reviews"))
            report.run_total_reviews = int(total) if total is not None else None

    sources: Counter[str] = Counter()
    for index, item in enumerate(data):
        if not isinstance(item, dict):
            report.skipped.append(f"row {index}: not an object")
            continue
        raw_id = item.get("product_id")
        if raw_id == BENCHMARK_SENTINEL:
            continue
        if raw_id in (None, ""):
            report.skipped.append(f"row {index}: missing product_id")
            continue

        product = _resolve_product(db, raw_id)
        if product is None:
            report.skipped.append(f"row {index} ({raw_id!r}): no unique matching product")
            continue

        source = _row_source(item)
        if source is None:
            report.skipped.append(f"row {index} ({raw_id!r}): unrecognized analysis source")
            continue

        pcts = {name: _as_number(item.get(name)) for name in _PCT_FIELDS}
        if any(v is None or not 0.0 <= v <= 1.0 for v in pcts.values()):
            report.skipped.append(f"row {index} ({raw_id!r}): pct fields missing or out of [0, 1]")
            continue

        total = _as_number(item.get("total_reviews"))
        if total is None or total < 0:
            report.skipped.append(f"row {index} ({raw_id!r}): invalid total_reviews")
            continue

        issues = item.get("top_issues_json", [])
        if not isinstance(issues, list):
            report.skipped.append(f"row {index} ({raw_id!r}): top_issues_json is not a list")
            continue

        # Complaint verdicts counted from per-review ground truth when the list
        # is complete; otherwise derived from the producer's pcts, which are
        # computed over total_reviews (unlike the runtime miner's graded pcts).
        classified = [r for r in item.get("classified_reviews", []) if isinstance(r, dict)]
        if classified and len(classified) == int(total):
            complaint_count = sum(
                1 for r in classified if r.get("fit_verdict") in ("small", "large")
            )
        else:
            complaint_count = round((pcts["pct_small"] + pcts["pct_large"]) * total)

        analysis = db.get(ReviewAnalysis, product.id) or ReviewAnalysis(product_id=product.id)
        analysis.pct_small = pcts["pct_small"]
        analysis.pct_large = pcts["pct_large"]
        analysis.pct_tts = pcts["pct_tts"]
        analysis.reviews_analyzed = int(total)
        analysis.complaint_count = complaint_count
        analysis.top_issues = [i for i in issues if isinstance(i, dict)]
        analysis.analysis_source = source
        analysis.analysis_mode = "batch"
        analysis.elapsed_seconds = report.run_elapsed_seconds
        analysis.throughput_note = _throughput_note(
            source, report.run_total_reviews, report.run_elapsed_seconds
        )
        analysis.updated_at = _parse_updated_at(item.get("updated_at"))
        db.add(analysis)

        sources[source] += 1
        report.imported.append(product.id)

    db.commit()
    if sources:
        report.source = sources.most_common(1)[0][0]
    return report
