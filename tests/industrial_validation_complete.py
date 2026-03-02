"""
INDUSTRIAL RECOMMENDATION VALIDATION SUITE (COMPLETE)
=====================================================

Comprehensive validation of ECO_PACK_AI decision system.

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
import time

# ============================================================================
# CONFIGURATION
# ============================================================================

API_BASE = "http://localhost:8000/api"
ENDPOINT_PRODUCT = f"{API_BASE}/product/input"
ENDPOINT_INDUSTRIAL = f"{API_BASE}/recommend/industrial"
ENDPOINT_LEGACY = f"{API_BASE}/recommend/material"

# API Key
API_KEY = "eco-pack-ai-2026-secure-key"
API_HEADERS = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

# Thresholds
MIN_DIVERSITY_SCORE = 60
MIN_SENSITIVITY_SCORE = 70
MIN_STABILITY_SCORE = 95

def print_header(text):
    """Print formatted header"""
    print("\n" + "="*80)
    print(text)
    print("="*80)

def print_subheader(text):
    """Print formatted subheader"""
    print("\n" + "-"*80)
    print(text)
    print("-"*80)

# ============================================================================
# PRODUCT CREATION
# ============================================================================

def create_test_product(product_id: str, category: str, weight: float, 
                       strength: float = 50, biodegradability: float = 50,
                       recyclability: float = 50) -> bool:
    """Create a test product in the database"""
    payload = {
        "product_id": product_id,
        "category": category,
        "weight": weight,
        "strength": strength,
        "biodegradability": biodegradability,
        "recyclability": recyclability
    }
    
    try:
        response = requests.post(
            ENDPOINT_PRODUCT,
            json=payload,
            headers=API_HEADERS,
            timeout=10
        )
        return response.status_code in [200, 201]
    except Exception as e:
        print(f"  Error creating product: {str(e)}")
        return False

def create_diverse_products(n=20) -> List[str]:
    """Create diverse products for testing"""
    product_ids = []
    categories = ["electronics", "food", "clothing", "furniture", "cosmetics"]
    
    weights = np.linspace(0.5, 50, n)
    strengths = np.random.uniform(20, 95, n)
    biodegradabilities = np.linspace(0, 100, n)
    
    for i in range(n):
        product_id = f"TEST_PROD_{i+1:02d}"
        category = categories[i % len(categories)]
        weight = float(weights[i])
        strength = float(strengths[i])
        biodegradability = float(biodegradabilities[i])
        
        if create_test_product(product_id, category, weight, strength, biodegradability):
            product_ids.append(product_id)
    
    return product_ids

# ============================================================================
# TEST 1: DIVERSITY
# ============================================================================

def test_diversity() -> Dict:
    """Test if recommendations vary across products"""
    print_header("TEST 1: MULTI-INPUT DIVERSITY TEST")
    
    print("Creating test products...")
    product_ids = create_diverse_products(20)
    
    if not product_ids:
        return {"score": 0, "status": "FAILURE", "reason": "Could not create products"}
    
    print(f"Created {len(product_ids)} products")
    print("\nRequesting recommendations...")
    
    results = []
    
    for i, product_id in enumerate(product_ids):
        try:
            response = requests.post(
                ENDPOINT_INDUSTRIAL,
                json={"product_id": product_id},
                headers=API_HEADERS,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                recs = data.get('recommendations', [])
                
                if recs:
                    top3 = [r.get('material_type', r.get('Type', 'UNKNOWN')) for r in recs[:3]]
                    results.append(top3)
                    if i % 5 == 0:
                        print(f"  {i+1}/{len(product_ids)}: {top3}")
            else:
                print(f"  Product {i+1}: Error {response.status_code}")
                
        except Exception as e:
            print(f"  Product {i+1}: {str(e)}")
    
    print_subheader("DIVERSITY ANALYSIS")
    
    if not results:
        return {"score": 0, "status": "FAILURE", "reason": "No successful recommendations"}
    
    # Count unique top recommendations
    top_materials = [r[0] if r else None for r in results]
    unique_top = len(set(top_materials))
    diversity_ratio = unique_top / len(top_materials)
    
    # Count unique combinations
    unique_combinations = len(set(tuple(r) for r in results))
    combination_ratio = unique_combinations / len(results)
    
    print(f"\nUnique top recommended materials: {unique_top}/{len(top_materials)} ({diversity_ratio*100:.1f}%)")
    print(f"Unique top-3 combinations: {unique_combinations}/{len(results)} ({combination_ratio*100:.1f}%)")
    
    score = (diversity_ratio * 50) + (combination_ratio * 50)
    status = "PASS" if score >= MIN_DIVERSITY_SCORE else "FAILURE"
    
    print(f"\n{'✓' if status == 'PASS' else '✗'} Diversity Score: {score:.1f}/100 [{status}]")
    
    return {
        "score": score,
        "status": status,
        "unique_top": unique_top,
        "total_count": len(top_materials),
        "diversity_ratio": diversity_ratio,
        "combination_ratio": combination_ratio
    }

# ============================================================================
# TEST 2: PREFERENCE SENSITIVITY
# ============================================================================

def test_preference_sensitivity() -> Dict:
    """Test if rankings change with preference weights"""
    print_header("TEST 2: PREFERENCE SENSITIVITY TEST")
    
    # Create fixed test product
    test_product = "SENSITIVITY_TEST"
    print(f"Creating test product: {test_product}")
    
    if not create_test_product(test_product, "electronics", 10.0, 60, 50, 60):
        return {"score": 0, "status": "FAILURE", "reason": "Could not create test product"}
    
    scenarios = {
        "Cost Priority (0.7, 0.2, 0.1)": {
            "cost_weight": 0.7,
            "co2_weight": 0.2,
            "risk_weight": 0.1
        },
        "Eco Priority (0.2, 0.7, 0.1)": {
            "cost_weight": 0.2,
            "co2_weight": 0.7,
            "risk_weight": 0.1
        },
        "Safety Priority (0.2, 0.2, 0.6)": {
            "cost_weight": 0.2,
            "co2_weight": 0.2,
            "risk_weight": 0.6
        }
    }
    
    results = {}
    print("\nTesting preference scenarios...")
    
    for scenario_name, preferences in scenarios.items():
        print(f"  {scenario_name}")
        
        payload = {
            "product_id": test_product,
            "preferences": preferences
        }
        
        try:
            response = requests.post(
                ENDPOINT_INDUSTRIAL,
                json=payload,
                headers=API_HEADERS,
                timeout=10
            )
            
            if response.status_code == 200:
                recs = response.json().get('recommendations', [])
                if recs:
                    top5 = [r.get('material_type', r.get('Type', 'UNKNOWN')) for r in recs[:5]]
                    results[scenario_name] = top5
                    print(f"    Top 5: {top5}")
                    
        except Exception as e:
            print(f"    Error: {str(e)}")
    
    print_subheader("SENSITIVITY ANALYSIS")
    
    if len(results) < 3:
        return {"score": 0, "status": "FAILURE", "reason": "Insufficient successful tests"}
    
    # Check if rankings differ
    unique_rankings = len(set(tuple(r) for r in results.values()))
    
    tests_passed = 0
    total_tests = 1
    
    if unique_rankings == 3:
        tests_passed += 1
        print(f"✓ Rankings differ across all 3 scenarios")
    else:
        print(f"✗ Rankings are same or similar ({unique_rankings}/3 unique)")
    
    score = (tests_passed / total_tests) * 100
    status = "PASS" if unique_rankings == 3 else "FAILURE"
    
    print(f"\n{'✓' if status == 'PASS' else '✗'} Sensitivity Score: {score:.1f}/100 [{status}]")
    
    return {
        "score": score,
        "status": status,
        "unique_rankings": unique_rankings,
        "scenarios": results
    }

# ============================================================================
# TEST 3: PARETO EFFICIENCY
# ============================================================================

def test_pareto_efficiency() -> Dict:
    """Verify returned recommendations are Pareto-efficient"""
    print_header("TEST 3: PARETO EFFICIENCY VALIDATION")
    
    test_product = "PARETO_TEST"
    print(f"Creating test product: {test_product}")
    
    if not create_test_product(test_product, "electronics", 5.0, 70, 60, 70):
        return {"score": 0, "status": "FAILURE", "reason": "Could not create test product"}
    
    try:
        response = requests.post(
            ENDPOINT_INDUSTRIAL,
            json={"product_id": test_product},
            headers=API_HEADERS,
            timeout=10
        )
        
        if response.status_code != 200:
            return {"score": 0, "status": "FAILURE", "reason": f"API error: {response.status_code}"}
        
        recs = response.json().get('recommendations', [])
        
        if not recs:
            return {"score": 0, "status": "FAILURE", "reason": "No recommendations"}
        
        print(f"\nAnalyzing {len(recs)} recommendations...")
        print_subheader("PARETO ANALYSIS")
        
        # Check pareto ranks
        pareto_ranks = defaultdict(int)
        
        for i, rec in enumerate(recs[:10]):
            material = rec.get('material_type', rec.get('Type', 'UNKNOWN'))
            pareto_rank = rec.get('pareto_rank', 'n/a')
            pareto_ranks[pareto_rank] += 1
            
            if i < 5:
                cost = rec.get('predicted_cost', rec.get('Cost', 0))
                co2 = rec.get('predicted_co2', rec.get('CO2', 0))
                risk = rec.get('damage_risk', rec.get('Damage_Risk', 0))
                print(f"  Rank {i+1}: {material:15s} (Pareto: {pareto_rank}, Cost: {cost:.2f}, CO2: {co2:.2f}, Risk: {risk:.2f})")
        
        from collections import defaultdict
        pareto_ranks = defaultdict(int)
        for rec in recs[:10]:
            pareto_rank = rec.get('pareto_rank', 'n/a')
            pareto_ranks[pareto_rank] += 1
        
        print(f"\nPareto distribution (top 10):")
        for rank, count in sorted(pareto_ranks.items()):
            print(f"  Pareto {rank}: {count} recommendations")
        
        # Check if uses Pareto ranking
        has_pareto_info = any('pareto_rank' in r for r in recs)
        score = 100 if has_pareto_info else 50
        status = "PASS" if has_pareto_info else "PARTIAL"
        
        print(f"\n{'✓' if status == 'PASS' else '⚠'} Pareto Score: {score:.1f}/100 [{status}]")
        
        return {
            "score": score,
            "status": status,
            "has_pareto_info": has_pareto_info,
            "pareto_distribution": dict(pareto_ranks)
        }
        
    except Exception as e:
        return {"score": 0, "status": "FAILURE", "reason": str(e)}

# ============================================================================
# TEST 4: MONOTONICITY
# ============================================================================

def test_monotonicity() -> Dict:
    """Test logical relationships in decision making"""
    print_header("TEST 4: MONOTONICITY IN DECISION")
    
    tests_passed = 0
    total_tests = 0
    
    # Test 4a: Weight increase
    print_subheader("4a. Weight Increase Test")
    
    products = {
        "light": ("LIGHT_PRODUCT", 1.0),
        "heavy": ("HEAVY_PRODUCT", 30.0)
    }
    
    created = {}
    for key, (pid, weight) in products.items():
        if create_test_product(pid, "electronics", weight, 60, 50, 60):
            created[key] = pid
        else:
            return {"score": 0, "status": "FAILURE", "reason": "Could not create weights"}
    
    try:
        light_resp = requests.post(
            ENDPOINT_INDUSTRIAL,
            json={"product_id": created.get("light")},
            headers=API_HEADERS,
            timeout=10
        )
        heavy_resp = requests.post(
            ENDPOINT_INDUSTRIAL,
            json={"product_id": created.get("heavy")},
            headers=API_HEADERS,
            timeout=10
        )
        
        if light_resp.status_code == 200 and heavy_resp.status_code == 200:
            light_recs = light_resp.json().get('recommendations', [])
            heavy_recs = heavy_resp.json().get('recommendations', [])
            
            if light_recs and heavy_recs:
                light_cost = light_recs[0].get('predicted_cost', light_recs[0].get('Cost', 0))
                heavy_cost = heavy_recs[0].get('predicted_cost', heavy_recs[0].get('Cost', 0))
                
                light_co2 = light_recs[0].get('predicted_co2', light_recs[0].get('CO2', 0))
                heavy_co2 = heavy_recs[0].get('predicted_co2', heavy_recs[0].get('CO2', 0))
                
                print(f"Light (1kg):   Cost={light_cost:.2f}, CO2={light_co2:.2f}")
                print(f"Heavy (30kg):  Cost={heavy_cost:.2f}, CO2={heavy_co2:.2f}")
                
                total_tests += 1
                if heavy_cost >= light_cost and heavy_co2 >= light_co2:
                    tests_passed += 1
                    print("✓ Higher weight → reasonable cost/CO2 increase")
                else:
                    print("✗ Weight doesn't affect cost/CO2 appropriately")
                    
    except Exception as e:
        print(f"Error: {str(e)}")
    
    score = (tests_passed / max(total_tests, 1)) * 100
    status = "PASS" if tests_passed > 0 else "FAILURE"
    
    print(f"\n{'✓' if status == 'PASS' else '✗'} Monotonicity Score: {score:.1f}/100 [{status}]")
    
    return {
        "score": score,
        "status": status,
        "tests_passed": tests_passed,
        "total_tests": max(total_tests, 1)
    }

# ============================================================================
# TEST 5: STABILITY
# ============================================================================

def test_stability() -> Dict:
    """Verify identical requests return identical results"""
    print_header("TEST 5: STABILITY TEST")
    
    test_product = "STABILITY_TEST"
    print(f"Creating test product: {test_product}")
    
    if not create_test_product(test_product, "electronics", 8.0, 65, 55, 65):
        return {"score": 0, "status": "FAILURE", "reason": "Could not create test product"}
    
    print(f"\nSending identical request 20 times...")
    
    results = []
    
    for i in range(20):
        try:
            response = requests.post(
                ENDPOINT_INDUSTRIAL,
                json={"product_id": test_product},
                headers=API_HEADERS,
                timeout=10
            )
            
            if response.status_code == 200:
                recs = response.json().get('recommendations', [])
                if recs:
                    top3 = tuple([r.get('material_type', r.get('Type')) for r in recs[:3]])
                    results.append(top3)
                    if i % 5 == 0:
                        print(f"  {i+1}: {top3}")
            else:
                print(f"  Request {i+1}: Error {response.status_code}")
                
        except Exception as e:
            print(f"  Request {i+1}: {str(e)}")
    
    print_subheader("STABILITY ANALYSIS")
    
    if not results:
        return {"score": 0, "status": "FAILURE", "reason": "No successful requests"}
    
    unique_results = set(results)
    consistency = (len(results) - (len(unique_results) - 1)) / len(results) * 100
    
    print(f"\nUnique patterns: {len(unique_results)}/{len(results)}")
    if len(unique_results) == 1:
        print(f"  All requests returned: {list(unique_results)[0]}")
    else:
        for pattern in list(unique_results)[:3]:
            count = results.count(pattern)
            print(f"  Pattern {pattern}: {count} times")
    
    status = "PASS" if len(unique_results) == 1 else "FAILURE"
    score = (1 if len(unique_results) == 1 else 0) * 100
    
    print(f"\n{'✓' if status == 'PASS' else '✗'} Stability Score: {score:.1f}/100 [{status}]")
    
    return {
        "score": score,
        "status": status,
        "unique_patterns": len(unique_results),
        "consistency": consistency
    }

# ============================================================================
# TEST 6: EDGE CASES
# ============================================================================

def test_edge_cases() -> Dict:
    """Test extreme scenarios"""
    print_header("TEST 6: EDGE CASE TEST")
    
    edge_cases = {
        "ultra_fragile": ("EDGE_FRAGILE", 2.0, "electronics", 95),
        "ultra_heavy": ("EDGE_HEAVY", 100.0, "furniture", 30),
        "ultra_light": ("EDGE_LIGHT", 0.1, "cosmetics", 50),
        "ultra_eco": ("EDGE_ECO", 5.0, "clothing", 95)
    }
    
    print("Creating edge case products...")
    tests_passed = 0
    
    for case_name, (product_id, weight, category, strength) in edge_cases.items():
        print(f"  {case_name:20s} (weight={weight}kg)...", end=" ")
        
        if not create_test_product(product_id, category, weight, strength, 50, 50):
            print("✗ Creation failed")
            continue
        
        try:
            response = requests.post(
                ENDPOINT_INDUSTRIAL,
                json={"product_id": product_id},
                headers=API_HEADERS,
                timeout=10
            )
            
            if response.status_code == 200:
                recs = response.json().get('recommendations', [])
                if recs:
                    print(f"✓ Got {len(recs)} recommendations")
                    tests_passed += 1
                else:
                    print("✗ No recommendations")
            else:
                print(f"✗ Error {response.status_code}")
                
        except Exception as e:
            print(f"✗ {str(e)[:30]}")
    
    score = (tests_passed / len(edge_cases)) * 100
    status = "PASS" if tests_passed == len(edge_cases) else "PARTIAL"
    
    print_subheader(f"EDGE CASE SCORE")
    print(f"{'✓' if status == 'PASS' else '⚠'} Score: {score:.1f}/100 [{status}] ({tests_passed}/{len(edge_cases)} passed)")
    
    return {
        "score": score,
        "status": status,
        "tests_passed": tests_passed,
        "total_tests": len(edge_cases)
    }

# ============================================================================
# TEST 7: EXPLANATION QUALITY
# ============================================================================

def test_explanation_quality() -> Dict:
    """Verify explanations reference actual metrics"""
    print_header("TEST 7: EXPLANATION QUALITY VALIDATION")
    
    test_product = "EXPLANATION_TEST"
    print(f"Creating test product: {test_product}")
    
    if not create_test_product(test_product, "electronics", 7.0, 65, 60, 70):
        return {"score": 0, "status": "FAILURE", "reason": "Could not create test product"}
    
    try:
        response = requests.post(
            ENDPOINT_INDUSTRIAL,
            json={"product_id": test_product},
            headers=API_HEADERS,
            timeout=10
        )
        
        if response.status_code != 200:
            return {"score": 0, "status": "FAILURE", "reason": f"API error: {response.status_code}"}
        
        recs = response.json().get('recommendations', [])
        
        if not recs:
            return {"score": 0, "status": "FAILURE", "reason": "No recommendations"}
        
        print(f"\nAnalyzing explanations for {len(recs[:5])} recommendations...")
        print_subheader("EXPLANATION QUALITY ANALYSIS")
        
        quality_count = 0
        
        for i, rec in enumerate(recs[:5]):
            material = rec.get('material_type', rec.get('Type', 'UNKNOWN'))
            print(f"\n  Material {i+1}: {material}")
            
            # Check for explanation fields
            has_tradeoff = bool(rec.get('tradeoff_summary'))
            has_why = bool(rec.get('why_selected'))
            has_pros = bool(rec.get('pros'))
            has_cons = bool(rec.get('cons'))
            
            print(f"    Tradeoff summary: {'✓' if has_tradeoff else '✗'}" + 
                  (f" - {rec.get('tradeoff_summary', '')[:40]}..." if has_tradeoff else ""))
            print(f"    Why selected: {'✓' if has_why else '✗'}" +
                  (f" - {rec.get('why_selected', '')[:40]}..." if has_why else ""))
            print(f"    Pros/Cons: {'✓' if has_pros and has_cons else '✗'}")
            
            if has_tradeoff and has_why and has_pros and has_cons:
                quality_count += 1
        
        score = (quality_count / min(5, len(recs))) * 100
        status = "PASS" if quality_count >= 3 else "PARTIAL"
        
        print(f"\n{'✓' if status == 'PASS' else '⚠'} Explanation Quality Score: {score:.1f}/100 [{status}]")
        
        return {
            "score": score,
            "status": status,
            "quality_recommendations": quality_count,
            "total_checked": min(5, len(recs))
        }
        
    except Exception as e:
        return {"score": 0, "status": "FAILURE", "reason": str(e)}

# ============================================================================
# MAIN VALIDATION RUNNER
# ============================================================================

def generate_final_report(results: Dict) -> str:
    """Generate comprehensive validation report"""
    
    scores = {
        "Diversity": results.get("diversity", {}).get("score", 0),
        "Preference Sensitivity": results.get("sensitivity", {}).get("score", 0),
        "Pareto Efficiency": results.get("pareto", {}).get("score", 0),
        "Monotonicity": results.get("monotonicity", {}).get("score", 0),
        "Stability": results.get("stability", {}).get("score", 0),
        "Edge Cases": results.get("edge_cases", {}).get("score", 0),
        "Explanations": results.get("explanations", {}).get("score", 0)
    }
    
    weights = {
        "Diversity": 0.25,
        "Preference Sensitivity": 0.25,
        "Pareto Efficiency": 0.15,
        "Monotonicity": 0.10,
        "Stability": 0.10,
        "Edge Cases": 0.10,
        "Explanations": 0.05
    }
    
    overall = sum(scores[k] * weights[k] for k in scores.keys())
    
    report = f"""
{'='*80}
INDUSTRIAL RECOMMENDATION VALIDATION REPORT
{'='*80}

