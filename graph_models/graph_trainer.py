"""
Graph Model Training
Handles training loop, validation, and checkpointing
"""

from typing import Dict, Optional, Tuple
import os
from pathlib import Path
import torch
import torch.nn as nn
from torch.optim import AdamW
from torch.optim.lr_scheduler import CosineAnnealingWarmRestarts
from torch_geometric.data import HeteroData
from torch_geometric.loader import NeighborLoader
import mlflow
import structlog
from tqdm import tqdm

logger = structlog.get_logger(__name__)


class GraphTrainer:
    """
    Trainer for GNN models with MLflow tracking.
    """
    
    def __init__(
        self,
        model: nn.Module,
        device: str = 'cuda' if torch.cuda.is_available() else 'cpu',
        learning_rate: float = 0.001,
        weight_decay: float = 1e-5,
        patience: int = 20,
        min_delta: float = 1e-4
    ):
        """
        Initialize trainer.
        
        Args:
            model: GNN model to train
            device: Device to train on
            learning_rate: Initial learning rate
            weight_decay: L2 regularization weight
            patience: Early stopping patience
            min_delta: Minimum improvement for early stopping
        """
        self.model = model.to(device)
        self.device = device
        self.patience = patience
        self.min_delta = min_delta
        
        self.optimizer = AdamW(
            model.parameters(),
            lr=learning_rate,
            weight_decay=weight_decay
        )
        
        self.scheduler = CosineAnnealingWarmRestarts(
            self.optimizer,
            T_0=10,
            T_mult=2
        )
        
        self.best_val_loss = float('inf')
        self.patience_counter = 0
        self.epoch = 0
        
        logger.info("GraphTrainer initialized",
                   device=device,
                   learning_rate=learning_rate)
    
    def train_epoch(
        self,
        train_loader: NeighborLoader,
        criterion: nn.Module
    ) -> float:
        """
        Train for one epoch.
        
        Args:
            train_loader: Training data loader
            criterion: Loss function
        
        Returns:
            Average training loss
        """
        self.model.train()
        total_loss = 0
        num_batches = 0
        
        pbar = tqdm(train_loader, desc=f"Epoch {self.epoch} [Train]")
        
        for batch in pbar:
            batch = batch.to(self.device)
            
            self.optimizer.zero_grad()
            
            # Forward pass
            out_dict = self.model(
                {nt: batch[nt].x for nt in batch.node_types},
                {et: batch[et].edge_index for et in batch.edge_types}
            )
            
            # Compute loss (example for node classification)
            loss = criterion(
                out_dict['product'],
                batch['product'].y
            )
            
            # Backward pass
            loss.backward()
            
            # Gradient clipping
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
            
            self.optimizer.step()
            
            total_loss += loss.item()
            num_batches += 1
            
            pbar.set_postfix({'loss': loss.item()})
        
        avg_loss = total_loss / num_batches
        return avg_loss
    
    @torch.no_grad()
    def validate(
        self,
        val_loader: NeighborLoader,
        criterion: nn.Module
    ) -> Tuple[float, Dict[str, float]]:
        """
        Validate model.
        
        Args:
            val_loader: Validation data loader
            criterion: Loss function
        
        Returns:
            Average validation loss and metrics
        """
        self.model.eval()
        total_loss = 0
        num_batches = 0
        
        all_preds = []
        all_targets = []
        
        for batch in val_loader:
            batch = batch.to(self.device)
            
            # Forward pass
            out_dict = self.model(
                {nt: batch[nt].x for nt in batch.node_types},
                {et: batch[et].edge_index for et in batch.edge_types}
            )
            
            # Compute loss
            loss = criterion(
                out_dict['product'],
                batch['product'].y
            )
            
            total_loss += loss.item()
            num_batches += 1
            
            # Collect predictions
            all_preds.append(out_dict['product'].cpu())
            all_targets.append(batch['product'].y.cpu())
        
        avg_loss = total_loss / num_batches
        
        # Compute metrics
        all_preds = torch.cat(all_preds)
        all_targets = torch.cat(all_targets)
        
        metrics = self._compute_metrics(all_preds, all_targets)
        metrics['loss'] = avg_loss
        
        return avg_loss, metrics
    
    def _compute_metrics(
        self,
        predictions: torch.Tensor,
        targets: torch.Tensor
    ) -> Dict[str, float]:
        """Compute evaluation metrics."""
        with torch.no_grad():
            # For regression tasks
            mse = torch.mean((predictions - targets) ** 2).item()
            mae = torch.mean(torch.abs(predictions - targets)).item()
            
            # R² score
            ss_res = torch.sum((targets - predictions) ** 2)
            ss_tot = torch.sum((targets - torch.mean(targets)) ** 2)
            r2 = (1 - ss_res / ss_tot).item()
            
            return {
                'mse': mse,
                'mae': mae,
                'r2': r2
            }
    
    def train(
        self,
        train_loader: NeighborLoader,
        val_loader: NeighborLoader,
        num_epochs: int,
        criterion: nn.Module,
        checkpoint_dir: str = 'checkpoints'
    ) -> Dict[str, list]:
        """
        Full training loop with early stopping.
        
        Args:
            train_loader: Training data loader
            val_loader: Validation data loader
            num_epochs: Maximum epochs
            criterion: Loss function
            checkpoint_dir: Directory for checkpoints
        
        Returns:
            Training history
        """
        Path(checkpoint_dir).mkdir(parents=True, exist_ok=True)
        
        history = {
            'train_loss': [],
            'val_loss': [],
            'val_metrics': []
        }
        
        # Start MLflow run
        with mlflow.start_run():
            mlflow.log_params({
                'learning_rate': self.optimizer.param_groups[0]['lr'],
                'weight_decay': self.optimizer.param_groups[0]['weight_decay'],
                'num_epochs': num_epochs,
                'patience': self.patience
            })
            
            for epoch in range(num_epochs):
                self.epoch = epoch
                
                # Training
                train_loss = self.train_epoch(train_loader, criterion)
                history['train_loss'].append(train_loss)
                
                # Validation
                val_loss, val_metrics = self.validate(val_loader, criterion)
                history['val_loss'].append(val_loss)
                history['val_metrics'].append(val_metrics)
                
                # Logging
                logger.info("Epoch complete",
                           epoch=epoch,
                           train_loss=train_loss,
                           val_loss=val_loss,
                           **val_metrics)
                
                mlflow.log_metrics({
                    'train_loss': train_loss,
                    'val_loss': val_loss,
                    **{f'val_{k}': v for k, v in val_metrics.items()}
                }, step=epoch)
                
                # Learning rate scheduling
                self.scheduler.step()
                
                # Early stopping check
                if val_loss < self.best_val_loss - self.min_delta:
                    self.best_val_loss = val_loss
                    self.patience_counter = 0
                    
                    # Save best model
                    checkpoint_path = os.path.join(
                        checkpoint_dir,
                        'best_model.pt'
                    )
                    self.save_checkpoint(checkpoint_path)
                    
                    logger.info("New best model saved",
                               val_loss=val_loss,
                               path=checkpoint_path)
                else:
                    self.patience_counter += 1
                    
                    if self.patience_counter >= self.patience:
                        logger.info("Early stopping triggered",
                                   epoch=epoch,
                                   patience=self.patience)
                        break
                
                # Save periodic checkpoint
                if (epoch + 1) % 10 == 0:
                    checkpoint_path = os.path.join(
                        checkpoint_dir,
                        f'checkpoint_epoch_{epoch+1}.pt'
                    )
                    self.save_checkpoint(checkpoint_path)
            
            # Log best model to MLflow
            mlflow.pytorch.log_model(
                self.model,
                'model',
                registered_model_name='gnn_packaging_model'
            )
        
        logger.info("Training complete",
                   best_val_loss=self.best_val_loss,
                   total_epochs=self.epoch + 1)
        
        return history
    
    def save_checkpoint(self, path: str):
        """Save model checkpoint."""
        torch.save({
            'epoch': self.epoch,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'scheduler_state_dict': self.scheduler.state_dict(),
            'best_val_loss': self.best_val_loss,
            'patience_counter': self.patience_counter
        }, path)
    
    def load_checkpoint(self, path: str):
        """Load model checkpoint."""
        checkpoint = torch.load(path, map_location=self.device)
        
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
        self.epoch = checkpoint['epoch']
        self.best_val_loss = checkpoint['best_val_loss']
        self.patience_counter = checkpoint['patience_counter']
        
        logger.info("Checkpoint loaded",
                   epoch=self.epoch,
                   best_val_loss=self.best_val_loss,
                   path=path)
