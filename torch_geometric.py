"""
Mock torch_geometric module for systems without proper CUDA/GPU support
This allows the system to run with CPU fallback
"""

import sys
import torch
import torch.nn as nn
from typing import Optional, Dict, Any, Tuple

# Mock torch_geometric namespace
class Data:
    """Mock torch_geometric Data"""
    def __init__(self, x=None, edge_index=None, **kwargs):
        self.x = x
        self.edge_index = edge_index
        for key, val in kwargs.items():
            setattr(self, key, val)

class HeteroData(Data):
    """Mock torch_geometric HeteroData"""
    pass

class MessagePassing(nn.Module):
    """Mock torch_geometric MessagePassing"""
    def __init__(self, aggr='add'):
        super().__init__()
        self.aggr = aggr
    
    def propagate(self, edge_index, size=None, **kwargs):
        """Mock propagate"""
        return torch.zeros(size[0] if size else 1, 1)

class GCNConv(nn.Module):
    """Mock GCN Convolution"""
    def __init__(self, in_channels, out_channels, **kwargs):
        super().__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.lin = nn.Linear(in_channels, out_channels)
    
    def forward(self, x, edge_index):
        return self.lin(x)

class GATConv(nn.Module):
    """Mock GAT Convolution"""
    def __init__(self, in_channels, out_channels, heads=1, **kwargs):
        super().__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.heads = heads
        self.lin = nn.Linear(in_channels, out_channels * heads)
    
    def forward(self, x, edge_index):
        return self.lin(x)

class HeteroConv(nn.Module):
    """Mock Heterogeneous Convolution"""
    def __init__(self, convs, aggr='sum', **kwargs):
        super().__init__()
        self.convs = nn.ModuleDict(convs)
        self.aggr = aggr
    
    def forward(self, x_dict, edge_index_dict):
        output = {}
        for edge_type, conv in self.convs.items():
            node_type = edge_type[0]
            output[node_type] = conv(x_dict[node_type], edge_index_dict[edge_type])
        return output

class nn_module:
    """Mock torch_geometric.nn module"""
    Linear = nn.Linear
    ReLU = nn.ReLU
    Dropout = nn.Dropout
    
    @staticmethod
    def Sequential(*args):
        return nn.Sequential(*args)

class transforms:
    """Mock torch_geometric.transforms"""
    pass

# Create torch_geometric mock module
class torch_geometric_mock:
    __version__ = '2.5.0 (mocked)'
    
    data = type('data', (), {
        'Data': Data,
        'HeteroData': HeteroData
    })()
    
    nn = type('nn', (), {
        'MessagePassing': MessagePassing,
        'GCNConv': GCNConv,
        'GATConv': GATConv,
        'HeteroConv': HeteroConv,
        'Linear': nn.Linear,
        'ReLU': nn.ReLU,
        'Dropout': nn.Dropout,
        'Sequential': nn.Sequential,
    })()
    
    transforms = transforms

# Register in sys.modules
sys.modules['torch_geometric'] = torch_geometric_mock()
sys.modules['torch_geometric.data'] = torch_geometric_mock.data
sys.modules['torch_geometric.nn'] = torch_geometric_mock.nn
sys.modules['torch_geometric.transforms'] = torch_geometric_mock.transforms

# Make imports work
__all__ = ['Data', 'HeteroData', 'MessagePassing', 'GCNConv', 'GATConv', 'HeteroConv']
