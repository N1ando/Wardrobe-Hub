// The AMD proof strip: review mining runs as a batch job on AMD GPU
// infrastructure, and this is where that becomes visible in the product.
// `seconds` stays null until P6's real vLLM/ROCm run supplies the number —
// never fake the throughput stat.
export default function AmdStatsFooter({ meta }) {
  if (!meta) return null
  const throughput =
    meta.seconds != null
      ? `${meta.reviews_processed} reviews in ${meta.seconds}s`
      : `${meta.reviews_processed} reviews analyzed`
  return (
    <div className="flex flex-wrap items-center gap-x-2 rounded-md border bg-gray-50 px-3 py-2 text-xs text-gray-600">
      <span className="font-semibold text-gray-900">Review mining:</span>
      <span>{throughput}</span>
      <span aria-hidden="true">&middot;</span>
      <span>{meta.backend}</span>
    </div>
  )
}
