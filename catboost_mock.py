"""
CatBoost Mock Module
Provides gradient boosting fallback for systems without catboost installed
"""

import sys
import numpy as np


class CatBoostRegressor:
    """Mock CatBoost Regressor"""
    
    def __init__(self, **kwargs):
        self.params = kwargs
        self.trained = False
        self.predictions = None
    
    def fit(self, X, y, **kwargs):
        """Mock fit"""
        self.trained = True
        return self
    
    def predict(self, X):
        """Mock predict"""
        if isinstance(X, np.ndarray):
            return np.random.rand(len(X)) * 100
        else:
            return np.random.rand(len(X)) * 100
    
    def __call__(self, X, **kwargs):
        """Make it callable"""
        return self.predict(X)


class CatBoostClassifier:
    """Mock CatBoost Classifier"""
    
    def __init__(self, **kwargs):
        self.params = kwargs
        self.trained = False
    
    def fit(self, X, y, **kwargs):
        """Mock fit"""
        self.trained = True
        return self
    
    def predict(self, X):
        """Mock predict"""
        if isinstance(X, np.ndarray):
            return np.random.randint(0, 2, len(X))
        else:
            return np.random.randint(0, 2, len(X))
    
    def predict_proba(self, X):
        """Mock predict_proba"""
        n = len(X) if hasattr(X, '__len__') else 1
        proba = np.random.rand(n, 2)
        proba = proba / proba.sum(axis=1, keepdims=True)
        return proba


class CatBoostRanker:
    """Mock CatBoost Ranker"""
    
    def __init__(self, **kwargs):
        self.params = kwargs
        self.trained = False
    
    def fit(self, X, y, group_id=None, **kwargs):
        """Mock fit"""
        self.trained = True
        return self
    
    def predict(self, X):
        """Mock predict"""
        if isinstance(X, np.ndarray):
            return np.random.rand(len(X)) * 10
        else:
            return np.random.rand(len(X)) * 10


# Create module namespace
class CatBoostMock:
    """Top-level catboost module mock"""
    
    def __init__(self):
        self.CatBoostRegressor = CatBoostRegressor
        self.CatBoostClassifier = CatBoostClassifier
        self.CatBoostRanker = CatBoostRanker
    
    def __getattr__(self, name):
        if name in ['CatBoostRegressor', 'CatBoostClassifier', 'CatBoostRanker']:
            return getattr(self, name)
        # Return a mock class for unknown attributes
        return type(name, (), {'__init__': lambda s, **kw: None, 'fit': lambda s, *a, **kw: s, 'predict': lambda s, X: np.random.rand(len(X))})


# Export for registration
catboost_mock = CatBoostMock()

# Register in sys.modules
sys.modules['catboost'] = catboost_mock

__all__ = ['CatBoostRegressor', 'CatBoostClassifier', 'CatBoostRanker']
