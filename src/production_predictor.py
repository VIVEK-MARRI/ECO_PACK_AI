"""
Production ML Inference Pipeline - Industrial LightGBM Models
Replaces deprecated RF/XGBoost models with validated LightGBM models

Performance:
- Cost Model: R² = 0.7489
- CO2 Model: R² = 0.8800
- Monotonic constraints: Enforced
- Feature scaling: NOT REQUIRED (tree-based models trained on unscaled features)
- Target scaling: Unnormalized (original scale)
"""

import numpy as np
import pandas as pd
import lightgbm as lgb
import joblib
import json
import os
from typing import Dict, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class IndustrialMLPredictor:
    """Production-grade ML predictor with LightGBM models"""
    
    def __init__(self):
        self.cost_model = None
        self.co2_model = None
        self.scaler = None
        self.feature_metadata = None
        self.feature_names = None
        self.load_models()
    
    def load_models(self):
        """Load industrial LightGBM models"""
        try:
            # Paths to industrial models
            cost_model_path = os.path.join(BASE_DIR, 'models', 'lgb_cost_model_optimized.txt')
            co2_model_path = os.path.join(BASE_DIR, 'models', 'lgb_co2_model_industrial.txt')
            scaler_path = os.path.join(BASE_DIR, 'models', 'feature_scaler_industrial.pkl')
            metadata_path = os.path.join(BASE_DIR, 'models', 'feature_metadata_industrial.json')
            
            # Load LightGBM models
            if os.path.exists(cost_model_path):
                self.cost_model = lgb.Booster(model_file=cost_model_path)
                print("✓ Industrial Cost Model loaded (LightGBM, R²=0.7489)")
            else:
                raise FileNotFoundError(f"Cost model not found: {cost_model_path}")
            
            if os.path.exists(co2_model_path):
                self.co2_model = lgb.Booster(model_file=co2_model_path)
                print("✓ Industrial CO2 Model loaded (LightGBM, R²=0.8800)")
            else:
                raise FileNotFoundError(f"CO2 model not found: {co2_model_path}")
            
            # Load scaler
            if os.path.exists(scaler_path):
                self.scaler = joblib.load(scaler_path)
                print("✓ Feature Scaler loaded")
            else:
                raise FileNotFoundError(f"Scaler not found: {scaler_path}")
            
            # Load feature metadata
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r') as f:
                    self.feature_metadata = json.load(f)
                    self.feature_names = self.feature_metadata['feature_names']
                print(f"✓ Feature Metadata loaded ({len(self.feature_names)} features)")
            else:
                raise FileNotFoundError(f"Metadata not found: {metadata_path}")
            
            print(f"\n✅ All industrial models loaded successfully")
            print(f"   Expected features: {len(self.feature_names)}")
            print(f"   Cost model R²: {self.feature_metadata.get('cost_r2_test', 'N/A'):.4f}")
            print(f"   CO2 model R²: {self.feature_metadata.get('co2_r2_test', 'N/A'):.4f}")
            
        except Exception as e:
            print(f"❌ Model loading error: {e}")
            raise
    
    def engineer_features(self, input_data: Dict) -> pd.DataFrame:
        """
        Engineer features matching training pipeline
        
        Input data format:
        {
            'strength': float,
            'weight_capacity': float,
            'biodegradability_score': float,
            'recyclability_percentage': float,
            'fragility_level': int,
            'material_name': str ('paper', 'bamboo', 'plastic', etc.),
            'shipping_mode': str ('Air' or 'Ground')
        }
        
        Returns:
            DataFrame with 22 engineered features matching training
        """
        
        # Extract base features
        strength = float(input_data.get('strength', 50.0))
        weight_capacity = float(input_data.get('weight_capacity', 10.0))
        biodegradability = float(input_data.get('biodegradability_score', 0.5))
        recyclability = float(input_data.get('recyclability_percentage', 50.0))
        fragility = float(input_data.get('fragility_level', 2.0))
        material_name = input_data.get('material_name', 'paper').lower()
        shipping_mode = input_data.get('shipping_mode', 'Ground')
        
        # Physics-based engineered features (MUST match training pipeline)
        features = {
            # Base features
            'strength': strength,
            'weight_capacity': weight_capacity,
            'biodegradability_score': biodegradability,
            'recyclability_percentage': recyclability,
            'fragility_level': fragility,
            
            # Engineered features (match training exactly)
            'strength_weight_product': strength * weight_capacity,
            'strength_weight_ratio': strength / (weight_capacity + 0.1),
            'eco_quality_score': biodegradability * 0.5 + (recyclability / 100) * 0.5,
            'material_eco_strength': biodegradability * strength,
            'weight_fragility_interaction': weight_capacity * fragility,
            'weight_squared': weight_capacity ** 2,
            'strength_squared': strength ** 2,
            'biodegradability_squared': biodegradability ** 2,
            
            # Material one-hot encoding (7 types)
            'material_bagasse': 1 if material_name == 'bagasse' else 0,
            'material_bamboo': 1 if material_name == 'bamboo' else 0,
            'material_glass': 1 if material_name == 'glass' else 0,
            'material_jute': 1 if material_name == 'jute' else 0,
            'material_metal': 1 if material_name == 'metal' else 0,
            'material_paper': 1 if material_name == 'paper' else 0,
            'material_plastic': 1 if material_name == 'plastic' else 0,
            
            # Shipping one-hot encoding (2 types)
            'shipping_Air': 1 if shipping_mode == 'Air' else 0,
            'shipping_Ground': 1 if shipping_mode == 'Ground' else 0,
        }
        
        # Create DataFrame with exact feature order from training
        df = pd.DataFrame([features])
        
        # Ensure feature order matches training
        df = df[self.feature_names]
        
        return df
    
    def predict(self, input_data: Dict) -> Dict:
        """
        Make production predictions with industrial models
        
        Args:
            input_data: Dictionary with product/material properties
        
        Returns:
            Dictionary with predictions and metadata
            {
                'cost_prediction': float (original scale),
                'co2_prediction': float (original scale),
                'eco_score': float (0-100),
                'features_used': int,
                'model_version': str
            }
        """
        
        if self.cost_model is None or self.co2_model is None:
            raise RuntimeError("Models not loaded. Call load_models() first.")
        
        # Engineer features
        features_df = self.engineer_features(input_data)
        
        # IMPORTANT: LightGBM models were trained on UNSCALED features
        # Tree-based models are invariant to feature scaling
        # DO NOT apply scaler.transform() here
        
        # Make predictions (LightGBM returns unnormalized values)
        cost_pred = self.cost_model.predict(features_df.values)[0]
        co2_pred = self.co2_model.predict(features_df.values)[0]
        
        # Ensure non-negative (safety constraint)
        cost_pred = max(0.0, cost_pred)
        co2_pred = max(0.0, co2_pred)
        
        # Calculate eco score (weighted composite)
        # CO2: lower is better (normalize to 0-1, then invert)
        # Cost: lower is better (normalize to 0-1, then invert)
        co2_normalized = min(co2_pred / 25.0, 1.0)  # Normalize by max expected CO2
        cost_normalized = min(cost_pred / 0.80, 1.0)  # Normalize by max expected cost
        
        eco_score = (
            (1 - co2_normalized) * 40 +  # CO2: 40% weight
            input_data.get('biodegradability_score', 0.5) * 100 * 0.35 +  # Bio: 35%
            input_data.get('recyclability_percentage', 50.0) * 0.15 +  # Recycle: 15%
            (1 - cost_normalized) * 10  # Cost: 10%
        )
        
        return {
            'cost_prediction': round(float(cost_pred), 4),
            'co2_prediction': round(float(co2_pred), 4),
            'eco_score': round(float(eco_score), 2),
            'features_used': len(self.feature_names),
            'model_version': 'industrial_lightgbm_v1.0',
            'cost_model_r2': self.feature_metadata.get('cost_r2_test', 0.7489),
            'co2_model_r2': self.feature_metadata.get('co2_r2_test', 0.8800)
        }
    
    def batch_predict(self, input_data_list: list) -> list:
        """
        Batch prediction for multiple inputs
        
        Args:
            input_data_list: List of input dictionaries
        
        Returns:
            List of prediction dictionaries
        """
        return [self.predict(data) for data in input_data_list]
    
    def validate_monotonicity(self, base_input: Dict) -> Dict:
        """
        Validate monotonic constraints on predictions
        
        Tests:
        - weight ↑ → cost ↑
        - weight ↑ → CO2 ↑
        - biodegradability ↑ → CO2 ↓
        
        Returns:
            Dictionary with validation results
        """
        
        results = {
            'weight_cost_monotonic': False,
            'weight_co2_monotonic': False,
            'bio_co2_monotonic': False,
            'all_pass': False
        }
        
        # Test 1: Weight increase should increase cost
        base_pred = self.predict(base_input)
        
        increased_weight_input = base_input.copy()
        increased_weight_input['weight_capacity'] = base_input['weight_capacity'] * 1.5
        increased_weight_pred = self.predict(increased_weight_input)
        
        results['weight_cost_monotonic'] = increased_weight_pred['cost_prediction'] > base_pred['cost_prediction']
        results['weight_co2_monotonic'] = increased_weight_pred['co2_prediction'] > base_pred['co2_prediction']
        
        # Test 2: Biodegradability increase should decrease CO2
        increased_bio_input = base_input.copy()
        increased_bio_input['biodegradability_score'] = min(base_input.get('biodegradability_score', 0.5) + 0.3, 1.0)
        increased_bio_pred = self.predict(increased_bio_input)
        
        results['bio_co2_monotonic'] = increased_bio_pred['co2_prediction'] < base_pred['co2_prediction']
        
        # Overall status
        results['all_pass'] = all([
            results['weight_cost_monotonic'],
            results['weight_co2_monotonic'],
            results['bio_co2_monotonic']
        ])
        
        return results


