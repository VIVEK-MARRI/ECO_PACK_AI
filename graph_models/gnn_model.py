"""
Graph Neural Network Models
GAT, GraphSAGE, and Heterogeneous GNN architectures
"""

from typing import Dict, List, Optional
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GATConv, SAGEConv, HeteroConv, Linear
from torch_geometric.data import HeteroData
import structlog

logger = structlog.get_logger(__name__)


class PackagingGAT(nn.Module):
    """
    Graph Attention Network for packaging recommendations.
    Uses multi-head attention to learn importance of neighbor relationships.
    """
    
    def __init__(
        self,
        in_channels: int,
        hidden_channels: int,
        out_channels: int,
        num_heads: int = 4,
        num_layers: int = 3,
        dropout: float = 0.3
    ):
        """
        Initialize GAT model.
        
        Args:
            in_channels: Input feature dimension
            hidden_channels: Hidden layer dimension
            out_channels: Output embedding dimension
            num_heads: Number of attention heads
            num_layers: Number of GAT layers
            dropout: Dropout rate
        """
        super().__init__()
        
        self.num_layers = num_layers
        self.dropout = dropout
        
        self.convs = nn.ModuleList()
        self.norms = nn.ModuleList()
        
        # Input layer
        self.convs.append(
            GATConv(in_channels, hidden_channels, heads=num_heads, dropout=dropout)
        )
        self.norms.append(nn.BatchNorm1d(hidden_channels * num_heads))
        
        # Hidden layers
        for _ in range(num_layers - 2):
            self.convs.append(
                GATConv(
                    hidden_channels * num_heads,
                    hidden_channels,
                    heads=num_heads,
                    dropout=dropout
                )
            )
            self.norms.append(nn.BatchNorm1d(hidden_channels * num_heads))
        
        # Output layer
        self.convs.append(
            GATConv(
                hidden_channels * num_heads,
                out_channels,
                heads=1,
                concat=False,
                dropout=dropout
            )
        )
        
        logger.info("PackagingGAT initialized",
                   num_layers=num_layers,
                   hidden_channels=hidden_channels,
                   num_heads=num_heads)
    
    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.
        
        Args:
            x: Node features [num_nodes, in_channels]
            edge_index: Edge indices [2, num_edges]
        
        Returns:
            Node embeddings [num_nodes, out_channels]
        """
        for i in range(self.num_layers - 1):
            x = self.convs[i](x, edge_index)
            x = self.norms[i](x)
            x = F.elu(x)
            x = F.dropout(x, p=self.dropout, training=self.training)
        
        x = self.convs[-1](x, edge_index)
        return x


class PackagingGraphSAGE(nn.Module):
    """
    GraphSAGE for inductive learning on packaging graph.
    Learns to generate embeddings for unseen products.
    """
    
    def __init__(
        self,
        in_channels: int,
        hidden_channels: int,
        out_channels: int,
        num_layers: int = 3,
        dropout: float = 0.3,
        aggr: str = 'mean'
    ):
        """
        Initialize GraphSAGE model.
        
        Args:
            in_channels: Input feature dimension
            hidden_channels: Hidden layer dimension
            out_channels: Output embedding dimension
            num_layers: Number of SAGE layers
            dropout: Dropout rate
            aggr: Aggregation method ('mean', 'max', 'lstm')
        """
        super().__init__()
        
        self.num_layers = num_layers
        self.dropout = dropout
        
        self.convs = nn.ModuleList()
        self.norms = nn.ModuleList()
        
        # Input layer
        self.convs.append(SAGEConv(in_channels, hidden_channels, aggr=aggr))
        self.norms.append(nn.BatchNorm1d(hidden_channels))
        
        # Hidden layers
        for _ in range(num_layers - 2):
            self.convs.append(SAGEConv(hidden_channels, hidden_channels, aggr=aggr))
            self.norms.append(nn.BatchNorm1d(hidden_channels))
        
        # Output layer
        self.convs.append(SAGEConv(hidden_channels, out_channels, aggr=aggr))
        
        logger.info("PackagingGraphSAGE initialized",
                   num_layers=num_layers,
                   hidden_channels=hidden_channels,
                   aggr=aggr)
    
    def forward(self, x: torch.Tensor, edge_index: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.
        
        Args:
            x: Node features [num_nodes, in_channels]
            edge_index: Edge indices [2, num_edges]
        
        Returns:
            Node embeddings [num_nodes, out_channels]
        """
        for i in range(self.num_layers - 1):
            x = self.convs[i](x, edge_index)
            x = self.norms[i](x)
            x = F.relu(x)
            x = F.dropout(x, p=self.dropout, training=self.training)
        
        x = self.convs[-1](x, edge_index)
        return x


