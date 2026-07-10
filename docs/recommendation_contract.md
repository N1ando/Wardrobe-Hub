# Recommendation response contract

**This document + [recommend_response.example.json](recommend_response.example.json) are the frozen contract** for the recommendation payload. Frontend (P2/P3) builds against this, backend (P4) returns it verbatim from `POST /api/recommend`. If the shape must change, change it here first and tell everyone.

> **Live since the engine-unification PR:** `POST /api/recommend` serves exactly this
> shape. Request body: `{"product_id": <int>, "fit_pref": "slim|regular|relaxed",
> "measurements": {"chest|bust|waist|hips|inseam|sleeve|height": <cm>}}`.
> Unknown product → 404; invalid product data → 422. The backend imports the
> repo-root `core` package directly — there is exactly one engine.

## Producing a recommendation

```python
from core import recommend_size

result = recommend_size(
    product,            # dict: needs category, size_chart; optional stretch_pct, material, id
    body_measurements,  # dict: cm values; numeric strings ("83") accepted
    fit_pref,           # "slim" | "regular" | "relaxed"; anything else -> "regular"
    review_analysis,    # optional dict: pct_small/pct_tts/pct_large (+ optional caveat)
)
```

The result is a plain dict, fully JSON-serializable — FastAPI can return it as-is.

> **Backend warning:** `review_analysis` must be passed explicitly as the 4th argument. `recommend_size` does **not** read `product["review_analysis"]` — the seed products carry that key for convenience, but if you forget to extract and pass it, the review signal silently disappears (`review_signal` comes back null and no bias is applied).

**Error contract:** `ValueError` is the ONLY exception raised for bad input (non-dict product/body, unsupported category, missing/empty/malformed `size_chart`). Backend maps it to one HTTP 422 handler. A malformed `review_analysis` never raises — it degrades to "no review data".

## Response fields

| Field | Type | Notes |
|---|---|---|
| `recommended_size` | string | Label from the size chart. Ties prefer the smaller size. |
| `confidence` | int | Always 35–96. Never 0 or 100 by design. |
| `confidence_level` | string | `"low"` / `"medium"` / `"high"`. Forced `"low"` when less than half the required chart fields exist — render this state prominently. |
| `runner_up` | object \| null | `{size, score}`. Null when the chart has a single size. |
| `size_scores` | array | One entry per chart size: `{size, base_score, review_bonus, adjusted_score}` (0–1, 3 decimals). Powers the score-bar visual. |
| `fit_breakdown` | array | Per dimension of the **recommended** size — see below. Powers the tight↔loose bars. |
| `review_signal` | object \| null | Null when no review data was passed. `{pct_small, pct_large, pct_tts, bias_direction, applied_shift_bias, caveat}`. `caveat` is a display-ready sentence but is **null unless the bias thresholds fire** (≥25% one-sided and ≥15-point gap). |
| `material_note` | string | Display-ready sentence about stretch handling. |
| `missing_fields` | array of strings | Required dimensions absent from the chart row or the body input. Non-empty = the seller-dashboard hook. |
| `debug` | object | `{category, fit_pref, data_completeness, review_agreement, margin}`. For logs/tuning — don't render it and don't feed it to the explanation LLM. |

### `fit_breakdown` entries

```json
{"dim": "waist", "garment": 83.0, "body": 81.0,
 "raw_ease": 2.0, "effective_ease": 3.25, "scoring_ease": 2.0,
 "ideal_band": [2.0, 4.0], "verdict": "ideal", "score": 1.0, "weight": 0.45}
```

- `verdict`: `"ideal"` | `"tight"` | `"loose"` | `"missing_data"` (verdict reflects *raw* fit even when stretch softened the penalty).
- `raw_ease` = garment − body. `effective_ease` adds the stretch credit. `scoring_ease` is what was actually scored (stretch only ever excuses tightness, never looseness).
- When `verdict` is `"missing_data"`, the ease and score fields (`raw_ease`, `effective_ease`, `scoring_ease`, `score`) are null; `garment`/`body` are null only when that side is missing (e.g. a chart row without `sleeve` still reports the shopper's `body` value).
- Dimensions per category — pants: waist/hips/inseam · tops: chest/waist/sleeve · dress: bust/waist/hips (body `chest` and `bust` are interchangeable fallbacks).

## For the explanation generator (`/api/explain`)

Feed Gemma: `recommended_size`, `confidence`, `fit_breakdown`, `review_signal`, `material_note`, `missing_fields`. The strongest-reason heuristic: the highest-weight dimension whose verdict isn't `"ideal"`, else the highest-weight ideal one. Never let the explanation claim height/weight were used — the engine ignores them.
