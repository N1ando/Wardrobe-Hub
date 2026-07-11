// Recommendation API — live backend with a mock fallback.
// Set VITE_USE_MOCKS=1 to force mocks (demo insurance if the API is down).
// Response contract: docs/recommendation_contract.md on main — note the
// breakdown fields are raw_ease/effective_ease/scoring_ease (+ ideal_band,
// weight) and the top level carries confidence_level and size_scores.
// The mocks below mirror real responses from the seeded backend.

const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === '1'
const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'

const MOCK_RESPONSES = {
  // Classic Oxford Shirt — clean M, sleeve column missing from the chart.
  1: {
    recommended_size: "M",
    confidence: 77,
    confidence_level: "medium",
    runner_up: { size: "L", score: 0.62 },
    size_scores: [
      { size: "S", base_score: 0.41, review_bonus: 0, adjusted_score: 0.41 },
      { size: "M", base_score: 1.0, review_bonus: 0, adjusted_score: 1.0 },
      { size: "L", base_score: 0.62, review_bonus: 0, adjusted_score: 0.62 },
      { size: "XL", base_score: 0.18, review_bonus: 0, adjusted_score: 0.18 },
    ],
    fit_breakdown: [
      { dim: "chest", garment: 106, body: 96, raw_ease: 10, effective_ease: 10, scoring_ease: 10, ideal_band: [8, 12], verdict: "ideal", score: 1.0, weight: 0.55 },
      { dim: "waist", garment: 96, body: 84, raw_ease: 12, effective_ease: 12, scoring_ease: 12, ideal_band: [8, 14], verdict: "ideal", score: 1.0, weight: 0.3 },
      { dim: "sleeve", garment: null, body: null, raw_ease: null, effective_ease: null, scoring_ease: null, ideal_band: [-2, 2], verdict: "missing_data", score: null, weight: 0.15 },
    ],
    review_signal: { pct_small: 0.0, pct_tts: 1.0, pct_large: 0.0, bias_direction: "none", applied_shift_bias: false, caveat: null },
    material_note: "Rigid fabric (no stretch); ease was scored as measured.",
    missing_fields: ["sleeve"],
    debug: { category: "tops", fit_pref: "regular", data_completeness: 0.667, review_agreement: 1.0, margin: 0.38 },
  },
  // Slim Tapered Jeans — decisive 32 (mirrors the live seeded response).
  2: {
    recommended_size: "32",
    confidence: 82,
    confidence_level: "high",
    runner_up: { size: "31", score: 0.887 },
    size_scores: [
      { size: "30", base_score: 0.397, review_bonus: 0, adjusted_score: 0.397 },
      { size: "31", base_score: 0.887, review_bonus: 0, adjusted_score: 0.887 },
      { size: "32", base_score: 1.0, review_bonus: 0, adjusted_score: 1.0 },
      { size: "33", base_score: 0.688, review_bonus: 0, adjusted_score: 0.688 },
      { size: "34", base_score: 0.2, review_bonus: 0, adjusted_score: 0.2 },
    ],
    fit_breakdown: [
      { dim: "waist", garment: 82, body: 79, raw_ease: 3, effective_ease: 3.41, scoring_ease: 3, ideal_band: [2, 4], verdict: "ideal", score: 1.0, weight: 0.45 },
      { dim: "hips", garment: 98, body: 92, raw_ease: 6, effective_ease: 6.49, scoring_ease: 6, ideal_band: [4, 8], verdict: "ideal", score: 1.0, weight: 0.35 },
      { dim: "inseam", garment: 86, body: 85, raw_ease: 1, effective_ease: 1.43, scoring_ease: 1, ideal_band: [-2, 2], verdict: "ideal", score: 1.0, weight: 0.2 },
    ],
    review_signal: { pct_small: 0.0, pct_tts: 1.0, pct_large: 0.0, bias_direction: "none", applied_shift_bias: false, caveat: null },
    material_note: "Material: Denim, 1% elastane. 1% stretch detected (stretch fabric); stretch was only used to reduce tightness penalties, not looseness.",
    missing_fields: [],
    debug: { category: "pants", fit_pref: "regular", data_completeness: 1.0, review_agreement: 1.0, margin: 0.113 },
  },
  // Floral Wrap Dress — runs-small cluster fires; hips missing from chart.
  3: {
    recommended_size: "L",
    confidence: 62,
    confidence_level: "medium",
    runner_up: { size: "M", score: 0.53 },
    size_scores: [
      { size: "XS", base_score: 0.05, review_bonus: 0, adjusted_score: 0.05 },
      { size: "S", base_score: 0.21, review_bonus: 0, adjusted_score: 0.21 },
      { size: "M", base_score: 0.53, review_bonus: 0, adjusted_score: 0.53 },
      { size: "L", base_score: 1.0, review_bonus: 0.08, adjusted_score: 1.0 },
    ],
    fit_breakdown: [
      { dim: "bust", garment: 96, body: 90, raw_ease: 6, effective_ease: 7.44, scoring_ease: 6, ideal_band: [6, 10], verdict: "ideal", score: 1.0, weight: 0.4 },
      { dim: "waist", garment: 78, body: 72, raw_ease: 6, effective_ease: 7.17, scoring_ease: 6, ideal_band: [5, 9], verdict: "ideal", score: 1.0, weight: 0.35 },
      { dim: "hips", garment: null, body: null, raw_ease: null, effective_ease: null, scoring_ease: null, ideal_band: [6, 10], verdict: "missing_data", score: null, weight: 0.25 },
    ],
    review_signal: { pct_small: 0.857, pct_tts: 0.143, pct_large: 0.0, bias_direction: "up", applied_shift_bias: false, caveat: "Reviewers say this runs small in the waist; consider sizing up." },
    material_note: "Material: Cotton, 3% elastane. 3% stretch detected (stretch fabric); stretch was only used to reduce tightness penalties, not looseness.",
    missing_fields: ["hips"],
    debug: { category: "dress", fit_pref: "regular", data_completeness: 0.667, review_agreement: 0.42, margin: 0.47 },
  },
}

