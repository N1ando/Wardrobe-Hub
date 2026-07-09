import argparse
import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()


def get_env(name: str, default: str | None = None, required: bool = False) -> str:
    value = os.getenv(name, default)

    if required and not value:
        raise RuntimeError(f"Missing required environment variable: {name}")

    return value or ""


def load_json(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def normalize_reviews(raw_data: Any) -> list[dict]:
    if isinstance(raw_data, list):
        reviews = raw_data
    elif isinstance(raw_data, dict):
        reviews = raw_data.get("reviews", [])
    else:
        raise RuntimeError("Reviews JSON must be a list or an object with a reviews field.")

    normalized = []

    for item in reviews:
        if not isinstance(item, dict):
            continue

        product_id = item.get("product_id") or item.get("productId")
        text = item.get("text") or item.get("review") or item.get("content") or item.get("comment")

        if product_id is None or not text:
            continue

        normalized.append(
            {
                "product_id": str(product_id),
                "text": str(text),
                "rating": item.get("rating"),
                "size_bought": item.get("size_bought") or item.get("sizeBought"),
            }
        )

    return normalized


def classify_review(text: str) -> dict:
    lowered = text.lower()

    small_keywords = [
        "too small",
        "runs small",
        "tight",
        "snug",
        "size up",
        "sized up",
        "smaller than expected",
        "waist tight",
        "shoulders tight",
    ]

    large_keywords = [
        "too big",
        "runs large",
        "loose",
        "baggy",
        "size down",
        "larger than expected",
        "too long",
        "runs long",
        "length runs long",
    ]

    tts_keywords = [
        "true to size",
        "fits well",
        "perfect fit",
        "as expected",
        "fits perfectly",
    ]

    area_keywords = {
        "waist": ["waist"],
        "hips": ["hip", "hips"],
        "chest": ["chest"],
        "bust": ["bust"],
        "shoulders": ["shoulder", "shoulders"],
        "length": ["length", "long", "short"],
        "sleeve": ["sleeve", "sleeves"],
        "inseam": ["inseam"],
    }

    small_score = sum(keyword in lowered for keyword in small_keywords)
    large_score = sum(keyword in lowered for keyword in large_keywords)
    tts_score = sum(keyword in lowered for keyword in tts_keywords)

    if small_score > large_score and small_score > 0:
        verdict = "small"
    elif large_score > small_score and large_score > 0:
        verdict = "large"
    elif tts_score > 0:
        verdict = "tts"
    else:
        verdict = "none"

    areas = []

    for area, keywords in area_keywords.items():
        if any(keyword in lowered for keyword in keywords):
            areas.append(area)

    return {
        "fit_verdict": verdict,
        "areas": areas,
        "severity": 2 if verdict in {"small", "large"} else 1,
        "quote": text[:160],
    }


def aggregate_reviews(reviews: list[dict]) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)

    for review in reviews:
        grouped[review["product_id"]].append(review)

    output = []

    for product_id, product_reviews in grouped.items():
        verdict_counter = Counter()
        area_counter = Counter()
        classified_reviews = []

        for review in product_reviews:
            classification = classify_review(review["text"])
            verdict_counter[classification["fit_verdict"]] += 1
            area_counter.update(classification["areas"])

            classified_reviews.append(
                {
                    "product_id": product_id,
                    "text": review["text"],
                    "fit_verdict": classification["fit_verdict"],
                    "areas": classification["areas"],
                    "severity": classification["severity"],
                    "quote": classification["quote"],
                    "rating": review.get("rating"),
                    "size_bought": review.get("size_bought"),
                }
            )

        total = max(len(product_reviews), 1)

        output.append(
            {
                "product_id": product_id,
                "total_reviews": total,
                "pct_small": round(verdict_counter["small"] / total, 4),
                "pct_large": round(verdict_counter["large"] / total, 4),
                "pct_tts": round(verdict_counter["tts"] / total, 4),
                "top_issues_json": [
                    {"area": area, "count": count}
                    for area, count in area_counter.most_common(5)
                ],
                "classified_reviews": classified_reviews,
                "analysis_mode": get_env("REVIEW_ANALYSIS_MODE", "local"),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "notes": "Local deterministic placeholder. Replace classifier with AMD vLLM/Gemma when final model endpoint is available.",
            }
        )

    return output


def run_batch_analysis(input_path: Path, output_path: Path) -> None:
    raw_data = load_json(input_path)
    reviews = normalize_reviews(raw_data)

    if not reviews:
        raise RuntimeError("No valid reviews found. Expected product_id and text/review/content/comment.")

    analysis = aggregate_reviews(reviews)
    save_json(output_path, analysis)

    print("Review analysis complete.")
    print(f"Input reviews: {len(reviews)}")
    print(f"Products analyzed: {len(analysis)}")
    print(f"Output written to: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default=get_env("REVIEW_INPUT_PATH", "data/sample/reviews.sample.json"),
    )
    parser.add_argument(
        "--output",
        default=get_env("REVIEW_ANALYSIS_OUTPUT_PATH", "data/processed/review_analysis.example.json"),
    )
    args = parser.parse_args()

    run_batch_analysis(
        input_path=Path(args.input),
        output_path=Path(args.output),
    )
