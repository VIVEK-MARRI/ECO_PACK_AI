import React, { memo } from 'react'
import { motion } from 'framer-motion'

function ParetoSlider({ value, onChange }) {
  const normalized = Math.min(100, Math.max(0, value))

  return (
    <div className="rounded-xl border border-white/10 bg-white/5 p-4 backdrop-blur-xl">
      <div className="mb-3 flex items-center justify-between text-xs text-slate-300">
        <span>Cost Focus</span>
        <span>Eco Focus</span>
      </div>

      <div className="relative h-8">
        <div className="absolute top-1/2 h-2 w-full -translate-y-1/2 rounded-full bg-slate-700/70" />
        <motion.div
          className="absolute top-1/2 h-2 -translate-y-1/2 rounded-full bg-gradient-to-r from-cyan-500 to-emerald-400"
          animate={{ width: `${normalized}%` }}
          transition={{ type: 'spring', stiffness: 240, damping: 24 }}
        />
        <motion.div
          className="absolute top-1/2 h-5 w-5 -translate-y-1/2 rounded-full border border-white/50 bg-white shadow-lg shadow-cyan-500/30"
          animate={{ left: `calc(${normalized}% - 10px)` }}
          transition={{ type: 'spring', stiffness: 280, damping: 22 }}
        />
        <input
          type="range"
          min="0"
          max="100"
          value={normalized}
          onChange={(event) => onChange(Number(event.target.value))}
          className="absolute inset-0 h-full w-full cursor-pointer opacity-0"
          aria-label="Pareto optimization focus"
        />
      </div>

      <p className="mt-2 text-xs text-slate-400">Pareto Focus: {normalized}% sustainability bias</p>
    </div>
  )
}

export default memo(ParetoSlider)
