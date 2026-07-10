"""Batch Gemma workloads (plan Section 5): review mining, chart parsing, seller
suggestions. Designed to run on the AMD Dev Cloud vLLM endpoint and cache results
to SQLite before the demo, but it degrades to deterministic keyword fallbacks so
it always produces data offline.
"""

from __future__ import annotations

import json
import time
from collections import Counter
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.ai import prompts
from app.ai.gemma_client import complete_json
from app.models import Product, Review, ReviewAnalysis

# Keyword fallback so the miner still classifies without any LLM available.
_SMALL_KW = ("runs small", "too small", "too tight", "size up", "tight", "snug")
_LARGE_KW = ("runs large", "too big", "too loose", "size down", "baggy", "oversized")
_TTS_KW = ("true to size", "fits perfectly", "perfect fit", "as expected", "spot on")
_AREA_KW = ("waist", "chest", "bust", "hips", "shoulders", "sleeve", "length", "inseam", "thigh")


def _keyword_verdict(text: str) -> dict:
    low = text.lower()
    small = sum(low.count(k) for k in _SMALL_KW)
    large = sum(low.count(k) for k in _LARGE_KW)
    tts = sum(low.count(k) for k in _TTS_KW)
    if small > large and small > 0:
        verdict = "small"
    elif large > small and large > 0:
        verdict = "large"
    elif tts > 0:
        verdict = "tts"
    else:
        verdict = "none"
    areas = [a for a in _AREA_KW if a in low]
    return {"fit_verdict": verdict, "areas": areas, "severity": 2, "quote": ""}


def classify_review(text: str, size_bought: str | None = None) -> tuple[dict, str]:
    """Classify one review; returns (verdict dict, source that produced it).

    Source vocabulary follows the ladder: amd-vllm | fireworks | cache |
    keyword (the deterministic template fallback).
    """
    parsed, source = complete_json(
        prompts.REVIEW_MINER_SYSTEM,
        prompts.review_miner_user_prompt(text, size_bought),
        tag="review",
        temperature=0.2,
        template_fn=lambda: json.dumps(_keyword_verdict(text)),
    )
    if not isinstance(parsed, dict) or "fit_verdict" not in parsed:
        parsed = _keyword_verdict(text)
        source = "template"
    if parsed.get("fit_verdict") not in ("small", "large", "tts", "none"):
        parsed["fit_verdict"] = "none"
    parsed.setdefault("areas", [])
    return parsed, "keyword" if source == "template" else source


def analyze_product_reviews(db: Session, product_id: int, *, mode: str = "live") -> ReviewAnalysis:
    """Mine every review of a product, aggregate, and upsert ReviewAnalysis.

    `mode` labels how the run was triggered ("live" for on-demand API calls,
    "batch" for the pre-demo ingest script); it is downgraded to "fallback"
    when the verdicts came from the keyword classifier rather than an LLM.
    """
    reviews = db.query(Review).filter(Review.product_id == product_id).all()
    start = time.perf_counter()

    counts = Counter()
    area_counter = Counter()
    source_counter = Counter()
    for review in reviews:
        result, source = classify_review(review.text, review.size_bought)
        source_counter[source] += 1
        verdict = result["fit_verdict"]
        review.verdict = None if verdict == "none" else verdict
        review.areas = result.get("areas") or []
        counts[verdict] += 1
        if verdict in ("small", "large"):
            for area in review.areas:
                area_counter[area] += 1

    elapsed = time.perf_counter() - start
    total = len(reviews)
    graded = counts["small"] + counts["large"] + counts["tts"]
    denom = graded or 1
    dominant_source = source_counter.most_common(1)[0][0] if source_counter else None

    analysis = db.get(ReviewAnalysis, product_id) or ReviewAnalysis(product_id=product_id)
    analysis.pct_small = round(counts["small"] / denom, 3)
    analysis.pct_large = round(counts["large"] / denom, 3)
    analysis.pct_tts = round(counts["tts"] / denom, 3)
    analysis.reviews_analyzed = total
    analysis.complaint_count = counts["small"] + counts["large"]
    analysis.top_issues = [{"area": a, "count": c} for a, c in area_counter.most_common(3)]
    analysis.throughput_note = f"Analyzed {total} reviews in {elapsed:.1f}s"
    analysis.analysis_source = dominant_source
    analysis.analysis_mode = "fallback" if dominant_source == "keyword" else mode
    analysis.elapsed_seconds = round(elapsed, 3)
    analysis.updated_at = datetime.now(timezone.utc)

    db.add(analysis)
    db.commit()
    return analysis


def parse_size_chart(raw_text: str) -> dict | None:
    parsed, _ = complete_json(
        prompts.SIZE_CHART_PARSER_SYSTEM,
        prompts.size_chart_user_prompt(raw_text),
        tag="chart",
        temperature=0.2,
    )
    return parsed if isinstance(parsed, dict) else None


def suggest_seller_fixes(summary: dict) -> list[str]:
    def _template() -> str:
        tips = []
        for field in summary.get("missing_fields", [])[:2]:
            tips.append(f"Add {field} measurements to your size chart to cut fit guesswork.")
        for issue in summary.get("top_issues", [])[:1]:
            area = issue.get("area")
            if area:
                tips.append(f"Reviewers flag {area}; note true-to-size guidance for it.")
        if summary.get("pct_small", 0) >= 0.25:
            tips.append("Many buyers say it runs small; recommend sizing up on the page.")
        return json.dumps({"suggestions": tips[:3]})

    parsed, _ = complete_json(
        prompts.SELLER_SUGGESTIONS_SYSTEM,
        prompts.seller_suggestions_user_prompt(summary),
        tag="seller",
        temperature=0.4,
        template_fn=_template,
    )
    if isinstance(parsed, dict) and isinstance(parsed.get("suggestions"), list):
        return [str(s) for s in parsed["suggestions"]][:3]
    return json.loads(_template())["suggestions"]
