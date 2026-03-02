#!/usr/bin/env python3
"""
Optuna Hyperparameter Optimization for Cost Model
Target: R² > 0.80
"""

import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import cross_val_score, KFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_squared_error
import optuna
from optuna.samplers import TPESampler
import warnings
warnings.filterwarnings('ignore')

print("="*80)
print("OPTUNA HYPERPARAMETER OPTIMIZATION - COST MODEL")
print("="*80)

# Load processed data
df = pd.read_csv('data/processed/X_test_industrial.csv')
X = pd.read_csv('data/processed/X_test_industrial.csv')  
y_cost_test = pd.read_csv('data/processed/y_cost_test_industrial.csv').values.ravel()

# Load full dataset to re-split for optimization
df_raw = pd.read_csv('data/raw/ecopackai_raw_dataset.csv')
df_raw.columns = ['material_name', 'product_category', 'strength', 'weight_capacity',
                  'unit_cost', 'biodegradability_score', 'co2_emission', 'recyclability_percentage',
                  'fragility_level', 'shipping_mode']

df_clean = df_raw.dropna(subset=['unit_cost', 'co2_emission']).copy()

# Fill missing features
numeric_cols = ['strength', 'weight_capacity', 'biodegradability_score', 
                'recyclability_percentage', 'fragility_level']
for col in numeric_cols:
    df_clean[col].fillna(df_clean[col].median(), inplace=True)
df_clean['shipping_mode'].fillna('Ground', inplace=True)

# Feature engineering
df_clean['strength_weight_product'] = df_clean['strength'] * df_clean['weight_capacity']
df_clean['strength_weight_ratio'] = df_clean['strength'] / (df_clean['weight_capacity'] + 0.1)
df_clean['eco_quality_score'] = (
    df_clean['biodegradability_score'] * 0.5 + 
    df_clean['recyclability_percentage'] / 100 * 0.5
)
df_clean['material_eco_strength'] = df_clean['biodegradability_score'] * df_clean['strength']
df_clean['weight_fragility_interaction'] = df_clean['weight_capacity'] * df_clean['fragility_level']
df_clean['weight_squared'] = df_clean['weight_capacity'] ** 2
df_clean['strength_squared'] = df_clean['strength'] ** 2
df_clean['biodegradability_squared'] = df_clean['biodegradability_score'] ** 2

# One-hot encoding
material_dummies = pd.get_dummies(df_clean['material_name'], prefix='material')
df_clean = pd.concat([df_clean, material_dummies], axis=1)
shipping_dummies = pd.get_dummies(df_clean['shipping_mode'], prefix='shipping')
df_clean = pd.concat([df_clean, shipping_dummies], axis=1)

# Prepare features
feature_cols = [
    'strength', 'weight_capacity', 'biodegradability_score', 
    'recyclability_percentage', 'fragility_level',
    'strength_weight_product', 'strength_weight_ratio', 'eco_quality_score',
    'material_eco_strength', 'weight_fragility_interaction',
    'weight_squared', 'strength_squared', 'biodegradability_squared',
]
material_cols = [col for col in df_clean.columns if col.startswith('material_') and col not in ['material_name', 'material_eco_strength']]
feature_cols.extend(material_cols)
shipping_cols = [col for col in df_clean.columns if col.startswith('shipping_') and col != 'shipping_mode']
feature_cols.extend(shipping_cols)

X_full = df_clean[feature_cols].copy()
y_cost_full = df_clean['unit_cost'].copy()

# Split
from sklearn.model_selection import train_test_split
X_train, X_test, y_cost_train, y_cost_test = train_test_split(
    X_full, y_cost_full, test_size=0.2, random_state=42
)

print(f"Training set: {X_train.shape[0]} samples")
print(f"Test set: {X_test.shape[0]} samples")

# Monotonic constraints (same as before)
monotone_constraints_cost = [
    1, 1, -1, 0, 1,  # base features
    1, 0, -1, 0, 1,  # engineered features
    1, 1, -1,        # squared features
] + [0] * 9  # categorical features (7 materials + 2 shipping)

print("\n🔍 OPTUNA OPTIMIZATION")
print("-"*80)

