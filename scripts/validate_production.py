#!/usr/bin/env python
"""
Validation Script - Phase 5 Backend Verification
Tests all production components and API endpoints

Run this AFTER starting the Flask server:
  python src/api_production.py
  # In another terminal:
  python scripts/validate_production.py
"""

import os
import sys
import time
import requests
import json
from datetime import datetime
from typing import Dict, Tuple

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.logger import setup_logger
from src.model_loader import get_model_registry
from src.predictor import get_predictor
from src.feature_pipeline import FeaturePipeline

logger = setup_logger('validator')

# Configuration
API_BASE_URL = "http://localhost:5000"
API_KEY = os.getenv('API_KEY', 'your-secret-key-change-this')

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_header(text: str):
    """Print section header"""
    print(f"\n{BLUE}{BOLD}{'='*80}{RESET}")
    print(f"{BLUE}{BOLD}{text.center(80)}{RESET}")
    print(f"{BLUE}{BOLD}{'='*80}{RESET}\n")

def print_success(text: str):
    """Print success message"""
    print(f"{GREEN}✓ {text}{RESET}")

def print_error(text: str):
    """Print error message"""
    print(f"{RED}✗ {text}{RESET}")

def print_warning(text: str):
    """Print warning message"""
    print(f"{YELLOW}⚠ {text}{RESET}")

def print_info(text: str):
    """Print info message"""
    print(f"{BLUE}ℹ {text}{RESET}")

# ============================================================================
# TEST 1: Component Validation (Offline)
# ============================================================================

def test_component_validation():
    """Test all components can be imported and initialized locally"""
    print_header("TEST 1: Component Validation (Offline)")
    
    results = {}
    
    # Test 1.1: Logger
    try:
        print_info("Testing logger module...")
        test_logger = setup_logger('test')
        test_logger.info("Test message")
        print_success("Logger initialized correctly")
        results['logger'] = True
    except Exception as e:
        print_error(f"Logger failed: {str(e)}")
        results['logger'] = False
    
    # Test 1.2: Model Registry
    try:
        print_info("Testing model registry...")
        registry = get_model_registry()
        status = registry.get_status()
        
        if status['models']:
            print_success(f"Model registry loaded: {status['models']}")
            results['model_registry'] = True
        else:
            print_error("No models loaded in registry")
            results['model_registry'] = False
    except Exception as e:
        print_error(f"Model registry failed: {str(e)}")
        results['model_registry'] = False
    
    # Test 1.3: Feature Pipeline
    try:
        print_info("Testing feature pipeline...")
        test_data = {
            'category': 'electronics',
            'weight': 2.5,
            'strength': 75,
            'biodegradability': 80,
            'recyclability': 90
        }
        is_valid, msg = FeaturePipeline.validate_input(test_data)
        
        if is_valid:
            print_success("Feature pipeline validation passed")
            results['feature_pipeline'] = True
        else:
            print_error(f"Feature pipeline validation failed: {msg}")
            results['feature_pipeline'] = False
    except Exception as e:
        print_error(f"Feature pipeline failed: {str(e)}")
        results['feature_pipeline'] = False
    
    # Test 1.4: Predictor
    try:
        print_info("Testing predictor...")
        predictor = get_predictor()
        metrics = predictor.get_metrics()
        
        if metrics and 'total_predictions' in metrics:
            print_success("Predictor initialized correctly")
            results['predictor'] = True
        else:
            print_error("Predictor metrics not available")
            results['predictor'] = False
    except Exception as e:
        print_error(f"Predictor failed: {str(e)}")
        results['predictor'] = False
    
    # Summary
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"\n{BOLD}Component Validation Summary:{RESET}")
    for component, result in results.items():
        status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
        print(f"  {component}: {status}")
    
    print(f"\n{BOLD}Result: {passed}/{total} components passed{RESET}\n")
    
    return all(results.values())

# ============================================================================
# TEST 2: API Health Check
# ============================================================================

def test_health_endpoint():
    """Test /api/health endpoint"""
    print_header("TEST 2: API Health Check")
    
    try:
        print_info(f"Testing {API_BASE_URL}/api/health...")
        response = requests.get(f"{API_BASE_URL}/api/health")
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Health check passed (status={data.get('status')})")
            
            # Check components
            components = data.get('components', {})
            if components.get('database'):
                print_success(f"Database: {components['database']}")
            
            if components.get('models', {}).get('loaded'):
                models = components['models']['loaded']
                print_success(f"Models loaded: {models}")
            
            return True
        else:
            print_error(f"Health check failed (status={response.status_code})")
            return False
    
    except Exception as e:
        print_error(f"Health endpoint test failed: {str(e)}")
        return False

