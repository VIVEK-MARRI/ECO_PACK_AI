import React, { useState, useEffect } from 'react'
import './index.css'
import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import ProductForm from './pages/ProductForm'
import Recommendations from './pages/Recommendations'
import History from './pages/History'
import { api } from './services/api'

function App() {
  const [currentPage, setCurrentPage] = useState('dashboard')
  const [products, setProducts] = useState([])
  const [selectedProduct, setSelectedProduct] = useState(null)

  useEffect(() => {
    // Fetch products from database via API
    const fetchProducts = async () => {
      try {
        // Try to fetch from database
        const response = await api.getAllHistory()
        console.log('API Response:', response)
        if (response && response.status === 'success' && Array.isArray(response.history)) {
          const transformedProducts = response.history.map(item => ({
            id: item.id,
            productName: item.product_id || item.productName || 'Unnamed Product',
            category: item.category || 'other',
            weight: item.weight || 0,
            strength: item.strength || 50,
            biodegradability: item.biodegradability ? item.biodegradability * 100 : 50,
            recyclability: item.recyclability || 50,
            createdAt: item.created_at || item.createdAt || new Date().toISOString(),
            backendId: item.product_id
          }))
          setProducts(transformedProducts)
          localStorage.setItem('products', JSON.stringify(transformedProducts))
        } else {
          // Fallback to localStorage
          const saved = localStorage.getItem('products')
          if (saved) {
            const parsed = JSON.parse(saved)
            console.log('Loaded from localStorage:', parsed)
            setProducts(parsed)
          } else {
            console.log('No products found in localStorage')
            setProducts([])
          }
        }
      } catch (error) {
        console.log('Database fetch failed, using localStorage:', error.message)
        // Fallback to localStorage if API fails
        const saved = localStorage.getItem('products')
        if (saved) {
          const parsed = JSON.parse(saved)
          console.log('Loaded from localStorage:', parsed)
          setProducts(parsed)
        } else {
          console.log('No products found in localStorage')
          setProducts([])
        }
      }
    }
    
    fetchProducts()
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
