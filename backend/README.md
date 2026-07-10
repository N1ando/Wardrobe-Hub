# FitOS — Backend (Sizing Intelligence API)

FastAPI service behind FitOS: the sizing-intelligence layer for e-commerce
marketplaces. It turns messy seller size charts and mined fit reviews into
**explainable size recommendations** for buyers and **return-risk analytics**
for sellers.

The size recommendation is computed by a **deterministic, testable rules
engine** — the LLM never invents a size. Gemma is used only for the three
unstructured-language jobs: parsing messy size charts, mining fit signal from
reviews (batch, on AMD Developer Cloud vLLM/ROCm), and writing the shopper-facing
explanation (live, via Fireworks).

## Quick start (local, no LLM required)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python -m scripts.seed             # load 3 products + charts + reviews into SQLite
python -m scripts.ingest_analysis  # pre-mine reviews (keyword fallback if no LLM)

uvicorn app.main:app --reload      # http://127.0.0.1:8000/docs
```

With no API keys configured, review mining uses a deterministic keyword
classifier and explanations use a template, so the whole demo runs offline.

## Docker (from the repo root)

```bash
cp .env.example .env      # optional: add GEMMA_URL / FIREWORKS_API_KEY
docker compose up --build # API on :8000, seeded + pre-mined at build time
```

## API contract (frozen — plan Section 3)

| Method | Path | Purpose |
| ------ | ---- | ------- |
| GET  | `/health` | `{status, gemma_backend}` (which LLM path is active) |
| GET  | `/api/products` | list: id, name, price, image_url, category |
| GET  | `/api/products/{id}` | detail + normalized size chart + review fit summary |
| POST | `/api/recommend` | `{product_id, measurements{}, fit_pref}` → recommendation JSON |
| POST | `/api/explain` | `{recommendation}` → `{explanation, source}` (Gemma) |
| GET  | `/api/seller/overview` | per-product risk scores |
| GET  | `/api/seller/products/{id}/risk` | missing fields, complaint clusters, suggestions |
| POST | `/api/ai/parse-size-chart` | `{raw_text}` → normalized chart JSON (Gemma) |
| POST | `/api/ai/analyze-reviews` | `{product_id?}` → run/refresh review-mining batch |

### Example: `POST /api/recommend`

```json
{"product_id": 2, "fit_pref": "regular",
 "measurements": {"waist": 80, "hips": 96, "inseam": 84}}
```

returns `recommended_size`, `confidence` (35–96), `runner_up`, per-dimension
`fit_breakdown`, `review_signal` (with caveat + shift bias), `material_note`,
and `missing_fields`.

## Gemma / AMD / Fireworks — fallback ladder

`app/ai/gemma_client.py` tries, in order:

1. **AMD Developer Cloud vLLM** (`GEMMA_URL`, ROCm, OpenAI-compatible) — batch
   review mining + chart parsing.
2. **Fireworks Gemma API** (`FIREWORKS_API_KEY`) — low-latency live explanations.
3. **Cache** (`data/cache/*.json`, keyed by request hash).
4. **Template** (deterministic f-strings) — the demo never shows a dead spinner.

`GET /health` reports which backend is currently active.

## Recommendation engine

The engine is the **repo-root `core/` package** — shared with the persona CLI
and the root test suite, imported directly by the backend (single source of
truth; see `app/routers/recommend.py` for the thin adapter). The served
response is exactly `docs/recommendation_contract.md`.

- `app/core/fields.py` — the only backend-local piece: which DB chart columns
  each garment category needs (drives seller completeness checks). Note dress
  bust is stored in the `chest` column; the adapter maps it for the engine.

The adapter + demo personas are pinned by `tests/test_recommender.py`; engine
internals are covered by the root suite (`tests/` at the repo root).

## Tests

```bash
pytest -q
```

## Layout

```
app/
  main.py              FastAPI app + /health (uvicorn entrypoint)
  config.py            settings (DB, Gemma/AMD/Fireworks)
  db.py, models.py     SQLAlchemy engine + ORM (products, size_charts, reviews, ...)
  schemas.py           request/response contract
  core/                fields.py only — the engine itself is repo-root core/
  ai/                  gemma_client (fallback ladder), prompts, batch_analysis
  routers/             products, recommend, explain, seller, ai
data/seed/             products.json, size_charts.json, reviews.json
scripts/               seed.py, ingest_analysis.py
tests/                 persona suite + API contract tests
```

## Scope notes

- SQLite by design (no Postgres — zero ops value here).
- Deliberately imperfect seed charts (shirt missing sleeve, jeans in inches with
  vanity sizing, dress missing hips) — the imperfection drives the seller demo.
- Photo-based body measurement is explicitly out of scope (roadmap only).
