import { Routes, Route } from 'react-router-dom'
import Header from './components/Header'
import ProductList from './pages/ProductList'
import ProductDetail from './pages/ProductDetail'
import SellerOverview from './pages/SellerOverview'
import SellerProductDetail from './pages/SellerProductDetail'

function App() {
  return (
    <>
      <Header />
      <Routes>
        <Route path="/" element={<ProductList />} />
        <Route path="/product/:id" element={<ProductDetail />} />
        <Route path="/seller" element={<SellerOverview />} />
        <Route path="/seller/products/:id" element={<SellerProductDetail />} />
      </Routes>
      <footer className="border-t border-ink/10 mt-20">
        <div className="max-w-6xl mx-auto px-6 py-8 flex items-center justify-between text-xs text-muted">
          <span>Wardrobe-Hub — Sizing Intelligence Layer</span>
          <span>Built for AMD Developer Hackathon 2026</span>
        </div>
      </footer>
    </>
  )
}

export default App