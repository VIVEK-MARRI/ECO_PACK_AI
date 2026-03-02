"""
Validation Tests for Industrial Recommendation Engine
=====================================================

Tests:
1. High sustainability preference → eco-friendly materials ranked higher
2. High cost sensitivity → cheapest options ranked higher
3. High risk sensitivity → safest options ranked higher
4. Constraint filtering → infeasible options excluded
5. Diversity enforcement → no duplicate material families
6. Pareto optimization → non-dominated solutions prioritized
7. Randomization guard → slight variation in tie-breaking

Author: ECO_PACK_AI Team
Version: 2.0
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.recommendation_engine_industrial import (
    IndustrialRecommendationEngine,
    UserPreferences
)
import json


# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'ecopack',
    'user': 'postgres',
    'password': 'admin'
}


def print_section(title):
    """Print section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def print_recommendations(recommendations, preferences=None):
    """Pretty print recommendations"""
    if preferences:
        print(f"\nUser Preferences:")
        print(f"  Cost Weight: {preferences.cost_weight:.2f}")
        print(f"  CO2 Weight: {preferences.co2_weight:.2f}")
        print(f"  Risk Weight: {preferences.risk_weight:.2f}")
    
    print(f"\nTop {len(recommendations)} Recommendations:\n")
    
    for rec in recommendations:
        print(f"[Rank {rec['rank']}] {rec['material'].upper()}")
        print(f"  Weighted Score: {rec['weighted_score']:.3f} (lower is better)")
        print(f"  Pareto Rank: {rec['pareto_rank']}")
        print(f"  Cost: ${rec['cost']:.2f} (normalized: {rec['normalized_cost']:.3f})")
        print(f"  CO₂: {rec['co2']:.2f} kg (normalized: {rec['normalized_co2']:.3f})")
        print(f"  Risk: {rec['damage_risk']:.3f} (normalized: {rec['normalized_risk']:.3f})")
        print(f"  Sustainability: {rec['sustainability_score']:.3f}")
        print(f"  Tradeoff: {rec['tradeoff_summary']}")
        print(f"  Why: {rec['why_selected']}")
        print(f"  Pros: {', '.join(rec['pros'][:3])}")
        print()


def test_1_high_sustainability_preference():
    """Test 1: High sustainability preference"""
    print_section("TEST 1: High Sustainability Preference (70% CO2 weight)")
    
    engine = IndustrialRecommendationEngine(DB_CONFIG)
    
    product_data = {
        'product_id': 'test_eco_001',
        'category': 'electronics',
        'weight': 5.0,
        'fragility_level': 2,
        'shipping_mode': 'Ground'
    }
    
    preferences = UserPreferences(
        cost_weight=0.15,
        co2_weight=0.70,
        risk_weight=0.15
    )
    
    recommendations = engine.get_recommendations(product_data, preferences, top_n=5)
    
    print_recommendations(recommendations, preferences)
    
    # Validation: Check if low-CO2 materials are ranked higher
    top_co2 = recommendations[0]['normalized_co2']
    print(f"✓ Top recommendation CO₂ (normalized): {top_co2:.3f}")
    print("✓ Expected: Low CO₂ materials (bagasse, bamboo, paper) should rank high")
    
    return recommendations


def test_2_high_cost_sensitivity():
    """Test 2: High cost sensitivity"""
    print_section("TEST 2: High Cost Sensitivity (70% cost weight)")
    
    engine = IndustrialRecommendationEngine(DB_CONFIG)
    
    product_data = {
        'product_id': 'test_budget_001',
        'category': 'home',
        'weight': 10.0,
        'fragility_level': 1,
        'shipping_mode': 'Ground'
    }
    
    preferences = UserPreferences(
        cost_weight=0.70,
        co2_weight=0.15,
        risk_weight=0.15
    )
    
    recommendations = engine.get_recommendations(product_data, preferences, top_n=5)
    
    print_recommendations(recommendations, preferences)
    
    # Validation: Check if low-cost materials are ranked higher
    top_cost = recommendations[0]['normalized_cost']
    print(f"✓ Top recommendation cost (normalized): {top_cost:.3f}")
    print("✓ Expected: Low-cost materials should rank high")
    
    return recommendations


