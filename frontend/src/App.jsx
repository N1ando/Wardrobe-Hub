import { Routes, Route } from 'react-router-dom'
import ProductList from './pages/ProductList'
import ProductDetail from './pages/ProductDetail'
import SellerDashboard from './pages/SellerDashboard'

function App() {
  return (
    <Routes>
      <Route path="/" element={<ProductList />} />
      <Route path="/product/:id" element={<ProductDetail />} />
      <Route path="/seller" element={<SellerDashboard />} />
    </Routes>
  )
}

export default App
