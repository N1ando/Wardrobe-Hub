# FitOS — Wardrobe Hub

**The sizing intelligence layer for e-commerce marketplaces**: turns messy size charts and fit reviews into explainable size recommendations for buyers and return-risk analytics for sellers.

> Built for the AMD Developer Hackathon ACT II (Unicorn Track). AMD Developer Cloud + Gemma integration sections land with the backend — placeholders below.

## What's here now

The **deterministic recommendation engine** (`core/`) plus seeded demo data. Pure standard library — no framework dependencies. The LLM never invents a size: Gemma is used only for parsing charts, mining reviews, and explaining the engine's structured output.

```
core/recommender.py    # scoring engine: ease bands, stretch rules, review bias
core/confidence.py     # confidence blend (fit 45% / margin 20% / data 20% / reviews 15%)
data/seed/             # 3 demo products + 3 rehearsed personas (load-bearing: pinned by tests)
scripts/try_recommender.py         # poke the engine by hand
docs/recommendation_contract.md    # FROZEN response contract for frontend/backend
tests/                 # pytest suite + manual verification harness
```

## Quickstart

```bash
python -m venv venv
venv\Scripts\activate            # Windows   (source venv/bin/activate on Unix)
pip install -r requirements-dev.txt
python -m pytest -q              # full suite
python -m core.recommender       # smoke demo: prints 3 scenarios as JSON
```

## Try it

```bash
python scripts/try_recommender.py --list                                    # products + personas
python scripts/try_recommender.py jeans_001 --waist 81 --hips 94 --inseam 79
python scripts/try_recommender.py dress_001 --persona riley                 # review-driven M->L flip
python scripts/try_recommender.py dress_001 --persona riley --no-reviews    # ...vs. without reviews
python scripts/try_recommender.py shirt_001 --persona sam --fit regular     # fit-pref changes the size
```

Longer manual walkthrough: `python tests/manual_verify_recommender.py`

## Engine rules in one paragraph

For each size, ease = garment − body per dimension, scored against an ideal ease band for the garment type and fit preference (slim/regular/relaxed). Fabric stretch is credited at half its nominal percentage and **only ever excuses tightness, never looseness**. If ≥25% of reviews say an item runs small (and outnumber runs-large by ≥15 points), the next size up gets a +0.08 bias — the shift is capped at one size. Confidence blends fit quality, winner margin, data completeness, and reviewer agreement, clamped to 35–96; charts missing half their fields force a "low" label. Bad input raises `ValueError` only — see [docs/recommendation_contract.md](docs/recommendation_contract.md).

## Roadmap (hackathon week)

- [x] Deterministic recommendation engine + tests + seed data
- [ ] FastAPI backend (`/api/recommend`, `/api/explain`, seller endpoints)
- [ ] Gemma explanation generation (Fireworks) + review mining batch (vLLM on AMD Developer Cloud, ROCm)
- [ ] React frontend: product page, fit modal, seller dashboard
- [ ] docker-compose deployment on AMD Developer Cloud

<!-- AMD & Gemma usage section goes here once the backend lands: vLLM/ROCm batch pipeline, throughput stats, rocm-smi evidence, Fireworks live path. -->
