import React, { useState, useEffect, Suspense } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import './index.css'
import AppLayout from './layouts/AppLayout'
import Dashboard from './pages/Dashboard'
import ProductForm from './pages/ProductForm'
import Recommendations from './pages/Recommendations'
import History from './pages/History'
import Landing from './pages/Landing'
import { api } from './services/api'

// Loading Screen
function LoadingScreen() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-slate-950 flex items-center justify-center">
      <motion.div
        animate={{ rotate: 360 }}
        transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
        className="w-12 h-12 border-3 border-emerald-500/20 border-t-emerald-500 rounded-full"
      />
    </div>
  )
}

// Page Transition Wrapper
function PageWrapper({ children }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.4 }}
    >
      {children}
    </motion.div>
  )
}

function App() {
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
  }

  return (
    <Router>
      <Suspense fallback={<LoadingScreen />}>
        <AppRoutes 
          products={products}
          selectedProduct={selectedProduct}
          handleAddProduct={handleAddProduct}
          setSelectedProduct={setSelectedProduct}
        />
      </Suspense>
    </Router>
  )
}

// Inner component that uses useLocation - must be inside Router
function AppRoutes({ products, selectedProduct, handleAddProduct, setSelectedProduct }) {
  const location = useLocation()
  const recommendationProduct = location.state?.product || selectedProduct

  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
            <Route path="/" element={<PageWrapper><Landing /></PageWrapper>} />
            <Route
              path="/dashboard"
              element={
                <PageWrapper>
                  <AppLayout>
                    <Dashboard onNavigate={() => {}} productCount={products.length} products={products} />
                  </AppLayout>
                </PageWrapper>
              }
            />
            <Route
              path="/simulation"
              element={
                <PageWrapper>
                  <AppLayout>
                    <ProductForm onSubmit={handleAddProduct} />
                  </AppLayout>
                </PageWrapper>
              }
            />
            <Route
              path="/recommendations"
              element={
                <PageWrapper>
                  <AppLayout>
                    <Recommendations product={recommendationProduct} products={products} />
                  </AppLayout>
                </PageWrapper>
              }
            />
            <Route
              path="/recommendations/:id"
              element={
                <PageWrapper>
                  <AppLayout>
                    <Recommendations product={recommendationProduct} products={products} />
                  </AppLayout>
                </PageWrapper>
              }
            />
            <Route
              path="/history"
              element={
                <PageWrapper>
                  <AppLayout>
                    <History
                      products={products}
                      onSelectProduct={(p) => {
                        setSelectedProduct(p)
                      }}
                    />
                  </AppLayout>
                </PageWrapper>
              }
            />
            <Route
              path="/analytics"
              element={
                <PageWrapper>
                  <AppLayout>
                    <Dashboard onNavigate={() => {}} productCount={products.length} products={products} />
                  </AppLayout>
                </PageWrapper>
              }
            />
            <Route
              path="/sustainability"
              element={
                <PageWrapper>
                  <AppLayout>
                    <Dashboard onNavigate={() => {}} productCount={products.length} products={products} />
                  </AppLayout>
                </PageWrapper>
              }
            />
            <Route
              path="/settings"
              element={
                <PageWrapper>
                  <AppLayout>
                    <div className="p-8"><h1 className="text-2xl font-bold text-white">Settings</h1></div>
                  </AppLayout>
                </PageWrapper>
              }
            />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AnimatePresence>
    )
}

export default App