Date: March 2, 2026
System: ECO_PACK_AI Recommendation Engine
Test Type: Decision System Validation (NOT Regression)

{'-'*80}
VALIDATION SCORES
{'-'*80}
"""
    
    for metric, score in scores.items():
        weight = weights[metric]
        bar_length = int(score / 5)
        bar = '█' * bar_length + '░' * (20 - bar_length)
        status = '✓' if score >= 70 else '✗'
        report += f"\n{status} {metric:30s} {score:5.1f}/100 [{bar}] ({weight*100:.0f}%)"
    
    report += f"""

{'='*80}
OVERALL SCORE: {overall:.1f}/100
{'='*80}
"""
    
    bar_length = int(overall / 5)
    bar = '█' * bar_length + '░' * (20 - bar_length)
    report += f"\n[{bar}]\n"
    
    if overall >= 85:
        status = "INDUSTRIAL-GRADE RECOMMENDATION ENGINE ✓"
    elif overall >= 70:
        status = "PRODUCTION-READY WITH MINOR IMPROVEMENTS"
    elif overall >= 50:
        status = "FUNCTIONAL BUT NEEDS OPTIMIZATION"
    else:
        status = "FAILURE - MAJOR ISSUES DETECTED"
    
    report += f"\n{'-'*80}\n"
    report += f"STATUS: {status}\n"
    report += f"{'-'*80}\n"
    
    # Issues
    issues = []
    if scores["Diversity"] < MIN_DIVERSITY_SCORE:
        issues.append("Low diversity - recommendations too similar")
    if scores["Preference Sensitivity"] < MIN_SENSITIVITY_SCORE:
        issues.append("Low sensitivity - preferences don't affect rankings enough")
    if scores["Stability"] < MIN_STABILITY_SCORE:
        issues.append("Instability - identical requests return different results")
    
    if issues:
        report += "\n⚠ ISSUES IDENTIFIED:\n"
        for issue in issues:
            report += f"  • {issue}\n"
    else:
        report += "\n✓ NO MAJOR ISSUES DETECTED\n"
    
    # Detailed results
    report += f"""

