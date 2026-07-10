import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DIMENSIONS = ["chest", "bust", "waist", "hips", "length", "sleeve", "inseam", "shoulder"]


def env(name: str, default: str = "") -> str:
    return os.getenv(name, default)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def extract_json(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)

        if not match:
            raise ValueError("No JSON object found in model response.")

        return json.loads(match.group(0))


def inch_to_cm(value: float) -> float:
    return round(value * 2.54, 1)


def normalize_number(value: Any) -> float | None:
    if value is None:
        return None

    try:
        return round(float(value), 1)
    except (TypeError, ValueError):
        return None


def detect_unit(text: str) -> str:
    lowered = text.lower()

    if "inch" in lowered or " inches" in lowered or '"' in lowered:
        return "inch"

    if "cm" in lowered:
        return "cm"

    return "unknown"


def local_parse_chart(item: dict) -> dict:
    """
    Small deterministic fallback parser.
    This is not meant to be perfect. It keeps the demo from breaking if AMD vLLM is unavailable.
    """
    raw_chart = item["raw_chart"]
    unit = detect_unit(raw_chart)

    size_pattern = re.compile(
        r"(?:Size\s*)?(XS|S|M|L|XL|XXL|\d{2})\s*[:\-]?\s*([^\.]+)",
        re.IGNORECASE,
    )

    sizes = []

    for match in size_pattern.finditer(raw_chart):
        label = match.group(1).upper()
        chunk = match.group(2)

        parsed_size = {"label": label}

        for dim in DIMENSIONS:
            dim_pattern = re.compile(rf"{dim}\s*(?:length)?\s*(\d+(?:\.\d+)?)", re.IGNORECASE)
            dim_match = dim_pattern.search(chunk)

            if dim_match:
                value = float(dim_match.group(1))
                parsed_size[dim] = inch_to_cm(value) if unit == "inch" else round(value, 1)
            else:
                parsed_size[dim] = None

        sizes.append(parsed_size)

    present_fields = {
        dim
        for size in sizes
        for dim in DIMENSIONS
        if size.get(dim) is not None
    }

    missing_fields = [dim for dim in DIMENSIONS if dim not in present_fields]

    warnings = []

    if unit == "inch":
        warnings.append("Converted inch measurements to cm.")

    if not sizes:
        warnings.append("Local parser could not confidently extract sizes.")

    return {
        "product_id": item["product_id"],
        "category": item.get("category"),
        "unit_detected": unit,
        "sizes": sizes,
        "missing_fields": missing_fields,
        "warnings": warnings,
        "parser_backend": "local",
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def amd_client() -> tuple[OpenAI, str]:
    base_url = env("AMD_LLM_URL", "http://localhost:8000/v1").rstrip("/")
    model = env("AMD_LLM_MODEL", "fitos-gemma")

    return (
        OpenAI(
            base_url=base_url,
            api_key=env("AMD_LLM_API_KEY", "not-needed"),
        ),
        model,
    )


def validate_chart_output(product_id: str, category: str | None, parsed: dict, backend: str) -> dict:
    sizes = parsed.get("sizes", [])

    if not isinstance(sizes, list):
        sizes = []

    normalized_sizes = []

    for size in sizes:
        if not isinstance(size, dict):
            continue

        label = size.get("label")

        if not label:
            continue

        normalized = {"label": str(label)}

        for dim in DIMENSIONS:
            normalized[dim] = normalize_number(size.get(dim))

        normalized_sizes.append(normalized)

    missing_fields = parsed.get("missing_fields", [])
    if not isinstance(missing_fields, list):
        missing_fields = []

    warnings = parsed.get("warnings", [])
    if not isinstance(warnings, list):
        warnings = []

    unit_detected = parsed.get("unit_detected", "unknown")
    if unit_detected not in {"cm", "inch", "mixed", "unknown"}:
        unit_detected = "unknown"

    return {
        "product_id": product_id,
        "category": category,
        "unit_detected": unit_detected,
        "sizes": normalized_sizes,
        "missing_fields": [str(field) for field in missing_fields],
        "warnings": [str(warning) for warning in warnings],
        "parser_backend": backend,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def amd_parse_chart(item: dict) -> dict:
    client, model = amd_client()

    prompt = f"""
You normalize messy clothing size charts for FitOS.

Convert all numeric measurements to centimeters.

Return ONLY valid JSON with this exact schema:
{{
  "unit_detected": "cm|inch|mixed|unknown",
  "sizes": [
    {{
      "label": "M",
      "chest": 104,
      "bust": null,
      "waist": 90,
      "hips": null,
      "length": 70,
      "sleeve": null,
      "inseam": null,
      "shoulder": 45
    }}
  ],
  "missing_fields": ["hips"],
  "warnings": ["Converted inches to cm"]
}}

Rules:
- Output JSON only. No markdown.
- Use null for missing measurements.
- Do not invent measurements.
- Convert inches to cm using 1 inch = 2.54 cm.
- Round centimeters to 1 decimal place.
- Keep size labels exactly as shown, such as S, M, L, XL, 30, 31, 32.
- missing_fields should list fields missing across the chart.
- Allowed measurement fields: chest, bust, waist, hips, length, sleeve, inseam, shoulder.

Product id: {item["product_id"]}
Category: {item.get("category")}

Raw chart:
{item["raw_chart"]}
"""

    last_error = None

    for attempt in range(2):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=float(env("LLM_TEMPERATURE", "0.2")),
                max_tokens=700,
            )

            content = response.choices[0].message.content or ""
            parsed = extract_json(content)

            return validate_chart_output(
                product_id=item["product_id"],
                category=item.get("category"),
                parsed=parsed,
                backend="amd-vllm",
            )
        except Exception as error:
            last_error = error

    print(f"[WARN] AMD chart parsing failed for {item['product_id']}. Falling back local. Error: {last_error}")
    return local_parse_chart(item)


def parse_charts(items: list[dict], mode: str) -> list[dict]:
    outputs = []

    for item in items:
        if mode == "amd-vllm":
            outputs.append(amd_parse_chart(item))
        else:
            outputs.append(local_parse_chart(item))

    return outputs


def run(input_path: Path, output_path: Path, mode: str) -> None:
    raw = load_json(input_path)
    items = raw if isinstance(raw, list) else raw.get("charts", [])

    valid_items = []

    for item in items:
        if item.get("product_id") and item.get("raw_chart"):
            valid_items.append(item)

    if not valid_items:
        raise RuntimeError("No valid chart items found. Expected product_id and raw_chart.")

    output = parse_charts(valid_items, mode)
    save_json(output_path, output)

    print("Size chart parsing complete.")
    print(f"Mode: {mode}")
    print(f"Charts parsed: {len(output)}")
    print(f"Output written to: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=env("SIZE_CHART_INPUT_PATH", "data/sample/raw_size_charts.sample.json"))
    parser.add_argument("--output", default=env("SIZE_CHART_OUTPUT_PATH", "data/processed/parsed_size_charts.example.json"))
    parser.add_argument("--mode", default=env("SIZE_CHART_PARSE_MODE", "local"), choices=["local", "amd-vllm"])

    args = parser.parse_args()

    run(
        input_path=Path(args.input),
        output_path=Path(args.output),
        mode=args.mode,
    )
