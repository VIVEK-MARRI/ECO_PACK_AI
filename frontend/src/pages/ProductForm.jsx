import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import Card from '../components/Card'
import { api } from '../services/api'

export default function ProductForm({ onSubmit }) {
  const navigate = useNavigate()
  const [formData, setFormData] = useState({
    productName: '',
    category: 'electronics',
    weight: '',
    strength: '50',
    biodegradability: '50',
    recyclability: '50'
  })

  const [errors, setErrors] = useState({})
  const [isLoading, setIsLoading] = useState(false)

  const categories = [
    'electronics',
    'food',
    'beverages',
    'cosmetics',
    'pharmaceuticals',
    'home',
    'textiles',
    'other'
  ]

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }))
    }
  }

  const validateForm = () => {
    const newErrors = {}
    if (!formData.productName.trim()) newErrors.productName = 'Product name is required'
    if (!formData.weight || parseFloat(formData.weight) <= 0) newErrors.weight = 'Valid weight is required'
    return newErrors
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    console.log('[RecommendationsFlow] Get AI Recommendations clicked', formData)

    const newErrors = validateForm()
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors)
      return
    }

    setIsLoading(true)

    api.inputProduct({
      ...formData,
      weight: parseFloat(formData.weight),
      strength: parseFloat(formData.strength),
      biodegradability: parseFloat(formData.biodegradability),
      recyclability: parseFloat(formData.recyclability)
    })
    .then(response => {
      console.log('Product saved:', response)
      const preparedProduct = {
        ...formData,
        weight: parseFloat(formData.weight),
        strength: parseFloat(formData.strength),
        biodegradability: parseFloat(formData.biodegradability),
        recyclability: parseFloat(formData.recyclability),
        backendId: response.product_id || response.status
      }

      if (typeof onSubmit === 'function') {
        onSubmit(preparedProduct)
      }

      navigate('/recommendations', { 
        state: { 
          product: preparedProduct
        }
      })
    })
    .catch(error => {
      console.warn('Error:', error.message)
      const fallbackProduct = {
        ...formData,
        weight: parseFloat(formData.weight),
        strength: parseFloat(formData.strength),
        biodegradability: parseFloat(formData.biodegradability),
        recyclability: parseFloat(formData.recyclability),
        backendId: formData.productName || `PROD-${Date.now()}`
      }

      if (typeof onSubmit === 'function') {
        onSubmit(fallbackProduct)
      }

      navigate('/recommendations', {
        state: {
          product: fallbackProduct
        }
      })
    })
    .finally(() => setIsLoading(false))
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className="space-y-8"
    >
      <div>
        <h1 className="text-4xl font-bold text-white mb-2">Simulation</h1>
        <p className="text-slate-400">Create a new product for packaging optimization analysis</p>
      </div>

      <Card className="border border-white/10 bg-white/5 p-8">
        <form onSubmit={handleSubmit} className="space-y-8">
          {/* Product Name */}
          <div>
            <label className="block text-sm font-semibold text-white mb-3">
              Product Name *
            </label>
            <input
              type="text"
              name="productName"
              value={formData.productName}
              onChange={handleChange}
              placeholder="e.g., Premium Electronics Box"
              className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:border-transparent transition"
            />
            {errors.productName && <p className="text-rose-400 text-sm mt-2">{errors.productName}</p>}
          </div>

          {/* Category */}
          <div>
            <label className="block text-sm font-semibold text-white mb-3">
              Product Category
            </label>
            <select
              name="category"
              value={formData.category}
              onChange={handleChange}
              className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:border-transparent transition"
            >
              {categories.map(cat => (
                <option key={cat} value={cat} className="bg-slate-900">
                  {cat.charAt(0).toUpperCase() + cat.slice(1)}
                </option>
              ))}
            </select>
          </div>

          {/* Weight */}
          <div>
            <label className="block text-sm font-semibold text-white mb-3">
              Weight (kg) *
            </label>
            <input
              type="number"
              name="weight"
              value={formData.weight}
              onChange={handleChange}
              placeholder="0.5"
              step="0.1"
              min="0"
              className="w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-400 focus:border-transparent transition"
            />
            {errors.weight && <p className="text-rose-400 text-sm mt-2">{errors.weight}</p>}
          </div>

          {/* Sliders */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Strength */}
            <div>
              <label className="block text-sm font-semibold text-white mb-3">
                Durability / Strength
              </label>
              <div className="space-y-3">
                <input
                  type="range"
                  name="strength"
                  min="0"
                  max="100"
                  value={formData.strength}
                  onChange={handleChange}
                  className="w-full h-2 bg-white/20 rounded-lg appearance-none cursor-pointer accent-cyan-400"
                />
                <div className="flex justify-between items-center">
                  <span className="text-xs text-slate-400">Weak</span>
                  <span className="text-lg font-bold text-cyan-300">{formData.strength}%</span>
                  <span className="text-xs text-slate-400">Strong</span>
                </div>
              </div>
            </div>

            {/* Biodegradability */}
            <div>
              <label className="block text-sm font-semibold text-white mb-3">
                Biodegradability
              </label>
              <div className="space-y-3">
                <input
                  type="range"
                  name="biodegradability"
                  min="0"
                  max="100"
                  value={formData.biodegradability}
                  onChange={handleChange}
                  className="w-full h-2 bg-white/20 rounded-lg appearance-none cursor-pointer accent-emerald-400"
                />
                <div className="flex justify-between items-center">
                  <span className="text-xs text-slate-400">Low</span>
                  <span className="text-lg font-bold text-emerald-300">{formData.biodegradability}%</span>
                  <span className="text-xs text-slate-400">High</span>
                </div>
              </div>
            </div>

            {/* Recyclability */}
            <div>
              <label className="block text-sm font-semibold text-white mb-3">
                Recyclability
              </label>
              <div className="space-y-3">
                <input
                  type="range"
                  name="recyclability"
                  min="0"
                  max="100"
                  value={formData.recyclability}
                  onChange={handleChange}
                  className="w-full h-2 bg-white/20 rounded-lg appearance-none cursor-pointer accent-amber-400"
                />
                <div className="flex justify-between items-center">
                  <span className="text-xs text-slate-400">Low</span>
                  <span className="text-lg font-bold text-amber-300">{formData.recyclability}%</span>
                  <span className="text-xs text-slate-400">High</span>
                </div>
              </div>
            </div>
          </div>

          {/* Submit Button */}
          <motion.button
            type="submit"
            disabled={isLoading}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="w-full px-6 py-3 bg-gradient-to-r from-cyan-500 to-emerald-500 text-white rounded-lg font-semibold hover:shadow-lg hover:shadow-cyan-500/30 transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Processing...' : 'Get AI Recommendations →'}
          </motion.button>
        </form>
      </Card>
    </motion.div>
  )
}
