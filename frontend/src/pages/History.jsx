import React, { useState } from 'react'
import Card from '../components/Card'

export default function History({ products, onSelectProduct }) {
  const [sortBy, setSortBy] = useState('date')

  const sortedProducts = [...products].sort((a, b) => {
    if (sortBy === 'date') {
      return new Date(b.createdAt) - new Date(a.createdAt)
    }
    return 0
  })

  const getCategoryIcon = (category) => {
    const icons = {
      electronics: '📱',
      food: '🍕',
      beverages: '🥤',
      cosmetics: '💄',
      pharmaceuticals: '💊',
      home: '🏠',
      textiles: '👕',
      other: '📦'
    }
    return icons[category] || '📦'
  }

  if (products.length === 0) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <Card className="p-12 text-center">
          <div className="text-6xl mb-4">📋</div>
          <h3 className="text-2xl font-bold text-slate-900 mb-2">No Products Yet</h3>
          <p className="text-slate-600">Start by analyzing your first product to build your history</p>
        </Card>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-slate-900 mb-4">Analysis History</h2>
        <div className="flex items-center justify-between">
          <p className="text-slate-600">Total analyses: <span className="font-bold text-slate-900">{products.length}</span></p>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
          >
            <option value="date">Latest First</option>
            <option value="name">Name (A-Z)</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {sortedProducts.map(product => (
          <Card
            key={product.id}
            className="p-6 cursor-pointer hover:shadow-lg transition-all hover:-translate-y-1 animate-slide-in"
            onClick={() => onSelectProduct(product)}
          >
            <div className="flex items-start justify-between mb-4">
              <div>
                <div className="text-3xl mb-2">{getCategoryIcon(product.category)}</div>
                <h3 className="text-lg font-bold text-slate-900">{product.productName}</h3>
              </div>
              <div className="text-right">
                <p className="text-xs text-slate-500 capitalize">{product.category}</p>
              </div>
            </div>

            <div className="space-y-3 mb-4">
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-600">Weight</span>
                <span className="font-semibold text-slate-900">{product.weight} kg</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-600">Strength</span>
                <span className="font-semibold text-slate-900">{product.strength}%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-slate-600">Recyclability</span>
                <span className="font-semibold text-green-600">{product.recyclability}%</span>
              </div>
            </div>

            <div className="pt-4 border-t border-slate-200 flex items-center justify-between">
              <span className="text-xs text-slate-500">
                {new Date(product.createdAt).toLocaleDateString()}
              </span>
              <button className="text-green-600 font-semibold hover:text-green-700 flex items-center gap-1">
                View →
              </button>
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
