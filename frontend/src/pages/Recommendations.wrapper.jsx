import React, { Suspense, lazy, memo } from 'react'
import { motion } from 'framer-motion'
import { Skeleton3DPanel, SkeletonKPICard, SkeletonRecommendationCard, SkeletonParetoPanel } from '../components/SkeletonLoader'

const RecommendationsContent = lazy(() => import('./RecommendationsContent'))

function RecommendationsPage({ product }) {
  if (!product) {
    return (
      <div className="min-h-screen p-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="max-w-4xl mx-auto text-center py-20"
        >
          <div className="text-6xl mb-4">📦</div>
          <h1 className="text-2xl font-bold text-white mb-2">No Product Selected</h1>
          <p className="text-slate-400 mb-8">Create or select a product to see material recommendations</p>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="px-6 py-3 bg-gradient-to-r from-cyan-500 to-emerald-500 text-white rounded-lg font-medium"
          >
            Create Product
          </motion.button>
        </motion.div>
      </div>
    )
  }

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-2"
        >
          <h1 className="text-3xl font-bold text-white">Material Recommendations</h1>
          <div className="flex items-center gap-3">
            <p className="text-slate-400">AI-powered packaging optimization for {product?.productName || 'your product'}</p>
            <span className="px-3 py-1 text-xs font-semibold rounded-full bg-gradient-to-r from-cyan-500/20 to-emerald-500/20 text-cyan-300 border border-cyan-500/30">
              🚀 Industrial Multi-Objective Engine
            </span>
          </div>
        </motion.div>

        {/* Suspense with Skeleton Fallback */}
        <Suspense
          fallback={
            <div className="space-y-8">
              {/* KPI Skeleton Row */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {[...Array(4)].map((_, i) => (
                  <SkeletonKPICard key={i} />
                ))}
              </div>

              {/* Main Content Skeleton */}
              <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
                <div className="lg:col-span-3 space-y-6">
                  <Skeleton3DPanel />
                  <SkeletonParetoPanel />
                </div>

                <div className="lg:col-span-2 space-y-4">
                  {[...Array(3)].map((_, i) => (
                    <SkeletonRecommendationCard key={i} />
                  ))}
                </div>
              </div>
            </div>
          }
        >
          <RecommendationsContent product={product} />
        </Suspense>
      </div>
    </div>
  )
}

export default memo(RecommendationsPage)
