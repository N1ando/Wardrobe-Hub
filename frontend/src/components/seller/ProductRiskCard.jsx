import { Link } from 'react-router-dom'
import RiskBadge from './RiskBadge'
import FitComplaintChart from './FitComplaintChart'
import { fieldLabel } from './chartFields'
import { RISK } from './vizTheme'

function issueLine(product) {
  if (product.missing_fields?.length) {
    const fields = product.missing_fields
      .map((f) => fieldLabel(product.category, f))
      .join(', ')
    return `Size chart missing: ${fields}`
  }
  if (product.complaint_count > 0 && product.review_count > 0) {
    // Derived from the counts shown on the card so the two never disagree
    // (fit_complaint_pct uses graded reviews as denominator, not the total).
    const pct = Math.round((product.complaint_count / product.review_count) * 100)
    return `${pct}% of reviews report fit complaints`
  }
  return 'No fit complaints in mined reviews'
}

export default function ProductRiskCard({ product }) {
  const risk = RISK[product.risk_level] ?? RISK.medium

  return (
    <Link
      to={`/seller/products/${product.product_id}`}
      className="group relative flex flex-col gap-4 overflow-hidden rounded-xl border border-ink/10 bg-surface p-4 pl-6 shadow-[var(--shadow-soft)] transition-all duration-200 hover:shadow-[var(--shadow-lifted)] md:flex-row md:items-center"
    >
      {/* Risk-colored accent edge */}
      <span
        className="absolute left-0 top-0 bottom-0 w-1.5"
        style={{ backgroundColor: risk.color }}
        aria-hidden="true"
      />

      {/* Main info */}
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <h2 className="font-serif-strong truncate text-2xl font-bold tracking-tight text-ink">{product.name}</h2>
          <RiskBadge level={product.risk_level} />
        </div>
        <p className="mt-1 text-sm text-muted">
          {product.complaint_count} fit complaints in {product.review_count} reviews
        </p>
        <p className="mt-0.5 truncate text-sm text-muted">{issueLine(product)}</p>
      </div>

      {/* Chart */}
      <div className="w-full md:w-40 md:shrink-0">
        <FitComplaintChart distribution={product.fit_distribution} compact />
      </div>

      {/* Completeness + CTA */}
      <div className="flex shrink-0 items-center justify-between gap-4 md:w-44 md:flex-col md:items-end md:justify-center md:gap-1">
        <span className="text-sm text-muted">
          Chart{' '}
          <span className="font-semibold text-ink">
            {Math.round(product.chart_completeness * 100)}%
          </span>
        </span>
        <span className="flex items-center gap-1 text-sm font-medium text-accent">
          View details
          <span className="transition-transform duration-200 group-hover:translate-x-1">&rarr;</span>
        </span>
      </div>
    </Link>
  )
}