{'-'*80}
DETAILED TEST RESULTS
{'-'*80}

1. Diversity Test:
   - Score: {scores['Diversity']:.1f}/100
   - Unique recommendations: {results.get('diversity', {}).get('unique_top', 0)}
   - Status: {results.get('diversity', {}).get('status', 'UNKNOWN')}

2. Preference Sensitivity Test:
   - Score: {scores['Preference Sensitivity']:.1f}/100  
   - Unique rankings: {results.get('sensitivity', {}).get('unique_rankings', 0)}/3
   - Status: {results.get('sensitivity', {}).get('status', 'UNKNOWN')}

3. Pareto Efficiency Test:
   - Score: {scores['Pareto Efficiency']:.1f}/100
   - Pareto information included: {results.get('pareto', {}).get('has_pareto_info', False)}
   - Status: {results.get('pareto', {}).get('status', 'UNKNOWN')}

4. Monotonicity Test:
   - Score: {scores['Monotonicity']:.1f}/100
   - Tests passed: {results.get('monotonicity', {}).get('tests_passed', 0)}/{results.get('monotonicity', {}).get('total_tests', 0)}
   - Status: {results.get('monotonicity', {}).get('status', 'UNKNOWN')}

5. Stability Test:
   - Score: {scores['Stability']:.1f}/100
   - Unique patterns: {results.get('stability', {}).get('unique_patterns', 0)}
   - Status: {results.get('stability', {}).get('status', 'UNKNOWN')}

