import React from 'react'

export default function ScoreRing({ score, label, color = 'green' }) {
  const circumference = 2 * Math.PI * 45
  const offset = circumference - (score / 100) * circumference
  
  const colorMap = {
    green: { bg: 'from-green-500 to-emerald-600', text: 'text-green-600' },
    amber: { bg: 'from-amber-500 to-orange-600', text: 'text-amber-600' },
    red: { bg: 'from-red-500 to-rose-600', text: 'text-red-600' },
  }
  
  const colors = colorMap[color] || colorMap.green

  return (
    <div className="flex flex-col items-center">
      <div className="relative w-32 h-32">
        <svg className="w-full h-full transform -rotate-90">
          <circle cx="64" cy="64" r="45" fill="none" stroke="#e2e8f0" strokeWidth="8" />
          <circle
            cx="64"
            cy="64"
            r="45"
            fill="none"
            stroke="url(#gradient)"
            strokeWidth="8"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            className="transition-all duration-500"
          />
          <defs>
            <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor={color === 'green' ? '#10b981' : color === 'amber' ? '#f59e0b' : '#ef4444'} />
              <stop offset="100%" stopColor={color === 'green' ? '#059669' : color === 'amber' ? '#d97706' : '#dc2626'} />
            </linearGradient>
          </defs>
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center">
            <div className={`text-3xl font-bold ${colors.text}`}>{Math.round(score)}</div>
            <div className="text-xs text-slate-500">out of 100</div>
          </div>
        </div>
      </div>
      <p className="mt-4 text-center text-sm font-medium text-slate-700">{label}</p>
    </div>
  )
}
