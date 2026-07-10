import { VIZ } from './vizTheme'

const SEGMENTS = [
  { key: 'pct_small', label: 'Runs small', color: VIZ.small },
  { key: 'pct_tts', label: 'True to size', color: VIZ.neutral },
  { key: 'pct_large', label: 'Runs large', color: VIZ.large },
]

// Fit distribution as a 100% stacked bar with diverging color: the two
// problem poles (small/large) are chromatic, true-to-size is a recessive
// neutral — "nothing wrong here" is not supposed to pop. Every value is
// also in the legend text, so no reading depends on hover or color.
export default function FitComplaintChart({ distribution, compact = false }) {
  const parts = SEGMENTS.map((s) => ({ ...s, value: distribution?.[s.key] ?? 0 }))
  const total = parts.reduce((sum, p) => sum + p.value, 0) || 1

  return (
    <div>
      <div
        className={`flex w-full overflow-hidden ${compact ? 'h-2.5 rounded' : 'h-6 rounded-md'}`}
        style={{ boxShadow: `inset 0 0 0 1px ${VIZ.ring}`, gap: '2px' }}
        role="img"
        aria-label={parts.map((p) => `${p.label} ${Math.round((p.value / total) * 100)}%`).join(', ')}
      >
        {parts.map(
          (p) =>
            p.value > 0 && (
              <div
                key={p.key}
                title={`${p.label}: ${Math.round((p.value / total) * 100)}%`}
                style={{ width: `${(p.value / total) * 100}%`, backgroundColor: p.color }}
              />
            ),
        )}
      </div>
      {!compact && (
        <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-600">
          {parts.map((p) => (
            <span key={p.key} className="inline-flex items-center gap-1.5">
              <span
                className="h-2.5 w-2.5 rounded-sm"
                style={{
                  backgroundColor: p.color,
                  boxShadow: p.key === 'pct_tts' ? `inset 0 0 0 1px ${VIZ.ring}` : 'none',
                }}
                aria-hidden="true"
              />
              {p.label}{' '}
              <span className="font-semibold text-gray-900">
                {Math.round((p.value / total) * 100)}%
              </span>
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
