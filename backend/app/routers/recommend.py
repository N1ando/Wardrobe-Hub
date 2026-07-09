"""POST /api/recommend -> deterministic size recommendation."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.recommender import recommend as run_recommender
from app.db import get_db
from app.models import Product
from app.schemas import RecommendRequest, RecommendResponse

router = APIRouter(prefix="/api", tags=["recommend"])

_CHART_FIELDS = ("chest", "waist", "hips", "length", "sleeve", "inseam")


def product_size_chart(product: Product) -> list[dict]:
    chart = []
    for c in product.size_charts:
        row = {"size_label": c.size_label, "order_index": c.order_index}
        row.update({f: getattr(c, f) for f in _CHART_FIELDS})
        chart.append(row)
    return chart


def product_review_analysis(product: Product) -> dict | None:
    a = product.analysis
    if a is None:
        return None
    return {"pct_small": a.pct_small, "pct_large": a.pct_large,
            "pct_tts": a.pct_tts, "top_issues": a.top_issues or []}


@router.post("/recommend", response_model=RecommendResponse)
def recommend(req: RecommendRequest, db: Session = Depends(get_db)) -> RecommendResponse:
    product = db.get(Product, req.product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    result = run_recommender(
        category=product.category,
        size_chart=product_size_chart(product),
        measurements=req.measurements.model_dump(exclude_none=True),
        fit_pref=req.fit_pref.value,
        stretch_pct=product.stretch_pct or 0.0,
        material=product.material,
        review_analysis=product_review_analysis(product),
    )
    return RecommendResponse(**result)
