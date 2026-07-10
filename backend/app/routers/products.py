"""Product listing + detail endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Product
from app.schemas import (
    ProductDetail,
    ProductSummary,
    ReviewSummary,
    SizeRow,
)

router = APIRouter(prefix="/api/products", tags=["products"])

_CHART_FIELDS = ("chest", "waist", "hips", "length", "sleeve", "inseam")


def size_rows(product: Product) -> list[SizeRow]:
    rows = sorted(product.size_charts, key=lambda c: c.order_index)
    return [
        SizeRow(size_label=c.size_label, **{f: getattr(c, f) for f in _CHART_FIELDS})
        for c in rows
    ]


def review_summary(product: Product) -> ReviewSummary | None:
    a = product.analysis
    if a is None:
        return None
    return ReviewSummary(
        pct_small=a.pct_small, pct_large=a.pct_large, pct_tts=a.pct_tts,
        reviews_analyzed=a.reviews_analyzed, top_issues=a.top_issues or [],
        analysis_source=a.analysis_source, analysis_mode=a.analysis_mode,
        elapsed_seconds=a.elapsed_seconds,
    )


@router.get("", response_model=list[ProductSummary])
def list_products(db: Session = Depends(get_db)) -> list[ProductSummary]:
    products = db.query(Product).order_by(Product.id).all()
    return [
        ProductSummary(id=p.id, name=p.name, price=p.price,
                       image_url=p.image_url, category=p.category)
        for p in products
    ]


@router.get("/{product_id}", response_model=ProductDetail)
def get_product(product_id: int, db: Session = Depends(get_db)) -> ProductDetail:
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return ProductDetail(
        id=product.id, name=product.name, price=product.price,
        image_url=product.image_url, category=product.category,
        material=product.material, stretch_pct=product.stretch_pct,
        raw_size_chart_text=product.raw_size_chart_text,
        size_chart=size_rows(product), review_summary=review_summary(product),
    )
