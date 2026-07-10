# FitOS — Wardrobe Hub

**The sizing intelligence layer for e-commerce marketplaces.** FitOS turns messy
seller size charts and hundreds of fit reviews into explainable size
recommendations for buyers — and return-risk analytics for the sellers who pay
for them.

![CI](https://github.com/N1ando/Wardrobe-Hub/actions/workflows/python-tests.yml/badge.svg)
Built for the **AMD Developer Hackathon ACT II (Unicorn Track)** · AMD Developer Cloud · ROCm · vLLM · Gemma · Fireworks

> **Live demo:** _URL here after deploy_ · **Demo video:** _link here_

---

## What it does

- **Explainable recommendations** — not "we recommend M" but *why*: per-dimension
  fit bars (tight ↔ loose), a confidence score that is never faked (35–96 by
  design), and a Gemma-written explanation of the strongest reason.
- **Review mining** — Gemma classifies real buyer reviews into fit signals
  ("runs small in the bust"), which bias the recommendation by at most one size
  and surface as caveats a shopper can act on.
- **Fit Passport** — measurements entered once follow the shopper to the next
  garment: same body, different product, different (correct) size.
- **Seller risk dashboard** — per-product return-risk scores, complaint
  clusters, missing size-chart fields, mined review quotes as proof, and
  concrete fixes. This is the B2B story: returns are a P&L line.

The final size decision is always made by a **deterministic, test-pinned rules
engine** — the LLM never invents a size. Gemma does the three jobs LLMs are
actually good at: parsing messy charts, mining review text, explaining
structured output.

## Quickstart

```bash
git clone https://github.com/N1ando/Wardrobe-Hub && cd Wardrobe-Hub
cp .env.example .env      # optional: add keys for live Gemma; runs fully offline without
docker compose up --build
```

- Storefront + dashboard: http://localhost:5173
- API + docs: http://localhost:8000/docs

The API image seeds its SQLite database and pre-mines the reviews at build
time, so the demo serves real data on the first request. With no API keys the
stack degrades gracefully to deterministic keyword mining and template
explanations — it never hangs on a dead endpoint.

<details>
<summary><b>Running the pieces individually (development)</b></summary>

**Backend** (FastAPI, Python 3.12+):

```bash
cd backend
pip install -r requirements.txt
python -m scripts.seed && python -m scripts.ingest_analysis
uvicorn app.main:app --reload      # http://localhost:8000/docs
python -m pytest -q                # API + persona suite
```

**Frontend** (React + Vite + Tailwind, Node 20+):

```bash
cd frontend
npm ci
npm run dev                        # http://localhost:5173, expects the API on :8000
```

`VITE_USE_MOCKS=1` forces mock mode (the mocks are captured real API
responses); `VITE_API_BASE` points the build at a remote API.

**Recommendation engine** (pure standard library):

```bash
pip install -r requirements-dev.txt
python -m pytest -q                          # engine suite
python -m core.recommender                   # smoke demo: 3 scenarios as JSON
python scripts/try_recommender.py --list     # poke the engine by hand
python scripts/try_recommender.py dress_001 --persona riley   # review-driven size flip
```

</details>

## Architecture

```
React + Vite + Tailwind SPA (:5173)
  /            product listing          /product/:id  page + Find-My-Size modal
  /seller      risk dashboard           /seller/products/:id  drilldown
        │ REST
FastAPI (:8000)
  /api/recommend ──► core/ deterministic engine (ease bands, stretch rules,
  /api/explain       review bias; single source of truth, 28-test suite)
  /api/seller/*  ──► risk scoring + mined review analytics
  /api/ai/*      ──► Gemma jobs, every call through the fallback ladder:
                       AMD vLLM ► Fireworks ► response cache ► template
  SQLite (seeded at image build)
        │ batch
AMD Developer Cloud GPU · ROCm · vLLM · google/gemma-2-2b-it
  review mining + size-chart parsing (evidence: docs/amd_proof/)
```

The response shape of `/api/recommend` is frozen in
[docs/recommendation_contract.md](docs/recommendation_contract.md) with
examples captured from the live API.

## How the engine decides

For each candidate size: ease = garment − body per dimension, scored against an
ideal ease band for the garment type and fit preference (slim/regular/relaxed).
Fabric stretch is credited at half its nominal percentage and **only ever
excuses tightness, never looseness**. If ≥25% of mined reviews say an item runs
small (and outnumber runs-large by ≥15 points), the next size up gets a bounded
bias — the shift is capped at one size. Confidence blends fit quality, winner
margin, data completeness, and reviewer agreement; incomplete charts force a
visible "low confidence" state that feeds the seller dashboard's
missing-fields story.

## AMD & Gemma Usage

FitOS uses AMD Developer Cloud, ROCm, vLLM, Fireworks, and Gemma for the AI
parts of the system. The engine stays deterministic; Gemma handles the three
language-heavy jobs (chart parsing, review mining, explanations).

### AMD Developer Cloud + ROCm + vLLM (batch pipeline)

```txt
AMD Developer Cloud GPU instance
  -> ROCm
  -> vLLM
  -> google/gemma-2-2b-it (served as "fitos-gemma", OpenAI-compatible endpoint)
```

**Measured throughput: 240 reviews mined in 40.0s (6.0 reviews/sec)** against
the AMD-hosted Gemma endpoint. Evidence in [`docs/amd_proof/`](docs/amd_proof/)
— `rocm-smi` captures for the vLLM serve, the review-mining run, and the
chart-parser run, vLLM server logs, and raw analysis outputs — with the
reproduction commands in [docs/amd_pipeline.md](docs/amd_pipeline.md). The
seller dashboard surfaces live mining stats and their provenance (the strip
only claims AMD when the analysis actually ran there).

### Fireworks (live path) + fallback ladder

Low-latency in-demo explanation calls use the Fireworks Gemma API. Every LLM
call goes through **AMD vLLM → Fireworks → response cache → deterministic
template**, so the demo cannot hang: with no keys configured at all, the stack
still answers with keyword-mined analysis and template explanations.

## Repository map

| Path | What it is |
|---|---|
| `core/` | Deterministic recommendation engine (pure stdlib, the single source of truth) |
| `backend/` | FastAPI app: products, recommend, explain, seller analytics, Gemma client |
| `frontend/` | React SPA: storefront, Find-My-Size modal, seller dashboard |
| `data/seed/`, `backend/data/seed/` | Demo catalog, personas, and 180 seeded reviews (test-pinned) |
| `docs/recommendation_contract.md` | Frozen API contract + live-captured examples |
| `docs/amd_pipeline.md` · `docs/amd_proof/` | AMD benchmark pipeline + captured evidence |
| `tools/amd_benchmark/` | Standalone harness that produced the AMD evidence |

## Tests

| Suite | Scope | Run |
|---|---|---|
| `tests/` (28) | Engine: ease bands, stretch rules, review bias, error contract, demo personas | `python -m pytest -q` |
| `backend/tests/` (36) | API contracts, persona regressions through the live adapter, seller analytics, batch import | `cd backend && python -m pytest -q` |
| CI | Both suites + Docker build/boot + frontend lint/build on every PR | `.github/workflows/python-tests.yml` |

## Roadmap

Cross-brand Fit Passport, marketplace API licensing, and photo-based
measurement capture (prototyped during the hackathon) — the deck has the
details.