def objective(trial):
    """Optuna objective function for hyperparameter tuning"""
    
    params = {
        'objective': 'regression',
        'metric': 'rmse',
        'boosting_type': 'gbdt',
        'verbosity': -1,
        'monotone_constraints': monotone_constraints_cost,
        
        # Hyperparameters to tune
        'num_leaves': trial.suggest_int('num_leaves', 20, 100),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.2, log=True),
        'feature_fraction': trial.suggest_float('feature_fraction', 0.5, 1.0),
        'bagging_fraction': trial.suggest_float('bagging_fraction', 0.5, 1.0),
        'bagging_freq': trial.suggest_int('bagging_freq', 1, 10),
        'min_child_samples': trial.suggest_int('min_child_samples', 5, 50),
        'reg_alpha': trial.suggest_float('reg_alpha', 0.0, 1.0),
        'reg_lambda': trial.suggest_float('reg_lambda', 0.0, 1.0),
        'max_depth': trial.suggest_int('max_depth', 3, 15),
        'min_split_gain': trial.suggest_float('min_split_gain', 0.0, 1.0),
    }
    
    # Cross-validation
    kfold = KFold(n_splits=5, shuffle=True, random_state=42)
    r2_scores = []
    
    for train_idx, val_idx in kfold.split(X_train):
        X_tr, X_val = X_train.iloc[train_idx], X_train.iloc[val_idx]
        y_tr, y_val = y_cost_train.iloc[train_idx], y_cost_train.iloc[val_idx]
        
        lgb_train = lgb.Dataset(X_tr, y_tr)
        lgb_val = lgb.Dataset(X_val, y_val, reference=lgb_train)
        
        model = lgb.train(
            params,
            lgb_train,
            num_boost_round=500,
            valid_sets=[lgb_val],
            callbacks=[lgb.early_stopping(stopping_rounds=30), lgb.log_evaluation(period=0)]
        )
        
        y_pred = model.predict(X_val, num_iteration=model.best_iteration)
        r2 = r2_score(y_val, y_pred)
        r2_scores.append(r2)
    
    return np.mean(r2_scores)

# Run Optuna study
print("Starting Optuna study (50 trials)...")
study = optuna.create_study(direction='maximize', sampler=TPESampler(seed=42))
study.optimize(objective, n_trials=50, show_progress_bar=True)

print("\n✓ OPTUNA OPTIMIZATION COMPLETE")
print("-"*80)
print(f"Best R² (CV): {study.best_value:.4f}")
print(f"\nBest Hyperparameters:")
for key, value in study.best_params.items():
    print(f"  {key}: {value}")

# Train final model with best parameters
print("\n🤖 TRAINING FINAL MODEL WITH BEST PARAMS")
print("-"*80)

best_params = {
    'objective': 'regression',
    'metric': 'rmse',
    'boosting_type': 'gbdt',
    'verbosity': -1,
    'monotone_constraints': monotone_constraints_cost,
    **study.best_params
}

lgb_train_cost = lgb.Dataset(X_train, y_cost_train)
lgb_eval_cost = lgb.Dataset(X_test, y_cost_test, reference=lgb_train_cost)

final_model = lgb.train(
    best_params,
    lgb_train_cost,
    num_boost_round=1000,
    valid_sets=[lgb_eval_cost],
    callbacks=[lgb.early_stopping(stopping_rounds=50), lgb.log_evaluation(period=100)]
)

# Final evaluation
y_cost_pred_train = final_model.predict(X_train, num_iteration=final_model.best_iteration)
y_cost_pred_test = final_model.predict(X_test, num_iteration=final_model.best_iteration)

cost_r2_train = r2_score(y_cost_train, y_cost_pred_train)
cost_r2_test = r2_score(y_cost_test, y_cost_pred_test)
cost_rmse_test = np.sqrt(mean_squared_error(y_cost_test, y_cost_pred_test))

print("\n✓ FINAL COST MODEL PERFORMANCE:")
print(f"  Train R²: {cost_r2_train:.4f}")
print(f"  Test R²:  {cost_r2_test:.4f}")
print(f"  Test RMSE: {cost_rmse_test:.4f}")

if cost_r2_test >= 0.80:
    print("  ✅ MEETS INDUSTRIAL STANDARD (R² > 0.80)")
elif cost_r2_test >= 0.65:
    print("  ⚠️  ACCEPTABLE (R² > 0.65)")
else:
    print("  ❌ BELOW STANDARD (R² < 0.65)")

# Save optimized model
print("\n💾 SAVING OPTIMIZED MODEL")
print("-"*80)
final_model.save_model('models/lgb_cost_model_optimized.txt')
print("✓ Saved: models/lgb_cost_model_optimized.txt")

# Save best params
import json
with open('models/cost_model_best_params.json', 'w') as f:
    json.dump(best_params, f, indent=2)
print("✓ Saved: models/cost_model_best_params.json")

print("\n" + "="*80)
print("OPTIMIZATION COMPLETE")
print("="*80)