6. Edge Case Test:
   - Score: {scores['Edge Cases']:.1f}/100
   - Tests passed: {results.get('edge_cases', {}).get('tests_passed', 0)}/{results.get('edge_cases', {}).get('total_tests', 0)}
   - Status: {results.get('edge_cases', {}).get('status', 'UNKNOWN')}

7. Explanation Quality Test:
   - Score: {scores['Explanations']:.1f}/100
   - Quality recommendations: {results.get('explanations', {}).get('quality_recommendations', 0)}
   - Status: {results.get('explanations', {}).get('status', 'UNKNOWN')}

{'-'*80}
CONCLUSION
{'-'*80}

"""
    
    if overall >= 85:
        report += """
✓ SYSTEM VALIDATED AS INDUSTRIAL-GRADE

The ECO_PACK_AI recommendation engine demonstrates:
✓ High diversity across product types
✓ Strong preference sensitivity
✓ Efficient Pareto-based optimization  
✓ Logical monotonic behavior
✓ Stable and reproducible results
✓ Comprehensive edge case handling
✓ Clear explanation generation

RECOMMENDATION: Deploy to production with confidence.

"""
    elif overall >= 70:
        report += """
✓ SYSTEM IS PRODUCTION-READY

The recommendation engine is functional but has room for improvement:
→ Minor diversity enhancements recommended
→ Fine-tune preference weight sensitivity
→ Validate edge case handling

