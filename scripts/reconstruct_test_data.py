#!/usr/bin/env python
"""
Reconstruct proper feature-engineered test data
"""

import pandas as pd
import numpy as np

# Load the raw feature engineered data
df = pd.read_csv('data/processed/ecopackai_feature_engineered.csv')
print(f"Original data shape: {df.shape}")

# Create feature matrix from feature engineered data and targets
X_raw = df[['strength', 'weight_capacity', 'biodegradability_score', 'recyclability_percentage', 'fragility_level']].copy()

# Get one-hot for material_type
material_dummies = pd.get_dummies(df['material_type'], prefix='material_type')
print(f"Material dummies columns: {material_dummies.columns.tolist()}")

# Get one-hot for shipping_type  
shipping_dummies = pd.get_dummies(df['shipping_type'], prefix='shipping_type')
print(f"Shipping dummies columns: {shipping_dummies.columns.tolist()}")

# Combine
X_base = pd.concat([X_raw, material_dummies, shipping_dummies], axis=1)
print(f"X_base shape (before engineered features): {X_base.shape}")

# Add engineered features
X_engineered = X_base.copy()
X_engineered['strength_weight_product'] = X_raw['strength'] * X_raw['weight_capacity']
X_engineered['strength_weight_normalized'] = (X_raw['strength'] + X_raw['weight_capacity']) / 2
X_engineered['eco_quality_score'] = (X_raw['biodegradability_score'] + X_raw['recyclability_percentage']) / 2
X_engineered['strength_ratio'] = X_raw['strength'] / (X_raw['weight_capacity'] + 1e-6)
X_engineered['weight_capacity_ratio'] = X_raw['weight_capacity'] / (X_raw['strength'] + 1e-6)
X_engineered['biodegradability_squared'] = X_raw['biodegradability_score'] ** 2
X_engineered['biodegradability_cubed'] = X_raw['biodegradability_score'] ** 3
X_engineered['recyclability_squared'] = X_raw['recyclability_percentage'] ** 2
X_engineered['material_diversity'] = (material_dummies.sum(axis=1)) / len(material_dummies.columns)

print(f"X_engineered shape: {X_engineered.shape}")
print(f"Expected feature names (21): ['strength' 'weight_capacity' 'biodegradability_score' 'recyclability_percentage' 'fragility_level' 'material_type_bamboo' 'material_type_glass' 'material_type_jute' 'material_type_metal' 'material_type_paper' 'material_type_plastic' 'shipping_type_ground' 'strength_weight_product' 'strength_weight_normalized' 'eco_quality_score' 'strength_ratio' 'weight_capacity_ratio' 'biodegradability_squared' 'biodegradability_cubed' 'recyclability_squared' 'material_diversity']")
print(f"Actual feature names ({len(X_engineered.columns)}): {X_engineered.columns.tolist()}")

# Get target variables
y_cost = df['cost_per_unit'].values.reshape(-1, 1)
y_co2 = df['co2_emission_score'].values.reshape(-1, 1)

print(f"\ny_cost shape: {y_cost.shape}, mean: {y_cost.mean():.4f}, std: {y_cost.std():.4f}, min: {y_cost.min():.4f}, max: {y_cost.max():.4f}")
print(f"y_co2 shape: {y_co2.shape}, mean: {y_co2.mean():.4f}, std: {y_co2.std():.4f}, min: {y_co2.min():.4f}, max: {y_co2.max():.4f}")

# Split into train/test (80/20)
test_size = 520
X_test_recon = X_engineered.iloc[-test_size:].copy()
y_cost_test_recon = y_cost[-test_size:]
y_co2_test_recon = y_co2[-test_size:]

X_train_recon = X_engineered.iloc[:-test_size].copy()
y_cost_train_recon = y_cost[:-test_size]
y_co2_train_recon = y_co2[:-test_size]

print(f"\nTrain/Test Split:")
print(f"X_train_recon: {X_train_recon.shape}, X_test_recon: {X_test_recon.shape}")
print(f"y_cost_train_recon: {y_cost_train_recon.shape}, y_cost_test_recon: {y_cost_test_recon.shape}")
print(f"y_co2_train_recon: {y_co2_train_recon.shape}, y_co2_test_recon: {y_co2_test_recon.shape}")

# Save for evaluation script
X_test_recon.to_csv('data/processed/X_test_engineered.csv', index=False)
y_cost_test_recon_df = pd.DataFrame(y_cost_test_recon, columns=['cost_per_unit'])
y_cost_test_recon_df.to_csv('data/processed/y_cost_test_engineered.csv', index=False)
y_co2_test_recon_df = pd.DataFrame(y_co2_test_recon, columns=['co2_emission_score'])
y_co2_test_recon_df.to_csv('data/processed/y_co2_test_engineered.csv', index=False)

print("\nSaved engineered test data for evaluation:")
print(f"  data/processed/X_test_engineered.csv: {X_test_recon.shape}")
print(f"  data/processed/y_cost_test_engineered.csv: {y_cost_test_recon_df.shape}")
print(f"  data/processed/y_co2_test_engineered.csv: {y_co2_test_recon_df.shape}")