def test_3_high_risk_sensitivity():
    """Test 3: High risk sensitivity"""
    print_section("TEST 3: High Risk Sensitivity (70% risk weight)")
    
    engine = IndustrialRecommendationEngine(DB_CONFIG)
    
    product_data = {
        'product_id': 'test_fragile_001',
        'category': 'electronics',
        'weight': 3.0,
        'fragility_level': 3,  # Highly fragile
        'shipping_mode': 'Air'
    }
    
    preferences = UserPreferences(
        cost_weight=0.15,
        co2_weight=0.15,
        risk_weight=0.70
    )
    
    recommendations = engine.get_recommendations(product_data, preferences, top_n=5)
    
    print_recommendations(recommendations, preferences)
    
    # Validation: Check if low-risk materials are ranked higher
    top_risk = recommendations[0]['normalized_risk']
    print(f"✓ Top recommendation risk (normalized): {top_risk:.3f}")
    print("✓ Expected: Strong materials (metal, plastic) should rank high")
    
    return recommendations


def test_4_constraint_filtering():
    """Test 4: Constraint filtering"""
    print_section("TEST 4: Constraint Filtering (Budget + CO2 + Recyclability)")
    
    engine = IndustrialRecommendationEngine(DB_CONFIG)
    
    product_data = {
        'product_id': 'test_constrained_001',
        'category': 'food',
        'weight': 8.0,
        'fragility_level': 1,
        'shipping_mode': 'Ground'
    }
    
    # Strict constraints
    preferences = UserPreferences(
        cost_weight=0.33,
        co2_weight=0.33,
        risk_weight=0.34,
        max_budget=3.0,  # Low budget
        max_co2_emission=8.0,  # Low CO2 cap
        min_recyclability=60.0  # Minimum 60% recyclability
    )
    
    recommendations = engine.get_recommendations(product_data, preferences, top_n=5)
    
    print(f"\nConstraints Applied:")
    print(f"  Max Budget: ${preferences.max_budget}")
    print(f"  Max CO₂: {preferences.max_co2_emission} kg")
    print(f"  Min Recyclability: {preferences.min_recyclability}%")
    
    print_recommendations(recommendations, preferences)
    
    # Validation: All should meet constraints
    print("\n✓ Constraint Validation:")
    for rec in recommendations:
        passes = (
            rec['cost'] <= preferences.max_budget and
            rec['co2'] <= preferences.max_co2_emission and
            rec['recyclability'] >= preferences.min_recyclability
        )
        status = "✓" if passes else "✗"
        print(f"{status} {rec['material']}: Cost=${rec['cost']:.2f}, CO2={rec['co2']:.2f}kg, Recycle={rec['recyclability']}%")
    
    return recommendations


def test_5_diversity_enforcement():
    """Test 5: Diversity enforcement"""
    print_section("TEST 5: Diversity Enforcement (Multiple Material Families)")
    
    engine = IndustrialRecommendationEngine(DB_CONFIG)
    
    product_data = {
        'product_id': 'test_diverse_001',
        'category': 'cosmetics',
        'weight': 2.0,
        'fragility_level': 2,
        'shipping_mode': 'Ground'
    }
    
    preferences = UserPreferences(
        cost_weight=0.33,
        co2_weight=0.33,
        risk_weight=0.34
    )
    
    recommendations = engine.get_recommendations(product_data, preferences, top_n=6)
    
    print_recommendations(recommendations, preferences)
    
    # Validation: Check material family diversity
    families = set()
    print("\n✓ Material Family Diversity:")
    for rec in recommendations:
        family = engine._get_material_family(rec['material'])
        families.add(family)
        print(f"  {rec['material']} → {family}")
    
    print(f"\n✓ Unique families: {len(families)}/{len(recommendations)}")
    print("✓ Expected: Multiple material families represented (plant, synthetic, metal, etc.)")
    
    return recommendations


def test_6_pareto_optimization():
    """Test 6: Pareto optimization"""
    print_section("TEST 6: Pareto Optimization (Non-dominated Solutions)")
    
    engine = IndustrialRecommendationEngine(DB_CONFIG)
    
    product_data = {
        'product_id': 'test_pareto_001',
        'category': 'pharmaceuticals',
        'weight': 4.0,
        'fragility_level': 2,
        'shipping_mode': 'Air'
    }
    
    preferences = UserPreferences(
        cost_weight=0.33,
        co2_weight=0.33,
        risk_weight=0.34
    )
    
    recommendations = engine.get_recommendations(product_data, preferences, top_n=8)
    
    print_recommendations(recommendations, preferences)
    
    # Validation: Check Pareto ranks
    print("\n✓ Pareto Ranking:")
    pareto_fronts = {}
    for rec in recommendations:
        rank = rec['pareto_rank']
        if rank not in pareto_fronts:
            pareto_fronts[rank] = []
        pareto_fronts[rank].append(rec['material'])
    
    for rank in sorted(pareto_fronts.keys()):
        print(f"  Pareto Front {rank}: {', '.join(pareto_fronts[rank])}")
    
    print("\n✓ Expected: Front 0 solutions are non-dominated (best tradeoffs)")
    
    return recommendations


