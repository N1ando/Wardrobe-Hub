import { getSellerOverview } from '../api'
import { useApi } from '../hooks/useApi'
import ProductRiskCard from '../components/seller/ProductRiskCard'
import AmdStatsFooter from '../components/seller/AmdStatsFooter'
import SellerShell, { ErrorBox, Skeleton } from '../components/seller/SellerShell'

export default function SellerOverview() {
  const { data, loading, error, reload } = useApi(getSellerOverview, [])

  return (
    <SellerShell title="Seller dashboard" backTo="/" backLabel="Store view">
      <p className="mb-5 text-sm text-gray-600">
        Size-fit risk across your catalog, mined from buyer reviews and your size charts.
      </p>

      {loading && (
        <div className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3">
          <Skeleton className="h-52" />
          <Skeleton className="h-52" />
          <Skeleton className="h-52" />
        </div>
      )}

      {error && <ErrorBox message={error.message} onRetry={reload} />}

      {data && (
        <>
          <div className="grid grid-cols-1 gap-5 md:grid-cols-2 lg:grid-cols-3">
            {[...data.products]
              .sort((a, b) => b.risk_score - a.risk_score)
              .map((product) => (
                <ProductRiskCard key={product.product_id} product={product} />
              ))}
          </div>
          <div className="mt-5">
            <AmdStatsFooter note={data.throughput_note} />
          </div>
        </>
      )}
    </SellerShell>
  )
}
