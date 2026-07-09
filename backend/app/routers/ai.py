"""Gemma-backed AI endpoints: size-chart parsing + review-mining batch trigger."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.ai.batch_analysis import analyze_product_reviews, parse_size_chart
from app.db import get_db
from app.models import Product

router = APIRouter(prefix="/api/ai", tags=["ai"])


class ParseChartRequest(BaseModel):
    raw_text: str


class AnalyzeReviewsRequest(BaseModel):
    product_id: int | None = None  # None => analyze all products


@router.post("/parse-size-chart")
def parse_chart(req: ParseChartRequest) -> dict:
    parsed = parse_size_chart(req.raw_text)
    if parsed is None:
        raise HTTPException(status_code=502, detail="Could not parse chart into JSON")
    return parsed


@router.post("/analyze-reviews")
def analyze_reviews(req: AnalyzeReviewsRequest, db: Session = Depends(get_db)) -> dict:
    if req.product_id is not None:
        if db.get(Product, req.product_id) is None:
            raise HTTPException(status_code=404, detail="Product not found")
        product_ids = [req.product_id]
    else:
        product_ids = [p.id for p in db.query(Product).order_by(Product.id).all()]

    results = []
    for pid in product_ids:
        analysis = analyze_product_reviews(db, pid)
        results.append({
            "product_id": pid,
            "reviews_analyzed": analysis.reviews_analyzed,
            "pct_small": analysis.pct_small,
            "pct_large": analysis.pct_large,
            "pct_tts": analysis.pct_tts,
            "top_issues": analysis.top_issues,
            "throughput_note": analysis.throughput_note,
        })
    return {"analyzed": results}
