/**
 * API Connection Test Script
 * Tests frontend-backend integration
 */

import axios from 'axios';

const API_BASE_URL = process.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

async function testAPIConnection() {
  console.log('='.repeat(80));
  console.log('ECO_PACK_AI Frontend-Backend Integration Test');
  console.log('='.repeat(80));
  console.log(`\nTesting API at: ${API_BASE_URL}\n`);
  
  const results = {
    healthCheck: false,
    productInput: false,
    recommendations: false,
    history: false,
    cors: true
  };
  
  const testProductId = `TEST-${Date.now()}`;
  
  // Test 1: Health Check
  try {
    console.log('[1/4] Testing /api/health...');
    const response = await axios.get(`${API_BASE_URL}/health`, {
      timeout: 5000
    });
    console.log(`✓ Health Check: ${response.data.status}`);
    console.log(`  Models: ${response.data.models}`);
    results.healthCheck = true;
  } catch (error) {
    console.log(`✗ Health Check Failed: ${error.message}`);
    if (error.code === 'ECONNREFUSED') {
      console.log('  Backend is not running!');
    }
    results.cors = error.message.includes('CORS') ? false : results.cors;
  }
  
  // Test 2: Product Input
  try {
    console.log('\n[2/4] Testing /api/product/input...');
    const response = await axios.post(`${API_BASE_URL}/product/input`, {
      product_id: testProductId,
      category: 'electronics',
      weight: 1.5,
      strength: 70,
      biodegradability: 0.3,
      recyclability: 60
    }, {
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': 'eco-pack-ai-2026-secure-key'
      },
      timeout: 10000
    });
    console.log(`✓ Product Input: ${response.data.status}`);
    results.productInput = true;
  } catch (error) {
    console.log(`✗ Product Input Failed: ${error.message}`);
    if (error.response) {
      console.log(`  Status: ${error.response.status}`);
      console.log(`  Error: ${JSON.stringify(error.response.data)}`);
    }
    results.cors = error.message.includes('CORS') ? false : results.cors;
  }
  
  // Test 3: Recommendations
  try {
    console.log('\n[3/4] Testing /api/recommend/material...');
    const response = await axios.post(`${API_BASE_URL}/recommend/material`, {
      product_id: testProductId,
      category: 'electronics',
      weight: 1.5
    }, {
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': 'eco-pack-ai-2026-secure-key'
      },
      timeout: 10000
    });
    console.log(`✓ Recommendations: ${response.data.status}`);
    console.log(`  Materials found: ${response.data.recommendations ? response.data.recommendations.length : 0}`);
    results.recommendations = true;
  } catch (error) {
    console.log(`✗ Recommendations Failed: ${error.message}`);
    if (error.response) {
      console.log(`  Status: ${error.response.status}`);
    }
    results.cors = error.message.includes('CORS') ? false : results.cors;
  }
  
  // Test 4: History
  try {
    console.log('\n[4/4] Testing /api/history/all...');
    const response = await axios.get(`${API_BASE_URL}/history/all`, {
      headers: {
        'X-API-Key': 'eco-pack-ai-2026-secure-key'
      },
      timeout: 5000
    });
    console.log(`✓ History: ${response.data.status}`);
    console.log(`  Records: ${response.data.history ? response.data.history.length : 0}`);
    results.history = true;
  } catch (error) {
    console.log(`✗ History Failed: ${error.message}`);
    results.cors = error.message.includes('CORS') ? false : results.cors;
  }
  
  // Summary
  console.log('\n' + '='.repeat(80));
  console.log('TEST RESULTS');
  console.log('='.repeat(80));
  console.log(`Health Check:     ${results.healthCheck ? '✓ PASS' : '✗ FAIL'}`);
  console.log(`Product Input:    ${results.productInput ? '✓ PASS' : '✗ FAIL'}`);
  console.log(`Recommendations:  ${results.recommendations ? '✓ PASS' : '✗ FAIL'}`);
  console.log(`History:          ${results.history ? '✓ PASS' : '✗ FAIL'}`);
  console.log(`CORS:             ${results.cors ? '✓ ENABLED' : '✗ BLOCKED'}`);
  
  const passCount = Object.values(results).filter(Boolean).length;
  const totalTests = Object.keys(results).length;
  const score = Math.round((passCount / totalTests) * 100);
  
  console.log(`\nAPI Integration Score: ${score}/100`);
  console.log('='.repeat(80));
  
  return score >= 80;
}

testAPIConnection()
  .then(success => {
    process.exit(success ? 0 : 1);
  })
  .catch(error => {
    console.error('Test suite error:', error);
    process.exit(1);
  });
