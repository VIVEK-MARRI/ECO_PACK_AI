import React, { useState, useEffect } from 'react'
import Card from '../components/Card'
import ScoreRing from '../components/ScoreRing'
import { api } from '../services/api'

export default function Recommendations({ product }) {
  const [selectedMaterial, setSelectedMaterial] = useState(null)
  const [materials, setMaterials] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Fetch recommendations when product changes
  useEffect(() => {
    if (!product) return
    const productId = product.backendId || product.product_id || product.productId || product.productName
    if (productId) {
      fetchRecommendations(productId)
    } else {
      setError('Using default recommendations')
      setMaterials(getDefaultMaterials())
    }
  }, [product])

  const fetchRecommendations = async (productId) => {
    setLoading(true)
    setError(null)
    
    try {
      const response = await api.getMaterialRecommendations(productId)
      
      if (response.status === 'success' && response.recommendations) {
        // Transform API data to frontend format
        const transformedMaterials = response.recommendations.map(rec => ({
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
        
        if (transformedMaterials.length > 0) {
          setMaterials(transformedMaterials)
        } else {
          setError('No recommendations available, using defaults')
          setMaterials(getDefaultMaterials())
        }
      } else {
        setError('No recommendations available, using defaults')
        setMaterials(getDefaultMaterials())
      }
    } catch (err) {
      console.error('Error fetching recommendations:', err)
      setError('Unable to fetch recommendations. Using default data.')
      // Fallback to hardcoded data
      setMaterials(getDefaultMaterials())
    } finally {
      setLoading(false)
    }
  }

  const getMaterialIcon = (material) => {
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
  }

  const generatePros = (rec) => {
    const pros = []
    if (rec.biodegradability > 0.8) pros.push('Highly biodegradable')
    if (rec.recyclability > 85) pros.push('Excellent recyclability')
    if (rec.co2_impact < 0.15) pros.push('Low carbon footprint')
    if (rec.cost_efficiency > 0.6 || rec.cost_per_unit < 0.3) pros.push('Cost-effective')
    if (rec.strength > 70) pros.push('Strong and durable')
    if (pros.length === 0) pros.push('Moderate performance')
    return pros
  }

  const generateCons = (rec) => {
    const cons = []
    if (rec.biodegradability < 0.2) cons.push('Poor biodegradability')
    if (rec.recyclability < 40) cons.push('Limited recycling options')
    if (rec.co2_impact > 0.5) cons.push('High CO₂ emissions')
    if (rec.cost_efficiency < 0.3 || rec.cost_per_unit > 0.6) cons.push('Higher cost')
    if (rec.strength < 40) cons.push('Lower structural strength')
    if (cons.length === 0) cons.push('Trade-offs with specific attributes')
    return cons
  }

  const getDefaultMaterials = () => {
    return [
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
  ]}

  if (!product) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <Card className="p-12 text-center">
          <p className="text-slate-600 text-lg">Select or create a product to see recommendations</p>
        </Card>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <Card className="p-12 text-center">
          <div className="text-6xl mb-4 animate-pulse">🔄</div>
          <p className="text-slate-600 text-lg">Analyzing materials with AI...</p>
        </Card>
      </div>
    )
  }

  if (error && materials.length === 0) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <Card className="p-12 text-center">
          <div className="text-6xl mb-4">⚠️</div>
          <p className="text-slate-600 text-lg">{error}</p>
          <button 
            onClick={() => {
              const productId = product?.backendId || product?.product_id || product?.productId || product?.productName
              if (productId) fetchRecommendations(productId)
            }}
            className="mt-4 px-6 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600"
          >
            Retry
          </button>
        </Card>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* Product Summary */}
      <Card className="p-8 mb-8 bg-gradient-to-r from-blue-50 to-cyan-50 border-blue-200">
        <h3 className="text-lg font-bold text-slate-900 mb-4">Product Summary</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-slate-600">Product Name</p>
            <p className="font-semibold text-slate-900">{product.productName}</p>
          </div>
          <div>
            <p className="text-sm text-slate-600">Category</p>
            <p className="font-semibold text-slate-900 capitalize">{product.category}</p>
          </div>
          <div>
            <p className="text-sm text-slate-600">Weight</p>
            <p className="font-semibold text-slate-900">{product.weight} kg</p>
          </div>
          <div>
            <p className="text-sm text-slate-600">Date</p>
            <p className="font-semibold text-slate-900">{new Date(product.createdAt).toLocaleDateString()}</p>
          </div>
        </div>
      </Card>

      {/* Materials Grid */}
      <h2 className="text-3xl font-bold text-slate-900 mb-8">Recommended Materials</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
        {materials.map(material => (
          <Card
            key={material.name}
            className={`p-6 cursor-pointer transition-all hover:shadow-xl transform hover:-translate-y-1 ${
              selectedMaterial?.name === material.name
                ? 'ring-2 ring-green-500 shadow-lg'
                : ''
            }`}
            onClick={() => setSelectedMaterial(material)}
          >
            <div className="flex items-start justify-between mb-4">
              <div>
                <div className="text-4xl mb-2">{material.icon}</div>
                <h3 className="text-xl font-bold text-slate-900">{material.name}</h3>
              </div>
              <div className="text-right">
                <div className="text-3xl font-bold text-green-600">{material.score}</div>
                <p className="text-xs text-slate-500">Eco Score</p>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-2 mb-4 text-center">
              <div className="p-2 bg-slate-50 rounded">
                <p className="text-xs text-slate-600">CO₂</p>
                <p className="font-bold text-slate-900">{material.co2}</p>
              </div>
              <div className="p-2 bg-slate-50 rounded">
                <p className="text-xs text-slate-600">Recycle</p>
                <p className="font-bold text-slate-900">{material.recyclability}%</p>
              </div>
              <div className="p-2 bg-slate-50 rounded">
                <p className="text-xs text-slate-600">Cost</p>
                <p className="font-bold text-slate-900">${material.cost}</p>
              </div>
            </div>

            <button className="w-full py-2 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-lg font-semibold hover:shadow-md transition-shadow">
              Learn More
            </button>
          </Card>
        ))}
      </div>

      {/* Detailed View */}
      {selectedMaterial && (
        <Card className="p-8 bg-gradient-to-br from-slate-50 to-slate-100 animate-slide-in">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Left Side */}
            <div>
              <div className="flex items-center gap-4 mb-8">
                <div className="text-6xl">{selectedMaterial.icon}</div>
                <div>
                  <h3 className="text-3xl font-bold text-slate-900">{selectedMaterial.name}</h3>
                  <p className="text-slate-600">Comprehensive Analysis</p>
                </div>
              </div>

              <h4 className="text-lg font-bold text-slate-900 mb-4">Advantages</h4>
              <ul className="space-y-2 mb-8">
                {selectedMaterial.pros.map((pro, idx) => (
                  <li key={idx} className="flex items-center gap-3">
                    <span className="text-green-500 text-lg">✓</span>
                    <span className="text-slate-700">{pro}</span>
                  </li>
                ))}
              </ul>

              <h4 className="text-lg font-bold text-slate-900 mb-4">Considerations</h4>
              <ul className="space-y-2">
                {selectedMaterial.cons.map((con, idx) => (
                  <li key={idx} className="flex items-center gap-3">
                    <span className="text-amber-500 text-lg">⚠</span>
                    <span className="text-slate-700">{con}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Right Side - Scores */}
            <div className="grid grid-cols-2 gap-8 place-items-center">
              <ScoreRing score={selectedMaterial.score} label="Overall Eco Score" color="green" />
              <ScoreRing score={selectedMaterial.recyclability} label="Recyclability" color="green" />
              <ScoreRing score={(1 - selectedMaterial.co2) * 100} label="Low Carbon" color="amber" />
              <ScoreRing score={selectedMaterial.biodegradability} label="Biodegradability" color="green" />
            </div>
          </div>

          <div className="mt-8 pt-8 border-t border-slate-200">
            <button className="w-full bg-gradient-to-r from-green-500 to-emerald-600 text-white py-3 rounded-lg font-bold hover:shadow-lg transition-shadow">
              Use {selectedMaterial.name} for This Product
            </button>
          </div>
        </Card>
      )}
    </div>
  )
}
