// Minimal shared cart state: components subscribe via useSyncExternalStore,
// api mutations call setCart with the server response so every subscriber
// (header badge, dropdown) stays consistent without prop drilling.
let cart = { items: [], total: 0 }
const listeners = new Set()

export function getCartSnapshot() {
  return cart
}

export function setCart(next) {
  cart = next
  listeners.forEach((fn) => fn())
}

export function subscribeCart(fn) {
  listeners.add(fn)
  return () => listeners.delete(fn)
}
