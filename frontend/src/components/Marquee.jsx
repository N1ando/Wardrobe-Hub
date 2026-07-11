import { Ruler } from 'lucide-react'

const DEFAULT_ITEMS = [
  'Review-backed sizing',
  'Explainable fit scores',
  'No more guesswork',
  'Built on real buyer data',
  'Tight to loose, per dimension',
]

export default function Marquee({ items = DEFAULT_ITEMS }) {
  return (
    <div className="border-y border-ink/10 bg-ink text-background/90 overflow-hidden py-2.5 select-none" aria-hidden="true">
      {/* Four copies so the half-track shift always spans the viewport on wide screens */}
      <div className="flex w-max animate-marquee">
        {[0, 1, 2, 3].map((copy) => (
          <div key={copy} className="flex shrink-0">
            {items.map((item) => (
              <span
                key={`${copy}-${item}`}
                className="flex items-center gap-3 px-6 font-accent italic text-sm tracking-wide whitespace-nowrap"
              >
                {item}
                <Ruler size={12} className="text-accent rotate-45" />
              </span>
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}
