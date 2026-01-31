import React, { useState, useEffect } from 'react'
import './index.css'
import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import ProductForm from './pages/ProductForm'
import Recommendations from './pages/Recommendations'
import History from './pages/History'

function App() {
  const [currentPage, setCurrentPage] = useState('dashboard')
  const [products, setProducts] = useState([])
  const [selectedProduct, setSelectedProduct] = useState(null)

  useEffect(() => {
    // Load products from localStorage
    const saved = localStorage.getItem('products')
    if (saved) {
      setProducts(JSON.parse(saved))
    }
  }, [])

  useEffect(() => {
    // Save products to localStorage
    localStorage.setItem('products', JSON.stringify(products))
  }, [products])

  const handleAddProduct = (product) => {
    const newProduct = {
      id: Date.now(),
      ...product,
      createdAt: new Date().toISOString()
    }
    setProducts([newProduct, ...products])
    setSelectedProduct(newProduct)
    setCurrentPage('recommendations')
  }

  const handlePageChange = (page) => {
    setCurrentPage(page)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <Navbar currentPage={currentPage} onPageChange={handlePageChange} />
      
      <main className="pt-20">
        {currentPage === 'dashboard' && <Dashboard onNavigate={handlePageChange} productCount={products.length} />}
        {currentPage === 'product' && <ProductForm onSubmit={handleAddProduct} />}
        {currentPage === 'recommendations' && <Recommendations product={selectedProduct} products={products} />}
        {currentPage === 'history' && <History products={products} onSelectProduct={(p) => {
          setSelectedProduct(p)
          setCurrentPage('recommendations')
        }} />}
      </main>
    </div>
  )
}

export default App
