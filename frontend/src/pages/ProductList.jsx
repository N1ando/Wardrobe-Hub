import { Link } from 'react-router-dom'
import { Star } from 'lucide-react'
import { MOCK_PRODUCTS } from '../data/mockProducts'

export default function ProductList() {
  return (
    <div className="flex items-end justify-between gap-6 mb-8 pb-6 border-b border-ink/10">

      <div className="relative max-w-6xl mx-auto px-6 py-8">
        {/* Header */}
        <div className="relative flex items-end justify-between gap-6 mb-8 pb-6 border-b border-ink/10">
          <div className="relative">
            <div className="text-[10px] font-semibold tracking-[0.2em] text-accent uppercase mb-1.5">
              Sizing Intelligence Layer
            </div>
            <h1 className="font-display font-extrabold text-3xl text-ink">
              Wardrobe-Hub
            </h1>
          </div>
          <p className="text-muted text-sm max-w-xs text-right hidden sm:block">
            Know your size before you buy — explainable, review-backed recommendations.
          </p>
        </div>

        {/* Filter pills — NEW, sits right here between header and grid */}
        <div className="flex gap-2 mb-8">
          {["All", "Shirts", "Jeans", "Dresses"].map((cat, i) => (
            <button
              key={cat}
              className={`text-sm px-4 py-1.5 rounded-full border transition-colors ${
                i === 0
                  ? 'bg-ink text-white border-ink'
                  : 'border-ink/15 text-muted hover:border-ink/40'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Product grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
          {MOCK_PRODUCTS.map((product) => (
            <Link
              key={product.id}
              to={`/product/${product.id}`}
              className="group bg-surface rounded-2xl overflow-hidden shadow-[var(--shadow-soft)] hover:shadow-[var(--shadow-lifted)] hover:-translate-y-1 transition-all duration-300"
            >
              <div className="relative overflow-hidden bg-[#EEEEE9]">
                {product.rating >= 4.5 && (
                  <span className="absolute top-3 left-3 bg-ink text-white text-[10px] font-semibold tracking-wide uppercase px-2.5 py-1 rounded-full z-10">
                    Bestseller
                  </span>
                )}
                <img
                  src={product.image}
                  alt={product.name}
                  className="w-full h-64 object-cover group-hover:scale-[1.03] transition-transform duration-300"
                />
              </div>
              <div className="p-5">
                <h2 className="font-display font-semibold text-ink mb-1 leading-tight">{product.name}</h2>
                <div className="flex items-center justify-between mt-3">
                  <p className="text-lg font-bold text-ink">${product.price.toFixed(2)}</p>
                  <div className="flex items-center gap-1 text-xs text-muted bg-background px-2 py-1 rounded-full">
                    <Star size={11} className="fill-accent text-accent" />
                    <span>{product.rating}</span>
                  </div>
                </div>
                <div className="text-xs text-muted mt-1.5">{product.sold.toLocaleString()} sold</div>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}