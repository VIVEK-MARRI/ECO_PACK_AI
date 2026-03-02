import React, { memo, Suspense, useEffect, useMemo, useRef } from 'react'
import * as THREE from 'three'
import { Canvas, useFrame } from '@react-three/fiber'
import { ContactShadows, Environment, Html, OrbitControls } from '@react-three/drei'

function Loader() {
  return (
    <Html center>
      <div className="text-xs text-cyan-200">Loading 3D scene...</div>
    </Html>
  )
}

const riskColorMap = {
  low: '#10b981', // Emerald
  medium: '#f59e0b', // Amber
  high: '#ef4444' // Red
}

// Enhanced PackagingMesh with glow and idle animation
const PackagingMesh = memo(function PackagingMesh({ 
  dimensions, 
  riskLevel, 
  sustainabilityScore = 85,
  isSelected = false 
}) {
  const meshRef = useRef(null)
  const glowMeshRef = useRef(null)
  const targetScaleRef = useRef(new THREE.Vector3(1, 1, 1))
  const frameBucketRef = useRef(0)
  const timeRef = useRef(0)

  const baseColor = useMemo(() => riskColorMap[riskLevel] || riskColorMap.low, [riskLevel])

  useEffect(() => {
    const width = Math.max(0.7, dimensions.width)
    const height = Math.max(0.7, dimensions.height)
    const depth = Math.max(0.7, dimensions.depth)
    targetScaleRef.current = new THREE.Vector3(width, height, depth)
  }, [dimensions])

  useFrame((_, delta) => {
    if (!meshRef.current) return

    frameBucketRef.current += delta
    if (frameBucketRef.current < 1 / 55) return
    frameBucketRef.current = 0

    timeRef.current += delta

    // Smooth rotation with idle float animation
    meshRef.current.rotation.y += 0.009
    meshRef.current.rotation.x = Math.sin(timeRef.current * 0.3) * 0.05
    meshRef.current.position.y = Math.sin(timeRef.current * 0.5) * 0.1 // Floating motion

    // Scale lerp based on selection state
    const targetScale = isSelected ? 1.1 : 1
    meshRef.current.scale.lerp(targetScaleRef.current, 0.08)
    meshRef.current.scale.multiplyScalar(targetScale)

    // Update glow mesh
    if (glowMeshRef.current) {
      glowMeshRef.current.rotation.copy(meshRef.current.rotation)
      glowMeshRef.current.position.copy(meshRef.current.position)
      glowMeshRef.current.scale.copy(meshRef.current.scale).multiplyScalar(1.05)
    }
  })

  return (
    <>
      {/* Main box */}
      <mesh ref={meshRef} castShadow receiveShadow>
        <boxGeometry args={[1, 1, 1, 16, 16, 16]} />
        <meshStandardMaterial
          color={baseColor}
          roughness={0.2}
          metalness={0.6}
          emissive={baseColor}
          emissiveIntensity={0.2 + (sustainabilityScore / 100) * 0.4}
          envMapIntensity={1.2}
        />
      </mesh>

      {/* Glow outline */}
      <mesh ref={glowMeshRef} renderOrder={1}>
        <boxGeometry args={[1, 1, 1, 8, 8, 8]} />
        <meshStandardMaterial
          color={baseColor}
          transparent
          opacity={0.15}
          emissive={baseColor}
          emissiveIntensity={0.3}
          depthTest={false}
        />
      </mesh>
    </>
  )
})

// Enhanced reflective floor
const ReflectiveFloor = memo(function ReflectiveFloor() {
  return (
    <mesh position={[0, -1.5, 0]} rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
      <planeGeometry args={[10, 10]} />
      <meshStandardMaterial
        color="#0f172a"
        metalness={0.3}
        roughness={0.7}
        emissive="#0f172a"
        emissiveIntensity={0.1}
      />
    </mesh>
  )
})

function deriveDimensions(product) {
  const weight = Number(product?.weight || 1)
  const strength = Number(product?.strength || 50)
  const recyclability = Number(product?.recyclability || 50)

  const width = 0.9 + Math.min(weight / 8, 1.8)
  const height = 0.8 + (100 - strength) / 120
  const depth = 0.8 + recyclability / 120

  return {
    width,
    height,
    depth
  }
}

