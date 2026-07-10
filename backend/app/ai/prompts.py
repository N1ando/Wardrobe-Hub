"""Gemma prompt templates (plan Section 5). Always request strict JSON."""

from __future__ import annotations

import json

SIZE_CHART_PARSER_SYSTEM = (
    "You normalize clothing size charts. Convert every measurement to centimetres. "
    "Output ONLY JSON, no prose, matching:\n"
    '{"unit_detected": "cm|in|mixed", '
    '"sizes": [{"label": "M", "chest": 104, "waist": 90, "hips": null, '
    '"length": null, "sleeve": null, "inseam": null}], '
    '"missing_fields": ["hips"], "warnings": ["..."]}\n'
    "Use null for any field the chart does not provide."
)

REVIEW_MINER_SYSTEM = (
    "You classify a clothing product review for fit signal. "
    "Output ONLY JSON matching:\n"
    '{"fit_verdict": "small|large|tts|none", "areas": ["waist"], '
    '"severity": 2, "quote": "short supporting quote"}\n'
    '"tts" means true-to-size. "areas" lists body parts mentioned (empty if none). '
    "severity is 1-3."
)

EXPLANATION_SYSTEM = (
    "You are a sizing assistant. Given a fit-analysis JSON, write 2-3 plain "
    "sentences for the shopper. State the recommended size and the single "
    "strongest reason; mention the review caveat if one is present; never "
    "contradict the JSON; no hedging filler, no emojis."
)

SELLER_SUGGESTIONS_SYSTEM = (
    "You advise an e-commerce seller on reducing size-related returns. Given a "
    "JSON summary of a product's size-chart gaps and review fit complaints, output "
    "ONLY JSON: {\"suggestions\": [\"concrete action tied to the data\", ...]} with "
    "at most 3 short, specific suggestions. No emojis."
)


def size_chart_user_prompt(raw_text: str) -> str:
    return f"Chart:\n{raw_text}"


def review_miner_user_prompt(review_text: str, size_bought: str | None = None) -> str:
    tail = f"\nSize bought: {size_bought}" if size_bought else ""
    return f"Review:\n{review_text}{tail}"


def explanation_user_prompt(recommendation: dict, product_name: str | None = None) -> str:
    head = f"Product: {product_name}\n" if product_name else ""
    return head + "Fit analysis JSON:\n" + json.dumps(recommendation, ensure_ascii=False)


def seller_suggestions_user_prompt(summary: dict) -> str:
    return "Product summary JSON:\n" + json.dumps(summary, ensure_ascii=False)
