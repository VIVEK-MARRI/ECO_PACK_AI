"""
Production-grade global model loader and caching
Ensures models are loaded once at startup and cached globally
"""

import os
import joblib
import pickle
import threading
import time
from typing import Dict, Any, Optional
import numpy as np
from .logger import setup_logger

logger = setup_logger('model_loader')

class ModelRegistry:
    """Thread-safe global model registry"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ModelRegistry, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.models: Dict[str, Any] = {}
        self.scalers: Dict[str, Any] = {}
        self.feature_names: Dict[str, list] = {}
        self.load_timestamp: Dict[str, float] = {}
        self._load_lock = threading.RLock()
        
        # Load all models at initialization
        self._load_all_models()
    
    def _load_all_models(self):
        """Load all models from disk"""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        models_dir = os.path.join(base_dir, 'models')
        
        logger.info(f"Loading models from {models_dir}")
        
        self._load_model('rf_cost_model', os.path.join(models_dir, 'rf_cost_model.pkl'))
        self._load_model('xgb_co2_model', os.path.join(models_dir, 'xgb_co2_model.pkl'))
        self._load_scaler('feature_scaler', os.path.join(models_dir, 'feature_scaler.pkl'))
        
        logger.info(f"Models loaded: {list(self.models.keys())}")
    
    def _load_model(self, name: str, path: str):
        """Load a single model with error handling"""
        try:
            if not os.path.exists(path):
                logger.warning(f"Model file not found: {path}")
                return
            
            model = joblib.load(path)
            
            # Extract feature names if available
            if hasattr(model, 'feature_names_in_'):
                self.feature_names[name] = list(model.feature_names_in_)
            
            self.models[name] = model
            self.load_timestamp[name] = time.time()
            
            logger.info(f"✓ Model loaded: {name}")
            logger.info(f"  - Type: {type(model).__name__}")
            
            # Log model info
            if hasattr(model, 'n_features_in_'):
                logger.info(f"  - Features: {model.n_features_in_}")
            if hasattr(model, 'n_classes_'):
                logger.info(f"  - Classes: {model.n_classes_}")
        
        except Exception as e:
            logger.error(f"Failed to load model {name}: {str(e)}", exc_info=True)
    
    def _load_scaler(self, name: str, path: str):
        """Load a scaler"""
        try:
            if not os.path.exists(path):
                logger.warning(f"Scaler file not found: {path}")
                return
            
            scaler = joblib.load(path)
            self.scalers[name] = scaler
            logger.info(f"✓ Scaler loaded: {name}")
        
        except Exception as e:
            logger.error(f"Failed to load scaler {name}: {str(e)}", exc_info=True)
    
    def get_model(self, name: str) -> Optional[Any]:
        """Get a model by name (thread-safe)"""
        with self._load_lock:
            if name not in self.models:
                logger.warning(f"Model not found: {name}")
                return None
            return self.models[name]
    
    def get_scaler(self, name: str) -> Optional[Any]:
        """Get a scaler by name"""
        with self._load_lock:
            if name not in self.scalers:
                logger.warning(f"Scaler not found: {name}")
                return None
            return self.scalers[name]
    
    def predict_with_model(self, model_name: str, features: np.ndarray) -> np.ndarray:
        """Get prediction from a model (thread-safe)"""
        with self._load_lock:
            model = self.get_model(model_name)
            if model is None:
                raise ValueError(f"Model {model_name} not loaded")
            
            return model.predict(features)
    
    def predict_proba_with_model(self, model_name: str, features: np.ndarray) -> np.ndarray:
        """Get probability predictions (if supported)"""
        with self._load_lock:
            model = self.get_model(model_name)
            if model is None:
                raise ValueError(f"Model {model_name} not loaded")
            
            if not hasattr(model, 'predict_proba'):
                raise ValueError(f"Model {model_name} doesn't support predict_proba")
            
            return model.predict_proba(features)
    
    def get_status(self) -> Dict[str, Any]:
        """Get registry status"""
        return {
            'models': list(self.models.keys()),
            'scalers': list(self.scalers.keys()),
            'load_times': {name: time.time() - ts for name, ts in self.load_timestamp.items()},
            'feature_names': self.feature_names
        }

# Global singleton instance
_model_registry = ModelRegistry()

def get_model_registry() -> ModelRegistry:
    """Get global model registry"""
    return _model_registry

# Pre-load models at module import time
logger.info("ModelRegistry initialized as singleton")
