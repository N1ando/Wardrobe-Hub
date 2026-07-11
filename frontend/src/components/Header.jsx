import { useEffect, useRef, useState, useSyncExternalStore } from 'react'
import { Link, NavLink } from 'react-router-dom'
import { Search, ShoppingBag, Trash2 } from 'lucide-react'
import { LogoMark, Wordmark } from './Logo'
import { getCart, removeCartItem } from '../api'
import { getCartSnapshot, setCart, subscribeCart } from '../cartStore'

export default function Header() {
  return (
    <header className="sticky top-0 z-40 bg-surface/90 backdrop-blur-sm border-b border-ink/10">
      <div className="max-w-6xl mx-auto px-6 h-16 flex items-center gap-8">
        <Link to="/" className="flex items-center gap-2.5 shrink-0 group">
          <LogoMark size={28} />
          <Wordmark className="text-xl text-ink" />
        </Link>

        <nav className="hidden sm:flex items-center gap-6 text-sm">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              `link-underline transition-colors ${isActive ? 'text-ink font-medium' : 'text-muted hover:text-ink'}`
            }
          >
            Home
          </NavLink>
          <NavLink
            to="/shop"
            className={({ isActive }) =>
              `link-underline transition-colors ${isActive ? 'text-ink font-medium' : 'text-muted hover:text-ink'}`
            }
          >
            Shop
          </NavLink>
        </nav>

        <div className="flex items-center gap-4 ml-auto">
          <div className="relative w-64 hidden md:block">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
            <input
              type="text"
              placeholder="Search for your next outfit"
              className="w-full bg-background border border-ink/10 rounded-full pl-9 pr-4 py-2 text-sm placeholder:text-muted focus:outline-none focus:border-ink/30 transition-colors"
            />
          </div>
          <CartButton />
        </div>
      </div>
    </header>
  )
}

function CartButton() {
  const cart = useSyncExternalStore(subscribeCart, getCartSnapshot)
  const [open, setOpen] = useState(false)
  const panelRef = useRef(null)
  const count = cart.items.reduce((s, i) => s + i.quantity, 0)

  useEffect(() => {
    getCart().then(setCart).catch(() => {})
  }, [])

  useEffect(() => {
    if (!open) return
    function onClickOutside(e) {
      if (panelRef.current && !panelRef.current.contains(e.target)) setOpen(false)
    }
    document.addEventListener('mousedown', onClickOutside)
    return () => document.removeEventListener('mousedown', onClickOutside)
  }, [open])

  async function handleRemove(itemId) {
    try {
      setCart(await removeCartItem(itemId))
    } catch {
      // Leave the cart as-is; the item is still there on the server.
    }
  }

  return (
    <div className="relative" ref={panelRef}>
      <button
        onClick={() => setOpen((o) => !o)}
        aria-label={`Cart, ${count} items`}
        className="relative p-2 text-ink hover:text-accent transition-colors cursor-pointer"
      >
        <ShoppingBag size={20} />
        {count > 0 && (
          <span className="absolute -top-0.5 -right-0.5 bg-accent text-white text-[10px] font-bold min-w-4.5 h-4.5 px-1 rounded-full flex items-center justify-center">
            {count}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-full mt-2 w-80 bg-surface border border-ink/10 rounded-2xl shadow-[var(--shadow-lifted)] p-4 animate-modal-in">
          <div className="font-display font-bold text-sm text-ink mb-3">Your cart</div>
          {cart.items.length === 0 ? (
            <p className="text-sm text-muted py-4 text-center">
              Nothing here yet — find your size first.
            </p>
          ) : (
            <>
              <ul className="space-y-3 max-h-64 overflow-y-auto">
                {cart.items.map((item) => (
                  <li key={item.id} className="flex items-center justify-between gap-3 text-sm">
                    <div className="min-w-0">
                      <div className="font-medium text-ink truncate">{item.name}</div>
                      <div className="text-xs text-muted">
                        Size {item.size} · Qty {item.quantity}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <span className="font-medium text-ink">
                        ${(item.price * item.quantity).toFixed(2)}
                      </span>
                      <button
                        onClick={() => handleRemove(item.id)}
                        aria-label={`Remove ${item.name}`}
                        className="text-muted hover:text-red-600 transition-colors cursor-pointer p-1"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
              <div className="ticket-divider mt-4 pt-3 flex items-center justify-between text-sm">
                <span className="text-muted">Total</span>
                <span className="font-display font-bold text-ink">${cart.total.toFixed(2)}</span>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  )
}
