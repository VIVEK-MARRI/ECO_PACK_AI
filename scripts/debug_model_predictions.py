#!/usr/bin/env python3
"""
DEBUG: Model Prediction Mismatch
Investigate why R² is 0.25 instead of 0.734
"""

import pandas as pd
import numpy as np
import lightgbm as lgb
import joblib
from sklearn.metrics import r2_score

print("="*80)
print("DEBUG: MODEL PREDICTION MISMATCH")
print("="*80)

# Load testdata
print("\n1. Loading test data...")
X_test = pd.read_csv('data/processed/X_test_industrial.csv')
y_cost_test = pd.read_csv('data/processed/y_cost_test_industrial.csv').values.ravel()
y_co2_test = pd.read_csv('data/processed/y_co2_test_industrial.csv').values.ravel()

# Convert booleans to int
print("\n2. Converting booleans to int...")
for col in X_test.columns:
    if X_test[col].dtype == bool:
        print(f"   Converting {col}: bool -> int")
        X_test[col] = X_test[col].astype(int)

print(f"\nTest set shape: {X_test.shape}")
print(f"Features: {list(X_test.columns)}")
print(f"\nCost target: min={y_cost_test.min():.4f}, max={y_cost_test.max():.4f}, mean={y_cost_test.mean():.4f}")
print(f"CO2 target: min={y_co2_test.min():.4f}, max={y_co2_test.max():.4f}, mean={y_co2_test.mean():.4f}")

# Load models and scaler
print("\n3. Loading models and scaler...")
cost_model = lgb.Booster(model_file='models/lgb_cost_model_optimized.txt')
co2_model = lgb.Booster(model_file='models/lgb_co2_model_industrial.txt')
scaler = joblib.load('models/feature_scaler_industrial.pkl')

print(f"✓ Cost model loaded")
print(f"✓ CO2 model loaded")
print(f"✓ Scaler loaded: {type(scaler).__name__}")

# Check scaler stats
print("\n4. Scaler statistics:")
print(f"   Scaler mean shape: {scaler.mean_.shape}")
print(f"   Scaler scale shape: {scaler.scale_.shape}")
print(f"   Sample means: {scaler.mean_[:5]}")
print(f"   Sample scales: {scaler.scale_[:5]}")

# Scale features
print("\n5. Scaling features...")
X_test_scaled = scaler.transform(X_test)
print(f"   Scaled data shape: {X_test_scaled.shape}")
print(f"   Scaled data range: min={X_test_scaled.min():.4f}, max={X_test_scaled.max():.4f}")
print(f"   Sample scaled values (first row, first 5 features): {X_test_scaled[0, :5]}")

# Make predictions
print("\n6. Making predictions...")
cost_predictions = cost_model.predict(X_test_scaled)
co2_predictions = co2_model.predict(X_test_scaled)

print(f"   Cost predictions: min={cost_predictions.min():.4f}, max={cost_predictions.max():.4f}, mean={cost_predictions.mean():.4f}")
print(f"   CO2 predictions: min={co2_predictions.min():.4f}, max={co2_predictions.max():.4f}, mean={co2_predictions.mean():.4f}")

# Calculate R²
print("\n7. Calculating R² scores...")
cost_r2 = r2_score(y_cost_test, cost_predictions)
co2_r2 = r2_score(y_co2_test, co2_predictions)

print(f"   Cost R²: {cost_r2:.4f} (expected: 0.7341)")
print(f"   CO2 R²:  {co2_r2:.4f} (expected: 0.8800)")

# Check predictions WITHOUT scaling
print("\n8. Testing WITHOUT scaling (for comparison)...")
cost_pred_unscaled = cost_model.predict(X_test.values)
co2_pred_unscaled = co2_model.predict(X_test.values)

cost_r2_unscaled = r2_score(y_cost_test, cost_pred_unscaled)
co2_r2_unscaled = r2_score(y_co2_test, co2_pred_unscaled)

print(f"   Cost R² (unscaled): {cost_r2_unscaled:.4f}")
print(f"   CO2 R² (unscaled):  {co2_r2_unscaled:.4f}")

# Diagnosis
print("\n" + "="*80)
print("DIAGNOSIS")
print("="*80)

if cost_r2 > 0.7 and co2_r2 > 0.8:
    print("✅ Models working correctly WITH scaling")
elif cost_r2_unscaled > 0.7 and co2_r2_unscaled > 0.8:
    print("⚠️  Models work WITHOUT scaling - wrong scaler being used!")
else:
    print("❌ Models not working correctly - possibly wrong model files")

print(f"\nWith scaling:    Cost R²={cost_r2:.4f}, CO2 R²={co2_r2:.4f}")
print(f"Without scaling: Cost R²={cost_r2_unscaled:.4f}, CO2 R²={co2_r2_unscaled:.4f}")
