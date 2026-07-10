import argparse
import hashlib
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def get_env(name: str, default: str | None = None, required: bool = False) -> str:
    value = os.getenv(name, default)

    if required and not value:
        raise RuntimeError(f"Missing required environment variable: {name}")

    return value or ""


def get_cache_dir() -> Path:
    cache_dir = Path(get_env("CACHE_DIR", required=True))
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def get_fireworks_client() -> OpenAI:
    api_key = get_env("FIREWORKS_API_KEY", required=True)
    base_url = get_env("FIREWORKS_BASE_URL", required=True)

    return OpenAI(
        base_url=base_url,
        api_key=api_key,
    )


def get_model_id() -> str:
    return get_env("FIREWORKS_MODEL", required=True)


def get_timeout_seconds() -> int:
    raw_value = get_env("LLM_TIMEOUT_SECONDS", required=True)

    try:
        return int(raw_value)
    except ValueError:
        raise RuntimeError("LLM_TIMEOUT_SECONDS must be a valid integer")


def get_temperature() -> float:
    raw_value = get_env("LLM_TEMPERATURE", required=True)

    try:
        return float(raw_value)
    except ValueError:
        raise RuntimeError("LLM_TEMPERATURE must be a valid number")


def list_available_models(filter_text: str | None = None) -> list[str]:
    client = get_fireworks_client()
    models = client.models.list()

    model_ids = []

    for model in models.data:
        model_id = getattr(model, "id", "")

        if not filter_text or filter_text.lower() in model_id.lower():
            model_ids.append(model_id)

    return model_ids


def hello_llm() -> None:
    client = get_fireworks_client()
    model = get_model_id()
    hello_message = get_env("LLM_HELLO_MESSAGE", required=True)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": f"Reply with this exact sentence only: {hello_message}",
            }
        ],
        temperature=0.0,
        max_tokens=60,
        timeout=get_timeout_seconds(),
    )

    content = response.choices[0].message.content

    if not content:
        raise RuntimeError("Model returned empty content")

    print("\nFireworks LLM OK:")
    print(content.strip())


def payload_hash(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def template_explanation(recommendation: dict) -> str:
    size = recommendation.get("recommended_size", "the recommended size")
    confidence = recommendation.get("confidence", "medium")
    caveat = recommendation.get("review_signal", {}).get("caveat")

    explanation = (
        f"We recommend size {size} with {confidence}% confidence based on your "
        f"measurements, fit preference, and the garment size chart."
    )

    if caveat:
        explanation += (
            f" Review signals show this item {caveat}, "
            f"so the recommendation accounts for that fit risk."
        )

    return explanation


def build_explanation_prompt(recommendation: dict) -> str:
    return f"""
You are FitOS, a shopper-facing clothing size assistant.

Write the final customer explanation only.

Hard output rules:
- Exactly 2 sentences.
- No headings.
- No bullet points.
- No analysis.
- No step-by-step reasoning.
- Do not mention JSON.
- Do not repeat the instructions.
- Do not say "rules", "input", "output", "analyze", or "strongest reason".
- State the recommended size.
- Mention confidence.
- Mention the main fit reason.
- Mention the review caveat if present.
- Never invent measurements.
- Never contradict the fit result.

Fit result:
{json.dumps(recommendation, indent=2)}
""".strip()


def is_bad_explanation(explanation: str) -> bool:
    bad_phrases = [
        "analyze the request",
        "analyze the json",
        "we need to write",
        "rules:",
        "input:",
        "output:",
        "strongest reason:",
        "json:",
        "fit result:",
        "step",
    ]

    lowered = explanation.lower()
    return any(phrase in lowered for phrase in bad_phrases)


def explain_recommendation(recommendation: dict) -> str:
    model = get_model_id()
    prompt_version = get_env("LLM_PROMPT_VERSION", required=True)

    cache_payload = {
        "model": model,
        "prompt_version": prompt_version,
        "recommendation": recommendation,
    }

    cache_key = payload_hash(cache_payload)
    cache_path = get_cache_dir() / f"{cache_key}.json"

    if get_env("USE_CACHE", required=True).lower() == "true" and cache_path.exists():
        cached = json.loads(cache_path.read_text(encoding="utf-8"))
        return cached["explanation"]

    try:
        client = get_fireworks_client()
        prompt = build_explanation_prompt(recommendation)

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=get_temperature(),
            max_tokens=180,
            timeout=get_timeout_seconds(),
        )

        content = response.choices[0].message.content

        if not content:
            raise RuntimeError("Model returned empty content")

        explanation = content.strip()

        if is_bad_explanation(explanation):
            raise RuntimeError("Model returned non-shopper-facing explanation")

        cache_path.write_text(
            json.dumps({"explanation": explanation}, indent=2),
            encoding="utf-8",
        )

        return explanation

    except Exception as error:
        print(f"[WARN] Fireworks explanation failed: {error}")
        return template_explanation(recommendation)


def test_explanation() -> None:
    sample = {
        "recommended_size": "L",
        "confidence": 87,
        "runner_up": {"size": "M", "score": 0.71},
        "fit_breakdown": [
            {
                "dim": "chest",
                "garment": 106,
                "body": 96,
                "ease": 10,
                "verdict": "ideal",
                "score": 1.0,
            },
            {
                "dim": "waist",
                "garment": 92,
                "body": 84,
                "ease": 8,
                "verdict": "ideal",
                "score": 0.95,
            },
        ],
        "review_signal": {
            "pct_small": 0.30,
            "pct_tts": 0.58,
            "pct_large": 0.12,
            "caveat": "runs small in shoulders",
            "applied_shift_bias": True,
        },
        "material_note": "3% elastane - slight stretch accommodates chest",
        "missing_fields": ["sleeve"],
    }

    explanation = explain_recommendation(sample)

    print("\nExplanation OK:")
    print(explanation)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--list-models", action="store_true")
    parser.add_argument("--filter", default=None)
    parser.add_argument("--explain-test", action="store_true")
    args = parser.parse_args()

    if args.list_models:
        models = list_available_models(args.filter)

        print("\nAvailable models:")
        for model in models:
            print(model)

    elif args.explain_test:
        test_explanation()

    else:
        hello_llm()