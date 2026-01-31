import React from 'react'

export default function Card({ children, className = '' }) {
  return (
    <div className={`bg-white rounded-xl shadow-md border border-slate-100 ${className}`}>
      {children}
    </div>
  )
}