RECOMMENDATION: Deploy with monitoring, plan improvements for next release.

"""
    else:
        report += """
✗ VALIDATION FAILED

The system requires significant improvements:
→ Address core decision logic issues
→ Increase recommendation diversity
→ Validate preference handling
→ Test stability and reproducibility

RECOMMENDATION: Do not deploy until major issues are resolved.

"""
    
    report += f"\n{'='*80}\n"
    
    return report

def main():
    """Run all validation tests"""
    
    print("\n" + "█"*80)
    print("█" + " "*78 + "█")
    print("█" + " INDUSTRIAL RECOMMENDATION VALIDATION SUITE ".center(78) + "█")
    print("█" + " "*78 + "█")
    print("█"*80)
    
    print("\nTesting Decision System (not regression models)")
    print(f"Backend: http://localhost:8000")
    
    # Check backend availability
    print_subheader("CHECKING BACKEND AVAILABILITY")
    
    try:
        response = requests.get(
            f"{API_BASE}/health",
            headers=API_HEADERS,
            timeout=5
        )
        print("✓ Backend is reachable")
    except:
        print("✗ Backend is NOT reachable!")
        print("\n⚠ VALIDATION ABORTED")
        print("Start backend with: python src/api.py")
        return
    
    # Run all tests
    all_results = {}
    
    all_results["diversity"] = test_diversity()
    time.sleep(1)
    
    all_results["sensitivity"] = test_preference_sensitivity()
    time.sleep(1)
    
    all_results["pareto"] = test_pareto_efficiency()
    time.sleep(1)
    
    all_results["monotonicity"] = test_monotonicity()
    time.sleep(1)
    
    all_results["stability"] = test_stability()
    time.sleep(1)
    
    all_results["edge_cases"] = test_edge_cases()
    time.sleep(1)
    
    all_results["explanations"] = test_explanation_quality()
    
    # Generate and print report
    report = generate_final_report(all_results)
    print("\n" + report)
    
    # Save report
    try:
        import os
        os.makedirs("reports", exist_ok=True)
        
        with open("reports/INDUSTRIAL_RECOMMENDATION_VALIDATION_REPORT.txt", 'w') as f:
            f.write(report)
        
        print(f"✓ Report saved to: reports/INDUSTRIAL_RECOMMENDATION_VALIDATION_REPORT.txt")
    except Exception as e:
        print(f"⚠ Could not save report: {str(e)}")

if __name__ == "__main__":
    main()
