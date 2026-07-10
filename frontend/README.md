# FitOS Frontend

React + Vite + Tailwind SPA for the FitOS demo: Shopee-style product pages with
the **Find My Size** modal (deterministic recommendation + Gemma explanation +
fit bars), the **Fit Passport** (measurements persist across products), and the
**seller dashboard** (risk scores, complaint clusters, mined review quotes,
AMD analysis provenance strip).

## Run it

```bash
npm ci
npm run dev        # http://localhost:5173 — expects the API on :8000
npm run build      # production build to dist/
npm run lint
```

Backend for the live data: `docker compose up` from the repo root, or see
`backend/README.md`.

## Environment

- `VITE_API_BASE` — API origin (default `http://localhost:8000`). Baked in at
  build time; for a remote demo build with the public origin.
- `VITE_USE_MOCKS=1` — force mock mode (demo insurance). The mocks in
  `src/mocks/` are captured real API responses, so mock and live modes share
  one shape.

## Where things live

```
src/api.js               # all API calls (recommend, explain, seller, products)
src/components/FitModal.jsx        # measurements -> recommendation result card
src/components/seller/             # dashboard cards, charts, provenance strip
src/pages/                # ProductList, ProductDetail, SellerOverview, SellerProductDetail
src/data/mockProducts.js  # buyer-page product data (aligned with backend seed)
```

Response contract for recommendations: `docs/recommendation_contract.md` at the
repo root — the breakdown fields are `raw_ease`/`effective_ease`/`scoring_ease`
plus `ideal_band`/`weight`, and the top level carries `confidence_level` and
`size_scores`.
