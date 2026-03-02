import React, { useEffect, useRef, Suspense, lazy } from 'react';
import { motion } from 'framer-motion';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, PerspectiveCamera } from '@react-three/drei';
import * as THREE from 'three';
import { useNavigate } from 'react-router-dom';
import Footer from '../components/Footer';

// Animated 3D Package Box
function AnimatedPackageBox() {
  const meshRef = useRef();

  useEffect(() => {
    if (!meshRef.current) return;

    const animate = () => {
      if (meshRef.current) {
        meshRef.current.rotation.x += 0.002;
        meshRef.current.rotation.y += 0.003;
        meshRef.current.position.y = Math.sin(Date.now() * 0.0005) * 0.3;
      }
      requestAnimationFrame(animate);
    };
    animate();
  }, []);

  return (
    <>
      {/* Lights */}
      <ambientLight intensity={0.7} />
      <directionalLight position={[10, 10, 8]} intensity={1.2} castShadow />
      <pointLight position={[-10, 5, 10]} intensity={0.5} color="#00ff88" />
      <pointLight position={[10, 5, -10]} intensity={0.5} color="#00d4ff" />

      {/* Package Box */}
      <mesh ref={meshRef} castShadow receiveShadow>
        <boxGeometry args={[2, 2, 2]} />
        <meshPhongMaterial
          color="#1e3a5f"
          shininess={100}
          wireframe={false}
        />
      </mesh>

      {/* Decorative Spheres */}
      <mesh position={[3, 0, 0]} castShadow>
        <sphereGeometry args={[0.4, 32, 32]} />
        <meshPhongMaterial
          color="#00ff88"
          emissive="#00cc66"
          emissiveIntensity={0.3}
        />
      </mesh>
      <mesh position={[-3, 0, 0]} castShadow>
        <sphereGeometry args={[0.4, 32, 32]} />
        <meshPhongMaterial
          color="#00d4ff"
          emissive="#0099cc"
          emissiveIntensity={0.3}
        />
      </mesh>

      {/* Reflective Floor */}
      <mesh position={[0, -2.5, 0]} rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
        <planeGeometry args={[20, 20]} />
        <meshStandardMaterial
          color="#0a1628"
          metalness={0.3}
          roughness={0.7}
        />
      </mesh>

      {/* Camera & Controls */}
      <PerspectiveCamera makeDefault position={[5, 3, 5]} fov={50} />
      <OrbitControls
        autoRotate
        autoRotateSpeed={2}
        enableZoom={false}
        enablePan={false}
      />
    </>
  );
}

// Counter Animation Component
function AnimatedCounter({ end, duration = 2 }) {
  const [count, setCount] = React.useState(0);

  useEffect(() => {
    let startTime = null;
    const animate = (timestamp) => {
      if (!startTime) startTime = timestamp;
      const progress = (timestamp - startTime) / (duration * 1000);

      if (progress < 1) {
        setCount(Math.floor(end * progress));
        requestAnimationFrame(animate);
      } else {
        setCount(end);
      }
    };

    requestAnimationFrame(animate);
  }, [end, duration]);

  return <span>{count}</span>;
}

// Feature Card with Glassmorphism
function FeatureCard({ icon, title, description, index }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1, duration: 0.6 }}
      viewport={{ once: true }}
      className="relative p-8 rounded-2xl backdrop-blur-xl bg-gradient-to-br from-white/5 to-white/[2%] border border-white/10 hover:border-emerald-500/50 transition-all duration-300 group cursor-pointer overflow-hidden"
      whileHover={{ y: -5 }}
    >
      {/* Hover glow background */}
      <motion.div
        className="absolute inset-0 bg-gradient-to-r from-emerald-500/20 to-blue-500/20 opacity-0 blur-xl"
        whileHover={{ opacity: 1 }}
        transition={{ duration: 0.3 }}
      />
      
      <div className="relative z-10 space-y-3">
        <div className="text-5xl transform group-hover:scale-125 transition-transform duration-300">
          {icon}
        </div>
        <h3 className="text-lg font-semibold text-white leading-snug">{title}</h3>
        <p className="text-gray-400 text-sm leading-relaxed">{description}</p>
      </div>
    </motion.div>
  );
}

