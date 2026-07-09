import argparse
import json
import os
import re
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def env(name: str, default: str = "") -> str:
    return os.getenv(name, default)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def normalize_reviews(raw: Any) -> list[dict]:
    reviews = raw if isinstance(raw, list) else raw.get("reviews", [])

    normalized = []

    for item in reviews:
        product_id = item.get("product_id") or item.get("productId")
        text = item.get("text") or item.get("review") or item.get("content") or item.get("comment")

        if product_id and text:
            normalized.append(
                {
                    "product_id": str(product_id),
                    "text": str(text),
                    "rating": item.get("rating"),
                    "size_bought": item.get("size_bought") or item.get("sizeBought"),
                }
            )

    return normalized


def local_classify(text: str) -> dict:
    lowered = text.lower()

    small_words = ["too small", "runs small", "tight", "snug", "size up", "sized up"]
    large_words = ["too big", "runs large", "loose", "baggy", "size down", "too long", "runs long"]
    tts_words = ["true to size", "fits well", "perfect fit", "fits perfectly", "as expected"]

    areas_map = {
        "waist": ["waist"],
        "hips": ["hip", "hips"],
        "chest": ["chest"],
        "bust": ["bust"],
        "shoulders": ["shoulder", "shoulders"],
        "length": ["length", "long", "short"],
        "sleeve": ["sleeve", "sleeves"],
        "inseam": ["inseam"],
    }

    small = sum(word in lowered for word in small_words)
    large = sum(word in lowered for word in large_words)
    tts = sum(word in lowered for word in tts_words)

    if small > large and small > 0:
        verdict = "small"
    elif large > small and large > 0:
        verdict = "large"
    elif tts > 0:
        verdict = "tts"
    else:
        verdict = "none"

    areas = [
        area
        for area, words in areas_map.items()
        if any(word in lowered for word in words)
    ]

    return {
        "fit_verdict": verdict,
        "areas": areas,
        "severity": 2 if verdict in {"small", "large"} else 1,
        "quote": text[:160],
        "backend": "local",
    }


def extract_json(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise ValueError("No JSON object found in model response.")
        return json.loads(match.group(0))


def amd_client() -> tuple[OpenAI, str]:
    base_url = env("AMD_LLM_URL", "http://localhost:8000/v1").rstrip("/")
    model = env("AMD_LLM_MODEL", "fitos-gemma")

    client = OpenAI(
        base_url=base_url,
        api_key=env("AMD_LLM_API_KEY", "not-needed"),
    )

    return client, model


def amd_classify(review: dict) -> dict:
    client, model = amd_client()

    prompt = f"""
You are a fit-review classifier for FitOS.

Classify this clothing review.

Return ONLY valid JSON with this exact schema:
{{
  "fit_verdict": "small|large|tts|none",
  "areas": ["waist"],
  "severity": 1,
  "quote": "short quote from the review"
}}

Rules:
- fit_verdict must be one of: small, large, tts, none.
- areas can include: waist, hips, chest, bust, shoulders, length, sleeve, inseam.
- severity must be 1, 2, or 3.
- quote must be copied or shortened from the review.
- Do not include markdown.
- Do not explain reasoning.

Review:
{review["text"]}
"""

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=float(env("LLM_TEMPERATURE", "0.2")),
        max_tokens=160,
    )

    content = response.choices[0].message.content or ""
    parsed = extract_json(content)

    verdict = parsed.get("fit_verdict", "none")
    if verdict not in {"small", "large", "tts", "none"}:
        verdict = "none"

    areas = parsed.get("areas", [])
    if not isinstance(areas, list):
        areas = []

    severity = parsed.get("severity", 1)
    if severity not in {1, 2, 3}:
        severity = 1

    return {
        "fit_verdict": verdict,
        "areas": [str(area) for area in areas],
        "severity": severity,
        "quote": str(parsed.get("quote") or review["text"][:160])[:160],
        "backend": "amd-vllm",
    }


def classify_review(review: dict, mode: str) -> dict:
    if mode == "amd-vllm":
        try:
            return amd_classify(review)
        except Exception as error:
            print(f"[WARN] AMD vLLM failed, falling back local: {error}")

    return local_classify(review["text"])


def aggregate(reviews: list[dict], classifications: list[dict], mode: str, elapsed: float) -> list[dict]:
    grouped = defaultdict(list)

    for review, classification in zip(reviews, classifications):
        grouped[review["product_id"]].append((review, classification))

    output = []

    for product_id, items in grouped.items():
        verdicts = Counter()
        areas = Counter()
        classified_reviews = []

        for review, classification in items:
            verdicts[classification["fit_verdict"]] += 1
            areas.update(classification["areas"])

            classified_reviews.append(
                {
                    "product_id": product_id,
                    "text": review["text"],
                    "fit_verdict": classification["fit_verdict"],
                    "areas": classification["areas"],
                    "severity": classification["severity"],
                    "quote": classification["quote"],
                    "backend": classification["backend"],
                    "rating": review.get("rating"),
                    "size_bought": review.get("size_bought"),
                }
            )

        total = len(items)

        output.append(
            {
                "product_id": product_id,
                "total_reviews": total,
                "pct_small": round(verdicts["small"] / total, 4),
                "pct_large": round(verdicts["large"] / total, 4),
                "pct_tts": round(verdicts["tts"] / total, 4),
                "top_issues_json": [
                    {"area": area, "count": count}
                    for area, count in areas.most_common(5)
                ],
                "classified_reviews": classified_reviews,
                "analysis_mode": mode,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    output.append(
        {
            "product_id": "__benchmark__",
            "analysis_mode": mode,
            "total_reviews": len(reviews),
            "elapsed_seconds": round(elapsed, 4),
            "reviews_per_second": round(len(reviews) / elapsed, 4) if elapsed > 0 else None,
            "amd_llm_url": env("AMD_LLM_URL", "") if mode == "amd-vllm" else "",
            "amd_llm_model": env("AMD_LLM_MODEL", "") if mode == "amd-vllm" else "",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
    )

    return output


def run(input_path: Path, output_path: Path, mode: str) -> None:
    raw = load_json(input_path)
    reviews = normalize_reviews(raw)

    if not reviews:
        raise RuntimeError("No valid reviews found.")

    start = time.perf_counter()
    classifications = [classify_review(review, mode) for review in reviews]
    elapsed = time.perf_counter() - start

    output = aggregate(reviews, classifications, mode, elapsed)
    save_json(output_path, output)

    print("Review analysis complete.")
    print(f"Mode: {mode}")
    print(f"Input reviews: {len(reviews)}")
    print(f"Products analyzed: {len(output) - 1}")
    print(f"Elapsed seconds: {elapsed:.4f}")
    print(f"Reviews/sec: {len(reviews) / elapsed:.4f}")
    print(f"Output written to: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=env("REVIEW_INPUT_PATH", "data/sample/reviews.sample.json"))
    parser.add_argument("--output", default=env("REVIEW_ANALYSIS_OUTPUT_PATH", "data/processed/review_analysis.example.json"))
    parser.add_argument("--mode", default=env("REVIEW_ANALYSIS_MODE", "local"), choices=["local", "amd-vllm"])

    args = parser.parse_args()

    run(
        input_path=Path(args.input),
        output_path=Path(args.output),
        mode=args.mode,
    )
