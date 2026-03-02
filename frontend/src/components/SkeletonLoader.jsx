import React, { memo } from 'react'
import { motion } from 'framer-motion'

function Skeleton({ className = '', width = '100%', height = '100%', variant = 'default' }) {
  return (
    <motion.div
      className={`bg-gradient-to-r from-slate-800 via-slate-700 to-slate-800 rounded-lg overflow-hidden ${className}`}
      style={{ width, height }}
      animate={{ backgroundPosition: ['200% 0', '-200% 0'] }}
      transition={{ duration: 2, repeat: Infinity }}
    />
  )
}

export function Skeleton3DPanel() {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 p-6 space-y-4">
      <Skeleton height="24px" className="w-32" />
      <Skeleton height="288px" />
      <div className="space-y-2">
        <Skeleton height="16px" className="w-full" />
        <Skeleton height="16px" className="w-3/4" />
      </div>
    </div>
  )
}

export function SkeletonKPICard() {
  return (
    <div className="rounded-xl border border-white/10 bg-white/5 p-4 space-y-3">
      <Skeleton height="12px" className="w-24" />
      <Skeleton height="28px" className="w-32" />
      <Skeleton height="12px" className="w-16" />
    </div>
  )
}

export function SkeletonRecommendationCard() {
  return (
    <div className="rounded-xl border border-white/10 bg-white/5 p-4 space-y-3">
      <div className="flex items-start justify-between">
        <div className="space-y-2 flex-1">
          <Skeleton height="20px" className="w-24" />
          <Skeleton height="16px" className="w-32" />
        </div>
        <Skeleton height="40px" className="w-16" />
      </div>
      <div className="grid grid-cols-3 gap-2">
        <Skeleton height="12px" />
        <Skeleton height="12px" />
        <Skeleton height="12px" />
      </div>
    </div>
  )
}

export function SkeletonParetoPanel() {
  return (
    <div className="rounded-xl border border-white/10 bg-white/5 p-4 space-y-4">
      <Skeleton height="20px" className="w-32" />
      <Skeleton height="40px" />
      <Skeleton height="16px" className="w-full" />
    </div>
  )
}

export default memo(Skeleton)
