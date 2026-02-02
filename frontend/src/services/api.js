import axios from 'axios'

const API_BASE_URL = 'http://localhost:5000/api'
const API_KEY = 'your-secret-key-change-this' // Should match backend

const apiClient = axios.create({
  baseURL: API_BASE_URL,
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
  async getMaterialRecommendations(productId) {
    try {
      const response = await apiClient.post('/recommend/material', {
        product_id: productId
      })
      return response.data
    } catch (error) {
      console.error('Error getting recommendations:', error)
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
