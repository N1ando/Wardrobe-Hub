import { useParams } from 'react-router-dom'
import { getProduct, getProductRisk } from '../api'
import { useApi } from '../hooks/useApi'
import RiskBadge from '../components/seller/RiskBadge'
import FitComplaintChart from '../components/seller/FitComplaintChart'
import ComplaintAreasChart from '../components/seller/ComplaintAreasChart'
import MissingFieldsChecklist from '../components/seller/MissingFieldsChecklist'
import SuggestionsPanel from '../components/seller/SuggestionsPanel'
import ReviewQuoteList from '../components/seller/ReviewQuoteList'
import AmdStatsFooter from '../components/seller/AmdStatsFooter'
import { fieldLabel, requiredFieldsFor } from '../components/seller/chartFields'
import SellerShell, { ErrorBox, SectionCard, Skeleton } from '../components/seller/SellerShell'

// The API reports complaint clusters as counts; the chart wants shares.
function clustersToAreas(clusters) {
  const total = (clusters ?? []).reduce((sum, c) => sum + (c.count ?? 0), 0)
  if (!total) return []
  return clusters.map((c) => ({ area: c.area, pct: c.count / total }))
}

// Impact note when a missing chart field is also a complaint area.
function impactFromClusters(missingFields, clusters, category) {
  const impact = {}
  for (const field of missingFields ?? []) {
    const hit = (clusters ?? []).find((c) => c.area === field)
    if (hit) {
      impact[field] =
        `${hit.count} reviewer${hit.count === 1 ? '' : 's'} complained about ` +
        `${fieldLabel(category, field)} — and buyers have no chart data to check it`
    }
  }
  return impact
}

export default function SellerProductDetail() {
  const { id } = useParams()
  const { data, loading, error, reload } = useApi(
    () =>
      Promise.all([getProductRisk(Number(id)), getProduct(Number(id))]).then(
        ([risk, product]) => ({ risk, product }),
      ),
    [id],
  )
  const risk = data?.risk
  const category = data?.product?.category

  return (
    <SellerShell title={risk?.name ?? 'Product risk'} backTo="/seller" backLabel="All products">
      {loading && (
        <div className="space-y-5">
          <Skeleton className="h-10" />
          <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
            <Skeleton className="h-44" />
            <Skeleton className="h-44" />
            <Skeleton className="h-44" />
            <Skeleton className="h-44" />
          </div>
        </div>
      )}

      {error && <ErrorBox message={error.message} onRetry={reload} />}

      {risk && (
        <div className="space-y-5">
          <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
            <RiskBadge level={risk.risk_level} />
            <span className="text-sm text-gray-600">
              Risk score <span className="text-lg font-bold text-gray-900">{risk.risk_score}</span>
              /100
            </span>
            <span className="text-sm text-gray-600">
              {risk.complaint_count} fit complaints in {risk.review_count} reviews
            </span>
          </div>

          {/* AMD proof strip: above the fold on purpose. */}
          <AmdStatsFooter reviewCount={risk.review_count} />

          <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
            <SectionCard title={`Fit verdicts from ${risk.review_count} mined reviews`}>
              <FitComplaintChart distribution={risk.fit_distribution} />
            </SectionCard>

            <SectionCard title="Share of complaints by area">
              <ComplaintAreasChart areas={clustersToAreas(risk.complaint_clusters)} />
            </SectionCard>

            <SectionCard title="Size chart completeness">
              <MissingFieldsChecklist
                requiredFields={requiredFieldsFor(category)}
                missingFields={risk.missing_fields}
                fieldImpact={impactFromClusters(risk.missing_fields, risk.complaint_clusters, category)}
                category={category}
              />
            </SectionCard>

            <SectionCard title="Suggested fixes">
              <SuggestionsPanel suggestions={risk.suggestions} />
            </SectionCard>

            <SectionCard title="What reviewers actually said" className="lg:col-span-2">
              <ReviewQuoteList quotes={risk.quotes} />
            </SectionCard>
          </div>
        </div>
      )}
    </SellerShell>
  )
}
