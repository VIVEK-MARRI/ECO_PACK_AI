import React from 'react'

export default function Navbar({ currentPage, onPageChange }) {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: '🏠' },
    { id: 'product', label: 'New Product', icon: '📦' },
    { id: 'history', label: 'History', icon: '📋' },
  ]

  return (
    <nav className="fixed top-0 left-0 right-0 bg-white border-b border-slate-200 shadow-sm z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-20">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-green-500 to-emerald-600 rounded-lg flex items-center justify-center">
              <span className="text-white text-lg font-bold">🌿</span>
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900">ECO PACK AI</h1>
              <p className="text-xs text-slate-500">Smart Packaging Solutions</p>
            </div>
          </div>

          {/* Navigation */}
          <div className="hidden md:flex items-center gap-1">
            {navItems.map(item => (
              <button
                key={item.id}
                onClick={() => onPageChange(item.id)}
                className={`px-4 py-2 rounded-lg font-medium transition-all duration-300 flex items-center gap-2 ${
                  currentPage === item.id
                    ? 'bg-gradient-to-r from-green-500 to-emerald-600 text-white shadow-md'
                    : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                <span>{item.icon}</span>
                <span>{item.label}</span>
              </button>
            ))}
          </div>

          {/* Mobile Menu */}
          <div className="md:hidden flex items-center gap-2">
            {navItems.map(item => (
              <button
                key={item.id}
                onClick={() => onPageChange(item.id)}
                className={`p-2 rounded-lg transition-all duration-300 ${
                  currentPage === item.id
                    ? 'bg-green-500 text-white'
                    : 'text-slate-600 hover:bg-slate-100'
                }`}
                title={item.label}
              >
                <span className="text-lg">{item.icon}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </nav>
  )
}
