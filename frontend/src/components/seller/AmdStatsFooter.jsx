// Analysis provenance strip: shows where the review mining actually ran.
// `note` comes from the backend's analysis run (throughput_note); `source`
// and `mode` are the backend's analysis_source / analysis_mode metadata.
// The label only claims AMD when the metadata says amd-vllm — never fake
// the provenance, and never fake the throughput.
const SOURCE_LABELS = {
  'amd-vllm': 'AMD vLLM Batch Analysis',
  fireworks: 'Fireworks Analysis',
  keyword: 'Local Fallback Analysis',
  cache: 'Cached Analysis',
}

function sourceLabel(source, mode) {
  const label = SOURCE_LABELS[source] ?? 'Review Analysis'
  // Only append the mode when the label doesn't already say it
  // (amd-vllm is always batch; keyword is by definition the fallback).
  if (mode && !label.toLowerCase().includes(mode.toLowerCase())) {
    return `${label} (${mode})`
  }
  return label
}

export default function AmdStatsFooter({ note, reviewCount, source, mode }) {
  const stats = note ?? (reviewCount != null ? `${reviewCount} reviews analyzed` : null)
  if (!stats) return null
  return (
    <div className="flex flex-wrap items-center gap-x-2 rounded-md border bg-gray-50 px-3 py-2 text-xs text-gray-600">
      <span className="font-semibold text-gray-900">Review mining:</span>
      <span>{stats}</span>
      <span aria-hidden="true">&middot;</span>
      <span>{sourceLabel(source, mode)}</span>
    </div>
  )
}
