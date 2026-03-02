import React, { memo, useEffect, useMemo, useRef, useState } from 'react'
import { animate, motion, useInView } from 'framer-motion'

function AnimatedValue({ value, decimals = 0, prefix = '', suffix = '' }) {
  const [displayValue, setDisplayValue] = useState(0)
  const previousValueRef = useRef(0)
  const numericValue = Number(value) || 0

  useEffect(() => {
    const startValue = +previousValueRef.current
    const endValue = +numericValue

    if (!isFinite(startValue) || !isFinite(endValue)) {
      setDisplayValue(0)
      return
    }

    const controls = animate(startValue, endValue, {
      duration: 1.2,
      ease: [0.25, 0.46, 0.45, 0.94], // Custom easing curve
      onUpdate: (latest) => setDisplayValue(Number(latest))
    })

    previousValueRef.current = endValue

    return () => controls.stop()
  }, [numericValue])

  const roundedValue = Number(displayValue) || 0
  return (
    <span>
      {prefix}
      {roundedValue.toFixed(decimals)}
      {suffix}
    </span>
  )
}

function AnimatedKPI({ 
  label, 
  value, 
  prefix, 
  suffix, 
  decimals = 0, 
  colorClass = 'text-cyan-300',
  index = 0,
  maxValue = null,
  showProgress = false
}) {
  const ref = useRef(null)
  const isInView = useInView(ref, { once: true, margin: '0px 0px -100px 0px' })
  const [tilt, setTilt] = useState({ x: 0, y: 0 })

  const cardGlow = useMemo(() => {
    if (colorClass.includes('emerald')) return 'from-emerald-500/20 to-emerald-500/5 shadow-emerald-500/20'
    if (colorClass.includes('amber')) return 'from-amber-500/20 to-amber-500/5 shadow-amber-500/20'
    if (colorClass.includes('rose')) return 'from-rose-500/20 to-rose-500/5 shadow-rose-500/20'
    return 'from-cyan-500/20 to-cyan-500/5 shadow-cyan-500/20'
  }, [colorClass])

  const glowColor = useMemo(() => {
    if (colorClass.includes('emerald')) return '#10b981'
    if (colorClass.includes('amber')) return '#f59e0b'
    if (colorClass.includes('rose')) return '#f43f5e'
    return '#06b6d4'
  }, [colorClass])

  const progressValue = useMemo(() => {
    if (!maxValue) return 0
    return Math.min((Number(value) / maxValue) * 100, 100)
  }, [value, maxValue])

  // Hover tilt effect
  const handleMouseMove = (e) => {
    if (!ref.current) return
    const rect = ref.current.getBoundingClientRect()
    const x = (e.clientY - rect.top - rect.height / 2) / 20
    const y = -(e.clientX - rect.left - rect.width / 2) / 20
    setTilt({ x, y })
  }

  const handleMouseLeave = () => {
    setTilt({ x: 0, y: 0 })
  }

  return (
    <motion.div
      ref={ref}
      layout
      initial={{ opacity: 0, y: 20, scale: 0.9 }}
      animate={isInView ? { opacity: 1, y: 0, scale: 1 } : {}}
      transition={{ 
        duration: 0.6, 
        delay: index * 0.1,
        ease: [0.34, 1.56, 0.64, 1]
      }}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      style={{
        rotateX: tilt.x,
        rotateY: tilt.y,
        perspective: 1000
      }}
      whileHover={{ 
        y: -6,
        scale: 1.03,
        boxShadow: `0 20px 40px rgba(0, 0, 0, 0.3)`
      }}
      className={`group relative rounded-xl border border-white/10 bg-gradient-to-br ${cardGlow} p-6 backdrop-blur-xl overflow-hidden cursor-pointer`}
    >
      {/* Animated background glow */}
      <motion.div
        className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500"
        initial={{ opacity: 0 }}
        whileHover={{ opacity: 0.1 }}
      >
        <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent blur-2xl"></div>
      </motion.div>

      {/* Glow orb effect */}
      <motion.div
        className="absolute -top-1/2 -right-1/2 w-96 h-96 rounded-full opacity-0 group-hover:opacity-30 transition-opacity duration-500 blur-3xl pointer-events-none"
        style={{ backgroundColor: glowColor }}
        animate={{ y: [0, 20, 0] }}
        transition={{ duration: 4, repeat: Infinity }}
      />

      {/* Content */}
      <div className="relative z-10">
        <div className="flex items-start justify-between mb-3">
          <p className="text-xs uppercase tracking-widest font-semibold text-slate-400 group-hover:text-slate-300 transition">
            {label}
          </p>
          {isInView && (
            <motion.span 
              className="text-xl"
              animate={{ scale: [1, 1.2, 1] }}
              transition={{ duration: 0.6 }}
            >
              ✓
            </motion.span>
          )}
        </div>

        <p className={`text-3xl font-bold ${colorClass} group-hover:scale-110 transition-transform duration-300 origin-left`}>
          <AnimatedValue 
            value={isInView ? value : 0} 
            prefix={prefix} 
            suffix={suffix} 
            decimals={decimals} 
          />
        </p>

        {/* Progress bar */}
        {showProgress && maxValue && (
          <motion.div className="mt-4 h-1.5 bg-white/5 rounded-full overflow-hidden border border-white/10">
            <motion.div
              initial={{ width: '0%' }}
              animate={isInView ? { width: `${progressValue}%` } : {}}
              transition={{ duration: 1.5, delay: index * 0.1 + 0.3 }}
              className={`h-full rounded-full bg-gradient-to-r ${
                colorClass.includes('emerald') ? 'from-emerald-400 to-emerald-500' :
                colorClass.includes('amber') ? 'from-amber-400 to-amber-500' :
                colorClass.includes('rose') ? 'from-rose-400 to-rose-500' :
                'from-cyan-400 to-cyan-500'
              }`}
            />
          </motion.div>
        )}
      </div>

      {/* Border glow effect on hover */}
      <motion.div
        className="absolute inset-0 rounded-xl pointer-events-none"
        initial={{ boxShadow: `inset 0 0 0 1px rgba(255, 255, 255, 0.1)` }}
        whileHover={{ boxShadow: `inset 0 0 20px 0 ${glowColor}20` }}
        transition={{ duration: 0.3 }}
      />
    </motion.div>
  )
}

export default memo(AnimatedKPI)
