import React, { useState } from 'react'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import Card from '../components/Card'

export default function History({ products = [] }) {
  const navigate = useNavigate()
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

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className="space-y-8"
    >
      <div>
        <h1 className="text-4xl font-bold text-white mb-2">History</h1>
        <p className="text-slate-400">View and manage all your past analyses</p>
      </div>

      {products.length === 0 ? (
        <Card className="border border-white/10 bg-white/5 p-12 text-center">
          <div className="text-6xl mb-4">📋</div>
          <h3 className="text-2xl font-bold text-white mb-2">No Products Yet</h3>
          <p className="text-slate-400 mb-6">Start by creating your first product analysis</p>
          <motion.button
            onClick={() => navigate('/simulation')}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="px-6 py-2 bg-gradient-to-r from-cyan-500 to-emerald-500 text-white rounded-lg font-medium"
          >
            Create Product
          </motion.button>
        </Card>
      ) : (
        <>
          <div className="flex items-center justify-between">
            <p className="text-slate-400">Total analyses: <span className="font-bold text-cyan-300">{products.length}</span></p>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="px-4 py-2 rounded-lg bg-white/10 border border-white/20 text-white focus:outline-none focus:ring-2 focus:ring-cyan-400"
            >
              <option value="date" className="bg-slate-900">Latest First</option>
              <option value="name" className="bg-slate-900">Name (A-Z)</option>
            </select>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {sortedProducts.map((product, idx) => (
              <motion.div
                key={product.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: idx * 0.05 }}
              >
                <Card
                  className="border border-white/10 bg-white/5 p-6 cursor-pointer hover:border-cyan-400/30 hover:bg-white/8 transition group"
                  onClick={() => navigate('/recommendations', { state: { product } })}
                >
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <div className="text-3xl mb-2">{getCategoryIcon(product.category)}</div>
                      <h3 className="text-lg font-bold text-white group-hover:text-cyan-300 transition">{product.productName}</h3>
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-slate-500 capitalize">{product.category}</p>
                    </div>
                  </div>

                  <div className="space-y-3 mb-4">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-slate-400">Weight</span>
                      <span className="font-semibold text-white">{product.weight} kg</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-slate-400">Strength</span>
                      <span className="font-semibold text-cyan-300">{product.strength}%</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-slate-400">Recyclability</span>
                      <span className="font-semibold text-emerald-300">{product.recyclability}%</span>
                    </div>
                  </div>

                  <div className="pt-4 border-t border-white/10 flex items-center justify-between">
                    <span className="text-xs text-slate-500">
                      {new Date(product.createdAt).toLocaleDateString()}
                    </span>
                    <span className="text-cyan-400 font-semibold group-hover:translate-x-1 transition">
                      View →
                    </span>
                  </div>
                </Card>
              </motion.div>
            ))}
          </div>
        </>
      )}
    </motion.div>
  )
}
