"""
Graph Model Inference
Real-time embedding generation and product-packaging scoring
"""

from typing import Dict, List, Optional, Tuple
import torch
import torch.nn as nn
from torch_geometric.data import HeteroData
import numpy as np
import structlog

logger = structlog.get_logger(__name__)


class GraphInference:
    """
    Fast inference engine for GNN-based recommendations.
    Caches embeddings for efficient prediction.
    """
    
    def __init__(
        self,
        model: nn.Module,
        scorer: nn.Module,
        device: str = 'cuda' if torch.cuda.is_available() else 'cpu'
    ):
        """
        Initialize inference engine.
        
        Args:
            model: Trained GNN model
            scorer: Product-packaging scorer model
            device: Device for inference
        """
        self.model = model.to(device)
        self.scorer = scorer.to(device)
        self.device = device
        
        self.model.eval()
        self.scorer.eval()
        
        # Embedding cache
        self.product_embeddings: Optional[torch.Tensor] = None
        self.packaging_embeddings: Optional[torch.Tensor] = None
        
        logger.info("GraphInference initialized", device=device)
    
    @torch.no_grad()
    def generate_embeddings(self, data: HeteroData) -> Dict[str, torch.Tensor]:
        """
        Generate embeddings for all nodes.
        
        Args:
            data: Heterogeneous graph data
        
        Returns:
            Dictionary of embeddings for each node type
        """
        logger.info("Generating graph embeddings...")
        
        # Move data to device
        data = data.to(self.device)
        
        # Get node features
        x_dict = {nt: data[nt].x for nt in data.node_types}
        edge_index_dict = {et: data[et].edge_index for et in data.edge_types}
        
        # Forward pass
        embeddings = self.model(x_dict, edge_index_dict)
        
        # Cache embeddings
        if 'product' in embeddings:
            self.product_embeddings = embeddings['product'].cpu()
        if 'packaging' in embeddings:
            self.packaging_embeddings = embeddings['packaging'].cpu()
        
        logger.info("Embeddings generated",
                   num_node_types=len(embeddings),
                   product_emb_shape=self.product_embeddings.shape if self.product_embeddings is not None else None)
        
        return {k: v.cpu() for k, v in embeddings.items()}
    
    @torch.no_grad()
    def predict_for_product(
        self,
        product_id: int,
        packaging_ids: Optional[List[int]] = None,
        top_k: int = 10
    ) -> List[Dict]:
        """
        Predict best packaging options for a product.
        
        Args:
            product_id: Product node ID
            packaging_ids: Optional list of packaging IDs to score
            top_k: Number of top recommendations
        
        Returns:
            List of predictions with cost, co2, damage scores
        """
        if self.product_embeddings is None or self.packaging_embeddings is None:
            raise ValueError("Embeddings not generated. Call generate_embeddings first.")
        
        # Get product embedding
        product_emb = self.product_embeddings[product_id].unsqueeze(0).to(self.device)
        
        # Select packaging to score
        if packaging_ids is None:
            # Score all packaging options
            packaging_embs = self.packaging_embeddings.to(self.device)
            packaging_ids = list(range(len(packaging_embs)))
        else:
            packaging_embs = self.packaging_embeddings[packaging_ids].to(self.device)
        
        # Expand product embedding to match packaging batch
        product_emb = product_emb.expand(len(packaging_embs), -1)
        
        # Predict scores
        predictions = self.scorer(product_emb, packaging_embs)
        
        # Extract individual predictions
        costs = predictions[:, 0].cpu().numpy()
        co2s = predictions[:, 1].cpu().numpy()
        damage_probs = predictions[:, 2].cpu().numpy()
        
        # Create results
        results = []
        for i, pack_id in enumerate(packaging_ids):
            results.append({
                'packaging_id': int(pack_id),
                'predicted_cost': float(costs[i]),
                'predicted_co2': float(co2s[i]),
                'predicted_damage_prob': float(damage_probs[i]),
                'combined_score': self._compute_combined_score(
                    costs[i], co2s[i], damage_probs[i]
                )
            })
        
        # Sort by combined score (lower is better)
        results.sort(key=lambda x: x['combined_score'])
        
        return results[:top_k]
    
    @torch.no_grad()
    def batch_predict(
        self,
        product_ids: List[int],
        packaging_id: int
    ) -> np.ndarray:
        """
        Predict for multiple products with single packaging.
        
        Args:
            product_ids: List of product node IDs
            packaging_id: Packaging node ID
        
        Returns:
            Predictions [num_products, 3] (cost, co2, damage)
        """
        if self.product_embeddings is None or self.packaging_embeddings is None:
            raise ValueError("Embeddings not generated.")
        
        # Get embeddings
        product_embs = self.product_embeddings[product_ids].to(self.device)
        packaging_emb = self.packaging_embeddings[packaging_id].unsqueeze(0).to(self.device)
        
        # Expand packaging embedding
        packaging_emb = packaging_emb.expand(len(product_ids), -1)
        
        # Predict
        predictions = self.scorer(product_embs, packaging_emb)
        
        return predictions.cpu().numpy()
    
    def _compute_combined_score(
        self,
        cost: float,
        co2: float,
        damage_prob: float,
        weights: Optional[Tuple[float, float, float]] = None
    ) -> float:
        """
        Compute weighted combined score.
        
        Args:
            cost: Predicted cost
            co2: Predicted CO2 emissions
            damage_prob: Predicted damage probability
            weights: Tuple of (cost_weight, co2_weight, damage_weight)
        
        Returns:
            Combined score (lower is better)
        """
        if weights is None:
            weights = (0.4, 0.3, 0.3)  # Default weights
        
        # Normalize values to [0, 1] range
        # These should ideally be based on dataset statistics
        norm_cost = min(cost / 100.0, 1.0)  # Assuming max cost ~100
        norm_co2 = min(co2 / 50.0, 1.0)  # Assuming max CO2 ~50 kg
        norm_damage = damage_prob  # Already in [0, 1]
        
        score = (
            weights[0] * norm_cost +
            weights[1] * norm_co2 +
            weights[2] * norm_damage
        )
        
        return score
    
    @torch.no_grad()
    def get_product_embedding(self, product_id: int) -> np.ndarray:
        """Get embedding for specific product."""
        if self.product_embeddings is None:
            raise ValueError("Embeddings not generated.")
        
        return self.product_embeddings[product_id].numpy()
    
    @torch.no_grad()
    def get_packaging_embedding(self, packaging_id: int) -> np.ndarray:
        """Get embedding for specific packaging."""
        if self.packaging_embeddings is None:
            raise ValueError("Embeddings not generated.")
        
        return self.packaging_embeddings[packaging_id].numpy()
    
    @torch.no_grad()
    def compute_similarity(
        self,
        product_id: int,
        packaging_id: int
    ) -> float:
        """
        Compute cosine similarity between product and packaging.
        
        Args:
            product_id: Product node ID
            packaging_id: Packaging node ID
        
        Returns:
            Similarity score in [-1, 1]
        """
        product_emb = self.get_product_embedding(product_id)
        packaging_emb = self.get_packaging_embedding(packaging_id)
        
        # Cosine similarity
        dot_product = np.dot(product_emb, packaging_emb)
        norm_product = np.linalg.norm(product_emb)
        norm_packaging = np.linalg.norm(packaging_emb)
        
        similarity = dot_product / (norm_product * norm_packaging + 1e-8)
        
        return float(similarity)
    
    def find_similar_products(
        self,
        product_id: int,
        top_k: int = 5,
        exclude_self: bool = True
    ) -> List[Tuple[int, float]]:
        """
        Find similar products based on embedding similarity.
        
        Args:
            product_id: Query product ID
            top_k: Number of similar products to return
            exclude_self: Exclude the query product itself
        
        Returns:
            List of (product_id, similarity_score) tuples
        """
        if self.product_embeddings is None:
            raise ValueError("Embeddings not generated.")
        
        query_emb = self.product_embeddings[product_id].unsqueeze(0)
        
        # Compute similarities
        similarities = torch.nn.functional.cosine_similarity(
            query_emb,
            self.product_embeddings,
            dim=1
        )
        
        # Get top-k
        if exclude_self:
            similarities[product_id] = -1.0  # Exclude self
        
        top_indices = torch.argsort(similarities, descending=True)[:top_k]
        top_scores = similarities[top_indices]
        
        results = [
            (int(idx), float(score))
            for idx, score in zip(top_indices, top_scores)
        ]
        
        return results
    
    def clear_cache(self):
        """Clear embedding cache to free memory."""
        self.product_embeddings = None
        self.packaging_embeddings = None
        
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        logger.info("Embedding cache cleared")
