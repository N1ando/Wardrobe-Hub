import { fieldLabel } from './chartFields'

// Size-chart completeness: every required dimension for the garment type,
// present or missing, with the business impact of each gap spelled out.
// This mirrors the buyer modal's "missing data" warning — same flaw, both
// sides of the marketplace.
export default function MissingFieldsChecklist({ requiredFields, missingFields, fieldImpact, category }) {
  const missing = new Set(missingFields ?? [])
  return (
    <ul className="space-y-2">
      {(requiredFields ?? []).map((field) => {
        const isMissing = missing.has(field)
        return (
          <li key={field} className="flex items-start gap-2.5 text-sm">
            <span
              className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-xs font-bold ${
                isMissing ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'
              }`}
              aria-hidden="true"
            >
              {isMissing ? '!' : '✓'}
            </span>
            <span>
              <span className="font-medium capitalize text-gray-900">{fieldLabel(category, field)}</span>{' '}
              <span className="text-gray-600">{isMissing ? 'missing from chart' : 'provided'}</span>
              {isMissing && fieldImpact?.[field] && (
                <span className="mt-0.5 block text-gray-600">{fieldImpact[field]}</span>
              )}
            </span>
          </li>
        )
      })}
    </ul>
  )
}
