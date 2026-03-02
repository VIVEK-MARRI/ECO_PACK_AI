import React, { memo, useState, useEffect } from 'react'
import { motion } from 'framer-motion'

function TopBar({ onSidebarToggle }) {
  const [systemStatus, setSystemStatus] = useState('operational')
  const [apiLatency, setApiLatency] = useState(45)
  const [driftStatus, setDriftStatus] = useState('stable')

  // Simulate status updates
  useEffect(() => {
    const interval = setInterval(() => {
      setApiLatency(Math.floor(Math.random() * 80 + 20))
    }, 5000)
    return () => clearInterval(interval)
  }, [])

  const getStatusColor = (status) => {
    switch (status) {
      case 'operational':
        return 'text-emerald-400'
      case 'degraded':
        return 'text-amber-400'
      case 'offline':
        return 'text-rose-400'
      default:
        return 'text-slate-400'
    }
  }

  const getLatencyColor = (latency) => {
    if (latency < 50) return 'text-emerald-400'
    if (latency < 100) return 'text-amber-400'
    return 'text-rose-400'
  }

  return (
    <header className="h-16 border-b border-white/5 bg-slate-900/50 backdrop-blur-xl flex items-center justify-between px-6 sticky top-0 z-40 shadow-lg">
      {/* Left: Menu Toggle */}
      <div className="flex items-center gap-4">
        <button
          onClick={onSidebarToggle}
          className="p-2 hover:bg-white/5 rounded-lg transition text-slate-400 hover:text-slate-200"
          aria-label="Toggle sidebar"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
        <div className="h-8 w-px bg-white/10" />
        <h2 className="text-sm font-semibold text-slate-200">ECO_PACK_AI Dashboard</h2>
      </div>

      {/* Right: Status Indicators & User */}
      <div className="flex items-center gap-6">
        {/* System Status */}
        <motion.div
          className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/5 border border-white/10"
          whileHover={{ bg: 'rgba(255, 255, 255, 0.08)' }}
        >
          <motion.div
            className="w-2 h-2 rounded-full bg-emerald-400"
            animate={{ scale: [1, 1.2, 1] }}
            transition={{ duration: 2, repeat: Infinity }}
          />
          <span className={`text-xs font-medium ${getStatusColor(systemStatus)}`}>
            {systemStatus.charAt(0).toUpperCase() + systemStatus.slice(1)}
          </span>
        </motion.div>

        {/* API Latency */}
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/5 border border-white/10">
          <span className="text-xs text-slate-400">API</span>
          <span className={`text-xs font-mono font-medium ${getLatencyColor(apiLatency)}`}>{apiLatency}ms</span>
        </div>

        {/* Drift Status */}
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/5 border border-white/10">
          <span className="text-xs text-slate-400">Drift</span>
          <span className={`text-xs font-medium ${driftStatus === 'stable' ? 'text-emerald-400' : 'text-amber-400'}`}>
            {driftStatus.charAt(0).toUpperCase() + driftStatus.slice(1)}
          </span>
        </div>

        {/* Divider */}
        <div className="h-6 w-px bg-white/10" />

        {/* User Avatar */}
        <button className="w-8 h-8 rounded-lg bg-gradient-to-br from-cyan-500 to-emerald-500 flex items-center justify-center text-sm font-bold text-white hover:shadow-lg hover:shadow-cyan-500/30 transition">
          👤
        </button>
      </div>
    </header>
  )
}

export default memo(TopBar)
