// Chart + status colors for the seller dashboard (light surface).
// Validated for CVD separation and surface contrast — if you change a hue,
// re-validate before shipping; don't eyeball it.
export const VIZ = {
  // Diverging pair for the fit distribution: runs-small and runs-large are
  // opposite poles, true-to-size is the neutral midpoint (it SHOULD recede —
  // "nothing wrong here" isn't supposed to pop).
  small: '#2a78d6',
  neutral: '#f0efec',
  large: '#e34948',

  // Single sequential hue for magnitude bars (complaint areas).
  bar: '#2a78d6',

  // Ink + chrome.
  ink: '#0b0b0b',
  inkSecondary: '#52514e',
  muted: '#898781',
  grid: '#e1e0d9',
  ring: 'rgba(11,11,11,0.10)',
}

// Status palette (reserved for risk state, never reused for data series).
// Always rendered with a text label — color never carries meaning alone.
export const RISK = {
  low: { color: '#0ca30c', label: 'LOW RISK' },
  medium: { color: '#fab219', label: 'MEDIUM RISK' },
  high: { color: '#d03b3b', label: 'HIGH RISK' },
}
