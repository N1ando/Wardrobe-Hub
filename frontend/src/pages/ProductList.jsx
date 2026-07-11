import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Star, ArrowRight, Ruler } from 'lucide-react'
import { MOCK_PRODUCTS } from '../data/mockProducts'
import Marquee from '../components/Marquee'

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
      <section className="max-w-6xl mx-auto px-6 pt-14 pb-12">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-8 items-end">
          <div className="md:col-span-8 stagger-child" style={{ '--stagger-i': 0 }}>
            <div className="font-accent italic text-sm tracking-[0.15em] text-accent uppercase mb-5">
              The collection
            </div>
            <h1 className="font-display font-extrabold text-ink leading-[0.92] mb-6 text-[clamp(2.5rem,6vw,4.5rem)]">
              Shop <span className="text-outline">every piece</span>,
              <br />
              <span className="font-accent italic font-medium text-accent">fit-checked.</span>
            </h1>
            <p className="font-accent text-muted text-lg max-w-md leading-relaxed">
              Every product below carries a review-backed size recommendation —
              tap one and let your Fit Passport do the guessing.
            </p>
          </div>
          <div className="md:col-span-4 flex md:justify-end stagger-child" style={{ '--stagger-i': 2 }}>
            <div className="flex gap-10">
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

      <Marquee />

      <div className="max-w-6xl mx-auto px-6 pt-12">
        {/* Filters */}
        <div className="flex items-center gap-2 mb-10 pb-8 border-b border-ink/10 flex-wrap">
          {FILTERS.map(({ label, category }) => {
            const count = category
              ? MOCK_PRODUCTS.filter((p) => p.category === category).length
              : MOCK_PRODUCTS.length
            const active = activeFilter === label
            return (
              <button
                key={label}
                onClick={() => setActiveFilter(label)}
                className={`text-sm pl-4 pr-2.5 py-1.5 rounded-full border transition-all duration-200 cursor-pointer inline-flex items-center gap-2 ${
                  active
                    ? 'bg-ink text-white border-ink'
                    : 'border-ink/15 text-muted hover:border-ink/40 hover:text-ink'
                }`}
              >
                {label}
                <span
                  className={`text-[10px] font-semibold rounded-full min-w-5 h-5 px-1 inline-flex items-center justify-center ${
                    active ? 'bg-white/20 text-white' : 'bg-ink/5 text-muted'
                  }`}
                >
                  {count}
                </span>
              </button>
            )
          })}
          <span className="ml-auto hidden sm:block font-accent italic text-xs text-muted tracking-wide">
            Every piece fit-checked against mined reviews
          </span>
        </div>

        {/* Product grid — first item featured, larger */}
        {filteredProducts.length === 0 ? (
          <div className="text-center py-16 text-muted text-sm">
            No products in this category yet.
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pb-20">
            {filteredProducts.map((product, i) => (
              <ProductCard key={product.id} product={product} featured={i === 0} index={i} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function Stat({ value, label }) {
  return (
    <div className="relative pl-4 border-l-2 border-accent/40">
      <div className="font-display font-bold text-4xl text-ink">{value}</div>
      <div className="text-xs text-muted mt-0.5 uppercase tracking-wider">{label}</div>
    </div>
  )
}

function ProductCard({ product, featured, index }) {
  return (
    <Link
      to={`/product/${product.id}`}
      style={{ '--stagger-i': index + 1 }}
      className={`group relative bg-surface rounded-2xl overflow-hidden shadow-[var(--shadow-soft)] hover:shadow-[var(--shadow-lifted)] hover:-translate-y-1 transition-all duration-300 stagger-child ${
        featured ? 'md:col-span-2 md:flex md:items-stretch' : ''
      }`}
    >
      <div className={`relative overflow-hidden bg-[#EEEEE9] ${featured ? 'md:w-2/5' : ''}`}>
        <span className="absolute top-4 right-4 font-display font-bold text-sm text-ink/25 z-10">
          {String(index + 1).padStart(2, '0')}
        </span>
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
        <span className="absolute bottom-4 left-4 z-10 flex items-center gap-1.5 bg-surface/90 backdrop-blur-sm text-accent text-[10px] font-semibold tracking-wide uppercase px-2.5 py-1 rounded-full opacity-0 translate-y-1 group-hover:opacity-100 group-hover:translate-y-0 transition-all duration-300">
          <Ruler size={10} /> Fit-checked
        </span>
      </div>
      <div className={`p-6 flex flex-col ${featured ? 'md:w-3/5 md:justify-center' : ''}`}>
        <h2 className={`font-display font-semibold text-ink leading-tight ${featured ? 'text-4xl mb-3' : 'text-xl mb-2'}`}>
          {product.name}
        </h2>
        {featured && (
          <p className="font-accent text-muted text-base mb-4 leading-relaxed">{product.description}</p>
        )}
        <div className={`flex items-center justify-between ${featured ? 'mt-2' : 'mt-auto'}`}>
          <p className={`font-bold text-ink ${featured ? 'text-2xl' : 'text-lg'}`}>
            ${product.price.toFixed(2)}
          </p>
          <div className="flex items-center gap-1 text-xs text-muted bg-background px-2 py-1 rounded-full">
            <Star size={11} className="fill-accent text-accent" />
            <span>{product.rating}</span>
          </div>
        </div>
        <div className="text-xs text-muted mt-1.5">{product.sold.toLocaleString()} sold</div>
        <div
          className={`flex items-center gap-1 text-sm font-medium text-accent mt-4 ${
            featured ? '' : 'opacity-0 -translate-x-1 group-hover:opacity-100 group-hover:translate-x-0 transition-all duration-300'
          }`}
        >
          View product <ArrowRight size={14} className="transition-transform group-hover:translate-x-1" />
        </div>
      </div>
    </Link>
  )
}
