import React, { useState, useEffect, useMemo, useRef, useCallback } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import Card from '../components/Card'
import ScoreRing from '../components/ScoreRing'
import AnimatedKPI from '../components/AnimatedKPI'
import ParetoSlider from '../components/ParetoSlider'
import CarbonIntensityIndicator from '../components/CarbonIntensityIndicator'
import { api } from '../services/api'
import useDebounce from '../hooks/useDebounce'
import { usePredictionStore } from '../store/predictionStore'
import Packaging3D from '../components/Packaging3D'

function getDamageRisk(material) {
  const strength = material.suitability ?? material.score
  return Math.max(5, Math.min(95, 100 - Number(strength || 0)))
}

function getMaterialRankScore(material, ecoWeight) {
  const costWeight = 1 - ecoWeight
  const riskWeight = 0.2 + costWeight * 0.35

  const normalizedEco = Number(material.score || 0) / 100
  const normalizedCost = Math.min(Number(material.cost || 1.5) / 1.5, 1)
  const normalizedRisk = getDamageRisk(material) / 100

  return normalizedEco * ecoWeight - normalizedCost * costWeight - normalizedRisk * riskWeight
}

export default function RecommendationsContent({ product }) {
  const [selectedMaterial, setSelectedMaterial] = useState(null)
  const [materials, setMaterials] = useState([])
  const [paretoBias, setParetoBias] = useState(65)
  const [debugResponseData, setDebugResponseData] = useState(null)

  const { prediction, loading, error, beginRequest, finishRequest, setPrediction, setError } = usePredictionStore(
    (state) => ({
      prediction: state.prediction,
      loading: state.loading,
      error: state.error,
      beginRequest: state.beginRequest,
      finishRequest: state.finishRequest,
      setPrediction: state.setPrediction,
      setError: state.setError
    })
  )

  const abortControllerRef = useRef(null)
  const latestRequestIdRef = useRef(0)
  const activeProductIdRef = useRef(null)
  const inFlightRef = useRef(false)
  const isMountedRef = useRef(true)

  const productId = useMemo(() => {
    if (!product) return null
    return product.backendId || product.product_id || product.productId || product.productName
  }, [product])

  const debouncedProductId = useDebounce(productId, 300)
  const debouncedPareto = useDebounce(paretoBias, 200)

  const getMaterialIcon = useCallback((material) => {
    const icons = {
      bamboo: '🌿',
      paper: '📄',
      jute: '🧵',
      glass: '🔷',
      metal: '⚙️',
      plastic: '♻️',
      bagasse: '🌾'
    }
    return icons[material.toLowerCase()] || '📦'
  }, [])

  const generatePros = useCallback((rec) => {
    const pros = []
    if (rec.biodegradability > 0.8) pros.push('Highly biodegradable')
    if (rec.recyclability > 85) pros.push('Excellent recyclability')
    if (rec.co2_impact < 0.15) pros.push('Low carbon footprint')
    if (rec.cost_efficiency > 0.6 || rec.cost_per_unit < 0.3) pros.push('Cost-effective')
    if (rec.strength > 70) pros.push('Strong and durable')
    if (pros.length === 0) pros.push('Moderate performance')
    return pros
  }, [])

  const generateCons = useCallback((rec) => {
    const cons = []
    if (rec.biodegradability < 0.2) cons.push('Poor biodegradability')
    if (rec.recyclability < 40) cons.push('Limited recycling options')
    if (rec.co2_impact > 0.5) cons.push('High CO₂ emissions')
    if (rec.cost_efficiency < 0.3 || rec.cost_per_unit > 0.6) cons.push('Higher cost')
    if (rec.strength < 40) cons.push('Lower structural strength')
    if (cons.length === 0) cons.push('Trade-offs with specific attributes')
    return cons
  }, [])

  const defaultMaterials = useMemo(
    () => [
      {
        name: 'Bamboo',
        icon: '🌿',
        score: 92,
        co2: 0.2,
        cost: 0.85,
        recyclability: 85,
        biodegradability: 98,
        pros: ['Highly biodegradable', 'Low CO₂ footprint', 'Renewable resource'],
        cons: ['Moderate cost', 'Limited durability']
      },
      {
        name: 'Paper',
        icon: '📄',
        score: 88,
        co2: 0.3,
        cost: 0.72,
        recyclability: 90,
        biodegradability: 95,
        pros: ['Easy to recycle', 'Biodegradable', 'Cost-effective'],
        cons: ['Low strength', 'Water sensitive']
      },
      {
        name: 'Jute',
        icon: '🧵',
        score: 90,
        co2: 0.25,
        cost: 0.68,
        recyclability: 88,
        biodegradability: 99,
        pros: ['Natural fiber', 'Very strong', 'Excellent biodegradability'],
        cons: ['Limited customization', 'Heavier than alternatives']
      },
      {
        name: 'Glass',
        icon: '🔷',
        score: 80,
        co2: 0.5,
        cost: 1.2,
        recyclability: 90,
        biodegradability: 0,
        pros: ['100% recyclable', 'Elegant appearance', 'Long-lasting'],
        cons: ['High CO₂ in production', 'Fragile', 'Heavy']
      },
      {
        name: 'Metal',
        icon: '⚙️',
        score: 82,
        co2: 0.6,
        cost: 1.5,
        recyclability: 95,
        biodegradability: 0,
        pros: ['Highly recyclable', 'Durable', 'Premium feel'],
        cons: ['High production emissions', 'Expensive']
      },
      {
        name: 'Plastic',
        icon: '♻️',
        score: 45,
        co2: 0.7,
        cost: 0.35,
        recyclability: 40,
        biodegradability: 10,
        pros: ['Low cost', 'Lightweight', 'Versatile'],
        cons: ['Poor biodegradability', 'High carbon footprint', 'Pollution risk']
      }
    ],
    []
  )

  const isCanceledRequest = useCallback((err) => {
    return err?.code === 'ERR_CANCELED' || err?.name === 'CanceledError' || err?.name === 'AbortError'
  }, [])

  const fetchRecommendations = useCallback(
    async (targetProductId, options = {}) => {
      if (!targetProductId) {
        setError('Using default recommendations', 0)
        setMaterials(defaultMaterials)
        console.warn('[RecommendationsFlow] Missing product_id, using default recommendations')
        return
      }

      if (!options.force && inFlightRef.current && activeProductIdRef.current === targetProductId) {
        return
      }

      if (abortControllerRef.current) {
        console.log('[RecommendationsFlow] Aborting previous request', {
          previousRequestId: latestRequestIdRef.current,
          reason: 'new recommendation request'
        })
        abortControllerRef.current.abort()
      }

      const controller = new AbortController()
      abortControllerRef.current = controller

      const requestId = latestRequestIdRef.current + 1
      latestRequestIdRef.current = requestId
      activeProductIdRef.current = targetProductId
      inFlightRef.current = true
      beginRequest(requestId)

      const payload = { product_id: targetProductId }
      console.log('[RecommendationsFlow] Sending INDUSTRIAL recommendation request', {
        endpoint: '/recommend/industrial',
        requestId,
        payload,
        signalAborted: controller.signal.aborted
      })

      try {
        // Try industrial engine first
        const response = await api.getIndustrialRecommendations(targetProductId, {
          cost_weight: 0.33,
          co2_weight: 0.33,
          risk_weight: 0.34,
          top_n: 6
        }, {
          signal: controller.signal
        })

        console.log('[IndustrialEngine] Recommendation response received', {
          requestId,
          response,
          engine: response?.engine
        })
        setDebugResponseData(response)

        if (!isMountedRef.current || requestId !== latestRequestIdRef.current) {
          return
        }

        if (response.status === 'success' && response.recommendations) {
          const transformedMaterials = response.recommendations.map((rec) => ({
            name: rec.material.charAt(0).toUpperCase() + rec.material.slice(1),
            icon: getMaterialIcon(rec.material),
            score: Math.round(rec.sustainability_score * 100),
            co2: rec.co2,
            cost: rec.cost,
            recyclability: Math.round(rec.recyclability),
            biodegradability: Math.round(rec.biodegradability * 100),
            suitability: rec.damage_risk ? (1 - rec.damage_risk) : 0.7,
            // Industrial engine features
            rank: rec.rank,
            pareto_rank: rec.pareto_rank,
            weighted_score: rec.weighted_score,
            tradeoff_summary: rec.tradeoff_summary,
            why_selected: rec.why_selected,
            // Use industrial pros/cons if available, otherwise generate
            pros: rec.pros && rec.pros.length > 0 ? rec.pros : generatePros(rec),
            cons: rec.cons && rec.cons.length > 0 ? rec.cons : generateCons(rec)
          }))

          if (transformedMaterials.length > 0) {
            setMaterials(transformedMaterials)
            setPrediction(
              {
                topMaterial: transformedMaterials[0],
                recommendationCount: transformedMaterials.length
              },
              requestId
            )
            console.log('[RecommendationsFlow] Store updated with recommendations', {
              requestId,
              recommendationCount: transformedMaterials.length,
              topMaterial: transformedMaterials[0]?.name
            })
          } else {
            setMaterials(defaultMaterials)
            setError('No recommendations available, using defaults', requestId)
            console.warn('[RecommendationsFlow] Empty recommendations array, using defaults', {
              requestId
            })
          }
        } else {
          setMaterials(defaultMaterials)
          setError('No recommendations available, using defaults', requestId)
          console.warn('[IndustrialEngine] Invalid response shape, using defaults', {
            requestId,
            response
          })
        }
      } catch (err) {
        // If industrial engine fails, fallback to legacy
        if (!isCanceledRequest(err) && err?.response?.status === 503) {
          console.warn('[IndustrialEngine] Not available, falling back to legacy', err)
          try {
            const legacyResponse = await api.getMaterialRecommendations(targetProductId, {
              signal: controller.signal
            })
            if (legacyResponse.status === 'success' && legacyResponse.recommendations) {
              const transformedMaterials = legacyResponse.recommendations.map((rec) => ({
                name: rec.material.charAt(0).toUpperCase() + rec.material.slice(1),
                icon: getMaterialIcon(rec.material),
                score: Math.round(rec.eco_score),
                co2: rec.co2_impact,
                cost: rec.cost_per_unit || rec.cost_efficiency,
                recyclability: Math.round(rec.recyclability),
                biodegradability: Math.round(rec.biodegradability * 100),
                suitability: rec.suitability,
                pros: generatePros(rec),
                cons: generateCons(rec)
              }))
              setMaterials(transformedMaterials)
              setPrediction({ topMaterial: transformedMaterials[0] }, requestId)
              return
            }
          } catch (legacyErr) {
            console.error('[LegacyEngine] Fallback failed', legacyErr)
          }
        }

        if (isCanceledRequest(err)) {
          console.log('[RecommendationsFlow] Request canceled', {
            requestId,
            signalAborted: controller.signal.aborted
          })

          if (requestId === latestRequestIdRef.current) {
            finishRequest(requestId)
            inFlightRef.current = false
            activeProductIdRef.current = null

            if (materials.length === 0) {
              setMaterials(defaultMaterials)
            }
          }

          return
        }

        if (!isMountedRef.current || requestId !== latestRequestIdRef.current) {
          return
        }

        setError('Unable to fetch recommendations. Using default data.', requestId)
        setMaterials(defaultMaterials)
        console.error('[RecommendationsFlow] Recommendation request failed', {
          requestId,
          message: err?.message,
          code: err?.code,
          response: err?.response?.data,
          status: err?.response?.status
        })
      } finally {
        if (requestId === latestRequestIdRef.current) {
          finishRequest(requestId)
          inFlightRef.current = false
          activeProductIdRef.current = null
        }
      }
    },
    [beginRequest, defaultMaterials, finishRequest, generateCons, generatePros, getMaterialIcon, isCanceledRequest, setError, setPrediction]
  )

  useEffect(() => {
    if (!product) return

    console.log('[RecommendationsFlow] Product received by RecommendationsContent', {
      product,
      resolvedProductId: debouncedProductId
    })

    if (debouncedProductId) {
      fetchRecommendations(debouncedProductId)
    } else {
      setMaterials(defaultMaterials)
    }
  }, [product, debouncedProductId, fetchRecommendations, defaultMaterials])

  useEffect(() => {
    return () => {
      isMountedRef.current = false
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
    }
  }, [])

  const rankedMaterials = useMemo(() => {
    const ecoWeight = debouncedPareto / 100
    return [...materials].sort((a, b) => getMaterialRankScore(b, ecoWeight) - getMaterialRankScore(a, ecoWeight))
  }, [debouncedPareto, materials])

  useEffect(() => {
    if (!selectedMaterial && rankedMaterials.length > 0) {
      setSelectedMaterial(rankedMaterials[0])
      return
    }

    if (selectedMaterial) {
      const freshSelected = rankedMaterials.find((item) => item.name === selectedMaterial.name)
      if (freshSelected) {
        setSelectedMaterial(freshSelected)
      }
    }
  }, [rankedMaterials, selectedMaterial])

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className="space-y-8"
    >
      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <AnimatedKPI label="Avg Cost / Unit" value={rankedMaterials[0]?.cost || 0} prefix="$" decimals={2} colorClass="text-cyan-300" />
        <AnimatedKPI label="CO2 Impact" value={rankedMaterials[0]?.co2 || 0} suffix=" kg" decimals={2} colorClass="text-emerald-300" />
        <AnimatedKPI label="Damage Risk" value={selectedMaterial ? getDamageRisk(selectedMaterial) : 0} suffix="%" colorClass="text-rose-300" />
        <AnimatedKPI
          label="Confidence"
          value={prediction?.recommendationCount ? Math.min(95, 70 + prediction.recommendationCount * 4) : 72}
          suffix="%"
          colorClass="text-amber-300"
        />
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
        {/* Left Column: 3D Visualizer + Pareto + Indicators */}
        <div className="lg:col-span-3 space-y-6">
          {/* 3D Package Visualizer */}
          <Card className="border border-white/10 bg-white/5 p-6">
            <div className="mb-4">
              <h3 className="text-lg font-semibold text-white mb-1">Packaging Design</h3>
              <p className="text-xs text-slate-400">Interactive 3D visualization with material properties</p>
            </div>
            <Packaging3D
              product={product}
              damageRisk={selectedMaterial ? getDamageRisk(selectedMaterial) : 30}
              sustainabilityScore={selectedMaterial?.score || 80}
            />
          </Card>

          {/* Pareto Control */}
          <Card className="border border-white/10 bg-white/5 p-6">
            <div className="mb-4">
              <h3 className="text-lg font-semibold text-white mb-1">Optimization Balance</h3>
              <p className="text-xs text-slate-400">Adjust focus between cost and sustainability</p>
            </div>
            <ParetoSlider value={paretoBias} onChange={setParetoBias} />
          </Card>

          {/* Indicators Row */}
          <div className="grid grid-cols-2 gap-4">
            <CarbonIntensityIndicator co2={selectedMaterial?.co2 || 0.25} />
            <div
              className={`rounded-xl border p-4 backdrop-blur-xl ${
                (selectedMaterial ? getDamageRisk(selectedMaterial) : 0) > 60
                  ? 'border-rose-500/40 bg-rose-500/10'
                  : 'border-emerald-500/30 bg-emerald-500/10'
              }`}
            >
              <p className="text-xs uppercase tracking-wide text-slate-300 mb-2">Stress Profile</p>
              <p className="text-sm font-semibold text-white">
                {(selectedMaterial ? getDamageRisk(selectedMaterial) : 0) > 60 ? '⚠️ High Risk' : '✓ Safe Band'}
              </p>
            </div>
          </div>

          {/* Error Message */}
          <AnimatePresence>
            {error && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="rounded-xl border border-amber-500/40 bg-amber-500/10 p-4 text-sm text-amber-200"
              >
                {error}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Right Column: Material Ranking */}
        <div className="lg:col-span-2 space-y-4">
          <div>
            <h3 className="text-lg font-semibold text-white mb-1">Live Rankings</h3>
            <p className="text-xs text-slate-400">Ranked by your current balance settings</p>
          </div>

          <div className="space-y-3">
            {rankedMaterials.map((material, index) => (
              <motion.button
                layout
                key={material.name}
                onClick={() => setSelectedMaterial(material)}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className={`w-full rounded-xl border p-4 text-left transition ${
                  selectedMaterial?.name === material.name
                    ? 'border-cyan-400/60 bg-cyan-500/10 shadow-lg shadow-cyan-500/20'
                    : 'border-white/10 bg-white/5 hover:border-cyan-400/30 hover:bg-white/8'
                }`}
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">{material.icon}</span>
                    <div>
                      <p className="font-semibold text-white">{material.name}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <p className="text-xs text-slate-400">#{material.rank || index + 1}</p>
                        {material.pareto_rank !== undefined && (
                          <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                            material.pareto_rank === 0 
                              ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' 
                              : 'bg-slate-500/20 text-slate-400 border border-slate-500/30'
                          }`}>
                            {material.pareto_rank === 0 ? '★ Pareto' : `P${material.pareto_rank}`}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-lg font-bold text-emerald-300">{material.score}</p>
                    <p className="text-xs text-slate-400">Score</p>
                  </div>
                </div>
                {material.tradeoff_summary && (
                  <p className="text-xs text-cyan-300 mb-2 italic">⚡ {material.tradeoff_summary}</p>
                )}
                <div className="grid grid-cols-3 gap-2 text-xs">
                  <span className="px-2 py-1 rounded bg-white/5 text-slate-300">CO2: {material.co2}</span>
                  <span className="px-2 py-1 rounded bg-white/5 text-slate-300">R: {material.recyclability}%</span>
                  <span className="px-2 py-1 rounded bg-white/5 text-slate-300">${material.cost.toFixed(2)}</span>
                </div>
              </motion.button>
            ))}

            {!loading && rankedMaterials.length === 0 && (
              <div className="rounded-xl border border-white/10 bg-white/5 p-4 text-sm text-slate-300">
                No recommendation data available.
              </div>
            )}
          </div>

          {loading && (
            <div className="rounded-xl border border-cyan-500/30 bg-cyan-500/10 p-3 text-xs text-cyan-200 text-center">
              Analyzing materials...
            </div>
          )}

          {debugResponseData && rankedMaterials.length === 0 && (
            <pre className="rounded-xl border border-white/10 bg-slate-950/70 p-3 text-xs text-slate-300 overflow-auto">
              {JSON.stringify(debugResponseData, null, 2)}
            </pre>
          )}
        </div>
      </div>

      {/* Detailed Analysis Panel */}
      {selectedMaterial && (
        <motion.div
          layoutId="selected-material-detail"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 20 }}
        >
          <Card className="border border-white/10 bg-white/5 p-8">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Left: Pros/Cons */}
              <div>
                <div className="flex items-center gap-3 mb-6">
                  <span className="text-4xl">{selectedMaterial.icon}</span>
                  <div>
                    <h3 className="text-2xl font-bold text-white">{selectedMaterial.name}</h3>
                    <p className="text-sm text-slate-400">Detailed Analysis</p>
                  </div>
                </div>

                {selectedMaterial.why_selected && (
                  <div className="mb-6 p-4 rounded-lg bg-cyan-500/10 border border-cyan-500/30">
                    <h4 className="text-xs font-semibold uppercase tracking-wide text-cyan-300 mb-2">
                      💡 Why Recommended
                    </h4>
                    <p className="text-sm text-slate-200">{selectedMaterial.why_selected}</p>
                  </div>
                )}

                <div className="space-y-6">
                  <div>
                    <h4 className="text-sm font-semibold uppercase tracking-wide text-emerald-300 mb-3">Advantages</h4>
                    <ul className="space-y-2">
                      {selectedMaterial.pros.map((pro, idx) => (
                        <li key={idx} className="flex items-center gap-2 text-sm text-slate-200">
                          <span className="text-emerald-400">✓</span>
                          <span>{pro}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div>
                    <h4 className="text-sm font-semibold uppercase tracking-wide text-amber-300 mb-3">Considerations</h4>
                    <ul className="space-y-2">
                      {selectedMaterial.cons.map((con, idx) => (
                        <li key={idx} className="flex items-center gap-2 text-sm text-slate-200">
                          <span className="text-amber-400">⚠</span>
                          <span>{con}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>

              {/* Right: Score Rings */}
              <div className="grid grid-cols-2 gap-8 place-items-center">
                <ScoreRing score={selectedMaterial.score} label="Eco Score" color="green" />
                <ScoreRing score={selectedMaterial.recyclability} label="Recyclability" color="green" />
                <ScoreRing score={(1 - selectedMaterial.co2) * 100} label="Low Carbon" color="amber" />
                <ScoreRing score={selectedMaterial.biodegradability} label="Biodegradable" color="green" />
              </div>
            </div>

            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="w-full mt-8 px-6 py-3 bg-gradient-to-r from-cyan-500 to-emerald-500 text-white rounded-lg font-semibold hover:shadow-lg hover:shadow-cyan-500/30 transition"
            >
              Select {selectedMaterial.name}
            </motion.button>
          </Card>
        </motion.div>
      )}
    </motion.div>
  )
}
