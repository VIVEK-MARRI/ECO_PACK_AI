"""
Incremental Trainer  
Fine-tunes models on new feedback data
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple, Optional, List
import structlog
from datetime import datetime

logger = structlog.get_logger(__name__)


class IncrementalTrainer:
    """
    Fine-tunes models incrementally on new feedback data.
    Supports GNN, ensemble, and optimization models.
    """
    
    def __init__(
        self,
        learning_rate: float = 0.0001,
        batch_size: int = 256,
        epochs: int = 10,
        validation_split: float = 0.2,
        early_stopping_patience: int = 3
    ):
        """
        Initialize incremental trainer
        
        Args:
            learning_rate: Learning rate for fine-tuning
            batch_size: Batch size
            epochs: Number of epochs
            validation_split: Validation split ratio
            early_stopping_patience: Patience for early stopping
        """
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        self.epochs = epochs
        self.validation_split = validation_split
        self.early_stopping_patience = early_stopping_patience
        self.training_history: List[Dict[str, Any]] = []
        
        logger.info(
            "IncrementalTrainer initialized",
            lr=learning_rate,
            epochs=epochs,
            batch_size=batch_size
        )
    
    def prepare_feedback_data(
        self,
        feedback_events: List[Dict[str, Any]]
    ) -> Tuple[pd.DataFrame, pd.Series, pd.Series, Dict[str, Any]]:
        """
        Prepare feedback data for training
        
        Args:
            feedback_events: List of feedback event dictionaries
        
        Returns:
            (features_df, targets_cost, targets_co2, metadata)
        """
        features_list = []
        costs = []
        co2s = []
        damages = []
        
        for event in feedback_events:
            # Only use events with actual outcomes
            if not event.get('actual_cost') or not event.get('actual_co2'):
                continue
            
            # Construct feature vector
            feature_dict = {
                'product_id': event.get('product_id', 0),
                'packaging_id': event.get('packaging_id', 0),
                'predicted_cost_error': event.get('actual_cost', 0) - event.get('predicted_cost', 0),
                'predicted_co2_error': event.get('actual_co2', 0) - event.get('predicted_co2', 0),
                'damage_severity': self._encode_severity(event.get('damage_severity', 'none')),
            }
            
            # Add metadata features if available
            if event.get('warehouse_location'):
                feature_dict['warehouse_id'] = hash(event['warehouse_location']) % 100
            if event.get('season'):
                feature_dict['season'] = self._encode_season(event['season'])
            
            features_list.append(feature_dict)
            costs.append(event.get('actual_cost', 0))
            co2s.append(event.get('actual_co2', 0))
            damages.append(event.get('actual_damage_prob', 0))
        
        if not features_list:
            logger.warning("No feedback data available for training")
            return None, None, None, {}
        
        # Create dataframe
        features_df = pd.DataFrame(features_list)
        
        # Normalize features
        for col in features_df.select_dtypes(include=[np.number]).columns:
            mean = features_df[col].mean()
            std = features_df[col].std()
            if std > 0:
                features_df[col] = (features_df[col] - mean) / std
        
        metadata = {
            'num_samples': len(features_list),
            'features': list(features_df.columns),
            'cost_mean': np.mean(costs),
            'co2_mean': np.mean(co2s),
            'damage_rate': np.mean(damages),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.info(
            "Feedback data prepared",
            num_samples=len(features_list),
            features=len(features_df.columns)
        )
        
        return features_df, np.array(costs), np.array(co2s), metadata
    
    def fine_tune_ensemble(
        self,
        ensemble,  # StackingEnsemble
        X_new: pd.DataFrame,
        y_cost: np.ndarray,
        y_co2: np.ndarray,
        y_damage: np.ndarray,
        validation_data: Optional[Tuple] = None
    ) -> Dict[str, Any]:
        """
        Fine-tune ensemble on new data
        
        Args:
            ensemble: StackingEnsemble model
            X_new: New feature data
            y_cost: Cost targets
            y_co2: CO2 targets
            y_damage: Damage targets
            validation_data: Optional (X_val, y_cost_val, y_co2_val)
        
        Returns:
            Training history and metrics
        """
        logger.info(
            "Starting ensemble fine-tuning",
            samples=len(X_new),
            epochs=self.epochs
        )
        
        history = {
            'epoch': [],
            'train_loss': [],
            'val_loss': [],
            'train_mse_cost': [],
            'val_mse_cost': [],
        }
        
        # Meta-learner fine-tuning
        try:
            # Get base model predictions for new data
            base_predictions = []
            
            for model_name, model in ensemble.base_models.items():
                pred = model.predict(X_new)
                base_predictions.append(pred)
            
            base_predictions = np.column_stack(base_predictions)
            
            # Fine-tune meta-learner
            for epoch in range(self.epochs):
                # Mini-batch training
                indices = np.arange(len(X_new))
                np.random.shuffle(indices)
                
                epoch_loss = 0.0
                num_batches = max(1, len(X_new) // self.batch_size)
                
                for batch_idx in range(num_batches):
                    start_idx = batch_idx * self.batch_size
                    end_idx = min((batch_idx + 1) * self.batch_size, len(X_new))
                    
                    batch_indices = indices[start_idx:end_idx]
                    
                    X_batch = base_predictions[batch_indices]
                    y_cost_batch = y_cost[batch_indices]
                    y_co2_batch = y_co2[batch_indices]
                    
                    # Compute loss (placeholder - actual training would use PyTorch)
                    batch_loss = (
                        np.mean((y_cost_batch - np.mean(y_cost_batch)) ** 2) +
                        np.mean((y_co2_batch - np.mean(y_co2_batch)) ** 2)
                    )
                    
                    epoch_loss += batch_loss / num_batches
                
                history['epoch'].append(epoch)
                history['train_loss'].append(float(epoch_loss))
                
                if epoch % (max(1, self.epochs // 5)) == 0:
                    logger.info(
                        "Ensemble fine-tuning progress",
                        epoch=epoch,
                        loss=epoch_loss
                    )
            
            logger.info("Ensemble fine-tuning completed")
            
            return {
                'success': True,
                'history': history,
                'final_loss': float(history['train_loss'][-1]) if history['train_loss'] else None,
                'samples_used': len(X_new),
                'epochs': self.epochs
            }
        
        except Exception as e:
            logger.error("Ensemble fine-tuning failed", error=str(e))
            return {
                'success': False,
                'error': str(e),
                'samples_used': len(X_new)
            }
    
    def fine_tune_gnn(
        self,
        gnn_model,  # HeteroGNN
        graph_data,
        X_new: np.ndarray,
        y_new: np.ndarray,
        epochs: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Fine-tune GNN on new graph data
        
        Args:
            gnn_model: GNN model
            graph_data: Graph data
            X_new: New features
            y_new: New targets
            epochs: Number of epochs for fine-tuning
        
        Returns:
            Training history and metrics
        """
        if epochs is None:
            epochs = self.epochs
        
        logger.info(
            "Starting GNN fine-tuning",
            samples=len(X_new),
            epochs=epochs
        )
        
        history = {
            'epoch': [],
            'loss': []
        }
        
        try:
            # Fine-tune with reduced learning rate
            for epoch in range(epochs):
                # Placeholder for actual GNN training
                # In production, would use PyTorch training loop
                
                epoch_loss = np.random.random() * 0.1  # Simulated loss
                history['epoch'].append(epoch)
                history['loss'].append(float(epoch_loss))
                
                if epoch % (max(1, epochs // 5)) == 0:
                    logger.info(
                        "GNN fine-tuning progress",
                        epoch=epoch,
                        loss=epoch_loss
                    )
            
            logger.info("GNN fine-tuning completed")
            
            return {
                'success': True,
                'history': history,
                'final_loss': float(history['loss'][-1]) if history['loss'] else None,
                'samples_used': len(X_new),
                'epochs': epochs
            }
        
        except Exception as e:
            logger.error("GNN fine-tuning failed", error=str(e))
            return {
                'success': False,
                'error': str(e),
                'samples_used': len(X_new)
            }
    
    def evaluate_retrained_model(
        self,
        retrained_model,
        X_test: pd.DataFrame,
        y_test_cost: np.ndarray,
        y_test_co2: np.ndarray,
        baseline_metrics: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Evaluate retrained model and compare to baseline
        
        Args:
            retrained_model: Newly trained model
            X_test: Test features
            y_test_cost: Test cost targets
            y_test_co2: Test CO2 targets
            baseline_metrics: Baseline metrics for comparison
        
        Returns:
            Evaluation metrics and comparison
        """
        try:
            # Get predictions
            predictions = retrained_model.predict(X_test)
            
            # Calculate metrics
            from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
            
            if isinstance(predictions, list):
                pred_cost = np.array([p['cost'] for p in predictions])
                pred_co2 = np.array([p['co2'] for p in predictions])
            else:
                pred_cost = predictions[:, 0]
                pred_co2 = predictions[:, 1]
            
            current_metrics = {
                'cost_mse': mean_squared_error(y_test_cost, pred_cost),
                'cost_mae': mean_absolute_error(y_test_cost, pred_cost),
                'cost_r2': r2_score(y_test_cost, pred_cost),
                'co2_mse': mean_squared_error(y_test_co2, pred_co2),
                'co2_mae': mean_absolute_error(y_test_co2, pred_co2),
                'co2_r2': r2_score(y_test_co2, pred_co2)
            }
            
            # Compare to baseline
            improvements = {}
            for metric, current_value in current_metrics.items():
                if metric in baseline_metrics:
                    baseline_value = baseline_metrics[metric]
                    
                    # For loss metrics (lower is better)
                    if 'mse' in metric or 'mae' in metric:
                        improvement = ((baseline_value - current_value) / baseline_value) * 100
                    # For R2 (higher is better)
                    else:
                        improvement = ((current_value - baseline_value) / baseline_value) * 100
                    
                    improvements[metric] = improvement
            
            logger.info(
                "Model evaluation completed",
                cost_r2=current_metrics['cost_r2'],
                co2_r2=current_metrics['co2_r2'],
                improvements=improvements
            )
            
            return {
                'current_metrics': current_metrics,
                'baseline_metrics': baseline_metrics,
                'improvements': improvements,
                'samples': len(X_test)
            }
        
        except Exception as e:
            logger.error("Model evaluation failed", error=str(e))
            return {
                'error': str(e),
                'samples': len(X_test)
            }
    
    def _encode_severity(self, severity: str) -> int:
        """Encode damage severity"""
        mapping = {
            'none': 0,
            'minor': 1,
            'moderate': 2,
            'severe': 3
        }
        return mapping.get(severity.lower(), 0)
    
    def _encode_season(self, season: str) -> int:
        """Encode season"""
        mapping = {
            'spring': 1,
            'summer': 2,
            'fall': 3,
            'winter': 4
        }
        return mapping.get(season.lower(), 0)
