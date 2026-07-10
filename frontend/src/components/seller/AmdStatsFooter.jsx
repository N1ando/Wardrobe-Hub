// The AMD proof strip: review mining runs as a batch job on AMD GPU
// infrastructure, and this is where that becomes visible in the product.
// `note` comes from the backend's analysis run (throughput_note); until P6's
// vLLM/ROCm batch supplies real numbers it reads as the local keyword-miner
// stats — never fake the throughput.
export default function AmdStatsFooter({ note, reviewCount }) {
  const stats = note ?? (reviewCount != null ? `${reviewCount} reviews analyzed` : null)
  if (!stats) return null
  return (
    <div className="flex flex-wrap items-center gap-x-2 rounded-md border bg-gray-50 px-3 py-2 text-xs text-gray-600">
      <span className="font-semibold text-gray-900">Review mining:</span>
      <span>{stats}</span>
      <span aria-hidden="true">&middot;</span>
      <span>Gemma pipeline &mdash; AMD vLLM/ROCm batch</span>
    </div>
  )
}