function deriveRiskLevel(risk) {
  if (risk >= 65) return 'high'
  if (risk >= 35) return 'medium'
  return 'low'
}

function Packaging3D({ product, damageRisk = 20, sustainabilityScore = 85, isSelected = false }) {
  const glRef = useRef(null)
  const cameraRef = useRef(null)
  const controlsRef = useRef(null)

  const dimensions = useMemo(() => deriveDimensions(product), [product])
  const riskLevel = useMemo(() => deriveRiskLevel(damageRisk), [damageRisk])

  useEffect(() => {
    return () => {
      if (glRef.current) {
        glRef.current.dispose()
        if (typeof glRef.current.forceContextLoss === 'function') {
          glRef.current.forceContextLoss()
        }
      }
    }
  }, [])

  // Smooth camera easing on selection
  useEffect(() => {
    if (cameraRef.current && controlsRef.current) {
      const targetDistance = isSelected ? 3 : 4.5
      controlsRef.current.maxDistance = targetDistance
    }
  }, [isSelected])

  return (
    <div className="h-72 w-full rounded-2xl overflow-hidden relative group bg-gradient-to-br from-slate-900/80 via-slate-900/60 to-emerald-950/40 ring-1 ring-white/10">
      {/* Glow background effect */}
      <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500">
        <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/10 to-blue-500/10 blur-xl"></div>
      </div>

      <Canvas
        shadows
        camera={{ fov: 45, position: [3, 2.6, 3.5] }}
        ref={cameraRef}
        onCreated={({ gl }) => {
          glRef.current = gl
          gl.setPixelRatio(Math.min(window.devicePixelRatio, 1.5))
          gl.setClearColor('#020617', 0.8)
          gl.outputColorSpace = THREE.SRGBColorSpace
          gl.toneMapping = THREE.ACESFilmicToneMapping
          gl.toneMappingExposure = 0.8
        }}
      >
        {/* Enhanced Lighting Setup */}
        <ambientLight intensity={0.6} color="#ffffff" />
        
        {/* Main directional light */}
        <directionalLight 
          position={[5, 8, 4]} 
          intensity={1.2} 
          castShadow 
          shadow-mapSize-width={2048}
          shadow-mapSize-height={2048}
          shadow-camera-left={-10}
          shadow-camera-right={10}
          shadow-camera-top={10}
          shadow-camera-bottom={-10}
        />
        
        {/* Accent point lights */}
        <pointLight position={[3, 2, 0]} intensity={0.5} color="#10b981" />
        <pointLight position={[-3, 2, 0]} intensity={0.5} color="#0ea5e9" />
        <pointLight position={[0, -1, 3]} intensity={0.3} color="#10b981" />

        {/* Rim light for depth */}
        <directionalLight 
          position={[-4, 3, -5]} 
          intensity={0.6} 
          color="#0ea5e9" 
        />

        <Suspense fallback={<Loader />}>
          <ReflectiveFloor />
          <PackagingMesh 
            dimensions={dimensions} 
            riskLevel={riskLevel} 
            sustainabilityScore={sustainabilityScore}
            isSelected={isSelected}
          />
          <ContactShadows 
            position={[0, -1.5, 0]} 
            opacity={0.4} 
            blur={2.5} 
            far={5}
            scale={6}
          />
          <Environment preset="night" background={false} intensity={0.4} />
        </Suspense>

        <OrbitControls
          ref={controlsRef}
          enablePan={false}
          enableZoom={true}
          minDistance={2.4}
          maxDistance={6}
          maxPolarAngle={Math.PI / 2.1}
          dampingFactor={0.1}
          enableDamping
          autoRotate
          autoRotateSpeed={2}
        />
      </Canvas>

      {/* Info overlay */}
      <div className="absolute bottom-3 left-3 text-xs text-white/60 opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none">
        <div className="font-medium text-white/80">{riskLevel.toUpperCase()} RISK</div>
        <div>Score: {sustainabilityScore}%</div>
      </div>
    </div>
  )
}

export default memo(Packaging3D)
