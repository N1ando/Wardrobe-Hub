import { useState } from 'react'
import { getRecommendation } from '../api'

export default function FitModal({ product, onClose }) {
  const [measurements, setMeasurements] = useState({
    chest: '',
    waist: '',
    hips: '',
    height: '',
  })
  const [fitPref, setFitPref] = useState('regular')
  const [status, setStatus] = useState('idle') // idle | loading | done | error
  const [result, setResult] = useState(null)

  function handleChange(field, value) {
    setMeasurements((prev) => ({ ...prev, [field]: value }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setStatus('loading')
    try {
      const data = await getRecommendation({
        product_id: product.id,
        fit_pref: fitPref,
        measurements: {
          chest: Number(measurements.chest),
          waist: Number(measurements.waist),
          hips: Number(measurements.hips),
          height: Number(measurements.height),
        },
      })
      setResult(data)
      setStatus('done')
    } catch (err) {
      console.error(err)
      setStatus('error')
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-md w-full p-6 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">Find My Size</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-700 text-2xl leading-none">
            &times;
          </button>
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
              <label className="block text-sm font-medium mb-1">Fit Preference</label>
              <select
                value={fitPref}
                onChange={(e) => setFitPref(e.target.value)}
                className="w-full border rounded px-3 py-2"
              >
                <option value="slim">Slim</option>
                <option value="regular">Regular</option>
                <option value="relaxed">Relaxed</option>
              </select>
            </div>

            <button
              type="submit"
              disabled={status === 'loading'}
              className="w-full bg-black text-white rounded py-2 font-semibold disabled:opacity-50"
            >
              {status === 'loading' ? 'Analyzing...' : 'Get My Size'}
            </button>
          </form>
        ) : status === 'done' ? (
          <ResultCard result={result} onReset={() => setStatus('idle')} />
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
      <label className="block text-sm font-medium mb-1">{label}</label>
      <input
        type="number"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        required
        className="w-full border rounded px-3 py-2"
      />
    </div>
  )
}

function ResultCard({ result, onReset }) {
  return (
    <div className="space-y-4">
      <div className="text-center">
        <div className="text-4xl font-bold">{result.recommended_size}</div>
        <div className="text-gray-500">{result.confidence}% confidence</div>
      </div>

      <div className="space-y-2">
        {result.fit_breakdown.map((dim) => (
          <div key={dim.dim} className="flex justify-between text-sm border-b pb-1">
            <span className="capitalize">{dim.dim}</span>
            <span className="text-gray-600">
              {dim.verdict === 'missing_data' ? 'No data' : `${dim.verdict} (ease ${dim.ease}cm)`}
            </span>
          </div>
        ))}
      </div>

      {result.review_signal?.caveat && (
        <div className="bg-yellow-50 border border-yellow-200 rounded p-3 text-sm">
          ⚠️ {result.review_signal.caveat} ({Math.round(result.review_signal.pct_small * 100)}% of reviewers)
        </div>
      )}

      {result.material_note && (
        <div className="text-sm text-gray-500">{result.material_note}</div>
      )}

      <button onClick={onReset} className="w-full border rounded py-2 font-semibold">
        Try Again
      </button>
    </div>
  )
}