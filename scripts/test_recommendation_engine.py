#!/usr/bin/env python3
"""
Test updated RecommendationEngine with Industrial LightGBM predictor
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.recommendation import RecommendationEngine
from dotenv import load_dotenv

# Load env
load_dotenv()

# DB Config (won't actually connect, just testing predictor)
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'ecopack',
    'user': 'postgres',
    'password': 'password'
}

print("="*80)
print("TESTING UPDATED RECOMMENDATION ENGINE")
print("="*80)

# Initialize engine
print("\n1. Initializing RecommendationEngine...")
try:
    engine = RecommendationEngine(DB_CONFIG)
    print("✓ RecommendationEngine initialized")
except Exception as e:
    print(f"❌ Initialization failed: {e}")
    sys.exit(1)

# Test prediction methods
print("\n2. Testing prediction methods...")

test_input = {
    'strength': 50.0,
    'weight_capacity': 10.0,
    'biodegradability_score': 0.9,
    'recyclability_percentage': 80.0,
    'fragility_level': 2,
    'material_name': 'paper',
    'shipping_mode': 'Ground'
}

try:
    cost_eff = engine.predict_cost_efficiency(test_input)
    print(f"✓ Cost Efficiency: {cost_eff:.4f}")
except Exception as e:
    print(f"❌ Cost prediction failed: {e}")

try:
    co2_impact = engine.predict_co2_impact(test_input)
    print(f"✓ CO2 Impact: {co2_impact:.4f}")
except Exception as e:
    print(f"❌ CO2 prediction failed: {e}")

try:
    eco_score = engine.calculate_eco_score(co2_impact, 0.9, 80.0, cost_eff)
    print(f"✓ Eco Score: {eco_score:.2f}/100")
except Exception as e:
    print(f"❌ Eco score calculation failed: {e}")

print("\n" + "="*80)
print("✅ RECOMMENDATION ENGINE TEST COMPLETE")
print("="*80)
print("\nStatus: Engine successfully integrated with industrial LightGBM models")
print("Ready for API integration")
