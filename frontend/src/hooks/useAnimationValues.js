import { useEffect, useRef, useState } from 'react'
import { useMotionValue, useTransform, animate } from 'framer-motion'

/**
 * Hook to animate a number from 0 to target value
 * @param {number} target - Target number to count to
 * @param {number} duration - Animation duration in seconds (default 2)
 * @param {boolean} enabled - Whether animation should run (default true)
 */
export const useAnimationCounter = (target, duration = 2, enabled = true) => {
  const ref = useRef(null)
  const [displayValue, setDisplayValue] = useState(0)

  useEffect(() => {
    if (!enabled || !target) return

    const updateCount = () => {
      let current = 0
      const increment = target / (duration * 60) // 60 FPS
      const interval = setInterval(() => {
        current += increment
        if (current >= target) {
          setDisplayValue(Math.round(target))
          clearInterval(interval)
        } else {
          setDisplayValue(Math.round(current))
        }
      }, 1000 / 60)

      return () => clearInterval(interval)
    }

    const cleanup = updateCount()
    return cleanup
  }, [target, duration, enabled])

  return displayValue
}

/**
 * Hook to smoothly animate between two values using Framer Motion
 * @param {number} initial - Initial value
 * @param {number} target - Target value
 * @param {number} duration - Animation duration in seconds (default 1)
 */
export const useSpringValue = (initial, target, duration = 1) => {
  const motionValue = useMotionValue(initial)
  const displayValue = useTransform(motionValue, (value) =>
    Math.round(value * 10) / 10
  )

  useEffect(() => {
    animate(motionValue, target, {
      duration: duration,
      ease: 'easeInOut'
    })
  }, [target, motionValue, duration])

  return displayValue
}

/**
 * Hook for 3D hover tilt effect
 * @param {React.RefObject} ref - Ref to element
 * @param {number} intensity - Tilt intensity (default 10)
 */
export const useHoverTilt = (intensity = 10) => {
  const ref = useRef(null)
  const [tilt, setTilt] = useState({ x: 0, y: 0 })

  useEffect(() => {
    const element = ref.current
    if (!element) return

    const handleMouseMove = (e) => {
      const rect = element.getBoundingClientRect()
      const x = e.clientX - rect.left
      const y = e.clientY - rect.top

      // Calculate tilt based on mouse position
      const centerX = rect.width / 2
      const centerY = rect.height / 2

      const rotateX = ((y - centerY) / centerY) * intensity
      const rotateY = -((x - centerX) / centerX) * intensity

      setTilt({ x: rotateX, y: rotateY })
    }

    const handleMouseLeave = () => {
      setTilt({ x: 0, y: 0 })
    }

    element.addEventListener('mousemove', handleMouseMove)
    element.addEventListener('mouseleave', handleMouseLeave)

    return () => {
      element.removeEventListener('mousemove', handleMouseMove)
      element.removeEventListener('mouseleave', handleMouseLeave)
    }
  }, [intensity])

  return { ref, tilt }
}

/**
 * Hook to detect if element is in viewport
 * @param {React.RefObject} ref - Ref to element
 * @param {number} threshold - Visibility threshold (0-1, default 0.1)
 */
export const useElementInViewport = (threshold = 0.1) => {
  const ref = useRef(null)
  const [isInView, setIsInView] = useState(false)

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsInView(true)
          observer.unobserve(entry.target)
        }
      },
      { threshold }
    )

    if (ref.current) {
      observer.observe(ref.current)
    }

    return () => {
      if (ref.current) {
        observer.unobserve(ref.current)
      }
    }
  }, [threshold])

  return { ref, isInView }
}

/**
 * Hook for smooth scroll-triggered counter animation
 * @param {number} target - Target count value
 * @param {number} duration - Animation duration in seconds
 */
export const useScrollCounter = (target, duration = 2) => {
  const { ref, isInView } = useElementInViewport(0.2)
  const displayValue = useAnimationCounter(target, duration, isInView)

  return { ref, displayValue }
}

/**
 * Hook for animated background glow effect
 * @param {number} duration - Animation duration (default 3)
 */
export const useGlowAnimation = (duration = 3) => {
  const opacity = useMotionValue(0.1)

  useEffect(() => {
    animate(
      opacity,
      [0.1, 0.2, 0.1],
      {
        duration: duration,
        repeat: Infinity,
        ease: 'easeInOut'
      }
    )
  }, [opacity, duration])

  return { opacity }
}

/**
 * Hook for ripple effect on button click
 * @param {React.RefObject} ref - Ref to button element
 */
export const useRippleEffect = () => {
  const ref = useRef(null)
  const [ripples, setRipples] = useState([])

  const createRipple = (e) => {
    const button = ref.current
    if (!button) return

    const rect = button.getBoundingClientRect()
    const size = Math.max(rect.width, rect.height)
    const x = e.clientX - rect.left - size / 2
    const y = e.clientY - rect.top - size / 2

    const ripple = {
      id: Date.now(),
      x,
      y,
      size
    }

    setRipples((prev) => [...prev, ripple])

    setTimeout(() => {
      setRipples((prev) => prev.filter((r) => r.id !== ripple.id))
    }, 600)
  }

  return { ref, ripples, createRipple }
}

export default {
  useAnimationCounter,
  useSpringValue,
  useHoverTilt,
  useElementInViewport,
  useScrollCounter,
  useGlowAnimation,
  useRippleEffect
}
