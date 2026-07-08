// Mock implementation of POST /api/recommend
// Matches the frozen contract in plan §4 exactly.
// TODO: replace the body of this function with a real fetch() once backend is live —
// nothing else in the app needs to change since the shape stays identical.

const MOCK_RESPONSE = {
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
    caveat: "runs small in shoulders",
    applied_shift_bias: true,
  },
  material_note: "3% elastane — slight stretch accommodates chest",
  missing_fields: ["sleeve"],
}

export async function getRecommendation({ product_id, fit_pref, measurements }) {
  // Simulate network delay so the loading state actually gets exercised
  await new Promise((resolve) => setTimeout(resolve, 900))

  // Later: replace everything above with —
  // const res = await fetch('http://localhost:8000/api/recommend', {
  //   method: 'POST',
  //   headers: { 'Content-Type': 'application/json' },
  //   body: JSON.stringify({ product_id, fit_pref, measurements }),
  // })
  // return res.json()

  return MOCK_RESPONSE
}