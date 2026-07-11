// fitOS brand mark: a lowercase "f" drawn as a measuring tape, with ruler
// ticks along the stem. Inherits size via props; colors are fixed brand ink
// on sage-tinted ground so it reads on both light and dark surfaces.
export function LogoMark({ size = 28 }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 28 28"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <rect width="28" height="28" rx="8" fill="#1C1C1A" />
      <path
        d="M16.5 6.5c-2.2 0-3.5 1.3-3.5 3.5v11.5"
        stroke="#F7F5F0"
        strokeWidth="2.2"
        strokeLinecap="round"
      />
      <path d="M9.5 13h7" stroke="#8FA989" strokeWidth="2.2" strokeLinecap="round" />
      <path d="M13 17.5h2.5M13 21h2.5" stroke="#8FA989" strokeWidth="1.4" strokeLinecap="round" />
    </svg>
  )
}

export function Wordmark({ className = '' }) {
  return (
    <span className={`font-display font-bold tracking-tight ${className}`}>
      fit<span className="text-accent">OS</span>
    </span>
  )
}
