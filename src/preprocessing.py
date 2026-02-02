"""
Preprocessing Module for EcoPackAI
Handles feature transformation and preparation for ML models
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
import joblib
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Feature columns expected by models
FEATURE_COLUMNS = [
    'strength',
    'weight_capacity',
    'cost_per_unit',
    'biodegradability_score',
    'recyclability_percentage',
    'co2_emission_score',
    'fragility_level',
    'shipping_type_encoded'
]

def load_scaler():
    """Load the fitted scaler"""
    scaler_path = os.path.join(BASE_DIR, 'models', 'feature_scaler.pkl')
    if os.path.exists(scaler_path):
        return joblib.load(scaler_path)
    return None

def encode_shipping_type(shipping_type):
    """Encode shipping type to numeric"""
    mapping = {'ground': 0, 'air': 1, 'sea': 2}
    return mapping.get(shipping_type.lower(), 0)

def prepare_features_for_prediction(product_data, material_data):
    """
    Prepare features for ML model prediction
    
    Args:
        product_data: dict with product properties (category, weight, strength, etc.)
        material_data: dict with material properties (from database)
    
    Returns:
        numpy array ready for model prediction
    """
    # Combine product and material features
    features = {
        'strength': material_data.get('strength', 50.0),
        'weight_capacity': product_data.get('weight', 1.0) * 10,  # Estimate capacity
        'cost_per_unit': material_data.get('cost_per_unit', 0.3),
        'biodegradability_score': product_data.get('biodegradability', 50) / 100,
        'recyclability_percentage': material_data.get('recyclability_percentage', 50),
        'co2_emission_score': 1.0 - (product_data.get('strength', 50) / 100),  # Inverse relation
        'fragility_level': map_category_to_fragility(product_data.get('category', 'general')),
        'shipping_type_encoded': encode_shipping_type('ground')
    }
    
    # Create feature array in correct order
    feature_array = np.array([[features[col] for col in FEATURE_COLUMNS]])
    
    # Apply scaling only if scaler exists and features match
    scaler = load_scaler()
    if scaler is not None:
        try:
            # Only scale if dimensions match
            if feature_array.shape[1] == scaler.n_features_in_:
                feature_array = scaler.transform(feature_array)
        except Exception as e:
            # If scaling fails, use unscaled features
            print(f"Note: Scaling skipped ({str(e)}) - using raw features")
    
    return feature_array

def map_category_to_fragility(category):
    """Map product category to fragility level (1-5)"""
    fragility_map = {
        'electronics': 4,
        'glass': 5,
        'pharmaceuticals': 3,
        'cosmetics': 3,
        'food': 2,
        'beverages': 2,
        'home': 2,
        'textiles': 1,
        'general': 2
    }
    return fragility_map.get(category.lower(), 2)

def calculate_material_suitability(product_data, material_data):
    """
    Calculate material suitability score based on product requirements
    
    Returns:
        float: suitability score (0-1)
    """
    product_strength_need = product_data.get('strength', 50) / 100
    material_strength = material_data.get('strength', 50) / 100
    
    product_bio_preference = product_data.get('biodegradability', 50) / 100
    material_bio = material_data.get('biodegradability_score', 0.5)
    
    product_recycle_preference = product_data.get('recyclability', 50) / 100
    material_recycle = material_data.get('recyclability_percentage', 50) / 100
    
    # Weighted suitability
    suitability = (
        0.3 * min(material_strength / max(product_strength_need, 0.1), 1.0) +
        0.4 * (1 - abs(material_bio - product_bio_preference)) +
        0.3 * (1 - abs(material_recycle - product_recycle_preference))
    )
    
    return max(0, min(1, suitability))

def normalize_score(value, min_val, max_val):
    """Normalize value to 0-100 scale"""
    if max_val == min_val:
        return 50.0
    return ((value - min_val) / (max_val - min_val)) * 100

def validate_product_input(data):
    """
    Validate product input data
    
    Returns:
        tuple: (is_valid, error_message)
    """
    required_fields = ['product_id', 'category', 'weight']
    
    for field in required_fields:
        if field not in data or not data[field]:
            return False, f"Missing required field: {field}"
    
    # Validate numeric fields
    try:
        weight = float(data.get('weight', 0))
        if weight <= 0:
            return False, "Weight must be greater than 0"
    except (ValueError, TypeError):
        return False, "Invalid weight value"
    
    # Validate ranges
    for field in ['strength', 'biodegradability', 'recyclability']:
        if field in data:
            try:
                val = float(data[field])
                if not 0 <= val <= 100:
                    return False, f"{field} must be between 0 and 100"
            except (ValueError, TypeError):
                return False, f"Invalid {field} value"
    
    return True, None
