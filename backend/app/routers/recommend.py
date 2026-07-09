"""POST /api/recommend -> deterministic size recommendation.

Thin adapter over the shared engine (repo-root ``core`` package): builds the
engine's product dict from the ORM rows, passes the mined review signal, and
returns the engine's dict unchanged — the response IS the frozen contract in
docs/recommendation_contract.md.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.recommender import recommend_size

from app.db import get_db
from app.models import Product
from app.schemas import RecommendRequest, RecommendResponse

router = APIRouter(prefix="/api", tags=["recommend"])

_CHART_FIELDS = ("chest", "waist", "hips", "length", "sleeve", "inseam")

# Review-bias thresholds mirrored from the engine so the synthesized caveat
# only appears when the engine will actually act on the signal.
_BIAS_TRIGGER = 0.25
_BIAS_MARGIN = 0.15


def product_size_chart(product: Product) -> list[dict]:
    chart = []
    for c in sorted(product.size_charts, key=lambda c: c.order_index):
        row = {"size_label": c.size_label}
        row.update({f: getattr(c, f) for f in _CHART_FIELDS})
        if product.category == "dress":
            # Dress charts store the bust measurement in the DB's `chest`
            # column (there is no bust column); the engine scores dresses on
            # `bust`, so surface it under that key.
            row["bust"] = row.get("chest")
        chart.append(row)
    return chart


def _caveat(pct_small: float, pct_large: float, top_issues: list) -> str | None:
    """Area-aware caveat, synthesized only when the bias thresholds fire."""
    if pct_small >= _BIAS_TRIGGER and (pct_small - pct_large) >= _BIAS_MARGIN:
        direction, advice = "small", "consider sizing up"
    elif pct_large >= _BIAS_TRIGGER and (pct_large - pct_small) >= _BIAS_MARGIN:
        direction, advice = "large", "consider sizing down"
    else:
        return None
    area = top_issues[0].get("area") if top_issues and isinstance(top_issues[0], dict) else None
    where = f" in the {area}" if area else ""
    return f"Reviewers say this runs {direction}{where}; {advice}."


def product_review_analysis(product: Product) -> dict | None:
    a = product.analysis
    if a is None:
        return None
    return {
        "pct_small": a.pct_small,
        "pct_large": a.pct_large,
        "pct_tts": a.pct_tts,
        "caveat": _caveat(a.pct_small, a.pct_large, a.top_issues or []),
    }


@router.post("/recommend", response_model=RecommendResponse)
def recommend(req: RecommendRequest, db: Session = Depends(get_db)) -> RecommendResponse:
    product = db.get(Product, req.product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    engine_product = {
        "id": product.id,
        "category": product.category,
        "size_chart": product_size_chart(product),
        "stretch_pct": product.stretch_pct or 0.0,
        "material": product.material,
    }
    try:
        result = recommend_size(
            engine_product,
            req.measurements.model_dump(exclude_none=True),
            req.fit_pref.value,
            product_review_analysis(product),
        )
    except ValueError as exc:
        # Engine's error contract: bad product data (e.g. empty chart) is the
        # only ValueError source — surface it as an unprocessable entity.
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return RecommendResponse(**result)
