"""POST /api/explain -> natural-language explanation via Gemma (live path)."""

from __future__ import annotations

from fastapi import APIRouter

from app.ai import prompts
from app.ai.gemma_client import complete
from app.schemas import ExplainRequest, ExplainResponse

router = APIRouter(prefix="/api", tags=["explain"])


def _template_explanation(rec: dict) -> str:
    """Deterministic fallback so the demo never stalls without an LLM."""
    size = rec.get("recommended_size", "?")
    conf = rec.get("confidence", 0)
    # Strongest reason = the heaviest-weighted dimension that fits ideally.
    reason = ""
    ideal = [b for b in rec.get("fit_breakdown", []) if b.get("verdict") == "ideal"]
    if ideal:
        top = max(ideal, key=lambda b: b.get("weight") or 0.0)
        reason = f" Your {top['dim']} fits with about {top.get('raw_ease')}cm of ease"
    caveat = ""
    sig = rec.get("review_signal") or {}
    if sig.get("caveat"):
        caveat = f" Heads up: {sig['caveat']}"  # caveat is a full sentence
    return f"We recommend size {size} ({conf}% confidence).{reason}.{caveat}".replace("..", ".")


@router.post("/explain", response_model=ExplainResponse)
def explain(req: ExplainRequest) -> ExplainResponse:
    rec = req.recommendation.model_dump()
    result = complete(
        prompts.EXPLANATION_SYSTEM,
        prompts.explanation_user_prompt(rec, req.product_name),
        tag="explain",
        temperature=0.6,
        template_fn=lambda: _template_explanation(rec),
    )
    return ExplainResponse(explanation=result.text, source=result.source)
