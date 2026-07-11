import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Star, ArrowRight } from 'lucide-react'
import { MOCK_PRODUCTS } from '../data/mockProducts'

const FILTERS = [
  { label: 'All', category: null },
  { label: 'Shirts', category: 'shirt' },
  { label: 'Jeans', category: 'jeans' },
  { label: 'Dresses', category: 'dress' },
]

export default function ProductList() {
  const [activeFilter, setActiveFilter] = useState('All')

  const filteredProducts = MOCK_PRODUCTS.filter((product) => {
    const filter = FILTERS.find((f) => f.label === activeFilter)
    if (!filter || filter.category === null) return true
    return product.category === filter.category
  })

  return (
    <div className="min-h-screen bg-page-gradient">
      {/* Hero */}
      <section className="max-w-6xl mx-auto px-6 pt-10 pb-10">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-8 items-end">
          <div className="md:col-span-8">
            <div className="font-accent italic text-sm tracking-[0.15em] text-accent uppercase mb-4">
              Sizing Intelligence Layer
            </div>
            <h1 className="font-display font-extrabold text-6xl md:text-7xl text-ink leading-[0.95] mb-6">
              Never guess<br />your size again.
            </h1>
          <p className="font-accent text-muted text-lg max-w-md leading-relaxed">
            Explainable, review-backed size recommendations — built
            on real fit data from thousands of buyers, not guesswork.
          </p>
          </div>
          <div className="md:col-span-4 flex md:justify-end">
            <div className="flex gap-8">
              <Stat value={`${MOCK_PRODUCTS.length}`} label="Products" />
              <Stat
                value={`${(
                  MOCK_PRODUCTS.reduce((s, p) => s + p.rating, 0) / MOCK_PRODUCTS.length
                ).toFixed(1)}`}
                label="Avg. rating"
              />
            </div>
          </div>
        </div>
      </section>

      <div className="max-w-6xl mx-auto px-6">
        {/* Filters */}
        <div className="flex gap-2 mb-10 pb-8 border-b border-ink/10">
          {FILTERS.map(({ label }) => (
            <button
              key={label}
              onClick={() => setActiveFilter(label)}
              className={`text-sm px-4 py-1.5 rounded-full border transition-colors ${
                activeFilter === label
                  ? 'bg-ink text-white border-ink'
                  : 'border-ink/15 text-muted hover:border-ink/40'
              }`}
            >
              {label}
            </button>
          ))}
        </div>

        {/* Product grid — first item featured, larger */}
        {filteredProducts.length === 0 ? (
          <div className="text-center py-16 text-muted text-sm">
            No products in this category yet.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pb-20">
            {filteredProducts.map((product, i) => (
              <ProductCard key={product.id} product={product} featured={i === 0} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function Stat({ value, label }) {
  return (
    <div>
      <div className="font-display font-bold text-3xl text-ink">{value}</div>
      <div className="text-xs text-muted mt-0.5">{label}</div>
    </div>
  )
}

function ProductCard({ product, featured }) {
  return (
    <Link
      to={`/product/${product.id}`}
      className={`group relative bg-surface rounded-2xl overflow-hidden shadow-[var(--shadow-soft)] hover:shadow-[var(--shadow-lifted)] transition-all duration-300 ${
        featured ? 'md:col-span-2 md:flex md:items-stretch' : ''
      }`}
    >
      <div className={`relative overflow-hidden bg-[#EEEEE9] ${featured ? 'md:w-2/5' : ''}`}>
        {product.rating >= 4.5 && (
          <span className="absolute top-4 left-4 bg-ink text-white text-[10px] font-semibold tracking-wide uppercase px-2.5 py-1 rounded-full z-10">
            Bestseller
          </span>
        )}
        <img
          src={product.image}
          alt={product.name}
          className={`w-full object-contain p-6 group-hover:scale-[1.04] transition-transform duration-500 ${
            featured ? 'h-full min-h-[320px] max-h-[440px]' : 'h-72'
          }`}
        />
      </div>
      <div className={`p-6 flex flex-col ${featured ? 'md:w-3/5 md:justify-center' : ''}`}>
        <h2 className={`font-display font-semibold text-ink leading-tight ${featured ? 'text-4xl mb-3' : 'text-xl mb-2'}`}>
          {product.name}
        </h2>
        {featured && (
          <p className="font-accent text-muted text-base mb-4 leading-relaxed">{product.description}</p>
        )}
        <div className="flex items-center justify-between mt-auto">
          <p className={`font-bold text-ink ${featured ? 'text-2xl' : 'text-lg'}`}>
            ${product.price.toFixed(2)}
          </p>
          <div className="flex items-center gap-1 text-xs text-muted bg-background px-2 py-1 rounded-full">
            <Star size={11} className="fill-accent text-accent" />
            <span>{product.rating}</span>
          </div>
        </div>
        <div className="text-xs text-muted mt-1.5">{product.sold.toLocaleString()} sold</div>
        {featured && (
          <div className="flex items-center gap-1 text-sm font-medium text-accent mt-4">
            View product <ArrowRight size={14} className="transition-transform group-hover:translate-x-1" />
          </div>
        )}
      </div>
    </Link>
  )
}