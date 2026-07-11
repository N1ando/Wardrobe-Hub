import { RISK } from './vizTheme'

export default function RiskBadge({ level, className = '' }) {
  const risk = RISK[level] ?? RISK.medium
  return (
    <span
      className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-3 py-1 text-[10px] font-semibold uppercase tracking-wide text-ink ${className}`}
      style={{ backgroundColor: `${risk.color}1f` }}
    >
      <span
        className="h-1.5 w-1.5 rounded-full"
        style={{ backgroundColor: risk.color }}
        aria-hidden="true"
      />
      {risk.label}
    </span>
  )
}