const MOCK_RESPONSES = {
  1: {
    recommended_size: "M",
    confidence: 82,
    runner_up: { size: "L", score: 0.68 },
    fit_breakdown: [
      { dim: "chest", garment: 100, body: 96, ease: 4, verdict: "ideal", score: 1.0 },
      { dim: "waist", garment: 88, body: 84, ease: 4, verdict: "tight", score: 0.7 },
      { dim: "sleeve", garment: null, verdict: "missing_data" },
    ],
    review_signal: {
      pct_small: 0.22,
      pct_tts: 0.65,
      pct_large: 0.13,
      caveat: "true to size overall",
      applied_shift_bias: false,
      caveat_review_ids: [1],
    },
    material_note: "2% elastane — minimal stretch",
    missing_fields: ["sleeve"],
  },
  2: {
    recommended_size: "L",
    confidence: 87,
    runner_up: { size: "M", score: 0.71 },
    fit_breakdown: [
      { dim: "chest", garment: 106, body: 96, ease: 10, verdict: "ideal", score: 1.0 },
      { dim: "waist", garment: 92, body: 84, ease: 8, verdict: "ideal", score: 0.95 },
      { dim: "sleeve", garment: null, verdict: "missing_data" },
    ],
    review_signal: {
      pct_small: 0.30,
      pct_tts: 0.58,
      pct_large: 0.12,
      caveat: "runs small in the waist",
      applied_shift_bias: true,
      caveat_review_ids: [2],
    },
    material_note: "3% elastane — slight stretch accommodates chest",
    missing_fields: ["sleeve"],
  },
  3: {
    recommended_size: "S",
    confidence: 79,
    runner_up: { size: "M", score: 0.65 },
    fit_breakdown: [
      { dim: "bust", garment: 92, body: 96, ease: -4, verdict: "tight", score: 0.6 },
      { dim: "waist", garment: 80, body: 84, ease: -4, verdict: "tight", score: 0.55 },
      { dim: "hips", garment: 98, body: 100, ease: -2, verdict: "tight", score: 0.65 },
    ],
    review_signal: {
      pct_small: 0.45,
      pct_tts: 0.40,
      pct_large: 0.15,
      caveat: "runs small — consider sizing up",
      applied_shift_bias: true,
      caveat_review_ids: [2],
    },
    material_note: "5% elastane — some stretch, but runs snug",
    missing_fields: [],
  },
}

export async function getRecommendation({ product_id, fit_pref, measurements }) {
  await new Promise((resolve) => setTimeout(resolve, 900))
  return MOCK_RESPONSES[product_id] || MOCK_RESPONSES[1]
}

// ---------------------------------------------------------------------------
// Seller dashboard — live endpoints with a mock fallback.
// Set VITE_USE_MOCKS=1 to force mocks (demo insurance if the API is down);
// the mock JSONs are captured real API responses, so both modes share one
// shape. Backend contract: backend/app/schemas.py (SellerOverview,
// SellerProductRisk, ProductDetail).
// ---------------------------------------------------------------------------

import sellerOverview from './mocks/seller_overview.json'
import sellerRisk1 from './mocks/seller_risk_1.json'
import sellerRisk2 from './mocks/seller_risk_2.json'
import sellerRisk3 from './mocks/seller_risk_3.json'
import productDetails from './mocks/product_details.json'

const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === '1'
const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'

const RISK_MOCKS = { 1: sellerRisk1, 2: sellerRisk2, 3: sellerRisk3 }

async function getJson(path) {
  const res = await fetch(`${API_BASE}${path}`)
  if (!res.ok) throw new Error(`${path} failed: HTTP ${res.status}`)
  return res.json()
}

export async function getSellerOverview() {
  if (USE_MOCKS) {
    await new Promise((resolve) => setTimeout(resolve, 600))
    return sellerOverview
  }
  return getJson('/api/seller/overview')
}

export async function getProductRisk(productId) {
  if (USE_MOCKS) {
    await new Promise((resolve) => setTimeout(resolve, 600))
    const risk = RISK_MOCKS[productId]
    if (!risk) throw new Error(`No risk data for product ${productId}`)
    return risk
  }
  return getJson(`/api/seller/products/${productId}/risk`)
}

// Product detail (category + size chart) — the seller drilldown uses it to
// derive which chart fields exist vs. are required for the garment type.
export async function getProduct(productId) {
  if (USE_MOCKS) {
    await new Promise((resolve) => setTimeout(resolve, 300))
    const product = productDetails[productId]
    if (!product) throw new Error(`No product ${productId}`)
    return product
  }
  return getJson(`/api/products/${productId}`)
}