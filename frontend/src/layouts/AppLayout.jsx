import React, { useState } from 'react'
import { motion } from 'framer-motion'
import Sidebar from '../components/Sidebar'
import TopBar from '../components/TopBar'

export default function AppLayout({ children }) {
  const [sidebarOpen, setSidebarOpen] = useState(true)

  return (
    <div className="h-screen bg-slate-950 text-slate-100 flex">
      {/* Animated Background Gradient */}
      <div className="fixed inset-0 -z-10 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-slate-900 via-slate-950 to-slate-900" />
        <motion.div
          className="absolute -top-40 -right-40 w-80 h-80 bg-cyan-500/10 rounded-full blur-3xl"
          animate={{
            y: [0, -20, 0],
            x: [0, 10, 0]
          }}
          transition={{ duration: 8, repeat: Infinity }}
        />
        <motion.div
          className="absolute -bottom-40 -left-40 w-80 h-80 bg-emerald-500/10 rounded-full blur-3xl"
          animate={{
            y: [0, 20, 0],
            x: [0, -10, 0]
          }}
          transition={{ duration: 10, repeat: Infinity }}
        />
      </div>

      {/* Sidebar */}
      <Sidebar isOpen={sidebarOpen} onToggle={setSidebarOpen} />

      {/* Main Content - adjusts with sidebar */}
      <div className={`flex flex-col flex-1 transition-all duration-300 ${sidebarOpen ? 'ml-64' : 'ml-0'}`}>
        {/* Top Navigation */}
        <TopBar onSidebarToggle={() => setSidebarOpen(!sidebarOpen)} />

        {/* Content Area */}
        <main className="flex-1 overflow-auto p-8">
          <div className="max-w-7xl mx-auto">{children}</div>
        </main>
      </div>
    </div>
  )
}
