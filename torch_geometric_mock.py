"""
PyTorch Geometric Mock Module
Provides CPU-compatible fallback for systems without CUDA-capable torch_geometric
"""

import sys
import types
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np


# Create base classes and functions for mocking

class Data:
    """Mock torch_geometric.data.Data"""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class HeteroData(dict):
    """Mock torch_geometric.data.HeteroData"""
    pass


class NodeStore:
    """Mock node store"""
    def __init__(self):
        pass


# Create transforms module

class ToUndirected:
    """Convert graph to undirected"""
    def __call__(self, data):
        return data


class Compose:
    """Compose multiple transforms"""
    def __init__(self, transforms):
        self.transforms = transforms
    
    def __call__(self, data):
        for t in self.transforms:
            data = t(data)
        return data


class NormalizeFeatures:
    """Normalize node features"""
    def __call__(self, data):
        if hasattr(data, 'x') and data.x is not None:
            data.x = F.normalize(data.x, p=2, dim=1)
        return data


class RandomNodeDrop:
    """Randomly drop nodes"""
    def __init__(self, p=0.5):
        self.p = p
    
    def __call__(self, data):
        return data


# Create nn module with graph convolutions

class MessagePassing(nn.Module):
    """Base message passing layer"""
    def __init__(self, aggr='add'):
        super().__init__()
        self.aggr = aggr
    
    def forward(self, x, edge_index, edge_attr=None):
        return self.propagate(edge_index, x=x, edge_attr=edge_attr)
    
    def propagate(self, edge_index, **kwargs):
        return kwargs.get('x', torch.zeros(1))


class GCNConv(MessagePassing):
    """Graph Convolutional Network layer"""
    def __init__(self, in_channels, out_channels, improved=False, cached=False, add_self_loops=True, bias=True):
        super().__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.improved = improved
        self.cached = cached
        self.add_self_loops = add_self_loops
        
        self.lin = nn.Linear(in_channels, out_channels, bias=bias)
    
    def forward(self, x, edge_index, edge_weight=None):
        if not isinstance(x, torch.Tensor):
            x = torch.tensor(x, dtype=torch.float32)
        
        return self.lin(x)


class GATConv(MessagePassing):
    """Graph Attention Network layer"""
    def __init__(self, in_channels, out_channels, heads=1, concat=True, dropout=0.0, add_self_loops=True, bias=True):
        super().__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.heads = heads
        self.concat = concat
        
        self.lin = nn.Linear(in_channels, out_channels * heads, bias=bias)
    
    def forward(self, x, edge_index, edge_attr=None, return_attention_weights=False):
        if not isinstance(x, torch.Tensor):
            x = torch.tensor(x, dtype=torch.float32)
        
        out = self.lin(x)
        
        if return_attention_weights:
            # Return dummy attention weights
            num_nodes = x.shape[0]
            num_edges = edge_index.shape[1] if isinstance(edge_index, torch.Tensor) else len(edge_index[0])
            attention = torch.ones(num_edges, self.heads) / self.heads
            return out, (edge_index, attention)
        
        return out


class HeteroConv(nn.Module):
    """Heterogeneous graph convolution"""
    def __init__(self, convs, aggr='sum'):
        super().__init__()
        self.convs = nn.ModuleDict(convs) if isinstance(convs, dict) else nn.ModuleList(convs)
        self.aggr = aggr
    
    def forward(self, x_dict, edge_index_dict, **kwargs):
        return x_dict


class SAGEConv(MessagePassing):
    """GraphSAGE layer"""
    def __init__(self, in_channels, out_channels, aggr='mean'):
        super().__init__(aggr=aggr)
        self.in_channels = in_channels
        self.out_channels = out_channels
        
        self.lin_l = nn.Linear(in_channels, out_channels)
        self.lin_r = nn.Linear(in_channels, out_channels)
    
    def forward(self, x, edge_index, size=None):
        if not isinstance(x, torch.Tensor):
            if isinstance(x, (list, tuple)):
                x_l, x_r = x
            else:
                x_l = x_r = x
        else:
            x_l = x_r = x
        
        if isinstance(x_l, torch.Tensor):
            out_l = self.lin_l(x_l)
        else:
            out_l = torch.zeros(1, self.out_channels)
        
        if isinstance(x_r, torch.Tensor):
            out_r = self.lin_r(x_r)
        else:
            out_r = torch.zeros(1, self.out_channels)
        
        return out_l + out_r


