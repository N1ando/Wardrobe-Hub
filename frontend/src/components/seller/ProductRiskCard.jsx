import { Link } from 'react-router-dom'
import RiskBadge from './RiskBadge'
import FitComplaintChart from './FitComplaintChart'

export default function ProductRiskCard({ product }) {
  return (
    <Link
      to={`/seller/products/${product.id}`}
      className="block rounded-lg border bg-white p-4 transition hover:shadow-lg"
    >
      <div className="flex items-start gap-4">
        <img
          src={product.image_url}
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
          <p className="mt-0.5 truncate text-sm text-gray-600">{product.top_issue}</p>
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
