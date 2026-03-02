import React, { useRef } from 'react'
import { motion } from 'framer-motion'

/**
 * Button with ripple effect on click
 */
export const RippleButton = React.forwardRef(({
  children,
  onClick,
  className,
  variant = 'primary',
  size = 'md',
  disabled = false,
  ...props
}, ref) => {
  const buttonRef = useRef(null)
  const [ripples, setRipples] = React.useState([])

  const createRipple = (e) => {
    if (disabled) return

    const button = buttonRef.current
    if (!button) return

    const rect = button.getBoundingClientRect()
    const size = Math.max(rect.width, rect.height)
    const x = e.clientX - rect.left - size / 2
    const y = e.clientY - rect.top - size / 2

    const ripple = {
      id: Date.now() + Math.random(),
      x,
      y,
      size
    }

    setRipples((prev) => [...prev, ripple])

    setTimeout(() => {
      setRipples((prev) => prev.filter((r) => r.id !== ripple.id))
    }, 600)
  }

  const handleClick = (e) => {
    createRipple(e)
    onClick?.(e)
  }

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg'
  }

  const variantClasses = {
    primary: 'bg-gradient-to-r from-cyan-500 to-emerald-500 text-white hover:shadow-lg hover:shadow-cyan-500/50',
    secondary: 'border border-white/20 text-white hover:border-white/50 hover:bg-white/10',
    danger: 'bg-rose-500/20 border border-rose-500/50 text-rose-300 hover:bg-rose-500/30',
    ghost: 'text-white hover:bg-white/5'
  }

  return (
    <motion.button
      ref={buttonRef}
      onClick={handleClick}
      disabled={disabled}
      whileHover={!disabled ? { scale: 1.02 } : {}}
      whileTap={!disabled ? { scale: 0.98 } : {}}
      className={`relative overflow-hidden rounded-lg font-medium transition-all duration-200 ${sizeClasses[size]} ${variantClasses[variant]} ${disabled ? 'opacity-50 cursor-not-allowed' : ''} ${className}`}
      {...props}
    >
      {ripples.map((ripple) => (
        <motion.span
          key={ripple.id}
          className="absolute rounded-full bg-white/30"
          initial={{
            width: 0,
            height: 0,
            x: ripple.x,
            y: ripple.y,
            opacity: 1
          }}
          animate={{
            width: ripple.size * 2,
            height: ripple.size * 2,
            x: ripple.x - ripple.size,
            y: ripple.y - ripple.size,
            opacity: 0
          }}
          transition={{
            duration: 0.6,
            ease: 'easeOut'
          }}
          pointerEvents="none"
        />
      ))}
      <span className="relative z-10">{children}</span>
    </motion.button>
  )
})

RippleButton.displayName = 'RippleButton'

/**
 * Loading shimmer skeleton
 */
export const ShimmerLoader = ({ width = 'w-full', height = 'h-8', className = '' }) => {
  return (
    <motion.div
      className={`${width} ${height} rounded-lg bg-gradient-to-r from-white/5 via-white/10 to-white/5 overflow-hidden ${className}`}
      animate={{
        backgroundPosition: ['200% 0', '-200% 0']
      }}
      transition={{
        duration: 2,
        repeat: Infinity,
        ease: 'linear'
      }}
      style={{
        backgroundSize: '200% 100%'
      }}
    />
  )
}

/**
 * Animated tooltip that fades in on hover
 */
export const Tooltip = ({ content, children, side = 'top' }) => {
  const [isVisible, setIsVisible] = React.useState(false)

  const positions = {
    top: 'bottom-full mb-2',
    bottom: 'top-full mt-2',
    left: 'right-full mr-2',
    right: 'left-full ml-2'
  }

  return (
    <div className="relative inline-block">
      <div
        onMouseEnter={() => setIsVisible(true)}
        onMouseLeave={() => setIsVisible(false)}
      >
        {children}
      </div>

      <motion.div
        initial={{ opacity: 0, scale: 0.9, y: -5 }}
        animate={isVisible ? { opacity: 1, scale: 1, y: 0 } : { opacity: 0, scale: 0.9 }}
        transition={{ duration: 0.2 }}
        className={`absolute whitespace-nowrap ${positions[side]} z-50 pointer-events-none`}
        style={{
          pointerEvents: isVisible ? 'auto' : 'none'
        }}
      >
        <div className="px-3 py-2 bg-slate-900 border border-white/20 rounded-lg text-xs text-white font-medium shadow-xl">
          {content}
          {/* Arrow */}
          <div
            className={`absolute w-2 h-2 bg-slate-900 border border-white/20 transform rotate-45 ${
              side === 'top' ? 'top-full left-1/2 -translate-x-1/2 -translate-y-1' :
              side === 'bottom' ? '-top-1 left-1/2 -translate-x-1/2 translate-y-0' :
              side === 'left' ? 'left-full top-1/2 -translate-y-1/2 -translate-x-1' :
              'right-full top-1/2 -translate-y-1/2 translate-x-0'
            }`}
          />
        </div>
      </motion.div>
    </div>
  )
}

