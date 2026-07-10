import { useState, useEffect, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Star, ChevronLeft, ShieldCheck, MessageCircle, Minus, Plus } from 'lucide-react'
import { MOCK_PRODUCTS } from '../data/mockProducts'
import FitModal from '../components/FitModal'
import { getFitProfile } from '../fitProfile'
import { getRecommendation } from '../api'

export default function ProductDetail() {
  const { id } = useParams()
  const product = MOCK_PRODUCTS.find((p) => p.id === Number(id))

  if (!product) {
    return <div className="p-8 text-ink">Product not found.</div>
  }

  // Keyed by product id: switching products remounts the detail view, which
  // resets size, image, quantity, and quick result without effect resets.
  return <ProductDetailContent key={product.id} product={product} />
}

function ProductDetailContent({ product }) {
  const [modalOpen, setModalOpen] = useState(false)
  const [selectedSize, setSelectedSize] = useState(null)
  const [quickResult, setQuickResult] = useState(null)
  const [activeImage, setActiveImage] = useState(0)
  const [quantity, setQuantity] = useState(1)
  const [highlightedIds, setHighlightedIds] = useState([])
  const [profile] = useState(() => getFitProfile())
  const [checking, setChecking] = useState(profile !== null)
  const reviewRefs = useRef({})

  useEffect(() => {
    if (!profile) return
    let alive = true
    getRecommendation({
      product_id: product.id,
      fit_pref: profile.fitPref,
      measurements: profile.measurements,
    })
      .then((data) => {
        if (alive) {
          setQuickResult(data)
          setChecking(false)
        }
      })
      .catch(() => {
        if (alive) setChecking(false)
      })
    return () => {
      alive = false
    }
  }, [product, profile])

  function handleViewReviews(ids) {
    setHighlightedIds(ids)
    const firstId = ids[0]
    if (firstId && reviewRefs.current[firstId]) {
      reviewRefs.current[firstId].scrollIntoView({ behavior: 'smooth', block: 'center' })
    }
  }

  return (
    <div className="min-h-screen bg-page-gradient">
      <div className="max-w-5xl mx-auto px-6 py-8">
        <Link to="/" className="inline-flex items-center gap-1 text-sm text-muted hover:text-ink transition-colors mb-6">
          <ChevronLeft size={16} /> Back to products
        </Link>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
          {/* Left: image + thumbnails */}
          <div>
            <div className="bg-[#EEEEE9] rounded-xl overflow-hidden mb-3">
              <img src={product.images[activeImage]} alt={product.name} className="w-full h-[420px] object-cover" />
            </div>
            <div className="flex gap-3">
              {product.images.map((img, i) => (
                <button
                  key={i}
                  onClick={() => setActiveImage(i)}
                  className={`flex-1 aspect-square rounded-lg overflow-hidden border-2 transition-colors ${
                    activeImage === i ? 'border-ink' : 'border-transparent hover:border-ink/30'
                  }`}
                >
                  <img src={img} alt={`${product.name} angle ${i + 1}`} className="w-full h-full object-cover" />
                </button>
              ))}
            </div>
          </div>

          {/* Right: details */}
          <div>
            <h1 className="font-display font-bold text-3xl text-ink mb-2">{product.name}</h1>
            <p className="text-sm text-muted mb-3">{product.description}</p>
            <div className="flex items-center gap-2 text-sm text-muted mb-4">
              <span className="flex items-center gap-1">
                <Star size={14} className="fill-accent text-accent" /> {product.rating}
              </span>
              <span>·</span>
              <span>{product.sold.toLocaleString()} sold</span>
            </div>
            <p className="font-display text-3xl font-bold text-ink mb-6">${product.price.toFixed(2)}</p>

            {/* Size selector */}
            <div className="mb-5">
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
            <div className="border border-accent/20 bg-gradient-to-br from-accent/8 to-accent/3 rounded-2xl p-5 mb-4 shadow-[var(--shadow-soft)]">
              <div className="flex items-center gap-2 text-accent text-sm font-medium mb-3">
                <ShieldCheck size={16} /> Wardrobe-Hub Sizing Intelligence
              </div>

              {checking ? (
                <FitPassportSkeleton />
              ) : quickResult ? (
                <div className="mb-3">
                  <div className="text-xs text-accent font-medium mb-1">✓ Fit Passport applied</div>
                  <div className="text-xl font-display font-bold text-ink">
                    Recommended: {quickResult.recommended_size}{" "}
                    <span className="text-sm font-normal text-muted">
                      (fit score {quickResult.confidence}/100)
                    </span>
                  </div>
                </div>
              ) : null}

              {!checking && (
                <button
                  onClick={() => setModalOpen(true)}
                  className="w-full bg-ink text-white px-6 py-3 rounded-lg font-medium hover:bg-ink/90 transition-colors"
                >
                  {quickResult ? "Re-check My Size" : "Find My Size"}
                </button>
              )}
            </div>

            {/* Quantity selector */}
            <div className="flex items-center gap-4 mb-3">
              <span className="text-sm font-medium text-ink">Quantity</span>
              <div className="flex items-center border border-ink/20 rounded-lg">
                <button
                  onClick={() => setQuantity((q) => Math.max(1, q - 1))}
                  className="p-2 text-ink hover:bg-ink/5"
                >
                  <Minus size={14} />
                </button>
                <span className="w-10 text-center text-sm font-medium">{quantity}</span>
                <button
                  onClick={() => setQuantity((q) => q + 1)}
                  className="p-2 text-ink hover:bg-ink/5"
                >
                  <Plus size={14} />
                </button>
              </div>
            </div>

            <button className="w-full border border-ink/20 text-ink px-6 py-3 rounded-lg font-medium hover:border-ink transition-colors mb-6">
              Add to Cart
            </button>

            {/* Seller mini-card */}
            <div className="flex items-center justify-between border border-ink/10 rounded-none p-4 w-full -ml-0">
              <div>
                <div className="text-sm font-medium text-ink">{product.seller.name}</div>
                <div className="flex items-center gap-2 text-xs text-muted mt-0.5">
                  <span className="flex items-center gap-0.5">
                    <Star size={11} className="fill-accent text-accent" /> {product.seller.rating}
                  </span>
                  <span>·</span>
                  <span>{product.seller.responseRate}% response rate</span>
                </div>
              </div>
              <button className="flex items-center gap-1.5 text-sm border border-ink/20 rounded-lg px-3 py-1.5 hover:border-ink transition-colors">
                <MessageCircle size={14} /> Chat
              </button>
            </div>        
          </div>
        </div>

        {/* Reviews */}
        <div className="mt-16 max-w-3xl">
          <div className="flex items-center justify-between mb-6">
            <h2 className="font-display font-bold text-xl text-ink">
              Reviews <span className="text-muted font-normal">({product.reviews.length})</span>
            </h2>
            <div className="flex items-center gap-1 text-sm">
              <Star size={14} className="fill-accent text-accent" />
              <span className="font-medium text-ink">{product.rating}</span>
              <span className="text-muted">average</span>
            </div>
          </div>
          <div className="space-y-5">
            {product.reviews.map((review) => (
              <div
                key={review.id}
                ref={(el) => (reviewRefs.current[review.id] = el)}
                className={`border-b pb-5 rounded-lg transition-colors ${
                  highlightedIds.includes(review.id)
                    ? 'bg-caution/10 border-caution/30 -mx-3 px-3 pt-3'
                    : 'border-ink/10'
                }`}
              >
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
        <FitModal
          product={product}
          onClose={() => setModalOpen(false)}
          onViewReviews={handleViewReviews}
        />
      )}
    </div>
  )
}

function FitPassportSkeleton() {
  return (
    <div className="animate-pulse space-y-2 mb-3">
      <div className="h-3 w-32 bg-ink/10 rounded" />
      <div className="h-6 w-48 bg-ink/10 rounded" />
      <div className="h-10 w-full bg-ink/10 rounded-lg mt-3" />
    </div>
  )
}