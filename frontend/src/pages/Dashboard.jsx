import React from 'react'
import Card from '../components/Card'
import StatCard from '../components/StatCard'

export default function Dashboard({ onNavigate, productCount }) {
  const materials = [
    { name: 'Bamboo', eco: '95%', icon: '🌿' },
    { name: 'Paper', eco: '88%', icon: '📄' },
    { name: 'Jute', eco: '92%', icon: '🧵' },
    { name: 'Glass', eco: '90%', icon: '🔷' },
  ]

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* Hero Section */}
      <div className="mb-12 animate-fade-in">
        <div className="bg-gradient-to-r from-green-500 to-emerald-600 rounded-2xl p-12 text-white shadow-lg">
          <h2 className="text-4xl md:text-5xl font-bold mb-4">Welcome to ECO PACK AI</h2>
          <p className="text-lg text-green-50 mb-8 max-w-2xl">
            Make sustainable packaging decisions with AI-powered recommendations. Reduce CO₂ emissions, cut costs, and help the planet.
          </p>
          <button
            onClick={() => onNavigate('product')}
            className="bg-white text-green-600 px-8 py-3 rounded-lg font-bold hover:bg-green-50 transition-colors shadow-lg"
          >
            Get Started →
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12 animate-slide-in">
        <StatCard icon="📦" title="Products Analyzed" value={productCount} />
        <StatCard icon="🌱" title="Avg CO₂ Reduction" value="42" unit="%" />
        <StatCard icon="💰" title="Cost Savings" value="$2.3K" change={15} />
        <StatCard icon="♻️" title="Recyclability Rate" value="87" unit="%" />
      </div>

      {/* Features */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
        <Card className="p-8 hover:shadow-lg transition-shadow">
          <div className="text-4xl mb-4">🤖</div>
          <h3 className="text-xl font-bold text-slate-900 mb-2">AI Recommendations</h3>
          <p className="text-slate-600">Get intelligent material recommendations based on your product requirements and environmental impact.</p>
        </Card>

        <Card className="p-8 hover:shadow-lg transition-shadow">
          <div className="text-4xl mb-4">📊</div>
          <h3 className="text-xl font-bold text-slate-900 mb-2">Impact Analysis</h3>
          <p className="text-slate-600">Detailed CO₂, cost, and recyclability scoring to help you make informed decisions.</p>
        </Card>

        <Card className="p-8 hover:shadow-lg transition-shadow">
          <div className="text-4xl mb-4">📈</div>
          <h3 className="text-xl font-bold text-slate-900 mb-2">Track History</h3>
          <p className="text-slate-600">Keep records of all your analyses and recommendations for continuous improvement.</p>
        </Card>
      </div>

      {/* Top Materials */}
      <Card className="p-8">
        <h3 className="text-2xl font-bold text-slate-900 mb-6">Eco-Friendly Materials</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {materials.map(material => (
            <div key={material.name} className="p-4 bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl text-center hover:shadow-md transition-shadow">
              <div className="text-3xl mb-2">{material.icon}</div>
              <h4 className="font-semibold text-slate-900">{material.name}</h4>
              <p className="text-sm text-green-600 font-bold mt-2">{material.eco} Eco Score</p>
            </div>
          ))}
        </div>
      </Card>

      {/* CTA Section */}
      <div className="mt-12 text-center">
        <h3 className="text-2xl font-bold text-slate-900 mb-4">Ready to make a difference?</h3>
        <p className="text-slate-600 mb-8 max-w-2xl mx-auto">
          Start analyzing your products today and discover how sustainable packaging can benefit both your business and the environment.
        </p>
        <button
          onClick={() => onNavigate('product')}
          className="bg-gradient-to-r from-green-500 to-emerald-600 text-white px-8 py-3 rounded-lg font-bold hover:shadow-lg transition-shadow"
        >
          Analyze New Product →
        </button>
      </div>
    </div>
  )
}
