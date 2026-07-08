import { Routes, Route } from 'react-router-dom'
import ProductList from './pages/ProductList'
import ProductDetail from './pages/ProductDetail'
import SellerOverview from './pages/SellerOverview'
import SellerProductDetail from './pages/SellerProductDetail'

function App() {
  return (
    <Routes>
      <Route path="/" element={<ProductList />} />
      <Route path="/product/:id" element={<ProductDetail />} />
      <Route path="/seller" element={<SellerOverview />} />
      <Route path="/seller/products/:id" element={<SellerProductDetail />} />
    </Routes>
  )
}

export default App