export async function getRecommendation({ product_id, fit_pref, measurements }) {
  if (USE_MOCKS) {
    await new Promise((resolve) => setTimeout(resolve, 900))
    return MOCK_RESPONSES[product_id] || MOCK_RESPONSES[1]
  }
  const res = await fetch(`${API_BASE}/api/recommend`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ product_id, fit_pref, measurements }),
  })
  if (!res.ok) throw new Error(`recommend failed: HTTP ${res.status}`)
  return res.json()
}

// Gemma explanation for a recommendation. The {recommendation: ...} wrapper
// is required by the backend schema — posting the raw object 422s. The
// backend's fallback ladder guarantees text (template worst case), so any
// non-ok response here just means "render no sentence".
export async function postExplain(recommendation, productName) {
  if (USE_MOCKS) {
    await new Promise((resolve) => setTimeout(resolve, 400))
    return {
      explanation: `We recommend size ${recommendation.recommended_size} (fit score ${recommendation.confidence}/100).`,
      source: 'template',
    }
  }
  const res = await fetch(`${API_BASE}/api/explain`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ recommendation, product_name: productName }),
  })
  if (!res.ok) throw new Error(`explain failed: HTTP ${res.status}`)
  return res.json()
}

// ---------------------------------------------------------------------------
// Seller dashboard — live endpoints with a mock fallback; the mock JSONs are
// captured real API responses, so both modes share one shape. Backend
// contract: backend/app/schemas.py (SellerOverview, SellerProductRisk,
// ProductDetail).
// ---------------------------------------------------------------------------

import sellerOverview from './mocks/seller_overview.json'
import sellerRisk1 from './mocks/seller_risk_1.json'
import sellerRisk2 from './mocks/seller_risk_2.json'
import sellerRisk3 from './mocks/seller_risk_3.json'
import productDetails from './mocks/product_details.json'

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

// ---------------------------------------------------------------------------
// Cart — backend-backed with a localStorage mock fallback so the demo works
// without the API. Backend contract: Backend/app/routers/cart.py.
// ---------------------------------------------------------------------------

const MOCK_CART_KEY = 'fitos_mock_cart'

function readMockCart() {
  try {
    return JSON.parse(localStorage.getItem(MOCK_CART_KEY)) ?? []
  } catch {
    return []
  }
}

function writeMockCart(items) {
  localStorage.setItem(MOCK_CART_KEY, JSON.stringify(items))
  return { items, total: items.reduce((s, i) => s + i.price * i.quantity, 0) }
}

export async function getCart() {
  if (USE_MOCKS) {
    const items = readMockCart()
    return { items, total: items.reduce((s, i) => s + i.price * i.quantity, 0) }
  }
  return getJson('/api/cart')
}

export async function addToCart({ product_id, size, quantity, name, price }) {
  if (USE_MOCKS) {
    await new Promise((resolve) => setTimeout(resolve, 300))
    const items = readMockCart()
    const existing = items.find((i) => i.product_id === product_id && i.size === size)
    if (existing) existing.quantity += quantity
    else items.push({ id: Date.now(), product_id, size, quantity, name, price })
    return writeMockCart(items)
  }
  const res = await fetch(`${API_BASE}/api/cart/items`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ product_id, size, quantity }),
  })
  if (!res.ok) throw new Error(`add to cart failed: HTTP ${res.status}`)
  return res.json()
}

export async function removeCartItem(itemId) {
  if (USE_MOCKS) {
    return writeMockCart(readMockCart().filter((i) => i.id !== itemId))
  }
  const res = await fetch(`${API_BASE}/api/cart/items/${itemId}`, { method: 'DELETE' })
  if (!res.ok) throw new Error(`remove cart item failed: HTTP ${res.status}`)
  return res.json()
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
