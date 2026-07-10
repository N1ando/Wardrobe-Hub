import { Link } from 'react-router-dom'
import RiskBadge from './RiskBadge'
import FitComplaintChart from './FitComplaintChart'
import { fieldLabel } from './chartFields'

// Seed image_url values point at /img/* assets that don't exist yet;
// fall back to a category placeholder so cards never show broken images.
function imageSrc(product) {
  const url = product.image_url || ''
  return url.startsWith('http')
    ? url
    : `https://placehold.co/160x200?text=${encodeURIComponent(product.category ?? 'item')}`
}

function issueLine(product) {
  if (product.missing_fields?.length) {
    const fields = product.missing_fields
      .map((f) => fieldLabel(product.category, f))
      .join(', ')
    return `Size chart missing: ${fields}`
  }
  if (product.fit_complaint_pct > 0) {
    return `${Math.round(product.fit_complaint_pct * 100)}% of reviews report fit complaints`
  }
  return 'No fit complaints in mined reviews'
}

export default function ProductRiskCard({ product }) {
  return (
    <Link
      to={`/seller/products/${product.product_id}`}
      className="block rounded-lg border bg-white p-4 transition hover:shadow-lg"
    >
      <div className="flex items-start gap-4">
        <img
          src={imageSrc(product)}
          alt={product.name}
          className="h-20 w-16 rounded object-cover"
        />
        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-2">
            <h2 className="truncate font-semibold">{product.name}</h2>
            <RiskBadge level={product.risk_level} />
          </div>
          <p className="mt-1 text-sm text-gray-600">
            {product.complaint_count} fit complaints in {product.review_count} reviews
          </p>
          <p className="mt-0.5 truncate text-sm text-gray-600">{issueLine(product)}</p>
        </div>
      </div>

      <div className="mt-4">
        <FitComplaintChart distribution={product.fit_distribution} compact />
      </div>

      <div className="mt-3 flex items-center justify-between text-sm">
        <span className="text-gray-600">
          Chart completeness{' '}
          <span
            className={`font-semibold ${product.chart_completeness < 1 ? 'text-gray-900' : 'text-gray-600'}`}
          >
            {Math.round(product.chart_completeness * 100)}%
          </span>
        </span>
        <span className="font-medium text-blue-700">View details &rarr;</span>
      </div>
    </Link>
  )
}
