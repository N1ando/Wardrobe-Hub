import { useState } from 'react'
import { getRecommendation, postExplain } from '../api'
import { saveFitProfile } from '../fitProfile'

export default function FitModal({ product, onClose, onViewReviews }) {
  const [measurements, setMeasurements] = useState({
    chest: '', waist: '', hips: '', height: '',
  })
  const [fitPref, setFitPref] = useState('regular')
  const [status, setStatus] = useState('idle')
  const [result, setResult] = useState(null)
  const [explanation, setExplanation] = useState(null)

  function handleChange(field, value) {
    setMeasurements((prev) => ({ ...prev, [field]: value }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setStatus('loading')
    setExplanation(null)
    try {
      const payload = {
        product_id: product.id,
        fit_pref: fitPref,
        measurements: {
          chest: Number(measurements.chest),
          waist: Number(measurements.waist),
          hips: Number(measurements.hips),
          height: Number(measurements.height),
        },
      }
      const data = await getRecommendation(payload)
      saveFitProfile({ measurements: payload.measurements, fitPref: payload.fit_pref })
      setResult(data)
      setStatus('done')
      // Gemma explanation is fire-and-forget: the recommendation never waits
      // on it, and a failed call simply renders no sentence.
      postExplain(data, product.name)
        .then((res) => setExplanation(res.explanation))
        .catch(() => {})
    } catch (err) {
      console.error(err)
      setStatus('error')
    }
  }

  return (
    <div className="fixed inset-0 bg-ink/50 flex items-center justify-center z-50 p-4">
      <div className="bg-surface rounded-xl max-w-md w-full p-6 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h2 className="font-display text-xl font-bold text-ink">Find My Size</h2>
          <button onClick={onClose} className="text-muted hover:text-ink text-2xl leading-none">&times;</button>
        </div>

        {status === 'idle' || status === 'loading' ? (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-3">
              <Field label="Chest/Bust (cm)" value={measurements.chest} onChange={(v) => handleChange('chest', v)} />
              <Field label="Waist (cm)" value={measurements.waist} onChange={(v) => handleChange('waist', v)} />
              <Field label="Hips (cm)" value={measurements.hips} onChange={(v) => handleChange('hips', v)} />
              <Field label="Height (cm)" value={measurements.height} onChange={(v) => handleChange('height', v)} />
            </div>
            <div>
              <label className="block text-sm font-medium text-ink mb-1">Fit Preference</label>
              <select
                value={fitPref}
                onChange={(e) => setFitPref(e.target.value)}
                className="w-full border border-ink/20 rounded-lg px-3 py-2"
              >
                <option value="slim">Slim</option>
                <option value="regular">Regular</option>
                <option value="relaxed">Relaxed</option>
              </select>
            </div>
            <button
              type="submit"
              disabled={status === 'loading'}
              className="w-full bg-ink text-white rounded-lg py-2.5 font-medium disabled:opacity-50"
            >
              {status === 'loading' ? 'Analyzing...' : 'Get My Size'}
            </button>
          </form>
        ) : status === 'done' ? (
          <ResultCard result={result} explanation={explanation} onReset={() => setStatus('idle')} onViewReviews={onViewReviews} onClose={onClose} />
        ) : (
          <div className="text-red-600">Something went wrong. Please try again.</div>
        )}
      </div>
    </div>
  )
}

function Field({ label, value, onChange }) {
  return (
    <div>
      <label className="block text-sm font-medium text-ink mb-1">{label}</label>
      <input
        type="number"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        required
        className="w-full border border-ink/20 rounded-lg px-3 py-2"
      />
    </div>
  )
}

function ResultCard({ result, explanation, onReset, onViewReviews, onClose }) {
  return (
    <div className="space-y-4">
      <div className="text-center">
        <ConfidenceRing confidence={result.confidence} />
        <div className="font-display text-3xl font-bold text-ink mt-2">{result.recommended_size}</div>
        <div className="text-muted text-sm">Recommended Size</div>
      </div>

      {explanation && (
        <p className="text-sm text-ink bg-accent/10 border border-accent/20 rounded-lg p-3">
          {explanation}
        </p>
      )}

      <div className="space-y-3">
        {result.fit_breakdown.map((dim) => (
          <FitBar key={dim.dim} dim={dim} />
        ))}
      </div>

      {result.review_signal?.caveat && (
        <button
          onClick={() => {
            onClose()
            onViewReviews?.(result.review_signal.caveat_review_ids || [])
          }}
          className="w-full text-left bg-caution/10 border border-caution/30 rounded-lg p-3 text-sm hover:bg-caution/15 transition-colors"
        >
          <span className="text-caution font-medium">⚠ {result.review_signal.caveat}</span>
          <span className="text-muted"> — {Math.round(result.review_signal.pct_small * 100)}% of reviewers. Tap to see reviews →</span>
        </button>
      )}

      {result.material_note && (
        <div className="text-sm text-muted">{result.material_note}</div>
      )}

      <button onClick={onReset} className="w-full border border-ink/20 rounded-lg py-2.5 font-medium text-ink">
        Try Again
      </button>
    </div>
  )
}

// Tight ↔ Loose visual bar per dimension
function FitBar({ dim }) {
  if (dim.verdict === 'missing_data') {
    return (
      <div>
        <div className="flex justify-between text-sm mb-1">
          <span className="capitalize text-ink">{dim.dim}</span>
          <span className="text-muted">No data</span>
        </div>
        <div className="h-2 bg-ink/10 rounded-full" />
      </div>
    )
  }

  // Map raw ease (cm) to a 0-100 position on a tight <-> loose scale.
  // Assume -6cm to +16cm is the visible range; clamp outside that.
  // (Live contract field is raw_ease — see docs/recommendation_contract.md.)
  const min = -6, max = 16
  const clamped = Math.max(min, Math.min(max, dim.raw_ease))
  const position = ((clamped - min) / (max - min)) * 100

  const verdictColor =
    dim.verdict === 'ideal' ? 'bg-accent' :
    dim.verdict === 'tight' ? 'bg-caution' : 'bg-ink/40'

  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className="capitalize text-ink">{dim.dim}</span>
        <span className="text-muted capitalize">{dim.verdict} · ease {dim.raw_ease}cm</span>
      </div>
      <div className="relative h-2 bg-ink/10 rounded-full">
        <div
          className={`absolute top-1/2 -translate-y-1/2 w-3 h-3 rounded-full ${verdictColor}`}
          style={{ left: `calc(${position}% - 6px)` }}
        />
      </div>
      <div className="flex justify-between text-[10px] text-muted/70 mt-0.5">
        <span>Tight</span>
        <span>Loose</span>
      </div>
    </div>
  )
}

function ConfidenceRing({ confidence }) {
  const radius = 40
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (confidence / 100) * circumference

  return (
    <div className="relative w-24 h-24 mx-auto">
      <svg className="w-24 h-24 -rotate-90">
        <circle cx="48" cy="48" r={radius} stroke="#E5E5E0" strokeWidth="6" fill="none" />
        <circle
          cx="48" cy="48" r={radius}
          stroke="#2F5233" strokeWidth="6" fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="transition-all duration-700 ease-out"
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center font-display font-bold text-lg text-ink">
        {confidence}%
      </div>
    </div>
  )
}