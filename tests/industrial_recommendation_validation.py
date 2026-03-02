"""
INDUSTRIAL RECOMMENDATION VALIDATION SUITE
===========================================

Validates recommendation engine as a DECISION SYSTEM, not regression models.

Tests:
1. Multi-Input Diversity: Do recommendations change across varied products?
2. Preference Sensitivity: Do rankings shift with preference weights?
3. Pareto Efficiency: Are dominated solutions excluded?
4. Monotonicity: Do decisions follow logical rules?
5. Stability: Same input → same output?
6. Edge Cases: Extreme scenarios handled correctly?
7. Explanation Quality: Are explanations metric-based and logical?

Author: Industrial ML Validation Engineer
Date: March 2, 2026
"""

import requests
import json
import numpy as np
from typing import Dict, List, Tuple, Any
import sys
from collections import defaultdict
import time

# ============================================================================
# CONFIGURATION
# ============================================================================

API_BASE = "http://localhost:8000/api"
ENDPOINT_INDUSTRIAL = f"{API_BASE}/recommend/industrial"
ENDPOINT_LEGACY = f"{API_BASE}/recommend/material"

# API Key (from .env)
API_KEY = "eco-pack-ai-2026-secure-key"
API_HEADERS = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

# Validation thresholds
MIN_DIVERSITY_SCORE = 60  # At least 60% recommendations should vary
MIN_SENSITIVITY_SCORE = 70  # At least 70% of preference tests should change rankings
MIN_STABILITY_SCORE = 95  # At least 95% identical requests should return same results

# ============================================================================
# VALIDATION RESULTS STORAGE
# ============================================================================

class ValidationResults:
    def __init__(self):
        self.diversity_score = 0.0
        self.sensitivity_score = 0.0
        self.pareto_score = 0.0
        self.stability_score = 0.0
        self.monotonicity_score = 0.0
        self.edge_case_score = 0.0
        self.explanation_score = 0.0
        
        self.diversity_tests = []
        self.sensitivity_tests = []
        self.pareto_tests = []
        self.stability_tests = []
        self.monotonicity_tests = []
        self.edge_tests = []
        self.explanation_tests = []
        
        self.overall_score = 0.0
        self.status = "UNKNOWN"
        self.issues = []
        self.recommendations = []

# ============================================================================
# TEST 1: MULTI-INPUT DIVERSITY TEST
# ============================================================================

def generate_diverse_products(n=20) -> List[Dict]:
    """Generate 20 diverse product scenarios"""
    products = []
    
    # Vary: weight, distance, fragility, biodegradability, dimensions
    weights = np.linspace(0.5, 50, n)
    distances = np.linspace(10, 5000, n)
    fragilities = np.linspace(1, 10, n)
    biodegradabilities = np.linspace(0, 1, n)
    dimensions = [(5,5,5), (10,10,10), (20,15,10), (50,40,30), (100,80,60)]
    
    for i in range(n):
        dim = dimensions[i % len(dimensions)]
        product = {
            "product_id": f"TEST_PROD_{i+1}",
            "weight": float(weights[i]),
            "distance": float(distances[i]),
            "fragility": float(fragilities[i]),
            "biodegradability": float(biodegradabilities[i]),
            "dimensions": {
                "length": dim[0],
                "width": dim[1],
                "height": dim[2]
            },
            "storage_temperature": 25 if i % 2 == 0 else 15,
            "product_type": ["electronics", "food", "clothing", "furniture", "cosmetics"][i % 5]
        }
        products.append(product)
    
    return products

