import { RISK } from './vizTheme'

// Color-coded pill. The text label always ships with the color (and a dot
// carries the hue) so risk state is never encoded by color alone.
export default function RiskBadge({ level, className = '' }) {
  const risk = RISK[level] ?? RISK.medium
  return (
    <span
      className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-2.5 py-1 text-xs font-semibold text-gray-900 ${className}`}
      style={{ backgroundColor: `${risk.color}1f` }}
    >
      <span
        className="h-2 w-2 rounded-full"
        style={{ backgroundColor: risk.color }}
        aria-hidden="true"
      />
      {risk.label}
    </span>
  )
}
