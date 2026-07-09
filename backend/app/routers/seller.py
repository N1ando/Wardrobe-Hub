"""Seller-side risk analytics (plan Sections 2, 5.4). This is the B2B story."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.ai.batch_analysis import suggest_seller_fixes
from app.core.fields import chart_fields_for_category
from app.db import get_db
from app.models import Product, Review, ReviewAnalysis
from app.schemas import (
    FitDistribution,
    QuoteItem,
    ReviewSummary,
    SellerOverview,
    SellerProductRisk,
    SellerRiskRow,
)

router = APIRouter(prefix="/api/seller", tags=["seller"])

# How many mined quotes the risk drilldown returns: enough to prove the
# percentages come from real review text, few enough to stay scannable.
_MAX_COMPLAINT_QUOTES = 3
_MAX_TTS_QUOTES = 1


def missing_chart_fields(product: Product) -> list[str]:
    needed = chart_fields_for_category(product.category)
    present = {
        f for f in needed
        if any(getattr(c, f) is not None for c in product.size_charts)
    }
    return [f for f in needed if f not in present]


def _risk(product: Product) -> tuple[int, str, float, list[str], float]:
    needed = chart_fields_for_category(product.category)
    missing = missing_chart_fields(product)
    completeness = 1.0 - (len(missing) / len(needed)) if needed else 1.0

    a = product.analysis
    complaint_pct = (a.pct_small + a.pct_large) if a else 0.0

    score = round(100 * (0.4 * (1 - completeness) + 0.6 * complaint_pct))
    score = max(0, min(100, score))
    # High from 60: a product with a dominant complaint cluster (like the
    # seeded dress) must read as high-risk on the dashboard.
    level = "low" if score < 34 else ("medium" if score < 60 else "high")
    return score, level, round(complaint_pct, 3), missing, round(completeness, 3)


def _distribution(analysis: ReviewAnalysis | None) -> FitDistribution:
    if analysis is None:
        return FitDistribution()
    return FitDistribution(
        pct_small=analysis.pct_small,
        pct_tts=analysis.pct_tts,
        pct_large=analysis.pct_large,
    )


def _counts(analysis: ReviewAnalysis | None, complaint_pct: float) -> tuple[int, int]:
    """(review_count, complaint_count) from the mined aggregate."""
    if analysis is None:
        return 0, 0
    return analysis.reviews_analyzed, round(complaint_pct * analysis.reviews_analyzed)


def _quotes(db: Session, product: Product) -> list[QuoteItem]:
    """Representative mined quotes: the dominant complaint verdict first,
    then one true-to-size voice. Ordered by id so the demo is stable."""
    a = product.analysis
    dominant = "small" if (a and a.pct_small >= a.pct_large) else "large"

    def fetch(verdict: str, limit: int) -> list[Review]:
        return (
            db.query(Review)
            .filter(Review.product_id == product.id, Review.verdict == verdict)
            .order_by(Review.id)
            .limit(limit)
            .all()
        )

    picked = fetch(dominant, _MAX_COMPLAINT_QUOTES) + fetch("tts", _MAX_TTS_QUOTES)
    return [
        QuoteItem(text=r.text, verdict=r.verdict, size_bought=r.size_bought)
        for r in picked
    ]


@router.get("/overview", response_model=SellerOverview)
def overview(db: Session = Depends(get_db)) -> SellerOverview:
    products = db.query(Product).order_by(Product.id).all()
    rows, note = [], None
    for p in products:
        score, level, complaint_pct, missing, completeness = _risk(p)
        review_count, complaint_count = _counts(p.analysis, complaint_pct)
        rows.append(SellerRiskRow(
            product_id=p.id, name=p.name, category=p.category,
            image_url=p.image_url,
            risk_level=level, risk_score=score,
            missing_fields=missing, fit_complaint_pct=complaint_pct,
            review_count=review_count, complaint_count=complaint_count,
            chart_completeness=completeness,
            fit_distribution=_distribution(p.analysis),
        ))
        if p.analysis and p.analysis.throughput_note and note is None:
            note = p.analysis.throughput_note
    return SellerOverview(products=rows, throughput_note=note)


@router.get("/products/{product_id}/risk", response_model=SellerProductRisk)
def product_risk(product_id: int, db: Session = Depends(get_db)) -> SellerProductRisk:
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    score, level, complaint_pct, missing, completeness = _risk(product)
    a = product.analysis
    summary = ReviewSummary(
        pct_small=a.pct_small if a else 0.0,
        pct_large=a.pct_large if a else 0.0,
        pct_tts=a.pct_tts if a else 0.0,
        reviews_analyzed=a.reviews_analyzed if a else 0,
        top_issues=(a.top_issues or []) if a else [],
    )
    clusters = (a.top_issues or []) if a else []

    suggestions = suggest_seller_fixes({
        "name": product.name,
        "category": product.category,
        "missing_fields": missing,
        "top_issues": clusters,
        "pct_small": summary.pct_small,
        "pct_large": summary.pct_large,
    })

    review_count, complaint_count = _counts(a, complaint_pct)
    return SellerProductRisk(
        product_id=product.id, name=product.name, image_url=product.image_url,
        risk_level=level, risk_score=score,
        missing_fields=missing, complaint_clusters=clusters,
        review_summary=summary, suggestions=suggestions,
        review_count=review_count, complaint_count=complaint_count,
        chart_completeness=completeness,
        fit_distribution=_distribution(a),
        quotes=_quotes(db, product),
    )