/**
 * Skeleton screen with animating placeholders
 */
export const SkeletonLoader = ({ count = 3, variant = 'card' }) => {
  const cardVariant = {
    card: (
      <div key="skeleton-card" className="rounded-lg border border-white/10 p-6 space-y-4 bg-white/5">
        <ShimmerLoader height="h-6" className="w-3/4" />
        <div className="space-y-2">
          <ShimmerLoader height="h-4" />
          <ShimmerLoader height="h-4" className="w-5/6" />
        </div>
        <ShimmerLoader height="h-10" />
      </div>
    ),
    line: <ShimmerLoader key={`skeleton-line-${count}`} height="h-4" className="mb-3" />,
    table: (
      <div key="skeleton-table" className="space-y-3">
        {[...Array(count)].map((_, i) => (
          <div key={`skeleton-row-${i}`} className="flex gap-4">
            <ShimmerLoader width="w-12" height="h-8" />
            <ShimmerLoader width="flex-1" height="h-8" />
            <ShimmerLoader width="w-24" height="h-8" />
          </div>
        ))}
      </div>
    )
  }

  if (variant === 'card') {
    return (
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[...Array(count)].map((_, i) => (
          <div key={i} className="rounded-lg border border-white/10 p-6 space-y-4 bg-white/5">
            <ShimmerLoader height="h-6" className="w-3/4" />
            <div className="space-y-2">
              <ShimmerLoader height="h-4" />
              <ShimmerLoader height="h-4" className="w-5/6" />
            </div>
            <ShimmerLoader height="h-10" />
          </div>
        ))}
      </div>
    )
  }

  if (variant === 'line') {
    return (
      <div>
        {[...Array(count)].map((_, i) => (
          <ShimmerLoader key={i} height="h-4" className="mb-3 last:mb-0" />
        ))}
      </div>
    )
  }

  if (variant === 'table') {
    return cardVariant.table
  }

  return null
}

/**
 * Smooth number counter with optional formatting
 */
export const CounterAnimation = ({ 
  from = 0, 
  to, 
  duration = 1.5,
  format = (n) => n.toFixed(0),
  className = ''
}) => {
  const [count, setCount] = React.useState(from)
  const animationRef = React.useRef(null)

  React.useEffect(() => {
    const startValue = from
    const endValue = to
    const startTime = Date.now()

    const animate = () => {
      const elapsed = Date.now() - startTime
      const progress = Math.min(elapsed / (duration * 1000), 1)

      const current = startValue + (endValue - startValue) * progress
      setCount(current)

      if (progress < 1) {
        animationRef.current = requestAnimationFrame(animate)
      }
    }

    animationRef.current = requestAnimationFrame(animate)

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
    }
  }, [from, to, duration])

  return <span className={className}>{format(count)}</span>
}

/**
 * Attention-grabbing pulse effect
 */
export const PulseEffect = ({ children, color = 'emerald' }) => {
  const colorClasses = {
    emerald: 'shadow-emerald-500',
    cyan: 'shadow-cyan-500',
    amber: 'shadow-amber-500',
    rose: 'shadow-rose-500'
  }

  return (
    <motion.div
      animate={{ boxShadow: [
        `0 0 0 0 rgba(16, 185, 129, 0.7)`,
        `0 0 0 10px rgba(16, 185, 129, 0)`
      ]}}
      transition={{ duration: 2, repeat: Infinity }}
      className="inline-block"
    >
      {children}
    </motion.div>
  )
}

/**
 * Success checkmark animation
 */
export const SuccessCheckmark = () => {
  return (
    <motion.svg
      viewBox="0 0 50 50"
      className="w-12 h-12"
      initial={{ scale: 0 }}
      animate={{ scale: 1 }}
      transition={{ type: 'spring', delay: 0.2 }}
    >
      <motion.circle
        cx="25"
        cy="25"
        r="25"
        fill="none"
        stroke="#10b981"
        strokeWidth="2"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 0.5 }}
      />
      <motion.path
        d="M 15 25 L 22 32 L 35 19"
        fill="none"
        stroke="#10b981"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 0.5, delay: 0.2 }}
      />
    </motion.svg>
  )
}

/**
 * Loading spinner animation
 */
export const LoadingSpinner = ({ size = 'md', color = 'cyan' }) => {
  const sizeClasses = {
    sm: 'w-6 h-6 border-2',
    md: 'w-10 h-10 border-3',
    lg: 'w-14 h-14 border-4'
  }

  const colorClasses = {
    cyan: 'border-cyan-500/20 border-t-cyan-500',
    emerald: 'border-emerald-500/20 border-t-emerald-500',
    amber: 'border-amber-500/20 border-t-amber-500'
  }

  return (
    <motion.div
      className={`rounded-full ${sizeClasses[size]} ${colorClasses[color]}`}
      animate={{ rotate: 360 }}
      transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
    />
  )
}

export default {
  RippleButton,
  ShimmerLoader,
  Tooltip,
  SkeletonLoader,
  CounterAnimation,
  PulseEffect,
  SuccessCheckmark,
  LoadingSpinner
}
