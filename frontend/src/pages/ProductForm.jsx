import React, { useState } from 'react'
import Card from '../components/Card'
import { api } from '../services/api'

export default function ProductForm({ onSubmit }) {
  const [formData, setFormData] = useState({
    productName: '',
    category: 'electronics',
    weight: '',
    strength: '50',
    biodegradability: '50',
    recyclability: '50',
    description: ''
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
    const newErrors = validateForm()
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors)
      return
    }

    setIsLoading(true)

    // Try to send to backend, fallback to local storage
    api.inputProduct({
      ...formData,
      weight: parseFloat(formData.weight),
      strength: parseFloat(formData.strength),
      biodegradability: parseFloat(formData.biodegradability),
      recyclability: parseFloat(formData.recyclability)
    })
    .then(response => {
      console.log('Product saved to backend:', response)
      onSubmit({
        ...formData,
        weight: parseFloat(formData.weight),
        strength: parseFloat(formData.strength),
        biodegradability: parseFloat(formData.biodegradability),
        recyclability: parseFloat(formData.recyclability),
        backendId: response.product_id
      })
      setIsLoading(false)
    })
    .catch(error => {
      console.warn('Backend unavailable, using local storage:', error.message)
      // Fallback to local storage
      onSubmit({
        ...formData,
        weight: parseFloat(formData.weight),
        strength: parseFloat(formData.strength),
        biodegradability: parseFloat(formData.biodegradability),
        recyclability: parseFloat(formData.recyclability)
      })
      setIsLoading(false)
    })

    setFormData({
      productName: '',
      category: 'electronics',
      weight: '',
      strength: '50',
      biodegradability: '50',
      recyclability: '50',
      description: ''
    })
  }

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <Card className="p-8 md:p-12 animate-slide-in">
        <h2 className="text-3xl font-bold text-slate-900 mb-2">Analyze New Product</h2>
        <p className="text-slate-600 mb-8">Provide product details for AI-powered packaging recommendations</p>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Product Name */}
          <div>
            <label className="block text-sm font-semibold text-slate-900 mb-2">
              Product Name *
            </label>
            <input
              type="text"
              name="productName"
              value={formData.productName}
              onChange={handleChange}
              placeholder="e.g., Smartphone Protection Box"
              className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent transition"
            />
            {errors.productName && <p className="text-red-500 text-sm mt-1">{errors.productName}</p>}
          </div>

          {/* Category */}
          <div>
            <label className="block text-sm font-semibold text-slate-900 mb-2">
              Product Category
            </label>
            <select
              name="category"
              value={formData.category}
              onChange={handleChange}
              className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent transition"
            >
              {categories.map(cat => (
                <option key={cat} value={cat}>
                  {cat.charAt(0).toUpperCase() + cat.slice(1)}
                </option>
              ))}
            </select>
          </div>

          {/* Weight */}
          <div>
            <label className="block text-sm font-semibold text-slate-900 mb-2">
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
              className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent transition"
            />
            {errors.weight && <p className="text-red-500 text-sm mt-1">{errors.weight}</p>}
          </div>

          {/* Sliders */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Strength */}
            <div>
              <label className="block text-sm font-semibold text-slate-900 mb-2">
                Strength Level
              </label>
              <div className="space-y-2">
                <input
                  type="range"
                  name="strength"
                  min="0"
                  max="100"
                  value={formData.strength}
                  onChange={handleChange}
                  className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer"
                />
                <p className="text-right text-sm font-semibold text-green-600">{formData.strength}%</p>
              </div>
            </div>

            {/* Biodegradability */}
            <div>
              <label className="block text-sm font-semibold text-slate-900 mb-2">
                Biodegradability
              </label>
              <div className="space-y-2">
                <input
                  type="range"
                  name="biodegradability"
                  min="0"
                  max="100"
                  value={formData.biodegradability}
                  onChange={handleChange}
                  className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer"
                />
                <p className="text-right text-sm font-semibold text-green-600">{formData.biodegradability}%</p>
              </div>
            </div>

            {/* Recyclability */}
            <div>
              <label className="block text-sm font-semibold text-slate-900 mb-2">
                Recyclability
              </label>
              <div className="space-y-2">
                <input
                  type="range"
                  name="recyclability"
                  min="0"
                  max="100"
                  value={formData.recyclability}
                  onChange={handleChange}
                  className="w-full h-2 bg-slate-200 rounded-lg appearance-none cursor-pointer"
                />
                <p className="text-right text-sm font-semibold text-green-600">{formData.recyclability}%</p>
              </div>
            </div>
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-semibold text-slate-900 mb-2">
              Additional Notes
            </label>
            <textarea
              name="description"
              value={formData.description}
              onChange={handleChange}
              placeholder="Add any additional details about your product..."
              rows="4"
              className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent transition resize-none"
            />
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-gradient-to-r from-green-500 to-emerald-600 text-white py-3 rounded-lg font-bold hover:shadow-lg transition-shadow disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Processing...' : 'Get AI Recommendations →'}
          </button>
        </form>
      </Card>
    </div>
  )
}