// Stat Card with Number Highlight
function StatCard({ label, value, unit, index }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      whileInView={{ opacity: 1, scale: 1 }}
      transition={{ delay: index * 0.15, duration: 0.5 }}
      viewport={{ once: true }}
      className="relative p-8 rounded-2xl backdrop-blur-lg bg-gradient-to-br from-emerald-500/10 to-blue-500/10 border border-white/10 text-center group hover:border-emerald-500/50 transition-all duration-300 overflow-hidden"
      whileHover={{ scale: 1.05 }}
    >
      {/* Animated glow background */}
      <motion.div
        className="absolute inset-0 rounded-2xl bg-gradient-to-r from-emerald-500/20 to-blue-500/20 opacity-0"
        whileHover={{ opacity: 1 }}
        transition={{ duration: 0.3 }}
      />

      <div className="relative z-10">
        <div className="text-5xl font-bold bg-gradient-to-r from-emerald-400 to-blue-400 bg-clip-text text-transparent mb-2 transform group-hover:scale-110 transition-transform duration-300">
          <AnimatedCounter end={parseInt(value)} />
          <span className="text-2xl">{unit}</span>
        </div>
        <p className="text-gray-400 text-sm font-medium tracking-wide">{label}</p>
      </div>

      <motion.div
        className="absolute inset-0 rounded-2xl bg-gradient-to-r from-emerald-500 to-blue-500 opacity-0 blur"
        animate={{
          opacity: [0.05, 0.1, 0.05],
        }}
        transition={{
          duration: 3,
          repeat: Infinity,
        }}
      />
    </motion.div>
  );
}

