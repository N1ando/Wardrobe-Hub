import { useParams } from 'react-router-dom'
import { getProductRisk } from '../api'
import { useApi } from '../hooks/useApi'
import RiskBadge from '../components/seller/RiskBadge'
import FitComplaintChart from '../components/seller/FitComplaintChart'
import ComplaintAreasChart from '../components/seller/ComplaintAreasChart'
import MissingFieldsChecklist from '../components/seller/MissingFieldsChecklist'
import SuggestionsPanel from '../components/seller/SuggestionsPanel'
import ReviewQuoteList from '../components/seller/ReviewQuoteList'
import AmdStatsFooter from '../components/seller/AmdStatsFooter'
import SellerShell, { ErrorBox, SectionCard, Skeleton } from '../components/seller/SellerShell'

export default function SellerProductDetail() {
  const { id } = useParams()
  const { data, loading, error, reload } = useApi(() => getProductRisk(Number(id)), [id])

  return (
    <SellerShell title={data?.name ?? 'Product risk'} backTo="/seller" backLabel="All products">
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

      {data && (
        <div className="space-y-5">
          <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
            <RiskBadge level={data.risk_level} />
            <span className="text-sm text-gray-600">
              Risk score <span className="text-lg font-bold text-gray-900">{data.risk_score}</span>
              /100
            </span>
            <span className="text-sm text-gray-600">
              {data.complaint_count} fit complaints in {data.review_count} reviews
            </span>
          </div>

          {/* AMD proof strip: above the fold on purpose. */}
          <AmdStatsFooter meta={data.analysis_meta} />

          <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
            <SectionCard title={`Fit verdicts from ${data.review_count} mined reviews`}>
              <FitComplaintChart distribution={data.fit_distribution} />
            </SectionCard>

            <SectionCard title="Share of complaints by area">
              <ComplaintAreasChart areas={data.complaint_areas} />
            </SectionCard>

            <SectionCard title="Size chart completeness">
              <MissingFieldsChecklist
                requiredFields={data.required_fields}
                missingFields={data.missing_fields}
                fieldImpact={data.field_impact}
              />
            </SectionCard>

            <SectionCard title="Suggested fixes">
              <SuggestionsPanel suggestions={data.suggestions} />
            </SectionCard>

            <SectionCard title="What reviewers actually said" className="lg:col-span-2">
              <ReviewQuoteList quotes={data.quotes} />
            </SectionCard>
          </div>
        </div>
      )}
    </SellerShell>
  )
}
