import { getSellerOverview } from '../api'
import { useApi } from '../hooks/useApi'
import ProductRiskCard from '../components/seller/ProductRiskCard'
import AmdStatsFooter from '../components/seller/AmdStatsFooter'
import SellerShell, { ErrorBox, Skeleton } from '../components/seller/SellerShell'

export default function SellerOverview() {
  const { data, loading, error, reload } = useApi(getSellerOverview, [])

  return (
    <SellerShell title="Seller dashboard" backTo="/" backLabel="Store view">
      <p className="mb-6 text-base text-muted">
        Size-fit risk across your catalog, mined from buyer reviews and your size charts.
      </p>

      {loading && (
        <div className="flex flex-col gap-4">
          <Skeleton className="h-28" />
          <Skeleton className="h-28" />
          <Skeleton className="h-28" />
        </div>
      )}

      {error && <ErrorBox message={error.message} onRetry={reload} />}

      {data && (
        <>
          <div className="mb-7 flex flex-wrap gap-3">
            <StatChip label="Products" value={data.products.length} />
            <StatChip
              label="High risk"
              value={data.products.filter((p) => p.risk_level === 'high').length}
              tone="danger"
            />
            <StatChip
              label="Avg. chart completeness"
              value={`${Math.round(
                (data.products.reduce((sum, p) => sum + p.chart_completeness, 0) /
                  data.products.length) *
                  100
              )}%`}
            />
          </div>

          <div className="flex flex-col gap-4">
            {[...data.products]
              .sort((a, b) => b.risk_score - a.risk_score)
              .map((product) => (
                <ProductRiskCard key={product.product_id} product={product} />
              ))}
          </div>

          <div className="mt-6">
            <AmdStatsFooter note={data.throughput_note} />
          </div>
        </>
      )}
    </SellerShell>
  )
}

function StatChip({ label, value, tone = 'default' }) {
  const toneClass =
    tone === 'danger'
      ? 'border-red-200 bg-red-50 text-red-700'
      : 'border-ink/10 bg-surface text-ink'
  return (
    <div className={`flex items-center gap-2.5 rounded-xl border px-5 py-3 ${toneClass}`}>
      <span className="font-serif-strong text-3xl font-bold tracking-tight">{value}</span>
      <span className="text-sm text-muted">{label}</span>
    </div>
  )
}