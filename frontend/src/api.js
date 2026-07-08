const MOCK_RESPONSES = {
  1: {
    // Shirt
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
    },
    material_note: "2% elastane — minimal stretch",
    missing_fields: ["sleeve"],
  },
  2: {
    // Jeans
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
  },
  3: {
    // Dress
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
    },
    material_note: "5% elastane — some stretch, but runs snug",
    missing_fields: [],
  },
}

export async function getRecommendation({ product_id, fit_pref, measurements }) {
  await new Promise((resolve) => setTimeout(resolve, 900))
  return MOCK_RESPONSES[product_id] || MOCK_RESPONSES[1]
}