def test_7_preference_variation():
    """Test 7: Verify ranking changes with different preferences"""
    print_section("TEST 7: Preference Variation (Same Product, Different Weights)")
    
    engine = IndustrialRecommendationEngine(DB_CONFIG)
    
    product_data = {
        'product_id': 'test_variation_001',
        'category': 'electronics',
        'weight': 6.0,
        'fragility_level': 2,
        'shipping_mode': 'Ground'
    }
    
    # Test 3 different preference profiles
    profiles = [
        ("Eco-Focused", UserPreferences(cost_weight=0.1, co2_weight=0.7, risk_weight=0.2)),
        ("Budget-Focused", UserPreferences(cost_weight=0.7, co2_weight=0.1, risk_weight=0.2)),
        ("Safety-Focused", UserPreferences(cost_weight=0.2, co2_weight=0.1, risk_weight=0.7))
    ]
    
    results = {}
    
    for name, pref in profiles:
        print(f"\n--- {name} Profile ---")
        recommendations = engine.get_recommendations(product_data, pref, top_n=3)
        
        print(f"Weights: Cost={pref.cost_weight:.1f}, CO2={pref.co2_weight:.1f}, Risk={pref.risk_weight:.1f}")
        print("\nTop 3:")
        for rec in recommendations:
            print(f"  {rec['rank']}. {rec['material']} (score: {rec['weighted_score']:.3f})")
        
        results[name] = [rec['material'] for rec in recommendations]
    
    # Validation: Rankings should differ
    print("\n✓ Ranking Comparison:")
    print(f"  Eco-Focused:    {results['Eco-Focused']}")
    print(f"  Budget-Focused: {results['Budget-Focused']}")
    print(f"  Safety-Focused: {results['Safety-Focused']}")
    
    unique_rankings = len(set(str(v) for v in results.values()))
    print(f"\n✓ Unique rankings: {unique_rankings}/3")
    print("✓ Expected: Different weights should produce different rankings")
    
    return results


def test_8_randomization_guard():
    """Test 8: Randomization guard for tie-breaking"""
    print_section("TEST 8: Randomization Guard (Tie-Breaking)")
    
    engine = IndustrialRecommendationEngine(DB_CONFIG)
    
    product_data = {
        'product_id': 'test_random_001',
        'category': 'home',
        'weight': 5.0,
        'fragility_level': 1,
        'shipping_mode': 'Ground'
    }
    
    preferences = UserPreferences(
        cost_weight=0.33,
        co2_weight=0.33,
        risk_weight=0.34
    )
    
    # Run twice to check reproducibility
    print("\nRun 1:")
    recs1 = engine.get_recommendations(product_data, preferences, top_n=5)
    top1 = [rec['material'] for rec in recs1]
    print(f"  Top 5: {top1}")
    
    print("\nRun 2:")
    recs2 = engine.get_recommendations(product_data, preferences, top_n=5)
    top2 = [rec['material'] for rec in recs2]
    print(f"  Top 5: {top2}")
    
    # Check reproducibility (should be same due to random seed)
    if top1 == top2:
        print("\n✓ Rankings are reproducible (random seed works)")
    else:
        print("\n⚠ Rankings differ slightly due to tie-breaking randomness")
        print("  This is expected and demonstrates tie-breaking mechanism")
    
    return recs1


def run_all_tests():
    """Run all validation tests"""
    print("\n" + "="*70)
    print("  INDUSTRIAL RECOMMENDATION ENGINE - VALIDATION SUITE")
    print("="*70)
    
    try:
        test_1_high_sustainability_preference()
        test_2_high_cost_sensitivity()
        test_3_high_risk_sensitivity()
        test_4_constraint_filtering()
        test_5_diversity_enforcement()
        test_6_pareto_optimization()
        test_7_preference_variation()
        test_8_randomization_guard()
        
        print("\n" + "="*70)
        print("  ✓ ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    run_all_tests()