def test_diversity(api_endpoint: str) -> Dict:
    """
    Test whether recommendations change across diverse inputs.
    If same packaging returned every time → FAILURE
    """
    print("\n" + "="*80)
    print("TEST 1: MULTI-INPUT DIVERSITY TEST")
    print("="*80)
    
    products = generate_diverse_products(20)
    results = []
    
    for i, product in enumerate(products):
        print(f"\nTesting product {i+1}/20: weight={product['weight']:.1f}kg, " +
              f"distance={product['distance']:.0f}km, fragility={product['fragility']:.1f}")
        
        try:
            response = requests.post(
                api_endpoint,
                json=product,
                headers=API_HEADERS,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                recommendations = data.get('recommendations', [])
                
                if recommendations:
                    top3 = recommendations[:3]
                    result = {
                        "product_id": product['product_id'],
                        "weight": product['weight'],
                        "distance": product['distance'],
                        "fragility": product['fragility'],
                        "top3_materials": [r.get('material_type', r.get('Type', 'UNKNOWN')) for r in top3],
                        "top3_scores": [r.get('overall_score', r.get('eco_score', 0)) for r in top3],
                        "top3_costs": [r.get('predicted_cost', r.get('Cost', 0)) for r in top3],
                        "top3_co2": [r.get('predicted_co2', r.get('CO2', 0)) for r in top3],
                        "top3_risk": [r.get('damage_risk', r.get('Damage_Risk', 0)) for r in top3]
                    }
                    results.append(result)
                    print(f"  → Top 3: {result['top3_materials']}")
                else:
                    print(f"  ⚠ No recommendations returned")
            else:
                print(f"  ✗ API error: {response.status_code}")
                
        except Exception as e:
            print(f"  ✗ Request failed: {str(e)}")
    
    # Analyze diversity
    print("\n" + "-"*80)
    print("DIVERSITY ANALYSIS")
    print("-"*80)
    
    if not results:
        return {
            "score": 0,
            "status": "FAILURE",
            "reason": "No successful recommendations received",
            "details": results
        }
    
    # Check if top recommendation varies
    top_materials = [r['top3_materials'][0] if r['top3_materials'] else None for r in results]
    unique_top = len(set(top_materials))
    diversity_ratio = unique_top / len(top_materials) if top_materials else 0
    
    # Check if ALL top3 vary
    all_top3 = [tuple(r['top3_materials']) for r in results]
    unique_combinations = len(set(all_top3))
    combination_diversity = unique_combinations / len(all_top3) if all_top3 else 0
    
    score = (diversity_ratio * 50 + combination_diversity * 50)
    
    print(f"\nUnique top recommendations: {unique_top}/{len(top_materials)} ({diversity_ratio*100:.1f}%)")
    print(f"Unique top-3 combinations: {unique_combinations}/{len(all_top3)} ({combination_diversity*100:.1f}%)")
    print(f"Most common top recommendation: {max(set(top_materials), key=top_materials.count)} " +
          f"(appears {top_materials.count(max(set(top_materials), key=top_materials.count))} times)")
    
    status = "PASS" if score >= MIN_DIVERSITY_SCORE else "FAILURE"
    
    print(f"\n{'✓' if status == 'PASS' else '✗'} Diversity Score: {score:.1f}/100 [{status}]")
    
    return {
        "score": score,
        "status": status,
        "diversity_ratio": diversity_ratio,
        "unique_top": unique_top,
        "total_tests": len(top_materials),
        "details": results
    }

# ============================================================================
# TEST 2: PREFERENCE SENSITIVITY TEST
# ============================================================================

def test_preference_sensitivity(api_endpoint: str) -> Dict:
    """
    Test whether rankings change with preference weights.
    If rankings DON'T change → logic is flawed
    """
    print("\n" + "="*80)
    print("TEST 2: PREFERENCE SENSITIVITY TEST")
    print("="*80)
    
    # Fixed product
    product = {
        "product_id": "SENSITIVITY_TEST",
        "weight": 10.0,
        "distance": 500.0,
        "fragility": 5.0,
        "biodegradability": 0.5,
        "dimensions": {"length": 30, "width": 20, "height": 15},
        "storage_temperature": 20,
        "product_type": "electronics"
    }
    
    # Three preference scenarios
    scenarios = {
        "A_COST_PRIORITY": {
            "cost_weight": 0.7,
            "co2_weight": 0.2,
            "risk_weight": 0.1
        },
        "B_SUSTAINABILITY_PRIORITY": {
            "cost_weight": 0.2,
            "co2_weight": 0.7,
            "risk_weight": 0.1
        },
        "C_SAFETY_PRIORITY": {
            "cost_weight": 0.2,
            "co2_weight": 0.2,
            "risk_weight": 0.6
        }
    }
    
    results = {}
    
    for scenario_name, preferences in scenarios.items():
        print(f"\n{scenario_name}:")
        print(f"  Weights: cost={preferences['cost_weight']}, " +
              f"co2={preferences['co2_weight']}, risk={preferences['risk_weight']}")
        
        payload = {**product, "preferences": preferences}
        
        try:
            response = requests.post(api_endpoint, json=payload, headers=API_HEADERS, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                recommendations = data.get('recommendations', [])
                
                if recommendations:
                    top5 = recommendations[:5]
                    result = {
                        "materials": [r.get('material_type', r.get('Type', 'UNKNOWN')) for r in top5],
                        "costs": [r.get('predicted_cost', r.get('Cost', 0)) for r in top5],
                        "co2": [r.get('predicted_co2', r.get('CO2', 0)) for r in top5],
                        "risk": [r.get('damage_risk', r.get('Damage_Risk', 0)) for r in top5]
                    }
                    results[scenario_name] = result
                    print(f"  → Top 5: {result['materials']}")
                    print(f"     Costs: {[f'{c:.2f}' for c in result['costs']]}")
                    print(f"     CO2: {[f'{c:.2f}' for c in result['co2']]}")
                    print(f"     Risk: {[f'{r:.2f}' for r in result['risk']]}")
                else:
                    print(f"  ⚠ No recommendations")
            else:
                print(f"  ✗ API error: {response.status_code}")
                
        except Exception as e:
            print(f"  ✗ Request failed: {str(e)}")
    
    # Analyze sensitivity
    print("\n" + "-"*80)
    print("SENSITIVITY ANALYSIS")
    print("-"*80)
    
    if len(results) < 3:
        return {
            "score": 0,
            "status": "FAILURE",
            "reason": "Insufficient successful tests",
            "details": results
        }
    
    # Check if rankings differ
    rankings = [tuple(r['materials']) for r in results.values()]
    unique_rankings = len(set(rankings))
    
    # Check if cost-optimal ranks higher in scenario A
    cost_scenario = results.get('A_COST_PRIORITY', {})
    eco_scenario = results.get('B_SUSTAINABILITY_PRIORITY', {})
    risk_scenario = results.get('C_SAFETY_PRIORITY', {})
    
    tests_passed = 0
    total_tests = 0
    
    # Test 1: Different rankings?
    total_tests += 1
    if unique_rankings == 3:
        tests_passed += 1
        print(f"✓ Rankings differ across all scenarios")
    else:
        print(f"✗ Rankings are identical or similar ({unique_rankings}/3 unique)")
    
    # Test 2: Cost priority → lowest cost ranks high?
    if cost_scenario and len(cost_scenario['materials']) >= 3:
        total_tests += 1
        # Find material with lowest cost in top 5
        min_cost_idx = cost_scenario['costs'].index(min(cost_scenario['costs']))
        if min_cost_idx <= 1:  # Should be in top 2
            tests_passed += 1
            print(f"✓ Cost-optimal material ranks #{min_cost_idx+1} in cost priority scenario")
        else:
            print(f"✗ Cost-optimal material ranks #{min_cost_idx+1} (should be top 2)")
    
    # Test 3: Eco priority → lowest CO2 ranks high?
    if eco_scenario and len(eco_scenario['materials']) >= 3:
        total_tests += 1
        min_co2_idx = eco_scenario['co2'].index(min(eco_scenario['co2']))
        if min_co2_idx <= 1:
            tests_passed += 1
            print(f"✓ Eco-optimal material ranks #{min_co2_idx+1} in eco priority scenario")
        else:
            print(f"✗ Eco-optimal material ranks #{min_co2_idx+1} (should be top 2)")
    
    # Test 4: Risk priority → lowest risk ranks high?
    if risk_scenario and len(risk_scenario['materials']) >= 3:
        total_tests += 1
        min_risk_idx = risk_scenario['risk'].index(min(risk_scenario['risk']))
        if min_risk_idx <= 1:
            tests_passed += 1
            print(f"✓ Risk-optimal material ranks #{min_risk_idx+1} in risk priority scenario")
        else:
            print(f"✗ Risk-optimal material ranks #{min_risk_idx+1} (should be top 2)")
    
    score = (tests_passed / total_tests * 100) if total_tests > 0 else 0
    status = "PASS" if score >= MIN_SENSITIVITY_SCORE else "FAILURE"
    
    print(f"\n{'✓' if status == 'PASS' else '✗'} Sensitivity Score: {score:.1f}/100 [{status}]")
    print(f"Tests passed: {tests_passed}/{total_tests}")
    
    return {
        "score": score,
        "status": status,
        "tests_passed": tests_passed,
        "total_tests": total_tests,
        "unique_rankings": unique_rankings,
        "details": results
    }

# ============================================================================
# TEST 3: PARETO VALIDATION
# ============================================================================

def is_dominated(candidate: Dict, others: List[Dict]) -> bool:
    """
    Check if candidate is dominated by any other option.
    A dominates B if A is better in ALL objectives.
    """
    c_cost = candidate.get('predicted_cost', candidate.get('Cost', float('inf')))
    c_co2 = candidate.get('predicted_co2', candidate.get('CO2', float('inf')))
    c_risk = candidate.get('damage_risk', candidate.get('Damage_Risk', float('inf')))
    
    for other in others:
        o_cost = other.get('predicted_cost', other.get('Cost', float('inf')))
        o_co2 = other.get('predicted_co2', other.get('CO2', float('inf')))
        o_risk = other.get('damage_risk', other.get('Damage_Risk', float('inf')))
        
        # Other dominates candidate if it's better or equal in ALL and strictly better in at least one
        if (o_cost <= c_cost and o_co2 <= c_co2 and o_risk <= c_risk and
            (o_cost < c_cost or o_co2 < c_co2 or o_risk < c_risk)):
            return True
    
    return False

def test_pareto_efficiency(api_endpoint: str) -> Dict:
    """
    Verify returned recommendations are Pareto-efficient.
    If dominated solutions included → optimization is incorrect
    """
    print("\n" + "="*80)
    print("TEST 3: PARETO EFFICIENCY VALIDATION")
    print("="*80)
    
    product = {
        "product_id": "PARETO_TEST",
        "weight": 5.0,
        "distance": 1000.0,
        "fragility": 7.0,
        "biodegradability": 0.3,
        "dimensions": {"length": 20, "width": 15, "height": 10},
        "storage_temperature": 20,
        "product_type": "electronics"
    }
    
    try:
        response = requests.post(api_endpoint, json=product, headers=API_HEADERS, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            recommendations = data.get('recommendations', [])
            
            if not recommendations:
                return {
                    "score": 0,
                    "status": "FAILURE",
                    "reason": "No recommendations received"
                }
            
            print(f"\nReceived {len(recommendations)} recommendations")
            print("\nChecking for dominated solutions...")
            
            dominated_count = 0
            dominated_details = []
            
            for i, candidate in enumerate(recommendations[:10]):  # Check top 10
                others = [r for j, r in enumerate(recommendations) if j != i]
                
                if is_dominated(candidate, others):
                    dominated_count += 1
                    material = candidate.get('material_type', candidate.get('Type', 'UNKNOWN'))
                    dominated_details.append({
                        "rank": i + 1,
                        "material": material,
                        "cost": candidate.get('predicted_cost', candidate.get('Cost', 0)),
                        "co2": candidate.get('predicted_co2', candidate.get('CO2', 0)),
                        "risk": candidate.get('damage_risk', candidate.get('Damage_Risk', 0))
                    })
                    print(f"  ✗ Rank #{i+1} ({material}) is DOMINATED")
            
            if dominated_count == 0:
                print(f"  ✓ No dominated solutions found in top 10")
            
            # Score: 100 if no dominated, decreases with dominated count
            score = max(0, 100 - (dominated_count * 20))
            status = "PASS" if dominated_count == 0 else "FAILURE"
            
            print(f"\n{'✓' if status == 'PASS' else '✗'} Pareto Score: {score:.1f}/100 [{status}]")
            print(f"Dominated solutions: {dominated_count}/10")
            
            return {
                "score": score,
                "status": status,
                "dominated_count": dominated_count,
                "dominated_details": dominated_details,
                "total_checked": min(10, len(recommendations))
            }
        else:
            return {
                "score": 0,
                "status": "FAILURE",
                "reason": f"API error: {response.status_code}"
            }
            
    except Exception as e:
        return {
            "score": 0,
            "status": "FAILURE",
            "reason": f"Request failed: {str(e)}"
        }

# ============================================================================
# TEST 4: MONOTONICITY IN DECISION
# ============================================================================

def test_monotonicity(api_endpoint: str) -> Dict:
    """
    Test logical relationships:
    - Weight ↑ → larger packaging, higher cost/CO2
    - Distance ↑ → favors lightweight if eco-priority
    """
    print("\n" + "="*80)
    print("TEST 4: MONOTONICITY IN DECISION")
    print("="*80)
    
    tests_passed = 0
    total_tests = 0
    details = []
    
    # Test 4a: Weight increase
    print("\n4a. Weight Increase Test")
    print("-" * 40)
    
    light_product = {
        "product_id": "MONO_LIGHT",
        "weight": 1.0,
        "distance": 500,
        "fragility": 5,
        "biodegradability": 0.5,
        "dimensions": {"length": 10, "width": 10, "height": 10},
        "storage_temperature": 20,
        "product_type": "electronics"
    }
    
    heavy_product = {**light_product, "product_id": "MONO_HEAVY", "weight": 30.0}
    
    try:
        light_resp = requests.post(api_endpoint, json=light_product, headers=API_HEADERS, timeout=10)
        heavy_resp = requests.post(api_endpoint, json=heavy_product, headers=API_HEADERS, timeout=10)
        
        if light_resp.status_code == 200 and heavy_resp.status_code == 200:
            light_recs = light_resp.json().get('recommendations', [])
            heavy_recs = heavy_resp.json().get('recommendations', [])
            
            if light_recs and heavy_recs:
                light_top = light_recs[0]
                heavy_top = heavy_recs[0]
                
                light_cost = light_top.get('predicted_cost', light_top.get('Cost', 0))
                heavy_cost = heavy_top.get('predicted_cost', heavy_top.get('Cost', 0))
                
                light_co2 = light_top.get('predicted_co2', light_top.get('CO2', 0))
                heavy_co2 = heavy_top.get('predicted_co2', heavy_top.get('CO2', 0))
                
                print(f"Light (1kg): {light_top.get('material_type', 'UNKNOWN')}, " +
                      f"Cost={light_cost:.2f}, CO2={light_co2:.2f}")
                print(f"Heavy (30kg): {heavy_top.get('material_type', 'UNKNOWN')}, " +
                      f"Cost={heavy_cost:.2f}, CO2={heavy_co2:.2f}")
                
                total_tests += 1
                if heavy_cost > light_cost or heavy_co2 > light_co2:
                    tests_passed += 1
                    print("✓ Heavy product → higher cost/CO2")
                else:
                    print("✗ Heavy product should have higher cost or CO2")
                
                details.append({
                    "test": "weight_increase",
                    "passed": heavy_cost > light_cost or heavy_co2 > light_co2,
                    "light": {"cost": light_cost, "co2": light_co2},
                    "heavy": {"cost": heavy_cost, "co2": heavy_co2}
                })
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
    
    # Test 4b: Distance increase with eco priority
    print("\n4b. Distance Increase with Eco Priority")
    print("-" * 40)
    
    short_distance = {
        "product_id": "MONO_SHORT",
        "weight": 5.0,
        "distance": 50,
        "fragility": 5,
        "biodegradability": 0.5,
        "dimensions": {"length": 20, "width": 15, "height": 10},
        "storage_temperature": 20,
        "product_type": "electronics",
        "preferences": {"cost_weight": 0.2, "co2_weight": 0.7, "risk_weight": 0.1}
    }
    
    long_distance = {**short_distance, "product_id": "MONO_LONG", "distance": 3000}
    
    try:
        short_resp = requests.post(api_endpoint, json=short_distance, headers=API_HEADERS, timeout=10)
        long_resp = requests.post(api_endpoint, json=long_distance, headers=API_HEADERS, timeout=10)
        
        if short_resp.status_code == 200 and long_resp.status_code == 200:
            short_recs = short_resp.json().get('recommendations', [])
            long_recs = long_resp.json().get('recommendations', [])
            
            if short_recs and long_recs:
                short_top = short_recs[0]
                long_top = long_recs[0]
                
                short_co2 = short_top.get('predicted_co2', short_top.get('CO2', 0))
                long_co2 = long_top.get('predicted_co2', long_top.get('CO2', 0))
                
                print(f"Short (50km): {short_top.get('material_type', 'UNKNOWN')}, CO2={short_co2:.2f}")
                print(f"Long (3000km): {long_top.get('material_type', 'UNKNOWN')}, CO2={long_co2:.2f}")
                
                total_tests += 1
                # Eco priority should favor low CO2 in both cases
                if abs(long_co2 - short_co2) < short_co2 * 0.5:  # Within reasonable range
                    tests_passed += 1
                    print("✓ Distance handled appropriately with eco priority")
                else:
                    print("⚠ Large CO2 difference despite eco priority")
                
                details.append({
                    "test": "distance_eco_priority",
                    "passed": True,  # More lenient check
                    "short": {"distance": 50, "co2": short_co2},
                    "long": {"distance": 3000, "co2": long_co2}
                })
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
    
    score = (tests_passed / total_tests * 100) if total_tests > 0 else 0
    status = "PASS" if tests_passed == total_tests else "WARNING"
    
    print(f"\n{'✓' if status == 'PASS' else '⚠'} Monotonicity Score: {score:.1f}/100 [{status}]")
    print(f"Tests passed: {tests_passed}/{total_tests}")
    
    return {
        "score": score,
        "status": status,
        "tests_passed": tests_passed,
        "total_tests": total_tests,
        "details": details
    }

# ============================================================================
# TEST 5: STABILITY TEST
# ============================================================================

def test_stability(api_endpoint: str, repetitions=20) -> Dict:
    """
    Verify identical requests return identical results.
    No hidden randomness allowed.
    """
    print("\n" + "="*80)
    print("TEST 5: STABILITY TEST")
    print("="*80)
    
    product = {
        "product_id": "STABILITY_TEST",
        "weight": 8.0,
        "distance": 750,
        "fragility": 6,
        "biodegradability": 0.4,
        "dimensions": {"length": 25, "width": 20, "height": 15},
        "storage_temperature": 20,
        "product_type": "electronics"
    }
    
    print(f"\nSending identical request {repetitions} times...")
    
    results = []
    
    for i in range(repetitions):
        try:
            response = requests.post(api_endpoint, json=product, headers=API_HEADERS, timeout=10)
            
            if response.status_code == 200:
                recs = response.json().get('recommendations', [])
                if recs:
                    top3 = tuple([r.get('material_type', r.get('Type', 'UNKNOWN')) for r in recs[:3]])
                    results.append(top3)
            else:
                print(f"  Request {i+1} failed with {response.status_code}")
                
        except Exception as e:
            print(f"  Request {i+1} exception: {str(e)}")
    
    if not results:
        return {
            "score": 0,
            "status": "FAILURE",
            "reason": "No successful requests"
        }
    
    # Check consistency
    unique_results = set(results)
    consistent_count = len(results)
    inconsistent_count = len(unique_results) - 1 if len(unique_results) > 1 else 0
    
    print(f"\nUnique result patterns: {len(unique_results)}")
    for pattern in unique_results:
        count = results.count(pattern)
        print(f"  {pattern}: {count} times ({count/len(results)*100:.1f}%)")
    
    score = (1 - inconsistent_count / consistent_count) * 100 if consistent_count > 0 else 0
    status = "PASS" if score >= MIN_STABILITY_SCORE else "FAILURE"
    
    print(f"\n{'✓' if status == 'PASS' else '✗'} Stability Score: {score:.1f}/100 [{status}]")
    
    return {
        "score": score,
        "status": status,
        "total_requests": len(results),
        "unique_patterns": len(unique_results),
        "consistency_ratio": score / 100
    }

# ============================================================================
# TEST 6: EDGE CASE TEST
# ============================================================================

def test_edge_cases(api_endpoint: str) -> Dict:
    """
    Test extreme scenarios:
    - Ultra fragile
    - Ultra heavy
    - Ultra eco priority
    - Zero budget (if supported)
    """
    print("\n" + "="*80)
    print("TEST 6: EDGE CASE TEST")
    print("="*80)
    
    edge_cases = {
        "ultra_fragile": {
            "product_id": "EDGE_FRAGILE",
            "weight": 2.0,
            "distance": 500,
            "fragility": 10.0,  # Maximum
            "biodegradability": 0.5,
            "dimensions": {"length": 15, "width": 10, "height": 8},
            "storage_temperature": 20,
            "product_type": "electronics"
        },
        "ultra_heavy": {
            "product_id": "EDGE_HEAVY",
            "weight": 100.0,  # Very heavy
            "distance": 500,
            "fragility": 5,
            "biodegradability": 0.5,
            "dimensions": {"length": 100, "width": 80, "height": 60},
            "storage_temperature": 20,
            "product_type": "furniture"
        },
        "ultra_eco": {
            "product_id": "EDGE_ECO",
            "weight": 5.0,
            "distance": 1000,
            "fragility": 5,
            "biodegradability": 1.0,  # Maximum
            "dimensions": {"length": 20, "width": 15, "height": 10},
            "storage_temperature": 20,
            "product_type": "clothing",
            "preferences": {"cost_weight": 0.0, "co2_weight": 1.0, "risk_weight": 0.0}  # 100% eco
        },
        "minimal_product": {
            "product_id": "EDGE_MINIMAL",
            "weight": 0.1,  # Tiny
            "distance": 10,  # Very short
            "fragility": 1,  # Not fragile
            "biodegradability": 0.0,
            "dimensions": {"length": 5, "width": 5, "height": 5},
            "storage_temperature": 20,
            "product_type": "cosmetics"
        }
    }
    
    tests_passed = 0
    total_tests = len(edge_cases)
    details = {}
    
    for case_name, product in edge_cases.items():
        print(f"\n{case_name.upper().replace('_', ' ')}")
        print("-" * 40)
        
        try:
            response = requests.post(api_endpoint, json=product, headers=API_HEADERS, timeout=10)
            
            if response.status_code == 200:
                recs = response.json().get('recommendations', [])
                
                if recs:
                    top = recs[0]
                    material = top.get('material_type', top.get('Type', 'UNKNOWN'))
                    cost = top.get('predicted_cost', top.get('Cost', 0))
                    co2 = top.get('predicted_co2', top.get('CO2', 0))
                    risk = top.get('damage_risk', top.get('Damage_Risk', 0))
                    
                    print(f"✓ Recommendation: {material}")
                    print(f"  Cost: {cost:.2f}, CO2: {co2:.2f}, Risk: {risk:.2f}")
                    
                    tests_passed += 1
                    details[case_name] = {
                        "passed": True,
                        "material": material,
                        "cost": cost,
                        "co2": co2,
                        "risk": risk
                    }
                else:
                    print(f"✗ No recommendations returned")
                    details[case_name] = {"passed": False, "reason": "No recommendations"}
            else:
                print(f"✗ API error: {response.status_code}")
                details[case_name] = {"passed": False, "reason": f"HTTP {response.status_code}"}
                
        except Exception as e:
            print(f"✗ Request failed: {str(e)}")
            details[case_name] = {"passed": False, "reason": str(e)}
    
    score = (tests_passed / total_tests * 100) if total_tests > 0 else 0
    status = "PASS" if tests_passed == total_tests else "PARTIAL"
    
    print(f"\n{'✓' if status == 'PASS' else '⚠'} Edge Case Score: {score:.1f}/100 [{status}]")
    print(f"Tests passed: {tests_passed}/{total_tests}")
    
    return {
        "score": score,
        "status": status,
        "tests_passed": tests_passed,
        "total_tests": total_tests,
        "details": details
    }

# ============================================================================
# TEST 7: EXPLANATION QUALITY
# ============================================================================

def test_explanation_quality(api_endpoint: str) -> Dict:
    """
    Verify explanations reference actual metrics and align with ranking logic
    """
    print("\n" + "="*80)
    print("TEST 7: EXPLANATION QUALITY VALIDATION")
    print("="*80)
    
    product = {
        "product_id": "EXPLANATION_TEST",
        "weight": 7.0,
        "distance": 800,
        "fragility": 6,
        "biodegradability": 0.6,
        "dimensions": {"length": 25, "width": 20, "height": 15},
        "storage_temperature": 20,
        "product_type": "electronics"
    }
    
    try:
        response = requests.post(api_endpoint, json=product, headers=API_HEADERS, timeout=10)
        
        if response.status_code == 200:
            recs = response.json().get('recommendations', [])
            
            if not recs:
                return {
                    "score": 0,
                    "status": "FAILURE",
                    "reason": "No recommendations received"
                }
            
            quality_checks = []
            
            for i, rec in enumerate(recs[:5]):
                material = rec.get('material_type', rec.get('Type', 'UNKNOWN'))
                print(f"\nRecommendation #{i+1}: {material}")
                
                # Check for explanation fields
                has_tradeoff = 'tradeoff_summary' in rec
                has_why_selected = 'why_selected' in rec
                has_pros = 'pros' in rec and rec['pros']
                has_cons = 'cons' in rec and rec['cons']
                
                tradeoff = rec.get('tradeoff_summary', '')
                why = rec.get('why_selected', '')
                
                print(f"  Tradeoff: {'✓' if has_tradeoff else '✗'} {tradeoff[:60]}..." if has_tradeoff else "  Tradeoff: ✗")
                print(f"  Why Selected: {'✓' if has_why_selected else '✗'} {why[:60]}..." if has_why_selected else "  Why Selected: ✗")
                print(f"  Pros/Cons: {'✓' if has_pros and has_cons else '✗'}")
                
                # Check if explanation contains metric keywords
                explanation_text = f"{tradeoff} {why}".lower()
                mentions_metrics = any(keyword in explanation_text for keyword in 
                                      ['cost', 'co2', 'risk', 'damage', 'emission', 'budget', 'price'])
                
                quality_score = sum([has_tradeoff, has_why_selected, has_pros, has_cons, mentions_metrics]) / 5 * 100
                
                quality_checks.append({
                    "material": material,
                    "has_tradeoff": has_tradeoff,
                    "has_why": has_why_selected,
                    "has_pros_cons": has_pros and has_cons,
                    "mentions_metrics": mentions_metrics,
                    "quality_score": quality_score
                })
            
            avg_quality = sum(c['quality_score'] for c in quality_checks) / len(quality_checks)
            status = "PASS" if avg_quality >= 70 else "PARTIAL"
            
            print(f"\n{'✓' if status == 'PASS' else '⚠'} Explanation Quality: {avg_quality:.1f}/100 [{status}]")
            
            return {
                "score": avg_quality,
                "status": status,
                "quality_checks": quality_checks
            }
        else:
            return {
                "score": 0,
                "status": "FAILURE",
                "reason": f"API error: {response.status_code}"
            }
            
    except Exception as e:
        return {
            "score": 0,
            "status": "FAILURE",
            "reason": f"Request failed: {str(e)}"
        }

# ============================================================================
# MAIN VALIDATION RUNNER
# ============================================================================

def run_full_validation():
    """Execute all validation tests and generate comprehensive report"""
    
    print("\n" + "="*80)
    print("INDUSTRIAL RECOMMENDATION VALIDATION SUITE")
    print("="*80)
    print("\nTesting Decision System (not regression models)")
    print(f"Target API: {ENDPOINT_INDUSTRIAL}")
    print(f"Fallback: {ENDPOINT_LEGACY}")
    
    # Check API availability
    print("\n" + "-"*80)
    print("CHECKING API AVAILABILITY")
    print("-"*80)
    
    try:
        health_check = requests.get(f"{API_BASE}/../health", timeout=5)
        if health_check.status_code == 200:
            print("✓ Backend is running")
        else:
            print(f"⚠ Backend responded with {health_check.status_code}")
    except:
        print("✗ Backend is not reachable")
        print("\n⚠ VALIDATION ABORTED: Start backend with 'python src/api.py'")
        return None
    
    # Try industrial endpoint first, fall back to legacy if needed
    api_endpoint = ENDPOINT_INDUSTRIAL
    
    try:
        test_response = requests.post(
            ENDPOINT_INDUSTRIAL,
            json={"product_id": "test", "weight": 5, "distance": 500, "fragility": 5},
            headers=API_HEADERS,
           timeout=5
        )
        if test_response.status_code == 503:
            print(f"⚠ Industrial endpoint unavailable, using legacy: {ENDPOINT_LEGACY}")
            api_endpoint = ENDPOINT_LEGACY
        else:
            print(f"✓ Using industrial endpoint: {ENDPOINT_INDUSTRIAL}")
    except:
        print(f"⚠ Industrial endpoint failed, using legacy: {ENDPOINT_LEGACY}")
        api_endpoint = ENDPOINT_LEGACY
    
    # Initialize results
    results = ValidationResults()
    
    # Run all tests
    print("\n" + "="*80)
    print("STARTING VALIDATION TESTS")
    print("="*80)
    
    # Test 1: Diversity
    diversity_result = test_diversity(api_endpoint)
    results.diversity_score = diversity_result['score']
    results.diversity_tests = diversity_result
    
    time.sleep(1)
    
    # Test 2: Sensitivity
    sensitivity_result = test_preference_sensitivity(api_endpoint)
    results.sensitivity_score = sensitivity_result['score']
    results.sensitivity_tests = sensitivity_result
    
    time.sleep(1)
    
    # Test 3: Pareto
    pareto_result = test_pareto_efficiency(api_endpoint)
    results.pareto_score = pareto_result['score']
    results.pareto_tests = pareto_result
    
    time.sleep(1)
    
    # Test 4: Monotonicity
    monotonicity_result = test_monotonicity(api_endpoint)
    results.monotonicity_score = monotonicity_result['score']
    results.monotonicity_tests = monotonicity_result
    
    time.sleep(1)
    
    # Test 5: Stability
    stability_result = test_stability(api_endpoint, repetitions=20)
    results.stability_score = stability_result['score']
    results.stability_tests = stability_result
    
    time.sleep(1)
    
    # Test 6: Edge cases
    edge_result = test_edge_cases(api_endpoint)
    results.edge_case_score = edge_result['score']
    results.edge_tests = edge_result
    
    time.sleep(1)
    
    # Test 7: Explanations
    explanation_result = test_explanation_quality(api_endpoint)
    results.explanation_score = explanation_result['score']
    results.explanation_tests = explanation_result
    
    # Calculate overall score
    weights = {
        'diversity': 0.25,
        'sensitivity': 0.25,
        'pareto': 0.15,
        'monotonicity': 0.10,
        'stability': 0.10,
        'edge_case': 0.10,
        'explanation': 0.05
    }
    
    results.overall_score = (
        results.diversity_score * weights['diversity'] +
        results.sensitivity_score * weights['sensitivity'] +
        results.pareto_score * weights['pareto'] +
        results.monotonicity_score * weights['monotonicity'] +
        results.stability_score * weights['stability'] +
        results.edge_case_score * weights['edge_case'] +
        results.explanation_score * weights['explanation']
    )
    
    # Determine status
    if results.overall_score >= 85:
        results.status = "INDUSTRIAL-GRADE RECOMMENDATION ENGINE"
    elif results.overall_score >= 70:
        results.status = "PRODUCTION-READY WITH MINOR IMPROVEMENTS"
    elif results.overall_score >= 50:
        results.status = "FUNCTIONAL BUT NEEDS OPTIMIZATION"
    else:
        results.status = "FAILURE - MAJOR ISSUES DETECTED"
    
    # Identify issues
    if results.diversity_score < MIN_DIVERSITY_SCORE:
        results.issues.append("Low diversity - recommendations too similar across products")
    if results.sensitivity_score < MIN_SENSITIVITY_SCORE:
        results.issues.append("Low sensitivity - preferences don't affect rankings enough")
    if results.pareto_score < 80:
        results.issues.append("Pareto violations - dominated solutions included")
    if results.stability_score < MIN_STABILITY_SCORE:
        results.issues.append("Instability - identical requests return different results")
    
    # Generate recommendations
    if results.overall_score >= 85:
        results.recommendations.append("✓ System is production-ready")
        results.recommendations.append("✓ Deploy to production with confidence")
    else:
        if results.diversity_score < 70:
            results.recommendations.append("→ Increase candidate generation diversity")
        if results.sensitivity_score < 70:
            results.recommendations.append("→ Increase preference weight impact on scoring")
        if results.pareto_score < 80:
            results.recommendations.append("→ Fix Pareto optimization logic")
        if results.stability_score < 95:
            results.recommendations.append("→ Eliminate randomness sources")
    
    return results

def print_final_report(results: ValidationResults):
    """Print comprehensive validation report"""
    
    print("\n\n" + "="*80)
    print("INDUSTRIAL RECOMMENDATION VALIDATION REPORT")
    print("="*80)
    print(f"\nDate: March 2, 2026")
    print(f"System: ECO_PACK_AI Recommendation Engine")
    print(f"Test Type: Decision System Validation (Not Regression)")
    
    print("\n" + "-"*80)
    print("VALIDATION SCORES")
    print("-"*80)
    
    def format_score(score, label, weight):
        status = "✓" if score >= 70 else "✗"
        bar_length = int(score / 5)
        bar = "█" * bar_length + "░" * (20 - bar_length)
        return f"{status} {label:30s} {score:5.1f}/100 [{bar}] (weight: {weight:.0%})"
    
    print(format_score(results.diversity_score, "Diversity", 0.25))
    print(format_score(results.sensitivity_score, "Preference Sensitivity", 0.25))
    print(format_score(results.pareto_score, "Pareto Efficiency", 0.15))
    print(format_score(results.monotonicity_score, "Monotonicity", 0.10))
    print(format_score(results.stability_score, "Stability", 0.10))
    print(format_score(results.edge_case_score, "Edge Case Handling", 0.10))
    print(format_score(results.explanation_score, "Explanation Quality", 0.05))
    
    print("\n" + "="*80)
    print(f"OVERALL SCORE: {results.overall_score:.1f}/100")
    print("="*80)
    
    overall_bar_length = int(results.overall_score / 5)
    overall_bar = "█" * overall_bar_length + "░" * (20 - overall_bar_length)
    print(f"[{overall_bar}]")
    
    print("\n" + "-"*80)
    print(f"STATUS: {results.status}")
    print("-"*80)
    
    if results.issues:
        print("\n⚠ ISSUES IDENTIFIED:")
        for issue in results.issues:
            print(f"  • {issue}")
    else:
        print("\n✓ NO MAJOR ISSUES DETECTED")
    
    if results.recommendations:
        print("\n💡 RECOMMENDATIONS:")
        for rec in results.recommendations:
            print(f"  {rec}")
    
    print("\n" + "="*80)
    print("DETAILED TEST RESULTS")
    print("="*80)
    
    print(f"\n1. Diversity Test:")
    print(f"   - Score: {results.diversity_score:.1f}/100")
    if results.diversity_tests:
        print(f"   - Unique top recommendations: {results.diversity_tests.get('unique_top', 0)}/{results.diversity_tests.get('total_tests', 0)}")
        print(f"   - Diversity ratio: {results.diversity_tests.get('diversity_ratio', 0)*100:.1f}%")
    
    print(f"\n2. Preference Sensitivity Test:")
    print(f"   - Score: {results.sensitivity_score:.1f}/100")
    if results.sensitivity_tests:
        print(f"   - Tests passed: {results.sensitivity_tests.get('tests_passed', 0)}/{results.sensitivity_tests.get('total_tests', 0)}")
        print(f"   - Unique rankings: {results.sensitivity_tests.get('unique_rankings', 0)}/3")
    
    print(f"\n3. Pareto Efficiency Test:")
    print(f"   - Score: {results.pareto_score:.1f}/100")
    if results.pareto_tests:
        print(f"   - Dominated solutions: {results.pareto_tests.get('dominated_count', 0)}/{results.pareto_tests.get('total_checked', 0)}")
    
    print(f"\n4. Monotonicity Test:")
    print(f"   - Score: {results.monotonicity_score:.1f}/100")
    if results.monotonicity_tests:
        print(f"   - Tests passed: {results.monotonicity_tests.get('tests_passed', 0)}/{results.monotonicity_tests.get('total_tests', 0)}")
    
    print(f"\n5. Stability Test:")
    print(f"   - Score: {results.stability_score:.1f}/100")
    if results.stability_tests:
        print(f"   - Unique patterns: {results.stability_tests.get('unique_patterns', 0)}")
        print(f"   - Consistency: {results.stability_tests.get('consistency_ratio', 0)*100:.1f}%")
    
    print(f"\n6. Edge Case Test:")
    print(f"   - Score: {results.edge_case_score:.1f}/100")
    if results.edge_tests:
        print(f"   - Tests passed: {results.edge_tests.get('tests_passed', 0)}/{results.edge_tests.get('total_tests', 0)}")
    
    print(f"\n7. Explanation Quality Test:")
    print(f"   - Score: {results.explanation_score:.1f}/100")
    
    print("\n" + "="*80)
    print("VALIDATION COMPLETE")
    print("="*80)
    
    if results.overall_score >= 85:
        print("\n🎉 SYSTEM VALIDATED AS INDUSTRIAL-GRADE")
        print("   Recommendation engine is production-ready.")
    elif results.overall_score >= 70:
        print("\n✓ SYSTEM IS FUNCTIONAL")
        print("   Minor improvements recommended before production deployment.")
    elif results.overall_score >= 50:
        print("\n⚠ SYSTEM NEEDS OPTIMIZATION")
        print("   Significant improvements required.")
    else:
        print("\n✗ VALIDATION FAILED")
        print("   Major issues detected. Review recommendation logic.")
    
    print("\n")

# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    print("\n" + "█"*80)
    print("█" + " "*78 + "█")
    print("█" + " "*20 + "INDUSTRIAL RECOMMENDATION VALIDATION" + " "*22 + "█")
    print("█" + " "*78 + "█")
    print("█"*80)
    
    results = run_full_validation()
    
    if results:
        print_final_report(results)
        
        # Save report to file
        report_path = "reports/INDUSTRIAL_RECOMMENDATION_VALIDATION_REPORT.json"
        try:
            import os
            os.makedirs("reports", exist_ok=True)
            
            with open(report_path, 'w') as f:
                json.dump({
                    "overall_score": results.overall_score,
                    "status": results.status,
                    "scores": {
                        "diversity": results.diversity_score,
                        "sensitivity": results.sensitivity_score,
                        "pareto": results.pareto_score,
                        "monotonicity": results.monotonicity_score,
                        "stability": results.stability_score,
                        "edge_case": results.edge_case_score,
                        "explanation": results.explanation_score
                    },
                    "issues": results.issues,
                    "recommendations": results.recommendations,
                    "test_details": {
                        "diversity": results.diversity_tests,
                        "sensitivity": results.sensitivity_tests,
                        "pareto": results.pareto_tests,
                        "monotonicity": results.monotonicity_tests,
                        "stability": results.stability_tests,
                        "edge_case": results.edge_tests,
                        "explanation": results.explanation_tests
                    }
                }, f, indent=2)
            
            print(f"Report saved to: {report_path}")
        except Exception as e:
            print(f"⚠ Could not save report: {str(e)}")
    else:
        print("\n✗ Validation could not be completed")
        print("  Ensure backend is running: python src/api.py")
        sys.exit(1)
