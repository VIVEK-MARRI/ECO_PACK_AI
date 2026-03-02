"""PyTorch TabNet mock package"""

import torch
import torch.nn as nn
import numpy as np


class TabNetEncoder(nn.Module):
    """Mock TabNet Encoder"""
    def __init__(self, input_dim, output_dim=None, n_steps=3, gamma=1.5, n_independent=2, n_shared=2, epsilon=1e-15, virtual_batch_size=128, momentum=0.9):
        super().__init__()
        self.input_dim = input_dim
        self.output_dim = output_dim or input_dim
        self.n_steps = n_steps
        
        self.initial_bn = nn.BatchNorm1d(input_dim, momentum=momentum)
        self.encoder = nn.Linear(input_dim, self.output_dim)
    
    def forward(self, x):
        x = self.initial_bn(x)
        x = self.encoder(x)
        return x


class TabNetRegressor(nn.Module):
    """Mock TabNet Regressor"""
    def __init__(self, input_dim, output_dim=1, n_steps=3):
        super().__init__()
        self.input_dim = input_dim
        self.output_dim = output_dim
        
        self.encoder = TabNetEncoder(input_dim, 128, n_steps)
        self.head = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, output_dim)
        )
    
    def forward(self, x):
        if not isinstance(x, torch.Tensor):
            x = torch.tensor(x, dtype=torch.float32)
        
        features = self.encoder(x)
        output = self.head(features)
        return output
    
    def fit(self, X_train, y_train=None, eval_set=None, **kwargs):
        """Mock fit method"""
        return self
    
    def predict(self, X):
        """Predict method"""
        if not isinstance(X, torch.Tensor):
            X = torch.tensor(X, dtype=torch.float32)
        
        with torch.no_grad():
            output = self.forward(X)
        
        return output.numpy() if hasattr(output, 'numpy') else np.array(output)


class TabNetClassifier(nn.Module):
    """Mock TabNet Classifier"""
    def __init__(self, input_dim, output_dim=1, n_steps=3):
        super().__init__()
        self.input_dim = input_dim
        self.output_dim = output_dim
        
        self.encoder = TabNetEncoder(input_dim, 128, n_steps)
        self.head = nn.Sequential(
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Linear(64, output_dim)
        )
    
    def forward(self, x):
        if not isinstance(x, torch.Tensor):
            x = torch.tensor(x, dtype=torch.float32)
        
        features = self.encoder(x)
        output = self.head(features)
        return output
    
    def fit(self, X_train, y_train=None, eval_set=None, **kwargs):
        """Mock fit method"""
        return self
    
    def predict(self, X):
        """Predict method"""
        if not isinstance(X, torch.Tensor):
            X = torch.tensor(X, dtype=torch.float32)
        
        with torch.no_grad():
            output = self.forward(X)
        
        return (output > 0.5).numpy().astype(int) if hasattr(output, 'numpy') else np.array(output > 0.5)
    
    def predict_proba(self, X):
        """Predict probability"""
        if not isinstance(X, torch.Tensor):
            X = torch.tensor(X, dtype=torch.float32)
        
        with torch.no_grad():
            output = self.forward(X)
        
        proba = torch.sigmoid(output)
        return proba.numpy() if hasattr(proba, 'numpy') else np.array(proba)


__all__ = ['TabNetRegressor', 'TabNetClassifier', 'TabNetEncoder']
