import { VIZ } from './vizTheme'

const VERDICT_META = {
  small: { label: 'runs small', color: VIZ.small },
  large: { label: 'runs large', color: VIZ.large },
  tts: { label: 'true to size', color: VIZ.muted },
}

// Mined review quotes with their classified verdicts — the proof that the
// dashboard percentages come from real review text, not invented numbers.
export default function ReviewQuoteList({ quotes }) {
  return (
    <ul className="space-y-3">
      {(quotes ?? []).map((quote, index) => {
        const meta = VERDICT_META[quote.verdict] ?? VERDICT_META.tts
        return (
          <li key={index} className="rounded-md border-l-2 bg-gray-50 p-3" style={{ borderLeftColor: meta.color }}>
            <p className="text-sm italic text-gray-800">&ldquo;{quote.text}&rdquo;</p>
            <p className="mt-1.5 text-xs text-gray-600">
              <span className="font-semibold" style={{ color: meta.color === VIZ.muted ? VIZ.inkSecondary : meta.color }}>
                {meta.label}
              </span>
              {quote.size_bought && <> &middot; bought size {quote.size_bought}</>}
            </p>
          </li>
        )
      })}
    </ul>
  )
}