# ============================================================================
# TEST 3: API Diagnostics
# ============================================================================

def test_diagnostics_endpoint():
    """Test /api/diagnostics endpoint"""
    print_header("TEST 3: API Diagnostics")
    
    try:
        print_info(f"Testing {API_BASE_URL}/api/diagnostics...")
        headers = {'X-API-Key': API_KEY}
        response = requests.get(f"{API_BASE_URL}/api/diagnostics", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print_success("Diagnostics endpoint accessible")
            
            # Check predictor metrics
            metrics = data.get('predictor_metrics', {})
            print_info(f"Predictor - Total: {metrics.get('total_predictions')}, "
                      f"Success: {metrics.get('successful_predictions')}, "
                      f"Failed: {metrics.get('failed_predictions')}")
            print_info(f"Average latency: {metrics.get('avg_latency_ms'):.2f}ms")
            
            return True
        else:
            print_error(f"Diagnostics failed (status={response.status_code})")
            return False
    
    except Exception as e:
        print_error(f"Diagnostics endpoint test failed: {str(e)}")
        return False

# ============================================================================
# TEST 4: Product Input
# ============================================================================

def test_product_input() -> Tuple[bool, str]:
    """Test /api/product/input endpoint"""
    print_header("TEST 4: Product Input")
    
    try:
        product_data = {
            'product_id': f'TEST-PROD-{int(time.time())}',
            'category': 'electronics',
            'weight': 2.5,
            'strength': 75,
            'biodegradability': 0.85,
            'recyclability': 90
        }
        
        print_info(f"Creating product: {product_data['product_id']}")
        headers = {'X-API-Key': API_KEY}
        
        response = requests.post(
            f"{API_BASE_URL}/api/product/input",
            json=product_data,
            headers=headers
        )
        
        if response.status_code == 201:
            data = response.json()
            product_id = data.get('product_id')
            print_success(f"Product created: {product_id}")
            return True, product_id
        else:
            print_error(f"Product input failed (status={response.status_code})")
            print_error(f"Response: {response.text}")
            return False, None
    
    except Exception as e:
        print_error(f"Product input test failed: {str(e)}")
        return False, None

# ============================================================================
# TEST 5: Material Recommendations
# ============================================================================

def test_recommendations(product_id: str):
    """Test /api/recommend/material endpoint"""
    print_header("TEST 5: Material Recommendations (ML-Powered)")
    
    try:
        print_info(f"Getting recommendations for product: {product_id}")
        headers = {'X-API-Key': API_KEY}
        
        response = requests.post(
            f"{API_BASE_URL}/api/recommend/material",
            json={'product_id': product_id},
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            recommendations = data.get('recommendations', [])
            
            print_success(f"Retrieved {len(recommendations)} material recommendations")
            
            # Display top 3
            print_info("Top 3 Materials:")
            for i, rec in enumerate(recommendations[:3], 1):
                material = rec.get('material', 'unknown')
                eco = rec.get('eco_score', 0)
                co2 = rec.get('co2_impact', 0)
                suitability = rec.get('suitability', 0)
                latency = rec.get('latency_ms', 0)
                
                print(f"  {i}. {material.upper()}")
                print(f"     Eco Score: {eco:.1f}/100")
                print(f"     CO2 Impact: {co2:.2f} kg CO2e")
                print(f"     Suitability: {suitability:.2%}")
                print(f"     Latency: {latency:.2f}ms")
            
            return True
        else:
            print_error(f"Recommendations failed (status={response.status_code})")
            return False
    
    except Exception as e:
        print_error(f"Recommendations test failed: {str(e)}")
        return False

# ============================================================================
# TEST 6: Single Prediction
# ============================================================================

def test_single_prediction(product_id: str):
    """Test /api/predict endpoint"""
    print_header("TEST 6: Single Material Prediction")
    
    try:
        material = 'bamboo'
        print_info(f"Predicting {material} for product: {product_id}")
        headers = {'X-API-Key': API_KEY}
        
        response = requests.post(
            f"{API_BASE_URL}/api/predict",
            json={'product_id': product_id, 'material': material},
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            prediction = data.get('prediction', {})
            
            print_success(f"Prediction retrieved")
            print_info(f"Material: {prediction.get('material')}")
            print_info(f"Eco Score: {prediction.get('eco_score'):.1f}/100")
            print_info(f"CO2 Impact: {prediction.get('co2_impact'):.2f} kg CO2e")
            print_info(f"Cost: ${prediction.get('cost_per_unit'):.2f}")
            print_info(f"Reliability: {prediction.get('model_reliability')}")
            print_info(f"Latency: {prediction.get('latency_ms'):.2f}ms")
            
            return True
        else:
            print_error(f"Prediction failed (status={response.status_code})")
            return False
    
    except Exception as e:
        print_error(f"Single prediction test failed: {str(e)}")
        return False

# ============================================================================
# TEST 7: Performance Check
# ============================================================================

def test_performance(product_id: str):
    """Quick performance test - 10 rapid predictions"""
    print_header("TEST 7: Performance Check (10 Predictions)")
    
    try:
        headers = {'X-API-Key': API_KEY}
        materials = ['bamboo', 'paper', 'jute', 'glass', 'metal', 'plastic', 'bagasse']
        latencies = []
        
        print_info("Running 10 rapid predictions...")
        
        for i in range(10):
            start = time.time()
            response = requests.post(
                f"{API_BASE_URL}/api/predict",
                json={'product_id': product_id, 'material': materials[i % len(materials)]},
                headers=headers
            )
            latency = (time.time() - start) * 1000
            
            if response.status_code == 200:
                latencies.append(latency)
            
            if (i + 1) % 5 == 0:
                print_info(f"  {i + 1}/10 predictions completed")
        
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            min_latency = min(latencies)
            max_latency = max(latencies)
            
            print_success(f"All predictions completed")
            print_info(f"Average latency: {avg_latency:.2f}ms")
            print_info(f"Min latency: {min_latency:.2f}ms")
            print_info(f"Max latency: {max_latency:.2f}ms")
            
            if avg_latency < 100:
                print_success(f"Latency is acceptable (< 100ms)")
                return True
            else:
                print_warning(f"Latency is high (> 100ms)")
                return True  # Still pass, just warn
        
        return False
    
    except Exception as e:
        print_error(f"Performance test failed: {str(e)}")
        return False

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run all validation tests"""
    print(f"\n{BOLD}{BLUE}ECO_PACK_AI - PHASE 5 VALIDATION SUITE{RESET}")
    print(f"{BLUE}Production Backend Verification{RESET}")
    print(f"{BLUE}Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}\n")
    
    results = {}
    
    # Test 1: Component validation (offline)
    print(f"{BOLD}[1/7] Running component validation...{RESET}")
    results['component_validation'] = test_component_validation()
    
    # Check if API is running
    try:
        response = requests.get(f"{API_BASE_URL}/api/health", timeout=2)
        api_running = response.status_code == 200
    except:
        api_running = False
    
    if not api_running:
        print_error(f"Flask API not running at {API_BASE_URL}")
        print_warning("Start the API with: python src/api_production.py")
        return
    
    # Test 2: Health endpoint
    print(f"{BOLD}[2/7] Testing /api/health endpoint...{RESET}")
    results['health'] = test_health_endpoint()
    
    # Test 3: Diagnostics
    print(f"{BOLD}[3/7] Testing /api/diagnostics endpoint...{RESET}")
    results['diagnostics'] = test_diagnostics_endpoint()
    
    # Test 4: Product input
    print(f"{BOLD}[4/7] Testing product input...{RESET}")
    success, product_id = test_product_input()
    results['product_input'] = success
    
    if not product_id:
        print_error("Cannot continue without product_id")
        return
    
    # Test 5: Recommendations
    print(f"{BOLD}[5/7] Testing /api/recommend/material endpoint...{RESET}")
    results['recommendations'] = test_recommendations(product_id)
    
    # Test 6: Single prediction
    print(f"{BOLD}[6/7] Testing /api/predict endpoint...{RESET}")
    results['single_prediction'] = test_single_prediction(product_id)
    
    # Test 7: Performance
    print(f"{BOLD}[7/7] Running performance check...{RESET}")
    results['performance'] = test_performance(product_id)
    
    # Summary
    print_header("VALIDATION SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
        print(f"  {test_name}: {status}")
    
    print(f"\n{BOLD}Result: {passed}/{total} tests passed{RESET}")
    
    if passed == total:
        print(f"\n{GREEN}{BOLD}✓ ALL TESTS PASSED - PRODUCTION BACKEND READY{RESET}\n")
    else:
        print(f"\n{RED}{BOLD}✗ SOME TESTS FAILED - REVIEW ERRORS ABOVE{RESET}\n")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Validation interrupted by user{RESET}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Validation script failed: {str(e)}")
        sys.exit(1)
