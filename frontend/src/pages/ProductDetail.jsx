import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Star, ChevronLeft, ShieldCheck } from 'lucide-react'
import { MOCK_PRODUCTS } from '../data/mockProducts'
import FitModal from '../components/FitModal'
import { getFitProfile } from '../fitProfile'
import { getRecommendation } from '../api'

export default function ProductDetail() {
  const { id } = useParams()
  const [modalOpen, setModalOpen] = useState(false)
  const [selectedSize, setSelectedSize] = useState(null)
  const [quickResult, setQuickResult] = useState(null)
  const [checking, setChecking] = useState(true)
  const product = MOCK_PRODUCTS.find((p) => p.id === Number(id))

  useEffect(() => {
    setQuickResult(null)
    setSelectedSize(null)
    setChecking(true)
    const profile = getFitProfile()
    if (profile && product) {
      getRecommendation({
        product_id: product.id,
        fit_pref: profile.fitPref,
        measurements: profile.measurements,
      }).then((data) => {
        setQuickResult(data)
        setChecking(false)
      })
    } else {
      setChecking(false)
    }
  }, [id])

  if (!product) {
    return <div className="p-8 text-ink">Product not found.</div>
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-5xl mx-auto px-6 py-8">
        <Link to="/" className="inline-flex items-center gap-1 text-sm text-muted hover:text-ink transition-colors mb-6">
          <ChevronLeft size={16} /> Back to products
        </Link>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
          {/* Left: image */}
          <div className="bg-[#EEEEE9] rounded-xl overflow-hidden">
            <img src={product.image} alt={product.name} className="w-full h-full object-cover" />
          </div>

          {/* Right: details */}
          <div>
            <h1 className="font-display font-bold text-3xl text-ink mb-2">{product.name}</h1>
            <div className="flex items-center gap-2 text-sm text-muted mb-4">
              <span className="flex items-center gap-1">
                <Star size={14} className="fill-accent text-accent" /> {product.rating}
              </span>
              <span>·</span>
              <span>{product.sold.toLocaleString()} sold</span>
            </div>
            <p className="font-display text-3xl font-bold text-ink mb-6">${product.price.toFixed(2)}</p>

            {/* Size selector */}
            <div className="mb-6">
              <div className="text-sm font-medium text-ink mb-2">Size</div>
              <div className="flex gap-2 flex-wrap">
                {product.sizes.map((size) => (
                  <button
                    key={size}
                    onClick={() => setSelectedSize(size)}
                    className={`min-w-12 border rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                      selectedSize === size
                        ? 'border-ink bg-ink text-white'
                        : 'border-ink/20 text-ink hover:border-ink'
                    }`}
                  >
                    {size}
                  </button>
                ))}
              </div>
            </div>

            {/* FitOS integration */}
            <div className="border border-accent/20 bg-accent/5 rounded-xl p-4 mb-4">
              <div className="flex items-center gap-2 text-accent text-sm font-medium mb-3">
                <ShieldCheck size={16} /> FitOS Sizing Intelligence
              </div>

              {checking ? (
                <div className="text-muted text-sm">Checking your Fit Passport...</div>
              ) : quickResult ? (
                <div className="mb-3">
                  <div className="text-xs text-accent font-medium mb-1">✓ Fit Passport applied</div>
                  <div className="text-xl font-display font-bold text-ink">
                    Recommended: {quickResult.recommended_size}{" "}
                    <span className="text-sm font-normal text-muted">
                      ({quickResult.confidence}% confidence)
                    </span>
                  </div>
                </div>
              ) : null}

              <button
                onClick={() => setModalOpen(true)}
                className="w-full bg-ink text-white px-6 py-3 rounded-lg font-medium hover:bg-ink/90 transition-colors"
              >
                {quickResult ? "Re-check My Size" : "Find My Size"}
              </button>
            </div>

            <button className="w-full border border-ink/20 text-ink px-6 py-3 rounded-lg font-medium hover:border-ink transition-colors">
              Add to Cart
            </button>
          </div>
        </div>

        {/* Reviews */}
        <div className="mt-16 max-w-3xl">
          <h2 className="font-display font-bold text-xl text-ink mb-6">
            Reviews <span className="text-muted font-normal">({product.reviews.length})</span>
          </h2>
          <div className="space-y-5">
            {product.reviews.map((review) => (
              <div key={review.id} className="border-b border-ink/10 pb-5">
                <div className="flex items-center gap-2 mb-1.5">
                  <span className="font-medium text-sm text-ink">{review.user}</span>
                  <span className="flex items-center gap-0.5">
                    {Array.from({ length: review.rating }).map((_, i) => (
                      <Star key={i} size={12} className="fill-accent text-accent" />
                    ))}
                  </span>
                  <span className="text-xs text-muted">· Size {review.size}</span>
                </div>
                <p className="text-sm text-ink/80">{review.text}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {modalOpen && (
        <FitModal product={product} onClose={() => setModalOpen(false)} />
      )}
    </div>
  )
}