class HeteroGNN(nn.Module):
    """
    Heterogeneous Graph Neural Network for packaging intelligence.
    Handles multiple node types and edge types with specialized convolutions.
    """
    
    def __init__(
        self,
        metadata: tuple,
        hidden_channels: int = 256,
        out_channels: int = 512,
        num_layers: int = 3,
        dropout: float = 0.3,
        use_attention: bool = True
    ):
        """
        Initialize Heterogeneous GNN.
        
        Args:
            metadata: Graph metadata (node_types, edge_types)
            hidden_channels: Hidden layer dimension
            out_channels: Output embedding dimension
            num_layers: Number of layers
            dropout: Dropout rate
            use_attention: Use GAT instead of SAGE in convolutions
        """
        super().__init__()
        
        self.num_layers = num_layers
        self.dropout = dropout
        
        node_types, edge_types = metadata
        
        # Input projections for each node type
        self.input_projections = nn.ModuleDict()
        for node_type in node_types:
            # Will be set dynamically based on input dimensions
            self.input_projections[node_type] = nn.Identity()
        
        # Heterogeneous convolutions
        self.convs = nn.ModuleList()
        self.norms = nn.ModuleDict()
        
        for i in range(num_layers):
            conv_dict = {}
            
            for edge_type in edge_types:
                src_type, rel_type, dst_type = edge_type
                
                if i == 0:
                    in_ch = hidden_channels
                else:
                    in_ch = hidden_channels
                
                if use_attention:
                    conv_dict[edge_type] = GATConv(
                        (in_ch, in_ch),
                        hidden_channels // 4,
                        heads=4,
                        add_self_loops=False
                    )
                else:
                    conv_dict[edge_type] = SAGEConv(
                        (in_ch, in_ch),
                        hidden_channels,
                        aggr='mean'
                    )
            
            self.convs.append(HeteroConv(conv_dict, aggr='sum'))
            
            # Batch normalization for each node type
            if i < num_layers - 1:
                norm_dict = {}
                for node_type in node_types:
                    norm_dict[node_type] = nn.BatchNorm1d(hidden_channels)
                self.norms[f'layer_{i}'] = nn.ModuleDict(norm_dict)
        
        # Output projections
        self.output_projections = nn.ModuleDict()
        for node_type in node_types:
            self.output_projections[node_type] = Linear(hidden_channels, out_channels)
        
        logger.info("HeteroGNN initialized",
                   num_layers=num_layers,
                   hidden_channels=hidden_channels,
                   out_channels=out_channels,
                   num_node_types=len(node_types),
                   num_edge_types=len(edge_types))
    
    def forward(self, x_dict: Dict[str, torch.Tensor], 
                edge_index_dict: Dict[tuple, torch.Tensor]) -> Dict[str, torch.Tensor]:
        """
        Forward pass through heterogeneous graph.
        
        Args:
            x_dict: Node features for each node type
            edge_index_dict: Edge indices for each edge type
        
        Returns:
            Node embeddings for each node type
        """
        # Project inputs to hidden dimension
        for node_type, x in x_dict.items():
            if node_type in self.input_projections:
                x_dict[node_type] = self.input_projections[node_type](x)
        
        # Message passing layers
        for i in range(self.num_layers):
            x_dict = self.convs[i](x_dict, edge_index_dict)
            
            # Apply normalization and activation (except last layer)
            if i < self.num_layers - 1:
                for node_type, x in x_dict.items():
                    x_dict[node_type] = self.norms[f'layer_{i}'][node_type](x)
                    x_dict[node_type] = F.relu(x_dict[node_type])
                    x_dict[node_type] = F.dropout(
                        x_dict[node_type],
                        p=self.dropout,
                        training=self.training
                    )
        
        # Project to output dimension
        out_dict = {}
        for node_type, x in x_dict.items():
            out_dict[node_type] = self.output_projections[node_type](x)
        
        return out_dict
    
    def get_embeddings(
        self,
        data: HeteroData,
        node_type: str = 'product'
    ) -> torch.Tensor:
        """
        Get embeddings for specific node type.
        
        Args:
            data: Heterogeneous graph data
            node_type: Type of nodes to get embeddings for
        
        Returns:
            Node embeddings
        """
        with torch.no_grad():
            self.eval()
            x_dict = {nt: data[nt].x for nt in data.node_types}
            edge_index_dict = {
                et: data[et].edge_index for et in data.edge_types
            }
            out_dict = self.forward(x_dict, edge_index_dict)
            return out_dict[node_type]


class ProductPackagingScorer(nn.Module):
    """
    Score product-packaging compatibility using GNN embeddings.
    Predicts cost, CO2, and damage probability.
    """
    
    def __init__(
        self,
        embedding_dim: int = 512,
        hidden_dim: int = 256,
        num_objectives: int = 3  # cost, co2, damage
    ):
        """
        Initialize scoring model.
        
        Args:
            embedding_dim: Dimension of input embeddings
            hidden_dim: Hidden layer dimension
            num_objectives: Number of objectives to predict
        """
        super().__init__()
        
        self.mlp = nn.Sequential(
            nn.Linear(embedding_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim // 2, num_objectives)
        )
        
        logger.info("ProductPackagingScorer initialized",
                   embedding_dim=embedding_dim,
                   num_objectives=num_objectives)
    
    def forward(
        self,
        product_emb: torch.Tensor,
        packaging_emb: torch.Tensor
    ) -> torch.Tensor:
        """
        Predict objectives for product-packaging pair.
        
        Args:
            product_emb: Product embeddings [batch, embedding_dim]
            packaging_emb: Packaging embeddings [batch, embedding_dim]
        
        Returns:
            Predictions [batch, num_objectives] (cost, co2, damage_prob)
        """
        # Concatenate embeddings
        combined = torch.cat([product_emb, packaging_emb], dim=-1)
        
        # Predict objectives
        predictions = self.mlp(combined)
        
        # Apply appropriate activations
        # cost: exponential (positive)
        # co2: exponential (positive)
        # damage: sigmoid (probability)
        predictions[:, 0] = torch.exp(predictions[:, 0])  # cost
        predictions[:, 1] = torch.exp(predictions[:, 1])  # co2
        predictions[:, 2] = torch.sigmoid(predictions[:, 2])  # damage_prob
        
        return predictions