export default function Landing() {
  const navigate = useNavigate();
  const containerRef = useRef(null);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-slate-950 overflow-hidden">
      {/* Animated Grid Background */}
      <div className="fixed inset-0 opacity-20 pointer-events-none">
        <div className="absolute inset-0 bg-[linear-gradient(90deg,rgba(0,255,136,0.03)_1px,transparent_1px),linear-gradient(rgba(0,212,255,0.03)_1px,transparent_1px)] bg-[size:50px_50px]" />
      </div>

      {/* Navigation Bar */}
      <motion.nav
        initial={{ y: -100 }}
        animate={{ y: 0 }}
        transition={{ duration: 0.6 }}
        className="fixed top-0 left-0 right-0 z-50 backdrop-blur-lg bg-slate-950/30 border-b border-white/5"
      >
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          <div className="text-2xl font-bold bg-gradient-to-r from-emerald-400 to-blue-400 bg-clip-text text-transparent">
            ECO_PACK_AI
          </div>
          <motion.button
            onClick={() => navigate('/dashboard')}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="px-6 py-2 rounded-lg bg-gradient-to-r from-emerald-500 to-blue-500 text-white font-semibold hover:shadow-lg hover:shadow-emerald-500/50 transition-all duration-300"
          >
            Try Demo
          </motion.button>
        </div>
      </motion.nav>

      {/* HERO SECTION */}
      <section className="relative min-h-screen flex items-center pt-20">
        <div className="absolute inset-0 overflow-hidden bg-gradient-to-b from-transparent via-emerald-500/5 to-transparent">
          {/* Lazy-loaded 3D Canvas with Suspense fallback */}
          <Suspense fallback={
            <div className="absolute inset-0 bg-gradient-to-br from-slate-900/50 to-transparent flex items-center justify-center">
              <div className="w-12 h-12 border-2 border-emerald-500/20 border-t-emerald-500 rounded-full animate-spin" />
            </div>
          }>
            <Canvas className="!absolute inset-0">
              <AnimatedPackageBox />
            </Canvas>
          </Suspense>
        </div>

        {/* Content Overlay */}
        <div className="relative z-10 max-w-7xl mx-auto px-6 py-20 w-full grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          {/* Left Content */}
          <motion.div
            initial={{ opacity: 0, x: -60 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="space-y-8"
          >
            {/* Badge */}
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.6 }}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-full backdrop-blur-lg bg-emerald-500/10 border border-emerald-500/30 w-fit"
            >
              <span className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
              <span className="text-emerald-300 text-sm font-semibold">
                AI-Powered Sustainability
              </span>
            </motion.div>

            {/* Headline */}
            <motion.h1
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.3 }}
              className="text-5xl lg:text-6xl xl:text-7xl font-bold text-white leading-tight"
            >
              AI-Powered Sustainable{' '}
              <span className="bg-gradient-to-r from-emerald-400 to-blue-400 bg-clip-text text-transparent">
                Packaging
              </span>
              <span className="bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
                {' '}Intelligence
              </span>
            </motion.h1>

            {/* Subheadline */}
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.4 }}
              className="text-lg text-gray-300 max-w-lg leading-relaxed"
            >
              Optimize cost, carbon footprint, and damage risk in real-time. Powered by industrial-grade LightGBM models with 88% prediction accuracy.
            </motion.p>

            {/* CTA Buttons */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.5 }}
              className="flex flex-col sm:flex-row gap-4 pt-4"
            >
              <motion.button
                whileHover={{ 
                  scale: 1.05,
                  boxShadow: '0 20px 25px -5px rgba(16, 185, 129, 0.4)'
                }}
                whileTap={{ scale: 0.95 }}
                onClick={() => navigate('/dashboard')}
                className="px-8 py-4 rounded-lg bg-gradient-to-r from-emerald-500 to-blue-500 text-white font-bold text-base shadow-lg hover:shadow-2xl transition-all duration-300"
              >
                <span className="flex items-center justify-center gap-2">
                  Try Live Demo
                  <span className="text-lg">→</span>
                </span>
              </motion.button>
              <motion.button
                whileHover={{ 
                  scale: 1.05,
                  backgroundColor: 'rgba(255,255,255,0.15)'
                }}
                whileTap={{ scale: 0.95 }}
                className="px-8 py-4 rounded-lg backdrop-blur-lg bg-white/10 border border-white/20 text-white font-bold text-base hover:border-white/40 transition-all duration-300"
              >
                View Documentation
              </motion.button>
            </motion.div>

            {/* Stats Row */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.6 }}
              className="flex flex-wrap gap-8 pt-8 border-t border-white/10"
            >
              <div className="flex items-center gap-3">
                <div className="w-2 h-2 bg-emerald-400 rounded-full" />
                <span className="text-sm text-gray-400">
                  <AnimatedCounter end={88} />% Accuracy
                </span>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-2 h-2 bg-blue-400 rounded-full" />
                <span className="text-sm text-gray-400">
                  <AnimatedCounter end={1656} />
                  {' '}req/sec
                </span>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-2 h-2 bg-emerald-400 rounded-full" />
                <span className="text-sm text-gray-400">&lt;35ms latency</span>
              </div>
            </motion.div>
          </motion.div>

          {/* Right Side - 3D Render Area (Background) */}
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 1, delay: 0.4 }}
            className="hidden lg:flex items-center justify-center h-[500px]"
          />
        </div>

        {/* Scroll Indicator */}
        <motion.div
          animate={{ y: [0, 10, 0] }}
          transition={{ duration: 2, repeat: Infinity }}
          className="absolute bottom-8 left-1/2 -translate-x-1/2 text-gray-400"
        >
          <svg
            className="w-6 h-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
          </svg>
        </motion.div>
      </section>

      {/* FEATURES SECTION */}
      <section className="relative z-10 max-w-7xl mx-auto px-6 py-32">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="text-center mb-20"
        >
          <h2 className="text-5xl font-bold text-white mb-4">
            Enterprise-Grade Features
          </h2>
          <p className="text-xl text-gray-400 max-w-2xl mx-auto">
            Built with production-proven technology and optimized for real-world sustainability challenges.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <FeatureCard
            index={0}
            icon="🎯"
            title="Real-Time Predictions"
            description="88% accurate CO2 and cost predictions with sub-35ms latency"
          />
          <FeatureCard
            index={1}
            icon="📊"
            title="Material Intelligence"
            description="Compare 7+ sustainable packaging materials with eco scores"
          />
          <FeatureCard
            index={2}
            icon="🚀"
            title="Scalable API"
            description="1,656 requests/sec throughput with 99th percentile SLA"
          />
          <FeatureCard
            index={3}
            icon="🌿"
            title="Carbon Tracking"
            description="Real-time CO2 impact modeling for supply chain visibility"
          />
          <FeatureCard
            index={4}
            icon="💰"
            title="Cost Optimization"
            description="Minimize packaging costs without compromising protection"
          />
          <FeatureCard
            index={5}
            icon="📈"
            title="Historical Analytics"
            description="Track sustainability metrics and generate insights"
          />
        </div>
      </section>

      {/* STATS SECTION */}
      <section className="relative z-10 max-w-7xl mx-auto px-6 py-32">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="text-center mb-20"
        >
          <h2 className="text-5xl font-bold text-white mb-4">
            Production Ready
          </h2>
          <p className="text-xl text-gray-400">
            Validated across 480 test cases with perfect monotonicity constraints
          </p>
        </motion.div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard label="Cost Model R²" value="7489" unit="%" index={0} />
          <StatCard label="CO2 Accuracy" value="8800" unit="%" index={1} />
          <StatCard label="Throughput" value="1656" unit=" req/s" index={2} />
          <StatCard label="Latency (p99)" value="32" unit=" ms" index={3} />
        </div>
      </section>

      {/* CTA SECTION */}
      <section className="relative z-10 max-w-7xl mx-auto px-6 py-40">
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          whileInView={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="relative rounded-3xl overflow-hidden backdrop-blur-2xl bg-gradient-to-r from-emerald-500/15 to-blue-500/15 border border-white/10 p-12 md:p-16 lg:p-20 text-center group"
        >
          {/* Animated background glow */}
          <motion.div
            className="absolute inset-0 bg-gradient-to-r from-emerald-500 to-blue-500 opacity-0 blur-3xl"
            animate={{
              opacity: [0.1, 0.15, 0.1],
            }}
            transition={{
              duration: 4,
              repeat: Infinity,
            }}
          />

          <div className="relative z-10 space-y-8">
            <motion.h2 
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.1 }}
              viewport={{ once: true }}
              className="text-4xl md:text-5xl font-bold text-white leading-tight"
            >
              Ready to Optimize Your{' '}
              <span className="bg-gradient-to-r from-emerald-400 to-blue-400 bg-clip-text text-transparent">
                Sustainable Packaging?
              </span>
            </motion.h2>
            
            <motion.p 
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              viewport={{ once: true }}
              className="text-lg text-gray-300 max-w-3xl mx-auto leading-relaxed"
            >
              Start making data-driven decisions about sustainable packaging in minutes. Reduce costs, lower carbon footprint, and improve supply chain visibility—all powered by industrial-grade AI.
            </motion.p>

            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.3 }}
              viewport={{ once: true }}
              className="flex flex-col sm:flex-row gap-4 justify-center pt-4"
            >
              <motion.button
                whileHover={{ 
                  scale: 1.05,
                  boxShadow: '0 25px 50px -12px rgba(16, 185, 129, 0.5)'
                }}
                whileTap={{ scale: 0.95 }}
                onClick={() => navigate('/dashboard')}
                className="px-10 py-4 rounded-xl bg-gradient-to-r from-emerald-500 to-blue-500 text-white font-bold text-lg shadow-xl hover:shadow-2xl transition-all duration-300 whitespace-nowrap"
              >
                <span className="flex items-center justify-center gap-2">
                  Launch Dashboard
                  <span>→</span>
                </span>
              </motion.button>
              <motion.button
                whileHover={{ 
                  scale: 1.05,
                  backgroundColor: 'rgba(255,255,255,0.15)',
                  borderColor: 'rgba(16, 185, 129, 0.5)'
                }}
                whileTap={{ scale: 0.95 }}
                className="px-10 py-4 rounded-xl backdrop-blur-lg bg-white/10 border border-white/20 text-white font-bold text-lg hover:border-emerald-500/50 transition-all duration-300"
              >
                View API Docs
              </motion.button>
            </motion.div>
          </div>
        </motion.div>
      </section>

      {/* FOOTER */}
      <Footer />
    </div>
  );
}
