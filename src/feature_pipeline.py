"""
Production-grade feature engineering pipeline
Ensures consistent preprocessing for training and inference
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, List, Any
from .logger import setup_logger

logger = setup_logger('feature_pipeline')

class FeaturePipeline:
    """
    Handles feature engineering for model prediction
    Ensures consistency between training and inference
    """
    
    # Standard features expected by models
    REQUIRED_FEATURES = [
        'category_electronics', 'category_food', 'category_beverages',
        'category_cosmetics', 'category_home', 'category_textiles',
        'weight', 'strength', 'biodegradability', 'recyclability'
    ]
    
    # Material mapping for encoding
    MATERIAL_ENCODING = {
        'bamboo': 0,
        'paper': 1,
        'jute': 2,
        'glass': 3,
        'metal': 4,
        'plastic': 5,
        'bagasse': 6
    }
    
    MATERIAL_DECODE = {v: k for k, v in MATERIAL_ENCODING.items()}
    
    @classmethod
    def validate_input(cls, data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate product input schema"""
        required = ['category', 'weight', 'strength', 'biodegradability', 'recyclability']
        
        for field in required:
            if field not in data:
                return False, f"Missing required field: {field}"
        
        # Type validation
        try:
            float(data['weight'])
            float(data['strength'])
            float(data['biodegradability'])
            float(data['recyclability'])
        except (ValueError, TypeError):
            return False, "Numeric fields must be convertible to float"
        
        # Range validation
        weight = float(data['weight'])
        if weight <= 0 or weight > 100:
            return False, "Weight must be between 0 and 100 kg"
        
        for field in ['strength', 'biodegradability', 'recyclability']:
            val = float(data[field])
            if val < 0 or val > 100:
                return False, f"{field} must be between 0 and 100"
        
        return True, "Valid input"
    
    @classmethod
    def encode_category(cls, category: str) -> np.ndarray:
        """One-hot encode product category"""
        categories = ['electronics', 'food', 'beverages', 'cosmetics', 'home', 'textiles']
        encoding = np.zeros(len(categories))
        
        if category.lower() in categories:
            encoding[categories.index(category.lower())] = 1.0
        else:
            # Default to 'electronics' if unknown
            logger.warning(f"Unknown category '{category}', defaulting to 'electronics'")
            encoding[0] = 1.0
        
        return encoding
    
    @classmethod
    def prepare_features(cls, data: Dict[str, Any]) -> Tuple[np.ndarray, List[str]]:
        """
        Prepare features for model prediction
        Returns: (feature_array, feature_names)
        """
        # Validate input
        is_valid, msg = cls.validate_input(data)
        if not is_valid:
            raise ValueError(f"Invalid input: {msg}")
        
        logger.info(f"Processing features for category={data.get('category')}")
        
        # One-hot encode category
        category_encoding = cls.encode_category(data['category'])
        
        # Normalize numeric features to 0-1 range
        weight = float(data['weight']) / 100.0  # Normalize to kg
        strength = float(data['strength']) / 100.0  # Normalize to 0-1
        biodegradability = float(data['biodegradability']) / 100.0  # Normalize to 0-1
        recyclability = float(data['recyclability']) / 100.0  # Normalize to 0-1
        
        # Build feature vector
        features = np.concatenate([
            category_encoding,
            [weight, strength, biodegradability, recyclability]
        ])
        
        # Feature names for debugging
        feature_names = [
            'category_electronics', 'category_food', 'category_beverages',
            'category_cosmetics', 'category_home', 'category_textiles',
            'weight', 'strength', 'biodegradability', 'recyclability'
        ]
        
        logger.info(f"Features prepared: shape={features.shape}")
        
        return features.reshape(1, -1), feature_names  # Reshape for sklearn
    
    @classmethod
    def encode_material(cls, material: str) -> int:
        """Encode material string to integer"""
        material_lower = material.lower()
        if material_lower in cls.MATERIAL_ENCODING:
            return cls.MATERIAL_ENCODING[material_lower]
        
        logger.warning(f"Unknown material '{material}', using default encoding")
        return 0
    
    @classmethod
    def decode_material(cls, material_code: int) -> str:
        """Decode material integer to string"""
        if material_code in cls.MATERIAL_DECODE:
            return cls.MATERIAL_DECODE[material_code]
        
        logger.warning(f"Unknown material code '{material_code}'")
        return 'unknown'

class DriftDetector:
    """
    Detect feature drift between training and production data
    """
    
    def __init__(self, baseline_stats: Dict[str, Dict[str, float]] = None):
        self.baseline_stats = baseline_stats or {}
        self.threshold = 3.0  # 3 sigma for anomaly detection
    
    def compute_stats(self, features: np.ndarray, names: List[str]) -> Dict[str, Dict[str, float]]:
        """Compute statistics for features"""
        stats = {}
        
        for i, name in enumerate(names):
            col = features[:, i] if len(features.shape) > 1 else features[i]
            stats[name] = {
                'mean': float(np.mean(col)),
                'std': float(np.std(col)),
                'min': float(np.min(col)),
                'max': float(np.max(col))
            }
        
        return stats
    
    def detect_drift(self, features: np.ndarray, names: List[str]) -> Tuple[bool, Dict[str, Any]]:
        """
        Detect if input features have drifted from baseline
        Returns: (has_drift, drift_report)
        """
        if not self.baseline_stats:
            return False, {}
        
        current_stats = self.compute_stats(features, names)
        drift_report = {
            'features_checked': len(names),
            'drifted_features': [],
            'drift_details': {}
        }
        
        for name in names:
            if name not in self.baseline_stats:
                continue
            
            baseline = self.baseline_stats[name]
            current = current_stats[name]
            
            # Check if mean is too far from baseline
            if baseline['std'] > 0:
                z_score = abs((current['mean'] - baseline['mean']) / baseline['std'])
                if z_score > self.threshold:
                    drift_report['drifted_features'].append(name)
                    drift_report['drift_details'][name] = {
                        'z_score': float(z_score),
                        'baseline_mean': baseline['mean'],
                        'current_mean': current['mean']
                    }
        
        has_drift = len(drift_report['drifted_features']) > 0
        
        if has_drift:
            logger.warning(f"Feature drift detected: {drift_report['drifted_features']}")
        
        return has_drift, drift_report
