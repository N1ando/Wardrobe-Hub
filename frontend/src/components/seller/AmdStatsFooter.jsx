const SOURCE_LABELS = {
  'amd-vllm': 'AMD vLLM Batch Analysis',
  fireworks: 'Fireworks Analysis',
  keyword: 'Local Fallback Analysis',
  cache: 'Cached Analysis',
}

function sourceLabel(source, mode) {
  const label = SOURCE_LABELS[source] ?? 'Review Analysis'
  if (mode && !label.toLowerCase().includes(mode.toLowerCase())) {
    return `${label} (${mode})`
  }
  return label
}

export default function AmdStatsFooter({ note, reviewCount, source, mode }) {
  const stats = note ?? (reviewCount != null ? `${reviewCount} reviews analyzed` : null)
  if (!stats) return null
  return (
    <div className="flex flex-wrap items-center gap-x-2.5 rounded-xl border border-accent/20 bg-accent/5 px-4 py-2.5 text-xs">
      <span className="flex items-center gap-1.5 font-semibold text-accent">
        <span className="w-1.5 h-1.5 rounded-full bg-accent" />
        Review mining
      </span>
      <span className="text-ink/70">{stats}</span>
      <span aria-hidden="true" className="text-ink/30">&middot;</span>
      <span className="font-mono text-[11px] text-muted">{sourceLabel(source, mode)}</span>
    </div>
  )
}