class RGCNConv(MessagePassing):
    """Relational Graph Convolutional Network layer"""
    def __init__(self, in_channels, out_channels, num_relations=1, aggr='mean'):
        super().__init__(aggr=aggr)
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.num_relations = num_relations
        
        self.weight = nn.Parameter(torch.ones(num_relations, in_channels, out_channels))
    
    def forward(self, x, edge_index, edge_attr=None):
        if not isinstance(x, torch.Tensor):
            x = torch.tensor(x, dtype=torch.float32)
        
        # Simple linear transformation
        return torch.matmul(x, self.weight[0])


class GINConv(MessagePassing):
    """Graph Isomorphism Network layer"""
    def __init__(self, nn_module):
        super().__init__()
        self.nn = nn_module
    
    def forward(self, x, edge_index):
        if not isinstance(x, torch.Tensor):
            x = torch.tensor(x, dtype=torch.float32)
        
        if self.nn is not None:
            return self.nn(x)
        return x


class Linear(nn.Linear):
    """Graph linear layer"""
    pass


class Sequential(nn.Sequential):
    """Sequential graph module"""
    pass


# Create transforms as module
class TransformsModule:
    """Transforms namespace"""
    ToUndirected = ToUndirected
    Compose = Compose
    NormalizeFeatures = NormalizeFeatures
    RandomNodeDrop = RandomNodeDrop


# Create loader as module
class LoaderModule:
    """Loader namespace for data loading"""
    
    class DataLoader:
        """Mock DataLoader"""
        def __init__(self, data, batch_size=1, shuffle=False):
            self.data = data
            self.batch_size = batch_size
            self.shuffle = shuffle
        
        def __iter__(self):
            yield self.data
        
        def __len__(self):
            return 1
    
    class NeighborLoader:
        """Mock NeighborLoader for neighbor sampling"""
        def __init__(self, data, num_neighbors=None, batch_size=1, shuffle=False, **kwargs):
            self.data = data
            self.num_neighbors = num_neighbors
            self.batch_size = batch_size
            self.shuffle = shuffle
        
        def __iter__(self):
            yield self.data
        
        def __len__(self):
            return 1


# Create nn as module
class NNModule:
    """NN namespace"""
    MessagePassing = MessagePassing
    GCNConv = GCNConv
    GATConv = GATConv
    SAGEConv = SAGEConv
    RGCNConv = RGCNConv
    GINConv = GINConv
    HeteroConv = HeteroConv
    Linear = Linear
    Sequential = Sequential


# Create data as module
class DataModule:
    """Data namespace"""
    Data = Data
    HeteroData = HeteroData
    NodeStore = NodeStore


# Create main torch_geometric module
class TorchGeometricModule:
    """Top-level torch_geometric module mock"""
    
    def __init__(self):
        self.data = DataModule()
        self.nn = NNModule()
        self.transforms = TransformsModule()
        self.loader = LoaderModule()


def torch_geometric_mock():
    """Factory function to create torch_geometric mock"""
    return TorchGeometricModule()


# Register in sys.modules
mock = torch_geometric_mock()
sys.modules['torch_geometric'] = mock
sys.modules['torch_geometric.data'] = mock.data
sys.modules['torch_geometric.nn'] = mock.nn
sys.modules['torch_geometric.transforms'] = mock.transforms
sys.modules['torch_geometric.loader'] = mock.loader

# Export classes directly at package level as well
sys.modules['torch_geometric'].Data = Data
sys.modules['torch_geometric'].HeteroData = HeteroData
sys.modules['torch_geometric'].MessagePassing = MessagePassing
sys.modules['torch_geometric'].ToUndirected = ToUndirected
sys.modules['torch_geometric'].GCNConv = GCNConv
sys.modules['torch_geometric'].GATConv = GATConv
sys.modules['torch_geometric'].SAGEConv = SAGEConv
sys.modules['torch_geometric'].RGCNConv = RGCNConv
sys.modules['torch_geometric'].GINConv = GINConv
sys.modules['torch_geometric'].HeteroConv = HeteroConv

__all__ = [
    'Data', 'HeteroData', 'MessagePassing',
    'GCNConv', 'GATConv', 'HeteroConv',
    'ToUndirected', 'Compose', 'NormalizeFeatures'
]
