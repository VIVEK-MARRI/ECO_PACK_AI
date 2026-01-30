"""
Test the Flask API
Run: python test_api.py
"""

import requests
import json

BASE_URL = "http://localhost:5000/api"
API_KEY = "your-secret-key-change-this"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

print("\n" + "="*50)
print("ECO_PACK_AI API Tests")
print("="*50 + "\n")

# Test 1: Health check
print("1. Health Check")
try:
    r = requests.get(f"{BASE_URL}/health")
    print(f"   Status: {r.status_code}")
    print(f"   Response: {json.dumps(r.json(), indent=2)}\n")
except Exception as e:
    print(f"   Error: {e}\n")

# Test 2: Input Product
print("2. Input Product")
try:
    r = requests.post(
        f"{BASE_URL}/product/input",
        headers=headers,
        json={
            "product_id": "PROD_001",
            "category": "electronics",
            "weight": 5.0,
            "strength": 75,
            "biodegradability": 0.8,
            "recyclability": 85
        }
    )
    print(f"   Status: {r.status_code}")
    print(f"   Response: {json.dumps(r.json(), indent=2)}\n")
except Exception as e:
    print(f"   Error: {e}\n")

# Test 3: Get Material Recommendation
print("3. Material Recommendation")
try:
    r = requests.post(
        f"{BASE_URL}/recommend/material",
        headers=headers,
        json={"product_id": "PROD_001"}
    )
    print(f"   Status: {r.status_code}")
    print(f"   Response: {json.dumps(r.json(), indent=2)}\n")
except Exception as e:
    print(f"   Error: {e}\n")

# Test 4: Environmental Score
print("4. Environmental Score")
try:
    r = requests.post(
        f"{BASE_URL}/score/environmental",
        headers=headers,
        json={
            "product_id": "PROD_001",
            "material": "bamboo"
        }
    )
    print(f"   Status: {r.status_code}")
    print(f"   Response: {json.dumps(r.json(), indent=2)}\n")
except Exception as e:
    print(f"   Error: {e}\n")

# Test 5: Get History
print("5. Get History")
try:
    r = requests.get(
        f"{BASE_URL}/history/PROD_001",
        headers=headers
    )
    print(f"   Status: {r.status_code}")
    print(f"   Response: {json.dumps(r.json(), indent=2)}\n")
except Exception as e:
    print(f"   Error: {e}\n")

print("="*50)
print("✓ Tests completed!")
print("="*50 + "\n")
