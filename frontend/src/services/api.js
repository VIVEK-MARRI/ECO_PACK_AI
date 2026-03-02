import axios from 'axios'

// Use environment variable if available, otherwise default to local backend
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'
const API_KEY = import.meta.env.VITE_API_KEY || 'eco-pack-ai-2026-secure-key'

console.log('[API] Base URL:', API_BASE_URL)

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000, // 10 second timeout
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': API_KEY
  }
})

export const api = {
  // Health check
  async checkHealth() {
    try {
      const response = await apiClient.get('/health')
      return response.data
    } catch (error) {
      console.error('Health check failed:', error)
      return null
    }
  },

  // Product endpoints
  async inputProduct(productData) {
    try {
      const response = await apiClient.post('/product/input', {
        product_id: `PROD-${Date.now()}`,
        category: productData.category,
        weight: productData.weight,
        strength: productData.strength,
        biodegradability: productData.biodegradability,
        recyclability: productData.recyclability
      })
      return response.data
    } catch (error) {
      console.error('Error inputting product:', error)
      throw error
    }
  },

  // Recommendation endpoints
  async getMaterialRecommendations(productId, options = {}) {
    try {
      const payload = {
        product_id: productId
      }
      console.log('[RecommendationsFlow] POST /recommend/material', payload)

      const response = await apiClient.post('/recommend/material', {
        product_id: productId
      }, {
        signal: options.signal
      })

      console.log('[RecommendationsFlow] /recommend/material status', response?.status)
      return response.data
    } catch (error) {
      if (error?.code === 'ERR_CANCELED' || error?.name === 'CanceledError') {
        throw error
      }
      console.error('Error getting recommendations:', error)
      throw error
    }
  },

  // Industrial recommendation engine (NEW)
  async getIndustrialRecommendations(productId, preferences = {}, options = {}) {
    try {
      const payload = {
        product_id: productId,
        preferences: {
          cost_weight: preferences.cost_weight || 0.33,
          co2_weight: preferences.co2_weight || 0.33,
          risk_weight: preferences.risk_weight || 0.34,
          max_budget: preferences.max_budget || null,
          max_damage_risk: preferences.max_damage_risk || 0.8,
          min_sustainability: preferences.min_sustainability || 0.3,
          max_co2_emission: preferences.max_co2_emission || null,
          min_recyclability: preferences.min_recyclability || 0.0
        },
        top_n: preferences.top_n || 6
      }
      console.log('[IndustrialEngine] POST /recommend/industrial', payload)

      const response = await apiClient.post('/recommend/industrial', payload, {
        signal: options.signal
      })

      console.log('[IndustrialEngine] Response status', response?.status)
      return response.data
    } catch (error) {
      if (error?.code === 'ERR_CANCELED' || error?.name === 'CanceledError') {
        throw error
      }
      console.error('[IndustrialEngine] Error:', error)
      throw error
    }
  },

  // Environmental score
  async getEnvironmentalScore(productId, material) {
    try {
      const response = await apiClient.post('/score/environmental', {
        product_id: productId,
        material: material
      })
      return response.data
    } catch (error) {
      console.error('Error getting environmental score:', error)
      throw error
    }
  },

  // History
  async getHistory(productId) {
    try {
      const response = await apiClient.get(`/history/${productId}`)
      return response.data
    } catch (error) {
      console.error('Error getting history:', error)
      throw error
    }
  },

  // Get all products/history
  async getAllHistory() {
    try {
      const response = await apiClient.get('/history/all')
      return response.data
    } catch (error) {
      console.error('Error getting all history:', error)
      throw error
    }
  }
}

export default apiClient
