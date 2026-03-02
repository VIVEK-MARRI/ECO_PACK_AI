"""
Meta-Learner for Stacking Ensemble
Neural network that combines base model predictions
"""

from typing import Optional
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset
import structlog

logger = structlog.get_logger(__name__)


class MetaLearner(nn.Module):
    """
    Neural meta-learner for combining base model predictions.
    Takes predictions from all base models + GNN embeddings as input.
    """
    
    def __init__(
        self,
        num_base_predictions: int,
        gnn_embedding_dim: int = 512,
        hidden_dims: list = [256, 128],
        num_outputs: int = 3,  # cost, co2, damage
        dropout: float = 0.3
    ):
        """
        Initialize meta-learner.
        
        Args:
            num_base_predictions: Number of base model predictions
            gnn_embedding_dim: Dimension of GNN embeddings
            hidden_dims: Hidden layer dimensions
            num_outputs: Number of output objectives
            dropout: Dropout rate
        """
        super().__init__()
        
        input_dim = num_base_predictions + gnn_embedding_dim
        
        # Build MLP
        layers = []
        prev_dim = input_dim
        
        for hidden_dim in hidden_dims:
            layers.extend([
                nn.Linear(prev_dim, hidden_dim),
                nn.BatchNorm1d(hidden_dim),
                nn.ReLU(),
                nn.Dropout(dropout)
            ])
            prev_dim = hidden_dim
        
        # Output layer (separate heads for each objective)
        self.shared_layers = nn.Sequential(*layers)
        
        # Separate output heads
        self.cost_head = nn.Linear(prev_dim, 1)
        self.co2_head = nn.Linear(prev_dim, 1)
        self.damage_head = nn.Linear(prev_dim, 1)
        
        logger.info("MetaLearner initialized",
                   input_dim=input_dim,
                   hidden_dims=hidden_dims,
                   num_outputs=num_outputs)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.
        
        Args:
            x: Input tensor [batch, num_base_predictions + gnn_embedding_dim]
        
        Returns:
            Predictions [batch, 3] (cost, co2, damage_prob)
        """
        # Shared layers
        shared = self.shared_layers(x)
        
        # Output heads
        cost = self.cost_head(shared)
        co2 = self.co2_head(shared)
        damage = self.damage_head(shared)
        
        # Apply activations
        cost = torch.exp(cost)  # Ensure positive
        co2 = torch.exp(co2)  # Ensure positive
        damage = torch.sigmoid(damage)  # Probability
        
        return torch.cat([cost, co2, damage], dim=1)


class MetaLearnerTrainer:
    """
    Trainer for meta-learner.
    """
    
    def __init__(
        self,
        model: MetaLearner,
        device: str = 'cuda' if torch.cuda.is_available() else 'cpu',
        learning_rate: float = 0.001
    ):
        """Initialize trainer."""
        self.model = model.to(device)
        self.device = device
        self.optimizer = torch.optim.AdamW(
            model.parameters(),
            lr=learning_rate,
            weight_decay=1e-4
        )
        self.scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer,
            mode='min',
            factor=0.5,
            patience=5,
            verbose=True
        )
        
        logger.info("MetaLearnerTrainer initialized", device=device)
    
    def train(
        self,
        oof_predictions: np.ndarray,
        gnn_embeddings: np.ndarray,
        y_cost: np.ndarray,
        y_co2: np.ndarray,
        y_damage: np.ndarray,
        num_epochs: int = 100,
        batch_size: int = 256,
        val_split: float = 0.2
    ) -> dict:
        """
        Train meta-learner.
        
        Args:
            oof_predictions: Out-of-fold predictions from base models [N, num_base]
            gnn_embeddings: GNN embeddings [N, embedding_dim]
            y_cost: Cost targets [N]
            y_co2: CO2 targets [N]
            y_damage: Damage targets [N]
            num_epochs: Number of epochs
            batch_size: Batch size
            val_split: Validation split ratio
        
        Returns:
            Training history
        """
        logger.info("Training meta-learner...")
        
        # Prepare data
        X = np.concatenate([oof_predictions, gnn_embeddings], axis=1)
        y = np.stack([y_cost, y_co2, y_damage], axis=1)
        
        # Train/val split
        n = X.shape[0]
        indices = np.random.permutation(n)
        split_idx = int(n * (1 - val_split))
        
        train_indices = indices[:split_idx]
        val_indices = indices[split_idx:]
        
        X_train, X_val = X[train_indices], X[val_indices]
        y_train, y_val = y[train_indices], y[val_indices]
        
        # Create data loaders
        train_dataset = TensorDataset(
            torch.FloatTensor(X_train),
            torch.FloatTensor(y_train)
        )
        val_dataset = TensorDataset(
            torch.FloatTensor(X_val),
            torch.FloatTensor(y_val)
        )
        
        train_loader = DataLoader(
            train_dataset,
            batch_size=batch_size,
            shuffle=True
        )
        val_loader = DataLoader(
            val_dataset,
            batch_size=batch_size
        )
        
        # Training loop
        history = {'train_loss': [], 'val_loss': []}
        best_val_loss = float('inf')
        
        for epoch in range(num_epochs):
            # Training
            train_loss = self._train_epoch(train_loader)
            history['train_loss'].append(train_loss)
            
            # Validation
            val_loss = self._validate(val_loader)
            history['val_loss'].append(val_loss)
            
            # Logging
            if (epoch + 1) % 10 == 0:
                logger.info("Epoch",
                           epoch=epoch+1,
                           train_loss=train_loss,
                           val_loss=val_loss)
            
            # Learning rate scheduling
            self.scheduler.step(val_loss)
            
            # Save best model
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                torch.save(
                    self.model.state_dict(),
                    'meta_learner_best.pt'
                )
        
        logger.info("Meta-learner training complete",
                   best_val_loss=best_val_loss)
        
        return history
    
    def _train_epoch(self, train_loader: DataLoader) -> float:
        """Train for one epoch."""
        self.model.train()
        total_loss = 0
        
        for X_batch, y_batch in train_loader:
            X_batch = X_batch.to(self.device)
            y_batch = y_batch.to(self.device)
            
            self.optimizer.zero_grad()
            
            # Forward pass
            predictions = self.model(X_batch)
            
            # Multi-objective loss
            loss = self._compute_loss(predictions, y_batch)
            
            # Backward pass
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
            self.optimizer.step()
            
            total_loss += loss.item()
        
        return total_loss / len(train_loader)
    
    @torch.no_grad()
    def _validate(self, val_loader: DataLoader) -> float:
        """Validate model."""
        self.model.eval()
        total_loss = 0
        
        for X_batch, y_batch in val_loader:
            X_batch = X_batch.to(self.device)
            y_batch = y_batch.to(self.device)
            
            predictions = self.model(X_batch)
            loss = self._compute_loss(predictions, y_batch)
            
            total_loss += loss.item()
        
        return total_loss / len(val_loader)
    
    def _compute_loss(
        self,
        predictions: torch.Tensor,
        targets: torch.Tensor
    ) -> torch.Tensor:
        """
        Compute multi-objective loss.
        
        Args:
            predictions: [batch, 3] (cost, co2, damage)
            targets: [batch, 3] (cost, co2, damage)
        
        Returns:
            Combined loss
        """
        # MSE for cost and co2
        cost_loss = F.mse_loss(predictions[:, 0], targets[:, 0])
        co2_loss = F.mse_loss(predictions[:, 1], targets[:, 1])
        
        # BCE for damage probability
        damage_loss = F.binary_cross_entropy(
            predictions[:, 2],
            targets[:, 2]
        )
        
        # Weighted combination
        total_loss = cost_loss + co2_loss + damage_loss
        
        return total_loss
