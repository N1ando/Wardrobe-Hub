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
    # Provenance metadata; optional so pre-existing clients and rows are
    # unaffected. Null means "recorded before provenance tracking".
    analysis_source: Optional[str] = None  # amd-vllm | fireworks | keyword | cache
    analysis_mode: Optional[str] = None  # batch | live | fallback
    elapsed_seconds: Optional[float] = None


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


# The response shape below IS docs/recommendation_contract.md — the engine's
# output passes through unchanged. Change the doc first if this must change.


class FitBreakdownItem(BaseModel):
    dim: str
    garment: Optional[float] = None
    body: Optional[float] = None
    raw_ease: Optional[float] = None        # garment - body
    effective_ease: Optional[float] = None  # raw_ease + stretch credit
    scoring_ease: Optional[float] = None    # what was actually scored
    ideal_band: list[float] = Field(default_factory=list)  # [low, high] cm
    verdict: str  # ideal | tight | loose | missing_data
    score: Optional[float] = None
    weight: float = 0.0


class SizeScore(BaseModel):
    size: str
    base_score: float
    review_bonus: float
    adjusted_score: float


class ReviewSignal(BaseModel):
    pct_small: Optional[float] = None
    pct_tts: Optional[float] = None
    pct_large: Optional[float] = None
    bias_direction: str = "none"  # up | down | none
    applied_shift_bias: bool = False
    caveat: Optional[str] = None


class RunnerUp(BaseModel):
    size: str
    score: float


class RecommendResponse(BaseModel):
    recommended_size: str
    confidence: int  # 35-96 by design
    confidence_level: str  # low | medium | high
    runner_up: Optional[RunnerUp] = None
    size_scores: list[SizeScore] = Field(default_factory=list)
    fit_breakdown: list[FitBreakdownItem] = Field(default_factory=list)
    review_signal: Optional[ReviewSignal] = None
    material_note: str = ""
    missing_fields: list[str] = Field(default_factory=list)
    debug: dict = Field(default_factory=dict)


# ---- Explain ----------------------------------------------------------------


class ExplainRequest(BaseModel):
    recommendation: RecommendResponse
    product_name: Optional[str] = None


class ExplainResponse(BaseModel):
    explanation: str
    source: str  # amd-vllm | fireworks | cache | template


# ---- Seller -----------------------------------------------------------------


class FitDistribution(BaseModel):
    """Share of mined review verdicts; drives the dashboard's stacked bar."""

    pct_small: float = 0.0
    pct_tts: float = 0.0
    pct_large: float = 0.0


class QuoteItem(BaseModel):
    """A mined review quote — the proof that dashboard numbers come from
    real review text, not invented percentages."""

    text: str
    verdict: str  # small | large | tts
    size_bought: Optional[str] = None


class SellerRiskRow(BaseModel):
    product_id: int
    name: str
    category: str
    image_url: Optional[str] = None
    risk_level: str  # low | medium | high
    risk_score: int  # 0-100
    missing_fields: list[str] = Field(default_factory=list)
    fit_complaint_pct: float = 0.0
    review_count: int = 0
    complaint_count: int = 0
    chart_completeness: float = 1.0
    fit_distribution: FitDistribution = Field(default_factory=FitDistribution)


class SellerOverview(BaseModel):
    products: list[SellerRiskRow] = Field(default_factory=list)
    throughput_note: Optional[str] = None


class SellerProductRisk(BaseModel):
    product_id: int
    name: str
    image_url: Optional[str] = None
    risk_level: str
    risk_score: int
    missing_fields: list[str] = Field(default_factory=list)
    complaint_clusters: list[dict] = Field(default_factory=list)  # [{"area":..,"count":..}]
    review_summary: ReviewSummary
    suggestions: list[str] = Field(default_factory=list)
    review_count: int = 0
    complaint_count: int = 0
    chart_completeness: float = 1.0
    fit_distribution: FitDistribution = Field(default_factory=FitDistribution)
    quotes: list[QuoteItem] = Field(default_factory=list)


# ---- Health -----------------------------------------------------------------


class HealthResponse(BaseModel):
    status: str = "ok"
    gemma_backend: str  # amd-vllm | fireworks | cache | template
