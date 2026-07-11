"""SQLAlchemy ORM models mirroring the plan's data model (SQLite tables)."""

from __future__ import annotations

from datetime import datetime, timezone


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    category: Mapped[str] = mapped_column(String)  # shirt | pants | dress | jacket
    price: Mapped[float] = mapped_column(Float, default=0.0)
    image_url: Mapped[str | None] = mapped_column(String, nullable=True)
    material: Mapped[str | None] = mapped_column(String, nullable=True)
    stretch_pct: Mapped[float] = mapped_column(Float, default=0.0)
    raw_size_chart_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    size_charts: Mapped[list["SizeChart"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )
    reviews: Mapped[list["Review"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )
    analysis: Mapped["ReviewAnalysis | None"] = relationship(
        back_populates="product", cascade="all, delete-orphan", uselist=False
    )


class SizeChart(Base):
    """One row per size label. All measurements are cm, nullable when missing."""

    __tablename__ = "size_charts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    size_label: Mapped[str] = mapped_column(String)  # "S", "M", "31", ...
    order_index: Mapped[int] = mapped_column(Integer, default=0)  # ordering for size shifts

    chest: Mapped[float | None] = mapped_column(Float, nullable=True)
    waist: Mapped[float | None] = mapped_column(Float, nullable=True)
    hips: Mapped[float | None] = mapped_column(Float, nullable=True)
    length: Mapped[float | None] = mapped_column(Float, nullable=True)
    sleeve: Mapped[float | None] = mapped_column(Float, nullable=True)
    inseam: Mapped[float | None] = mapped_column(Float, nullable=True)

    product: Mapped[Product] = relationship(back_populates="size_charts")


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    text: Mapped[str] = mapped_column(Text)
    size_bought: Mapped[str | None] = mapped_column(String, nullable=True)
    # LLM-filled fit verdict: small | large | tts | None
    verdict: Mapped[str | None] = mapped_column(String, nullable=True)
    # LLM-filled body areas mentioned, e.g. ["waist", "shoulders"]
    areas: Mapped[list | None] = mapped_column(JSON, nullable=True)

    product: Mapped[Product] = relationship(back_populates="reviews")


class ReviewAnalysis(Base):
    """Aggregated fit signal per product (produced by the batch miner)."""

    __tablename__ = "review_analysis"

    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), primary_key=True)
    pct_small: Mapped[float] = mapped_column(Float, default=0.0)
    pct_large: Mapped[float] = mapped_column(Float, default=0.0)
    pct_tts: Mapped[float] = mapped_column(Float, default=0.0)
    reviews_analyzed: Mapped[int] = mapped_column(Integer, default=0)
    # small+large verdicts counted at mining/import time, NOT derived from the
    # pcts (whose denominator is graded reviews only) so displayed counts can
    # never drift from the verdicts behind them.
    complaint_count: Mapped[int] = mapped_column(Integer, default=0)
    top_issues: Mapped[list | None] = mapped_column(JSON, nullable=True)  # [{"area":..,"count":..}]
    throughput_note: Mapped[str | None] = mapped_column(String, nullable=True)  # AMD proof string
    # Provenance of the aggregate. Nullable so rows written before these
    # columns existed keep working unchanged.
    analysis_source: Mapped[str | None] = mapped_column(String, nullable=True)  # amd-vllm | fireworks | keyword | cache
    analysis_mode: Mapped[str | None] = mapped_column(String, nullable=True)  # batch | live | fallback
    elapsed_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)  # wall time of the producing run
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    product: Mapped[Product] = relationship(back_populates="analysis")


class FitProfile(Base):
    """Optional server-side Fit Passport (localStorage is fine on the frontend)."""

    __tablename__ = "fit_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    measurements: Mapped[dict] = mapped_column(JSON)
    fit_pref: Mapped[str] = mapped_column(String, default="regular")


class CartItem(Base):
    """A line in the demo's single shared cart (no auth/users in scope)."""

    __tablename__ = "cart_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    size: Mapped[str] = mapped_column(String)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    product: Mapped[Product] = relationship()
