"""Seller-side risk analytics (plan Sections 2, 5.4). This is the B2B story."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.ai.batch_analysis import suggest_seller_fixes
from app.core.ease_bands import chart_fields_for_category
from app.db import get_db
from app.models import Product
from app.schemas import (
    ReviewSummary,
    SellerOverview,
    SellerProductRisk,
    SellerRiskRow,
)

router = APIRouter(prefix="/api/seller", tags=["seller"])


def missing_chart_fields(product: Product) -> list[str]:
    needed = chart_fields_for_category(product.category)
    present = {
        f for f in needed
        if any(getattr(c, f) is not None for c in product.size_charts)
    }
    return [f for f in needed if f not in present]


def _risk(product: Product) -> tuple[int, str, float, list[str]]:
    needed = chart_fields_for_category(product.category)
    missing = missing_chart_fields(product)
    completeness = 1.0 - (len(missing) / len(needed)) if needed else 1.0

    a = product.analysis
    complaint_pct = (a.pct_small + a.pct_large) if a else 0.0

    score = round(100 * (0.4 * (1 - completeness) + 0.6 * complaint_pct))
    score = max(0, min(100, score))
    level = "low" if score < 34 else ("medium" if score < 67 else "high")
    return score, level, round(complaint_pct, 3), missing


@router.get("/overview", response_model=SellerOverview)
def overview(db: Session = Depends(get_db)) -> SellerOverview:
    products = db.query(Product).order_by(Product.id).all()
    rows, note = [], None
    for p in products:
        score, level, complaint_pct, missing = _risk(p)
        rows.append(SellerRiskRow(
            product_id=p.id, name=p.name, category=p.category,
            risk_level=level, risk_score=score,
            missing_fields=missing, fit_complaint_pct=complaint_pct,
        ))
        if p.analysis and p.analysis.throughput_note and note is None:
            note = p.analysis.throughput_note
    return SellerOverview(products=rows, throughput_note=note)


@router.get("/products/{product_id}/risk", response_model=SellerProductRisk)
def product_risk(product_id: int, db: Session = Depends(get_db)) -> SellerProductRisk:
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    score, level, complaint_pct, missing = _risk(product)
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

    return SellerProductRisk(
        product_id=product.id, name=product.name, risk_level=level, risk_score=score,
        missing_fields=missing, complaint_clusters=clusters,
        review_summary=summary, suggestions=suggestions,
    )
