"""
Stacking Ensemble
Combines gradient boosting, deep learning, and GNN models
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import joblib
import structlog

from .base_models import GradientBoostingModels, DeepTabularModels, EnsembleConfig
from .meta_learner import MetaLearner, MetaLearnerTrainer

logger = structlog.get_logger(__name__)


class StackingEnsemble:
    """
    Complete stacking ensemble system.
    
    Level 0: Base models (Boosting + Deep Learning)
    Level 1: Meta-learner (Neural Network)
    
    Includes GNN embeddings as additional features.
    """
    
    def __init__(
        self,
        config: Optional[EnsembleConfig] = None,
        gnn_embedding_dim: int = 512
    ):
        """
        Initialize stacking ensemble.
        
        Args:
            config: Ensemble configuration
            gnn_embedding_dim: Dimension of GNN embeddings
        """
        self.config = config or EnsembleConfig()
        self.gnn_embedding_dim = gnn_embedding_dim
        
        # Base models
        self.gb_models = GradientBoostingModels(self.config)
        self.deep_models = DeepTabularModels(self.config)
        
        # Meta-learner
        self.meta_learner: Optional[MetaLearner] = None
        self.meta_trainer: Optional[MetaLearnerTrainer] = None
        
        # Scalers and metadata
        self.feature_scaler = None
        self.target_scalers = {}
        self.trained = False
        
        logger.info("StackingEnsemble initialized")
    
    def train(
        self,
        X_train: np.ndarray,
        y_cost: np.ndarray,
        y_co2: np.ndarray,
        y_damage: np.ndarray,
        gnn_embeddings: np.ndarray,
        categorical_features: Optional[List[int]] = None
    ) -> Dict:
        """
        Train complete stacking ensemble.
        
        Args:
            X_train: Training features
            y_cost: Cost targets
            y_co2: CO2 targets
            y_damage: Damage probability targets
            gnn_embeddings: GNN node embeddings
            categorical_features: Categorical feature indices
        
        Returns:
            Training metrics
        """
        logger.info("Training stacking ensemble...")
        
        # Step 1: Train base models and get OOF predictions
        logger.info("Step 1: Training base models...")
        
        gb_oof = self.gb_models.train(
            X_train, y_cost, y_co2, y_damage, categorical_features
        )
        
        # Collect OOF predictions
        oof_predictions_list = []
        
        for objective in ['cost', 'co2', 'damage']:
            for model_type in ['lgb', 'xgb', 'cb']:
                oof_predictions_list.append(gb_oof[objective][model_type])
        
        # Stack OOF predictions
        oof_predictions = np.column_stack(oof_predictions_list)
        
        logger.info("Base models trained",
                   oof_shape=oof_predictions.shape)
        
        # Step 2: Train meta-learner
        logger.info("Step 2: Training meta-learner...")
        
        num_base_predictions = oof_predictions.shape[1]
        
        self.meta_learner = MetaLearner(
            num_base_predictions=num_base_predictions,
            gnn_embedding_dim=self.gnn_embedding_dim
        )
        
        self.meta_trainer = MetaLearnerTrainer(self.meta_learner)
        
        history = self.meta_trainer.train(
            oof_predictions=oof_predictions,
            gnn_embeddings=gnn_embeddings,
            y_cost=y_cost,
            y_co2=y_co2,
            y_damage=y_damage,
            num_epochs=100,
            batch_size=256
        )
        
        self.trained = True
        
        logger.info("Stacking ensemble training complete")
        
        return {
            'oof_predictions': oof_predictions,
            'meta_learner_history': history
        }
    
    def predict(
        self,
        X: np.ndarray,
        gnn_embeddings: np.ndarray
    ) -> Dict[str, np.ndarray]:
        """
        Generate predictions using full ensemble.
        
        Args:
            X: Input features
            gnn_embeddings: GNN embeddings
        
        Returns:
            Predictions dictionary with cost, co2, damage
        """
        if not self.trained:
            raise ValueError("Ensemble not trained. Call train() first.")
        
        logger.info("Generating ensemble predictions...")
        
        # Step 1: Get base model predictions
        base_predictions_list = []
        
        for objective in ['cost', 'co2', 'damage']:
            for model_type in ['lgb', 'xgb', 'cb']:
                preds = self.gb_models.predict(X, objective, model_type)
                base_predictions_list.append(preds)
        
        base_predictions = np.column_stack(base_predictions_list)
        
        # Step 2: Combine with GNN embeddings
        meta_input = np.concatenate([base_predictions, gnn_embeddings], axis=1)
        
        # Step 3: Meta-learner prediction
        import torch
        self.meta_learner.eval()
        
        with torch.no_grad():
            meta_input_tensor = torch.FloatTensor(meta_input).to(self.meta_trainer.device)
            final_predictions = self.meta_learner(meta_input_tensor).cpu().numpy()
        
        logger.info("Ensemble predictions generated")
        
        return {
            'cost': final_predictions[:, 0],
            'co2': final_predictions[:, 1],
            'damage_prob': final_predictions[:, 2]
        }
    
    def predict_single(
        self,
        x: np.ndarray,
        gnn_embedding: np.ndarray
    ) -> Dict[str, float]:
        """
        Predict for single sample.
        
        Args:
            x: Single feature vector [1, n_features]
            gnn_embedding: Single GNN embedding [1, embedding_dim]
        
        Returns:
            Single prediction dictionary
        """
        predictions = self.predict(
            x.reshape(1, -1),
            gnn_embedding.reshape(1, -1)
        )
        
        return {
            'cost': float(predictions['cost'][0]),
            'co2': float(predictions['co2'][0]),
            'damage_prob': float(predictions['damage_prob'][0])
        }
    
    def save(self, path: str):
        """Save ensemble to disk."""
        logger.info("Saving ensemble...", path=path)
        
        import torch
        
        ensemble_state = {
            'config': self.config,
            'gnn_embedding_dim': self.gnn_embedding_dim,
            'gb_models': self.gb_models.models,
            'deep_models': self.deep_models.models,
            'meta_learner_state': self.meta_learner.state_dict() if self.meta_learner else None,
            'trained': self.trained
        }
        
        joblib.dump(ensemble_state, path)
        
        logger.info("Ensemble saved successfully")
    
    def load(self, path: str):
        """Load ensemble from disk."""
        logger.info("Loading ensemble...", path=path)
        
        ensemble_state = joblib.load(path)
        
        self.config = ensemble_state['config']
        self.gnn_embedding_dim = ensemble_state['gnn_embedding_dim']
        self.gb_models.models = ensemble_state['gb_models']
        self.deep_models.models = ensemble_state['deep_models']
        self.trained = ensemble_state['trained']
        
        if ensemble_state['meta_learner_state']:
            num_base_predictions = 9  # 3 objectives × 3 models
            self.meta_learner = MetaLearner(
                num_base_predictions=num_base_predictions,
                gnn_embedding_dim=self.gnn_embedding_dim
            )
            self.meta_learner.load_state_dict(ensemble_state['meta_learner_state'])
            self.meta_trainer = MetaLearnerTrainer(self.meta_learner)
        
        logger.info("Ensemble loaded successfully")
    
    def get_feature_importance(
        self,
        feature_names: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Get aggregated feature importance from gradient boosting models.
        
        Args:
            feature_names: Optional feature names
        
        Returns:
            DataFrame with feature importances
        """
        importances = {}
        
        for objective in ['cost', 'co2', 'damage']:
            for model_type in ['lgb', 'xgb', 'cb']:
                models = self.gb_models.models[objective][model_type]
                
                # Average importance across folds
                fold_importances = []
                for model in models:
                    if hasattr(model, 'feature_importances_'):
                        fold_importances.append(model.feature_importances_)
                
                if fold_importances:
                    avg_importance = np.mean(fold_importances, axis=0)
                    key = f'{objective}_{model_type}'
                    importances[key] = avg_importance
        
        # Create DataFrame
        if feature_names is None:
            feature_names = [f'feature_{i}' for i in range(len(next(iter(importances.values()))))]
        
        df = pd.DataFrame(importances, index=feature_names)
        df['mean'] = df.mean(axis=1)
        df = df.sort_values('mean', ascending=False)
        
        return df
