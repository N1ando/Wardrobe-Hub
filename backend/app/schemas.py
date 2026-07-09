"""Pydantic request/response schemas. Frozen contract per plan Sections 3-4."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class FitPref(str, Enum):
    slim = "slim"
    regular = "regular"
    relaxed = "relaxed"


# ---- Products ---------------------------------------------------------------


class ProductSummary(BaseModel):
    id: int
    name: str
    price: float
    image_url: Optional[str] = None
    category: str


class SizeRow(BaseModel):
    size_label: str
    chest: Optional[float] = None
    waist: Optional[float] = None
    hips: Optional[float] = None
    length: Optional[float] = None
    sleeve: Optional[float] = None
    inseam: Optional[float] = None


class ReviewSummary(BaseModel):
    pct_small: float = 0.0
    pct_large: float = 0.0
    pct_tts: float = 0.0
    reviews_analyzed: int = 0
    top_issues: list[dict] = Field(default_factory=list)


class ProductDetail(ProductSummary):
    material: Optional[str] = None
    stretch_pct: float = 0.0
    raw_size_chart_text: Optional[str] = None
    size_chart: list[SizeRow] = Field(default_factory=list)
    review_summary: Optional[ReviewSummary] = None


# ---- Recommend --------------------------------------------------------------


class Measurements(BaseModel):
    chest: Optional[float] = None
    bust: Optional[float] = None
    waist: Optional[float] = None
    hips: Optional[float] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    inseam: Optional[float] = None


class RecommendRequest(BaseModel):
    product_id: int
    fit_pref: FitPref = FitPref.regular
    measurements: Measurements


class FitBreakdownItem(BaseModel):
    dim: str
    garment: Optional[float] = None
    body: Optional[float] = None
    ease: Optional[float] = None
    verdict: str  # ideal | tight | loose | missing_data
    score: Optional[float] = None


class ReviewSignal(BaseModel):
    pct_small: float = 0.0
    pct_tts: float = 0.0
    pct_large: float = 0.0
    caveat: Optional[str] = None
    applied_shift_bias: bool = False


class RunnerUp(BaseModel):
    size: str
    score: float


class RecommendResponse(BaseModel):
    recommended_size: str
    confidence: int
    runner_up: Optional[RunnerUp] = None
    fit_breakdown: list[FitBreakdownItem] = Field(default_factory=list)
    review_signal: Optional[ReviewSignal] = None
    material_note: Optional[str] = None
    missing_fields: list[str] = Field(default_factory=list)
    low_confidence: bool = False


# ---- Explain ----------------------------------------------------------------


class ExplainRequest(BaseModel):
    recommendation: RecommendResponse
    product_name: Optional[str] = None


class ExplainResponse(BaseModel):
    explanation: str
    source: str  # amd-vllm | fireworks | cache | template


# ---- Seller -----------------------------------------------------------------


class SellerRiskRow(BaseModel):
    product_id: int
    name: str
    category: str
    risk_level: str  # low | medium | high
    risk_score: int  # 0-100
    missing_fields: list[str] = Field(default_factory=list)
    fit_complaint_pct: float = 0.0


class SellerOverview(BaseModel):
    products: list[SellerRiskRow] = Field(default_factory=list)
    throughput_note: Optional[str] = None


class SellerProductRisk(BaseModel):
    product_id: int
    name: str
    risk_level: str
    risk_score: int
    missing_fields: list[str] = Field(default_factory=list)
    complaint_clusters: list[dict] = Field(default_factory=list)  # [{"area":..,"count":..}]
    review_summary: ReviewSummary
    suggestions: list[str] = Field(default_factory=list)


# ---- Health -----------------------------------------------------------------


class HealthResponse(BaseModel):
    status: str = "ok"
    gemma_backend: str  # amd-vllm | fireworks | cache | template
