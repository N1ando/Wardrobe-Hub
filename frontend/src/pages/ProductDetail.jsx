import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { MOCK_PRODUCTS } from '../data/mockProducts'
import FitModal from '../components/FitModal'

export default function ProductDetail() {
  const { id } = useParams()
  const [modalOpen, setModalOpen] = useState(false)
  const product = MOCK_PRODUCTS.find((p) => p.id === Number(id))

  if (!product) {
    return <div className="p-8">Product not found.</div>
  }

  return (
    <div className="p-8 max-w-2xl mx-auto">
      <img src={product.image} alt={product.name} className="w-full h-96 object-cover rounded-lg mb-4" />
      <h1 className="text-2xl font-bold">{product.name}</h1>
      <p className="text-xl text-gray-600 mb-4">${product.price.toFixed(2)}</p>

      <button
        onClick={() => setModalOpen(true)}
        className="bg-black text-white px-6 py-3 rounded font-semibold"
      >
        Find My Size
      </button>

      {modalOpen && (
        <FitModal product={product} onClose={() => setModalOpen(false)} />
      )}
    </div>
  )
}