# Global singleton instance
_predictor_instance = None

def get_predictor() -> IndustrialMLPredictor:
    """Get or create global predictor instance"""
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = IndustrialMLPredictor()
    return _predictor_instance


# Convenience functions for API
def predict_cost_co2(input_data: Dict) -> Dict:
    """Convenience function for predictions"""
    predictor = get_predictor()
    return predictor.predict(input_data)


def validate_model_monotonicity(base_input: Dict) -> Dict:
    """Convenience function for validation"""
    predictor = get_predictor()
    return predictor.validate_monotonicity(base_input)


if __name__ == "__main__":
    # Test the predictor
    print("="*80)
    print("TESTING INDUSTRIAL ML PREDICTOR")
    print("="*80)
    
    predictor = IndustrialMLPredictor()
    
    # Test case 1: Paper material
    test_input_1 = {
        'strength': 50.0,
        'weight_capacity': 10.0,
        'biodegradability_score': 0.90,
        'recyclability_percentage': 85.0,
        'fragility_level': 2.0,
        'material_name': 'paper',
        'shipping_mode': 'Ground'
    }
    
    print("\nTest 1: Paper Material")
    print("-"*80)
    result_1 = predictor.predict(test_input_1)
    print(f"Cost Prediction: ${result_1['cost_prediction']:.4f}")
    print(f"CO2 Prediction: {result_1['co2_prediction']:.4f} kg")
    print(f"Eco Score: {result_1['eco_score']:.2f}/100")
    print(f"Features Used: {result_1['features_used']}")
    print(f"Model Version: {result_1['model_version']}")
    
    # Test case 2: Plastic material
    test_input_2 = {
        'strength': 75.0,
        'weight_capacity': 15.0,
        'biodegradability_score': 0.15,
        'recyclability_percentage': 40.0,
        'fragility_level': 1.0,
        'material_name': 'plastic',
        'shipping_mode': 'Ground'
    }
    
    print("\nTest 2: Plastic Material")
    print("-"*80)
    result_2 = predictor.predict(test_input_2)
    print(f"Cost Prediction: ${result_2['cost_prediction']:.4f}")
    print(f"CO2 Prediction: {result_2['co2_prediction']:.4f} kg")
    print(f"Eco Score: {result_2['eco_score']:.2f}/100")
    
    # Monotonicity validation
    print("\nMonotonicity Validation")
    print("-"*80)
    validation = predictor.validate_monotonicity(test_input_1)
    print(f"Weight → Cost (↑): {'✓ PASS' if validation['weight_cost_monotonic'] else '✗ FAIL'}")
    print(f"Weight → CO2 (↑): {'✓ PASS' if validation['weight_co2_monotonic'] else '✗ FAIL'}")
    print(f"Biodegradability → CO2 (↓): {'✓ PASS' if validation['bio_co2_monotonic'] else '✗ FAIL'}")
    print(f"\nOverall: {'✅ ALL PASS' if validation['all_pass'] else '❌ SOME FAILED'}")
    
    print("\n" + "="*80)
    print("✅ INDUSTRIAL ML PREDICTOR TEST COMPLETE")
    print("="*80)
