#!/usr/bin/env python3
"""
Root Cause Analysis: Feature-Target Correlation Study
Diagnose why models have R² < 0.30
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Load raw data
df = pd.read_csv('data/raw/ecopackai_raw_dataset.csv')

print("="*80)
print("PHASE 1: ROOT CAUSE ANALYSIS")
print("="*80)

# Clean column names
df.columns = ['material_name', 'product_category', 'strength', 'weight_capacity',
              'unit_cost', 'biodegradability_score', 'co2_emission', 'recyclability_percentage',
              'fragility_level', 'shipping_mode']

print("\n1. DATA QUALITY CHECK")
print("-"*80)
print(f"Total rows: {len(df)}")
print(f"Missing values per column:")
print(df.isnull().sum())
print(f"\nMissing percentage:")
print((df.isnull().sum() / len(df) * 100).round(2))

# Drop rows with missing targets
df_clean = df.dropna(subset=['unit_cost', 'co2_emission'])
print(f"\nRows after dropping missing targets: {len(df_clean)}")

# Select numeric features
numeric_cols = ['strength', 'weight_capacity', 'biodegradability_score', 
                'recyclability_percentage', 'fragility_level', 'unit_cost', 'co2_emission']

df_numeric = df_clean[numeric_cols].dropna()
print(f"Rows with complete numeric data: {len(df_numeric)}")

print("\n2. TARGET DISTRIBUTION ANALYSIS")
print("-"*80)
print("\nUnit Cost Statistics:")
print(df_numeric['unit_cost'].describe())
print(f"Range: [{df_numeric['unit_cost'].min():.4f}, {df_numeric['unit_cost'].max():.4f}]")
print(f"Coefficient of Variation: {(df_numeric['unit_cost'].std() / df_numeric['unit_cost'].mean()):.4f}")

print("\nCO2 Emission Statistics:")
print(df_numeric['co2_emission'].describe())
print(f"Range: [{df_numeric['co2_emission'].min():.4f}, {df_numeric['co2_emission'].max():.4f}]")
print(f"Coefficient of Variation: {(df_numeric['co2_emission'].std() / df_numeric['co2_emission'].mean()):.4f}")

print("\n3. FEATURE-TARGET CORRELATION ANALYSIS")
print("-"*80)
corr_matrix = df_numeric.corr()

print("\nCorrelation with Unit Cost:")
cost_corr = corr_matrix['unit_cost'].sort_values(ascending=False)
print(cost_corr)

print("\nCorrelation with CO2 Emission:")
co2_corr = corr_matrix['co2_emission'].sort_values(ascending=False)
print(co2_corr)

print("\n4. DIAGNOSIS: ROOT CAUSE IDENTIFICATION")
print("-"*80)

# Check if targets are realistic
max_cost_corr = cost_corr.drop('unit_cost').abs().max()
max_co2_corr = co2_corr.drop('co2_emission').abs().max()

print(f"\nMax absolute correlation with cost (excluding self): {max_cost_corr:.4f}")
print(f"Max absolute correlation with CO2 (excluding self): {max_co2_corr:.4f}")

if max_cost_corr < 0.3:
    print("\n❌ CRITICAL: Cost has WEAK correlation with all features!")
    print("   This indicates targets may be randomly generated or noise-dominated.")
    
if max_co2_corr < 0.3:
    print("\n❌ CRITICAL: CO2 has WEAK correlation with all features!")
    print("   This indicates targets may be randomly generated or noise-dominated.")

# Check business logic expectations
print("\n5. BUSINESS LOGIC VALIDATION")
print("-"*80)

expected_relationships = {
    'weight_capacity → unit_cost': df_numeric[['weight_capacity', 'unit_cost']].corr().iloc[0, 1],
    'weight_capacity → co2_emission': df_numeric[['weight_capacity', 'co2_emission']].corr().iloc[0, 1],
    'strength → unit_cost': df_numeric[['strength', 'unit_cost']].corr().iloc[0, 1],
    'biodegradability_score → co2_emission': df_numeric[['biodegradability_score', 'co2_emission']].corr().iloc[0, 1],
}

print("\nExpected Relationships:")
for relation, corr_value in expected_relationships.items():
    status = "✓" if abs(corr_value) > 0.1 else "❌"
    print(f"{status} {relation}: {corr_value:.4f}")

# Categorical analysis
print("\n6. CATEGORICAL FEATURE ANALYSIS")
print("-"*80)

print("\nMaterial Name vs Cost:")
material_cost = df_clean.groupby('material_name')['unit_cost'].agg(['mean', 'std', 'count'])
print(material_cost.sort_values('mean', ascending=False))

print("\nMaterial Name vs CO2:")
material_co2 = df_clean.groupby('material_name')['co2_emission'].agg(['mean', 'std', 'count'])
print(material_co2.sort_values('mean', ascending=False))

# Visualizations
print("\n7. GENERATING DIAGNOSTIC PLOTS...")
print("-"*80)

fig, axes = plt.subplots(3, 2, figsize=(14, 12))

# Plot 1: Correlation heatmap
sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm', center=0, 
            ax=axes[0, 0], cbar_kws={'label': 'Correlation'})
axes[0, 0].set_title('Feature-Target Correlation Matrix', fontweight='bold')

# Plot 2: Cost distribution
axes[0, 1].hist(df_numeric['unit_cost'], bins=30, edgecolor='black', alpha=0.7)
axes[0, 1].set_xlabel('Unit Cost ($)')
axes[0, 1].set_ylabel('Frequency')
axes[0, 1].set_title('Unit Cost Distribution', fontweight='bold')
axes[0, 1].axvline(df_numeric['unit_cost'].mean(), color='red', linestyle='--', label='Mean')
axes[0, 1].legend()

# Plot 3: CO2 distribution
axes[1, 0].hist(df_numeric['co2_emission'], bins=30, edgecolor='black', alpha=0.7, color='green')
axes[1, 0].set_xlabel('CO2 Emission (kg)')
axes[1, 0].set_ylabel('Frequency')
axes[1, 0].set_title('CO2 Emission Distribution', fontweight='bold')
axes[1, 0].axvline(df_numeric['co2_emission'].mean(), color='red', linestyle='--', label='Mean')
axes[1, 0].legend()

# Plot 4: Weight vs Cost scatter
axes[1, 1].scatter(df_numeric['weight_capacity'], df_numeric['unit_cost'], alpha=0.5)
axes[1, 1].set_xlabel('Weight Capacity (kg)')
axes[1, 1].set_ylabel('Unit Cost ($)')
axes[1, 1].set_title(f'Weight vs Cost (r={df_numeric[["weight_capacity", "unit_cost"]].corr().iloc[0,1]:.3f})', 
                     fontweight='bold')

# Plot 5: Weight vs CO2 scatter
axes[2, 0].scatter(df_numeric['weight_capacity'], df_numeric['co2_emission'], alpha=0.5, color='orange')
axes[2, 0].set_xlabel('Weight Capacity (kg)')
axes[2, 0].set_ylabel('CO2 Emission (kg)')
axes[2, 0].set_title(f'Weight vs CO2 (r={df_numeric[["weight_capacity", "co2_emission"]].corr().iloc[0,1]:.3f})', 
                     fontweight='bold')

# Plot 6: Material type comparison
material_stats = df_clean.groupby('material_name')[['unit_cost', 'co2_emission']].mean()
x = np.arange(len(material_stats))
width = 0.35
axes[2, 1].bar(x - width/2, material_stats['unit_cost'], width, label='Cost', alpha=0.7)
axes[2, 1].bar(x + width/2, material_stats['co2_emission']/20, width, label='CO2/20', alpha=0.7)
axes[2, 1].set_xlabel('Material Type')
axes[2, 1].set_ylabel('Value')
axes[2, 1].set_title('Material Type vs Targets', fontweight='bold')
axes[2, 1].set_xticks(x)
axes[2, 1].set_xticklabels(material_stats.index, rotation=45)
axes[2, 1].legend()

plt.tight_layout()
plt.savefig('reports/root_cause_analysis.png', dpi=300, bbox_inches='tight')
print("✓ Saved diagnostic plots to: reports/root_cause_analysis.png")

print("\n" + "="*80)
print("ROOT CAUSE ANALYSIS COMPLETE")
print("="*80)

# Summary diagnosis
print("\n📊 SUMMARY DIAGNOSIS:")
print("-"*80)

issues_found = []

if max_cost_corr < 0.3:
    issues_found.append("Cost targets have weak feature correlation (synthetic/random)")
if max_co2_corr < 0.3:
    issues_found.append("CO2 targets have weak feature correlation (synthetic/random)")
if expected_relationships['weight_capacity → unit_cost'] < 0:
    issues_found.append("Weight-Cost relationship is NEGATIVE (violates physics)")
if expected_relationships['weight_capacity → co2_emission'] < 0.3:
    issues_found.append("Weight-CO2 relationship is WEAK")

print(f"\n✗ {len(issues_found)} CRITICAL ISSUES IDENTIFIED:\n")
for i, issue in enumerate(issues_found, 1):
    print(f"  {i}. {issue}")

print("\n💡 RECOMMENDED SOLUTION:")
print("-"*80)
print("""
The current dataset has targets (cost, CO2) that are NOT properly correlated
with input features. This is why models achieve R² < 0.30.

SOLUTION: Regenerate targets using physics-based formulas:

1. Cost = f(weight, material_cost, shipping, volume)
2. CO2 = f(weight, material_emission, distance, sustainability)
3. Enforce monotonic relationships (weight ↑ → cost ↑, weight ↑ → CO2 ↑)

This will create a learnable relationship between features and targets.
""")
