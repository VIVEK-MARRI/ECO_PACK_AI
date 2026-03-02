import React, { memo } from 'react'
import { motion } from 'framer-motion'
import { useNavigate, useLocation } from 'react-router-dom'

function Sidebar({ isOpen, onToggle }) {
  const navigate = useNavigate()
  const location = useLocation()

  const menuItems = [
    { name: 'Dashboard', icon: '📊', path: '/', id: 'dashboard' },
    { name: 'Simulation', icon: '🧪', path: '/simulation', id: 'simulation' },
    { name: 'Analytics', icon: '📈', path: '/analytics', id: 'analytics' },
    { name: 'Sustainability', icon: '🌱', path: '/sustainability', id: 'sustainability' },
    { name: 'History', icon: '⏱️', path: '/history', id: 'history' },
    { name: 'Settings', icon: '⚙️', path: '/settings', id: 'settings' }
  ]

  const isActive = (path) => location.pathname === path

  return (
    <motion.aside
      initial={{ x: -300 }}
      animate={{ x: isOpen ? 0 : -300 }}
      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      className="fixed left-0 top-0 h-screen w-64 bg-gradient-to-b from-slate-900 to-slate-950 border-r border-white/5 flex flex-col z-50"
    >
      {/* Logo Section */}
      <div className="p-6 border-b border-white/5">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-cyan-500 to-emerald-500 flex items-center justify-center text-lg font-bold">
            🌿
          </div>
          <div>
            <h1 className="text-lg font-bold text-white">ECO_PACK</h1>
            <p className="text-xs text-slate-400">AI Optimizer</p>
          </div>
        </div>
      </div>

      {/* Navigation Menu */}
      <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto">
        {menuItems.map((item) => (
          <motion.button
            key={item.id}
            onClick={() => navigate(item.path)}
            whileHover={{ x: 4 }}
            whileTap={{ scale: 0.98 }}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
              isActive(item.path)
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-white/5 border border-transparent'
            }`}
          >
            <span className="text-lg">{item.icon}</span>
            <span className="font-medium">{item.name}</span>
            {isActive(item.path) && (
              <motion.div
                layoutId="active-indicator"
                className="ml-auto w-2 h-2 rounded-full bg-cyan-400"
                transition={{ type: 'spring', stiffness: 300, damping: 30 }}
              />
            )}
          </motion.button>
        ))}
      </nav>

      {/* Profile Section */}
      <div className="p-4 border-t border-white/5 space-y-4">
        <div className="px-4 py-3 bg-white/5 rounded-lg border border-white/10">
          <p className="text-xs text-slate-400">Logged in as</p>
          <p className="text-sm font-semibold text-white mt-1">Demo User</p>
        </div>
        <button className="w-full px-4 py-2 text-sm font-medium text-slate-400 hover:text-slate-200 transition">
          Sign Out
        </button>
      </div>
    </motion.aside>
  )
}

export default memo(Sidebar)
