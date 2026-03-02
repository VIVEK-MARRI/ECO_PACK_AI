import React, { memo } from 'react'
import { motion } from 'framer-motion'

function CarbonIntensityIndicator({ co2 = 0.2 }) {
  const normalized = Math.max(0, Math.min(1, Number(co2) / 1.2))
  const score = (1 - normalized) * 100

  const color = score >= 70 ? 'from-emerald-500 to-green-400' : score >= 40 ? 'from-amber-500 to-yellow-400' : 'from-rose-500 to-red-400'

  return (
    <div className="rounded-xl border border-white/10 bg-white/5 p-4 backdrop-blur-xl">
      <div className="mb-2 flex items-center justify-between text-xs text-slate-300">
        <span>Carbon Intensity</span>
        <span>{co2.toFixed(2)} kg CO2</span>
      </div>
      <div className="h-3 overflow-hidden rounded-full bg-slate-700/80">
        <motion.div
          className={`h-full bg-gradient-to-r ${color}`}
          animate={{ width: `${score}%` }}
          transition={{ duration: 0.7, ease: 'easeOut' }}
        />
      </div>
      <motion.div
        className="mt-2 text-xs text-slate-400"
        animate={{ opacity: [0.5, 1, 0.5] }}
        transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
      >
        Sustainability pulse active
      </motion.div>
    </div>
  )
}

export default memo(CarbonIntensityIndicator)
