import { Link } from 'react-router-dom'
import { Star } from 'lucide-react'
import { MOCK_PRODUCTS } from '../data/mockProducts'

export default function ProductList() {
  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-6xl mx-auto px-6 py-12">
        <div className="mb-10">
          <div className="text-xs font-medium tracking-widest text-muted uppercase mb-2">
            Sizing Intelligence
          </div>
          <h1 className="font-display font-extrabold text-4xl text-ink">Wardrobe-Hub</h1>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
          {MOCK_PRODUCTS.map((product) => (
            <Link
              key={product.id}
              to={`/product/${product.id}`}
              className="group bg-surface border border-ink/10 rounded-xl overflow-hidden hover:border-ink/30 hover:shadow-md transition-all duration-200"
            >
              <div className="relative overflow-hidden bg-[#EEEEE9]">
                <img
                  src={product.image}
                  alt={product.name}
                  className="w-full h-72 object-cover group-hover:scale-[1.03] transition-transform duration-300"
                />
              </div>
              <div className="p-5">
                <h2 className="font-display font-semibold text-ink mb-1">{product.name}</h2>
                <p className="text-lg font-semibold text-ink mb-2">${product.price.toFixed(2)}</p>
                <div className="flex items-center gap-1.5 text-sm text-muted">
                  <Star size={14} className="fill-accent text-accent" />
                  <span>{product.rating}</span>
                  <span>·</span>
                  <span>{product.sold.toLocaleString()} sold</span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}




