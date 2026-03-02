"""
Base Models for Ensemble
Gradient Boosting (LightGBM, XGBoost, CatBoost) and Deep Tabular Models
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np
import pandas as pd
from sklearn.model_selection import cross_val_predict
import lightgbm as lgb
import xgboost as xgb
import catboost as cb
from pytorch_tabnet.tab_model import TabNetRegressor
import torch
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class EnsembleConfig:
    """Configuration for ensemble models."""
    n_folds: int = 5
    random_state: int = 42
    verbose: bool = True
    use_gpu: bool = torch.cuda.is_available()


class GradientBoostingModels:
    """
    Collection of gradient boosting models (LightGBM, XGBoost, CatBoost).
    """
    
    def __init__(self, config: EnsembleConfig):
        """Initialize gradient boosting models."""
        self.config = config
        self.models: Dict[str, Dict[str, list]] = {
            'cost': {},
            'co2': {},
            'damage': {}
        }
        
        logger.info("GradientBoostingModels initialized",
                   n_folds=config.n_folds)
    
    def get_lightgbm_params(self, objective: str) -> dict:
        """Get LightGBM parameters."""
        params = {
            'objective': 'regression' if objective != 'damage' else 'binary',
            'metric': 'rmse' if objective != 'damage' else 'auc',
            'boosting_type': 'gbdt',
            'num_leaves': 31,
            'learning_rate': 0.05,
            'feature_fraction': 0.9,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'max_depth': -1,
            'min_child_samples': 20,
            'reg_alpha': 0.1,
            'reg_lambda': 0.1,
            'random_state': self.config.random_state,
            'n_jobs': -1,
            'verbose': -1,
            'device': 'gpu' if self.config.use_gpu else 'cpu'
        }
        return params
    
    def get_xgboost_params(self, objective: str) -> dict:
        """Get XGBoost parameters."""
        params = {
            'objective': 'reg:squarederror' if objective != 'damage' else 'binary:logistic',
            'eval_metric': 'rmse' if objective != 'damage' else 'auc',
            'tree_method': 'gpu_hist' if self.config.use_gpu else 'hist',
            'max_depth': 7,
            'learning_rate': 0.05,
            'n_estimators': 1000,
            'subsample': 0.8,
            'colsample_bytree': 0.9,
            'reg_alpha': 0.1,
            'reg_lambda': 0.1,
            'random_state': self.config.random_state,
            'n_jobs': -1
        }
        return params
    
    def get_catboost_params(self, objective: str) -> dict:
        """Get CatBoost parameters."""
        params = {
            'loss_function': 'RMSE' if objective != 'damage' else 'Logloss',
            'iterations': 1000,
            'depth': 7,
            'learning_rate': 0.05,
            'l2_leaf_reg': 3,
            'random_seed': self.config.random_state,
            'verbose': 0,
            'task_type': 'GPU' if self.config.use_gpu else 'CPU',
            'bootstrap_type': 'Bernoulli',
            'subsample': 0.8
        }
        return params
    
    def train(
        self,
        X_train: np.ndarray,
        y_cost: np.ndarray,
        y_co2: np.ndarray,
        y_damage: np.ndarray,
        categorical_features: Optional[List[int]] = None
    ) -> Dict[str, Dict[str, np.ndarray]]:
        """
        Train all gradient boosting models for all objectives.
        
        Args:
            X_train: Training features
            y_cost: Cost targets
            y_co2: CO2 targets
            y_damage: Damage probability targets
            categorical_features: Indices of categorical features
        
        Returns:
            Out-of-fold predictions for stacking
        """
        logger.info("Training gradient boosting models...")
        
        oof_predictions = {
            'cost': {},
            'co2': {},
            'damage': {}
        }
        
        # Train for each objective
        for objective, y_target in [
            ('cost', y_cost),
            ('co2', y_co2),
            ('damage', y_damage)
        ]:
            logger.info(f"Training {objective} models...")
            
            # LightGBM
            lgb_oof = self._train_lightgbm(
                X_train, y_target, objective, categorical_features
            )
            oof_predictions[objective]['lgb'] = lgb_oof
            
            # XGBoost
            xgb_oof = self._train_xgboost(
                X_train, y_target, objective
            )
            oof_predictions[objective]['xgb'] = xgb_oof
            
            # CatBoost
            cb_oof = self._train_catboost(
                X_train, y_target, objective, categorical_features
            )
            oof_predictions[objective]['cb'] = cb_oof
            
            logger.info(f"Completed {objective} models")
        
        logger.info("All gradient boosting models trained")
        return oof_predictions
    
    def _train_lightgbm(
        self,
        X: np.ndarray,
        y: np.ndarray,
        objective: str,
        categorical_features: Optional[List[int]] = None
    ) -> np.ndarray:
        """Train LightGBM with cross-validation."""
        params = self.get_lightgbm_params(objective)
        
        model = lgb.LGBMRegressor(**params, n_estimators=1000)
        
        # Cross-validation predictions
        oof_preds = cross_val_predict(
            model,
            X,
            y,
            cv=self.config.n_folds,
            n_jobs=-1,
            verbose=0
        )
        
        # Train final model on full data
        lgb_models = []
        from sklearn.model_selection import KFold
        kf = KFold(n_splits=self.config.n_folds, shuffle=True, random_state=self.config.random_state)
        
        for fold, (train_idx, val_idx) in enumerate(kf.split(X)):
            X_fold_train, X_fold_val = X[train_idx], X[val_idx]
            y_fold_train, y_fold_val = y[train_idx], y[val_idx]
            
            model = lgb.LGBMRegressor(**params, n_estimators=1000)
            model.fit(
                X_fold_train,
                y_fold_train,
                eval_set=[(X_fold_val, y_fold_val)],
                callbacks=[lgb.early_stopping(50), lgb.log_evaluation(0)]
            )
            lgb_models.append(model)
        
        self.models[objective]['lgb'] = lgb_models
        
        return oof_preds
    
    def _train_xgboost(
        self,
        X: np.ndarray,
        y: np.ndarray,
        objective: str
    ) -> np.ndarray:
        """Train XGBoost with cross-validation."""
        params = self.get_xgboost_params(objective)
        
        model = xgb.XGBRegressor(**params)
        
        # Cross-validation predictions
        oof_preds = cross_val_predict(
            model,
            X,
            y,
            cv=self.config.n_folds,
            n_jobs=-1,
            verbose=0
        )
        
        # Train final models
        xgb_models = []
        from sklearn.model_selection import KFold
        kf = KFold(n_splits=self.config.n_folds, shuffle=True, random_state=self.config.random_state)
        
        for fold, (train_idx, val_idx) in enumerate(kf.split(X)):
            X_fold_train, X_fold_val = X[train_idx], X[val_idx]
            y_fold_train, y_fold_val = y[train_idx], y[val_idx]
            
            model = xgb.XGBRegressor(**params)
            model.fit(
                X_fold_train,
                y_fold_train,
                eval_set=[(X_fold_val, y_fold_val)],
                early_stopping_rounds=50,
                verbose=False
            )
            xgb_models.append(model)
        
        self.models[objective]['xgb'] = xgb_models
        
        return oof_preds
    
    def _train_catboost(
        self,
        X: np.ndarray,
        y: np.ndarray,
        objective: str,
        categorical_features: Optional[List[int]] = None
    ) -> np.ndarray:
        """Train CatBoost with cross-validation."""
        params = self.get_catboost_params(objective)
        
        model = cb.CatBoostRegressor(**params)
        
        # Cross-validation predictions
        oof_preds = cross_val_predict(
            model,
            X,
            y,
            cv=self.config.n_folds,
            verbose=0
        )
        
        # Train final models
        cb_models = []
        from sklearn.model_selection import KFold
        kf = KFold(n_splits=self.config.n_folds, shuffle=True, random_state=self.config.random_state)
        
        for fold, (train_idx, val_idx) in enumerate(kf.split(X)):
            X_fold_train, X_fold_val = X[train_idx], X[val_idx]
            y_fold_train, y_fold_val = y[train_idx], y[val_idx]
            
            model = cb.CatBoostRegressor(**params)
            model.fit(
                X_fold_train,
                y_fold_train,
                eval_set=(X_fold_val, y_fold_val),
                early_stopping_rounds=50,
                verbose=False,
                cat_features=categorical_features
            )
            cb_models.append(model)
        
        self.models[objective]['cb'] = cb_models
        
        return oof_preds
    
    def predict(
        self,
        X: np.ndarray,
        objective: str,
        model_type: str
    ) -> np.ndarray:
        """
        Generate predictions using ensemble of folds.
        
        Args:
            X: Features
            objective: 'cost', 'co2', or 'damage'
            model_type: 'lgb', 'xgb', or 'cb'
        
        Returns:
            Averaged predictions across folds
        """
        models = self.models[objective][model_type]
        
        predictions = np.zeros((X.shape[0], len(models)))
        
        for i, model in enumerate(models):
            predictions[:, i] = model.predict(X)
        
        # Average across folds
        return predictions.mean(axis=1)


class DeepTabularModels:
    """
    Deep learning models for tabular data (TabNet, Wide & Deep, Transformer).
    """
    
    def __init__(self, config: EnsembleConfig):
        """Initialize deep tabular models."""
        self.config = config
        self.models: Dict[str, Dict[str, list]] = {
            'cost': {},
            'co2': {},
            'damage': {}
        }
        
        logger.info("DeepTabularModels initialized")
    
    def train_tabnet(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        objective: str,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Train TabNet model.
        
        Args:
            X_train: Training features
            y_train: Training targets
            objective: Objective name
            X_val: Validation features
            y_val: Validation targets
        
        Returns:
            Out-of-fold predictions
        """
        logger.info(f"Training TabNet for {objective}...")
        
        model = TabNetRegressor(
            n_d=64,
            n_a=64,
            n_steps=5,
            gamma=1.5,
            n_independent=2,
            n_shared=2,
            lambda_sparse=1e-4,
            optimizer_fn=torch.optim.Adam,
            optimizer_params=dict(lr=2e-2),
            scheduler_params={"step_size":50, "gamma":0.9},
            scheduler_fn=torch.optim.lr_scheduler.StepLR,
            mask_type='entmax',
            verbose=0,
            device_name='cuda' if self.config.use_gpu else 'cpu'
        )
        
        # Train with validation if provided
        if X_val is not None and y_val is not None:
            model.fit(
                X_train,
                y_train.reshape(-1, 1),
                eval_set=[(X_val, y_val.reshape(-1, 1))],
                max_epochs=200,
                patience=20,
                batch_size=1024,
                virtual_batch_size=128,
                eval_metric=['rmse']
            )
        else:
            model.fit(
                X_train,
                y_train.reshape(-1, 1),
                max_epochs=200,
                batch_size=1024,
                virtual_batch_size=128
            )
        
        # Store model
        if objective not in self.models:
            self.models[objective] = {}
        self.models[objective]['tabnet'] = model
        
        # Return predictions
        return model.predict(X_train).flatten()
    
    def predict_tabnet(
        self,
        X: np.ndarray,
        objective: str
    ) -> np.ndarray:
        """Generate TabNet predictions."""
        model = self.models[objective]['tabnet']
        return model.predict(X).flatten()
