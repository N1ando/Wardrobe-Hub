import { useState, useEffect, useRef } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Star, ChevronLeft, ShieldCheck, MessageCircle, Minus, Plus, BadgeCheck, Check } from 'lucide-react'
import { MOCK_PRODUCTS } from '../data/mockProducts'
import FitModal from '../components/FitModal'
import { getFitProfile } from '../fitProfile'
import { getRecommendation, addToCart } from '../api'
import { setCart } from '../cartStore'

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
  const [cartStatus, setCartStatus] = useState('idle')
  const [profile] = useState(() => getFitProfile())
  const [checking, setChecking] = useState(profile !== null)
  const reviewRefs = useRef({})
  const [lightboxOpen, setLightboxOpen] = useState(false)

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

  async function handleAddToCart() {
    if (!selectedSize) {
      setCartStatus('need-size')
      return
    }
    setCartStatus('adding')
    try {
      const cart = await addToCart({
        product_id: product.id,
        size: selectedSize,
        quantity,
        name: product.name,
        price: product.price,
      })
      setCart(cart)
      setCartStatus('added')
      setTimeout(() => setCartStatus('idle'), 2000)
    } catch {
      setCartStatus('error')
    }
  }

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
        <Link to="/shop" className="inline-flex items-center gap-1 text-sm text-muted hover:text-ink transition-colors mb-6">
          <ChevronLeft size={16} /> Back to products
        </Link>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
          {/* Left: image + thumbnails */}
          <div className="md:sticky md:top-24 md:self-start stagger-child" style={{ '--stagger-i': 0 }}>
            <div className="bg-[#EEEEE9] rounded-xl overflow-hidden mb-3 group">
              <img
                src={product.images[activeImage]}
                alt={product.name}
                className="w-full h-[420px] object-contain p-4 cursor-zoom-in group-hover:scale-[1.03] transition-transform duration-500"
                onClick={() => setLightboxOpen(true)}
              />
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
          <div className="stagger-child" style={{ '--stagger-i': 1 }}>
            <div className="font-accent italic text-xs tracking-[0.15em] text-accent uppercase mb-2">
              {product.category}
            </div>
            <h1 className="font-display font-bold text-4xl text-ink mb-2">{product.name}</h1>
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
                    onClick={() => {
                      setSelectedSize(size)
                      setCartStatus((s) => (s === 'need-size' ? 'idle' : s))
                    }}
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

            {/* FitOS integration — ticket-style fit passport */}
            <div className="relative border border-accent/25 bg-gradient-to-br from-accent/8 to-accent/3 rounded-2xl mb-4 shadow-[var(--shadow-soft)] overflow-hidden">
              <div className="absolute top-0 left-0 h-full w-1 bg-accent/60" />
              <div className="p-5 pb-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2 text-accent text-sm font-medium">
                    <ShieldCheck size={16} /> fitOS Sizing Intelligence
                  </div>
                  <span className="font-accent italic text-[10px] tracking-[0.15em] text-accent/70 uppercase">
                    Fit Passport
                  </span>
                </div>

                {checking ? (
                  <FitPassportSkeleton />
                ) : quickResult ? (
                  <div className="mb-1">
                    <div className="flex items-center gap-1 text-xs text-accent font-medium mb-1.5">
                      <BadgeCheck size={13} /> Fit Passport applied
                    </div>
                    <div className="flex items-end gap-3">
                      <span className="font-display font-bold text-4xl text-ink leading-none">
                        {quickResult.recommended_size}
                      </span>
                      <span className="text-sm text-muted pb-0.5">
                        recommended · fit score{' '}
                        <span className="font-semibold text-ink">{quickResult.confidence}</span>/100
                      </span>
                    </div>
                  </div>
                ) : (
                  <p className="font-accent italic text-sm text-muted mb-1">
                    Four measurements. One honest answer.
                  </p>
                )}
              </div>

              {!checking && (
                <div className="ticket-divider mx-5" />
              )}

              {!checking && (
                <div className="p-5 pt-4">
                  <button
                    onClick={() => setModalOpen(true)}
                    className="w-full bg-ink text-white px-6 py-3 rounded-lg font-medium hover:bg-accent transition-colors duration-300 cursor-pointer"
                  >
                    {quickResult ? "Re-check My Size" : "Find My Size"}
                  </button>
                </div>
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

            <button
              onClick={handleAddToCart}
              disabled={cartStatus === 'adding'}
              className={`w-full px-6 py-3 rounded-lg font-medium transition-colors mb-2 cursor-pointer disabled:opacity-60 ${
                cartStatus === 'added'
                  ? 'bg-accent text-white border border-accent'
                  : 'border border-ink/20 text-ink hover:border-ink'
              }`}
            >
              {cartStatus === 'adding' ? (
                'Adding...'
              ) : cartStatus === 'added' ? (
                <span className="inline-flex items-center gap-1.5">
                  <Check size={16} /> Added to cart
                </span>
              ) : (
                'Add to Cart'
              )}
            </button>
            <div className="h-5 mb-4 text-xs" aria-live="polite">
              {cartStatus === 'need-size' && (
                <span className="text-caution">Pick a size first — or let us find it for you above.</span>
              )}
              {cartStatus === 'error' && (
                <span className="text-red-600">Couldn't add to cart. Please try again.</span>
              )}
            </div>

            {/* Seller mini-card */}
            <div className="flex items-center justify-between border border-ink/10 bg-surface rounded-xl p-4 w-full shadow-[var(--shadow-soft)]">
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
            <h2 className="font-display font-bold text-2xl text-ink">
              What buyers said{' '}
              <span className="font-accent italic font-normal text-muted text-lg">
                ({product.reviews.length} reviews)
              </span>
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
                  <span className="w-6 h-6 rounded-full bg-accent/15 text-accent text-[10px] font-bold flex items-center justify-center uppercase">
                    {review.user.slice(0, 2)}
                  </span>
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
      
      {lightboxOpen && (
        <ImageLightbox
          images={product.images}
          activeIndex={activeImage}
          onClose={() => setLightboxOpen(false)}
          onNavigate={setActiveImage}
        />
      )}     

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

function ImageLightbox({ images, activeIndex, onClose, onNavigate }) {
  return (
    <div
      className="fixed inset-0 bg-ink/90 z-[60] flex items-center justify-center p-6"
      onClick={onClose}
    >
      <button
        onClick={onClose}
        className="absolute top-6 right-6 text-white text-3xl leading-none hover:opacity-70"
      >
        &times;
      </button>

      {images.length > 1 && (
        <button
          onClick={(e) => {
            e.stopPropagation()
            onNavigate(activeIndex === 0 ? images.length - 1 : activeIndex - 1)
          }}
          className="absolute left-6 text-white text-4xl hover:opacity-70"
        >
          &#8249;
        </button>
      )}

      <img
        src={images[activeIndex]}
        alt=""
        className="max-h-[85vh] max-w-[85vw] object-contain"
        onClick={(e) => e.stopPropagation()}
      />

      {images.length > 1 && (
        <button
          onClick={(e) => {
            e.stopPropagation()
            onNavigate(activeIndex === images.length - 1 ? 0 : activeIndex + 1)
          }}
          className="absolute right-6 text-white text-4xl hover:opacity-70"
        >
          &#8250;
        </button>
      )}
    </div>
  )
}