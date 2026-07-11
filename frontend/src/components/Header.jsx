import { Link } from 'react-router-dom'
import { Search, ShoppingBag } from 'lucide-react'

export default function Header() {
  return (
    <header className="sticky top-0 z-40 bg-surface/90 backdrop-blur-sm border-b border-ink/10">
      <div className="max-w-6xl mx-auto px-6 h-16 flex items-center gap-6">
        <Link to="/" className="font-display font-extrabold text-xl text-ink shrink-0">
          Wardrobe-Hub
        </Link>

        <div className="flex items-center gap-4 ml-auto">
          <div className="relative w-64">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
            <input
              type="text"
              placeholder="Search for your next outfit"
              className="w-full bg-background border border-ink/10 rounded-full pl-9 pr-4 py-2 text-sm placeholder:text-muted focus:outline-none focus:border-ink/30 transition-colors"
            />
          </div>

        </div>
      </div>
    </header>
  )
}