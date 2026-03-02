import React, { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { useNavigate } from 'react-router-dom'
import Card from '../components/Card'
import AnimatedKPI from '../components/AnimatedKPI'

export default function Dashboard({ products = [] }) {
  const navigate = useNavigate()
  const [stats, setStats] = useState({
    totalAnalyzed: 0,
    avgEcoScore: 0,
    carbonSaved: 0,
    costReduction: 0
  })

  useEffect(() => {
    if (products && products.length > 0) {
      const totalEco = products.reduce((sum, p) => sum + (p.ecoScore || 70), 0)
      const avgEco = Math.round(totalEco / products.length)
      
      setStats({
        totalAnalyzed: products.length,
        avgEcoScore: avgEco,
        carbonSaved: (products.length * 2.3).toFixed(1),
        costReduction: (products.length * 12).toFixed(0)
      })
    }
  }, [products])

  const recentProducts = products.slice(0, 5)

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className="space-y-8"
    >
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold text-white mb-2">Dashboard</h1>
        <p className="text-slate-400">Overview of your packaging optimization analysis</p>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <AnimatedKPI 
          index={0}
          label="Products Analyzed" 
          value={stats.totalAnalyzed} 
          colorClass="text-cyan-300" 
        />
        <AnimatedKPI 
          index={1}
          label="Avg Eco Score" 
          value={stats.avgEcoScore} 
          suffix=" / 100"
          colorClass="text-emerald-300" 
          maxValue={100}
          showProgress={true}
        />
        <AnimatedKPI 
          index={2}
          label="CO2 Saved" 
          value={parseFloat(stats.carbonSaved)} 
          suffix=" tons"
          decimals={1}
          colorClass="text-emerald-400" 
        />
        <AnimatedKPI 
          index={3}
          label="Cost Reduction" 
          value={stats.costReduction} 
          prefix="$"
          colorClass="text-amber-300" 
        />
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Activity/Recent Products */}
        <div className="lg:col-span-2">
          <Card className="border border-white/10 bg-white/5 p-6">
            <div className="mb-6">
              <h2 className="text-2xl font-bold text-white mb-1">Recent Analysis</h2>
              <p className="text-sm text-slate-400">Your latest packaging optimization projects</p>
            </div>

            {recentProducts.length > 0 ? (
              <motion.div className="space-y-3" layout>
                {recentProducts.map((product, idx) => (
                  <motion.button
                    key={product.id}
                    layoutId={`product-${product.id}`}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 20 }}
                    transition={{ delay: idx * 0.1, duration: 0.4 }}
                    onClick={() => navigate('/recommendations')}
                    whileHover={{ x: 8, scale: 1.01 }}
                    className="w-full text-left rounded-lg border border-white/10 bg-gradient-to-r from-white/5 to-transparent p-4 hover:border-cyan-400/50 hover:bg-white/10 transition-all duration-300 group"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex-1">
                        <p className="font-semibold text-white group-hover:text-cyan-200 transition">{product.productName}</p>
                        <p className="text-xs text-slate-400 capitalize">{product.category}</p>
                      </div>
                      <motion.div 
                        className="text-right ml-4"
                        whileHover={{ scale: 1.1 }}
                      >
                        <p className="text-lg font-bold text-emerald-300">{product.ecoScore || 70}</p>
                        <p className="text-xs text-slate-400">Score</p>
                      </motion.div>
                    </div>
                    <div className="grid grid-cols-3 gap-2 text-xs">
                      <span className="px-2 py-1 rounded bg-white/5 text-slate-300 group-hover:bg-white/10 transition">
                        {product.weight || 0} kg
                      </span>
                      <span className="px-2 py-1 rounded bg-white/5 text-slate-300 group-hover:bg-white/10 transition">
                        {product.recyclability || 70}% recyclable
                      </span>
                      <span className="px-2 py-1 rounded bg-white/5 text-slate-300 group-hover:bg-white/10 transition">
                        {new Date(product.createdAt).toLocaleDateString()}
                      </span>
                    </div>
                  </motion.button>
                ))}
              </motion.div>
            ) : (
              <div className="py-12 text-center">
                <p className="text-slate-400 mb-4">No products analyzed yet</p>
                <motion.button
                  onClick={() => navigate('/simulation')}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="px-6 py-2 bg-gradient-to-r from-cyan-500 to-emerald-500 text-white rounded-lg font-medium"
                >
                  Create First Product
                </motion.button>
              </div>
            )}
          </Card>
        </div>

        {/* Quick Actions / Status */}
        <div className="space-y-6">
          <Card className="border border-white/10 bg-white/5 p-6">
            <h3 className="text-lg font-bold text-white mb-4">Quick Actions</h3>
            <div className="space-y-3">
              <motion.button
                onClick={() => navigate('/simulation')}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="w-full px-4 py-3 bg-gradient-to-r from-cyan-500/20 to-emerald-500/20 border border-cyan-400/30 text-white rounded-lg hover:border-cyan-400/60 transition font-medium"
              >
                + New Analysis
              </motion.button>
              <motion.button
                onClick={() => navigate('/recommendations')}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="w-full px-4 py-3 border border-white/10 text-white rounded-lg hover:border-white/20 transition font-medium"
              >
                View Recommendations
              </motion.button>
              <motion.button
                onClick={() => navigate('/analytics')}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="w-full px-4 py-3 border border-white/10 text-white rounded-lg hover:border-white/20 transition font-medium"
              >
                View Analytics
              </motion.button>
            </div>
          </Card>

          <Card className="border border-emerald-500/30 bg-emerald-500/10 p-6">
            <div className="flex items-start gap-3">
              <span className="text-2xl">✨</span>
              <div>
                <h4 className="font-semibold text-white mb-1">System Status</h4>
                <p className="text-sm text-emerald-200">All models operational</p>
                <p className="text-xs text-emerald-300 mt-2">API latency: 120ms</p>
              </div>
            </div>
          </Card>
        </div>
      </div>

      {/* Info Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="border border-white/10 bg-white/5 p-6">
          <h3 className="text-lg font-bold text-white mb-3">💡 Optimization Tips</h3>
          <ul className="text-sm text-slate-300 space-y-2">
            <li>• Bamboo offers 92% eco-score with renewable properties</li>
            <li>• Paper is 90% recyclable and cost-effective</li>
            <li>• Jute provides natural fiber durability</li>
          </ul>
        </Card>

        <Card className="border border-white/10 bg-white/5 p-6">
          <h3 className="text-lg font-bold text-white mb-3">📊 Model Performance</h3>
          <ul className="text-sm text-slate-300 space-y-2">
            <li>• RF Cost Model: 94% accuracy</li>
            <li>• XGB CO2 Model: 91% accuracy</li>
            <li>• Recommendation Engine: 87% match rate</li>
          </ul>
        </Card>
      </div>
    </motion.div>
  )
}
