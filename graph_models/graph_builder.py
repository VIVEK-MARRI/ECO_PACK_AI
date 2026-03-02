"""
Heterogeneous Graph Builder for Packaging Intelligence
Constructs graph with products, packaging, materials, routes, climate zones
"""

import logging
from typing import Dict, List, Tuple, Optional
import numpy as np
import pandas as pd
import torch
from torch_geometric.data import HeteroData
from torch_geometric.transforms import ToUndirected
import structlog

logger = structlog.get_logger(__name__)


class GraphBuilder:
    """
    Build heterogeneous graph for packaging recommendations.
    
    Nodes:
        - products: Product features (dimensions, weight, fragility)
        - packaging: Packaging types (material, strength, dimensions)
        - materials: Material properties (composition, sustainability)
        - damage_events: Historical damage data
        - routes: Shipping routes (distance, mode, duration)
        - climate_zones: Climate characteristics
    
    Edges:
        - product → packaging (usage frequency)
        - packaging → damage (damage probability)
        - product → climate_risk (risk score)
        - packaging → co2 (emission factor)
        - material → sustainability (sustainability score)
        - product → route (shipment volume)
        - route → climate_zone (exposure)
    """
    
    def __init__(
        self,
        product_features: pd.DataFrame,
        packaging_data: pd.DataFrame,
        material_data: pd.DataFrame,
        damage_history: pd.DataFrame,
        route_data: Optional[pd.DataFrame] = None,
        climate_data: Optional[pd.DataFrame] = None
    ):
        """
        Initialize graph builder with data sources.
        
        Args:
            product_features: Product characteristics
            packaging_data: Packaging specifications
            material_data: Material properties
            damage_history: Historical damage events
            route_data: Shipping route information
            climate_data: Climate zone data
        """
        self.product_features = product_features
        self.packaging_data = packaging_data
        self.material_data = material_data
        self.damage_history = damage_history
        self.route_data = route_data
        self.climate_data = climate_data
        
        # Node mappings
        self.product_id_to_idx: Dict[str, int] = {}
        self.packaging_id_to_idx: Dict[str, int] = {}
        self.material_id_to_idx: Dict[str, int] = {}
        self.route_id_to_idx: Dict[str, int] = {}
        self.climate_id_to_idx: Dict[str, int] = {}
        
        logger.info("GraphBuilder initialized", 
                   num_products=len(product_features),
                   num_packaging=len(packaging_data))
    
    def build(self) -> HeteroData:
        """
        Build complete heterogeneous graph.
        
        Returns:
            HeteroData: PyTorch Geometric heterogeneous graph
        """
        logger.info("Building heterogeneous graph...")
        
        data = HeteroData()
        
        # Add nodes
        data = self._add_product_nodes(data)
        data = self._add_packaging_nodes(data)
        data = self._add_material_nodes(data)
        data = self._add_damage_nodes(data)
        
        if self.route_data is not None:
            data = self._add_route_nodes(data)
        
        if self.climate_data is not None:
            data = self._add_climate_nodes(data)
        
        # Add edges
        data = self._add_product_packaging_edges(data)
        data = self._add_packaging_damage_edges(data)
        data = self._add_packaging_co2_edges(data)
        data = self._add_material_sustainability_edges(data)
        
        if self.route_data is not None:
            data = self._add_product_route_edges(data)
        
        if self.climate_data is not None:
            data = self._add_product_climate_edges(data)
            if self.route_data is not None:
                data = self._add_route_climate_edges(data)
        
        # Convert to undirected for message passing
        transform = ToUndirected()
        data = transform(data)
        
        logger.info("Graph built successfully",
                   num_node_types=len(data.node_types),
                   num_edge_types=len(data.edge_types),
                   total_nodes=sum([data[node_type].num_nodes for node_type in data.node_types]))
        
        return data
    
    def _add_product_nodes(self, data: HeteroData) -> HeteroData:
        """Add product nodes with features."""
        features = []
        
        for idx, row in self.product_features.iterrows():
            product_id = row.get('product_id', f'prod_{idx}')
            self.product_id_to_idx[product_id] = len(self.product_id_to_idx)
            
            # Extract features
            feat = [
                row.get('weight', 0.0),
                row.get('length', 0.0),
                row.get('width', 0.0),
                row.get('height', 0.0),
                row.get('fragility', 0.5),
                row.get('value', 0.0),
                row.get('temperature_sensitive', 0.0),
                row.get('moisture_sensitive', 0.0),
                row.get('stackable', 1.0),
                row.get('hazardous', 0.0),
                row.get('perishable', 0.0),
                row.get('recyclability', 0.5)
            ]
            features.append(feat)
        
        data['product'].x = torch.tensor(features, dtype=torch.float)
        data['product'].num_nodes = len(features)
        
        logger.info("Added product nodes", count=len(features))
        return data
    
    def _add_packaging_nodes(self, data: HeteroData) -> HeteroData:
        """Add packaging nodes with features."""
        features = []
        
        for idx, row in self.packaging_data.iterrows():
            packaging_id = row.get('packaging_id', f'pack_{idx}')
            self.packaging_id_to_idx[packaging_id] = len(self.packaging_id_to_idx)
            
            # Extract features
            feat = [
                row.get('strength', 0.0),
                row.get('weight_capacity', 0.0),
                row.get('volume', 0.0),
                row.get('cost_per_unit', 0.0),
                row.get('biodegradability_score', 0.0),
                row.get('recyclability_percentage', 0.0),
                row.get('thickness', 0.0),
                row.get('water_resistance', 0.0),
                row.get('cushioning', 0.0),
                row.get('reusability', 0.0)
            ]
            features.append(feat)
        
        data['packaging'].x = torch.tensor(features, dtype=torch.float)
        data['packaging'].num_nodes = len(features)
        
        logger.info("Added packaging nodes", count=len(features))
        return data
    
    def _add_material_nodes(self, data: HeteroData) -> HeteroData:
        """Add material nodes with features."""
        features = []
        
        for idx, row in self.material_data.iterrows():
            material_id = row.get('material_id', f'mat_{idx}')
            self.material_id_to_idx[material_id] = len(self.material_id_to_idx)
            
            # Extract features
            feat = [
                row.get('carbon_footprint', 0.0),
                row.get('recyclability', 0.0),
                row.get('biodegradability', 0.0),
                row.get('durability', 0.0),
                row.get('cost', 0.0),
                row.get('renewable_source', 0.0),
                row.get('toxicity', 0.0)
            ]
            features.append(feat)
        
        data['material'].x = torch.tensor(features, dtype=torch.float)
        data['material'].num_nodes = len(features)
        
        logger.info("Added material nodes", count=len(features))
        return data
    
    def _add_damage_nodes(self, data: HeteroData) -> HeteroData:
        """Add damage event nodes."""
        features = []
        
        # Aggregate damage events by product-packaging pair
        for idx, row in self.damage_history.iterrows():
            feat = [
                row.get('damage_severity', 0.0),
                row.get('frequency', 0.0),
                row.get('cost_impact', 0.0),
                row.get('environmental_conditions', 0.0)
            ]
            features.append(feat)
        
        if len(features) == 0:
            # Add dummy node if no damage history
            features.append([0.0, 0.0, 0.0, 0.0])
        
        data['damage_event'].x = torch.tensor(features, dtype=torch.float)
        data['damage_event'].num_nodes = len(features)
        
        logger.info("Added damage nodes", count=len(features))
        return data
    
    def _add_route_nodes(self, data: HeteroData) -> HeteroData:
        """Add shipping route nodes."""
        if self.route_data is None:
            return data
        
        features = []
        
        for idx, row in self.route_data.iterrows():
            route_id = row.get('route_id', f'route_{idx}')
            self.route_id_to_idx[route_id] = len(self.route_id_to_idx)
            
            feat = [
                row.get('distance_km', 0.0),
                row.get('duration_hours', 0.0),
                row.get('transport_mode_truck', 0.0),
                row.get('transport_mode_rail', 0.0),
                row.get('transport_mode_ship', 0.0),
                row.get('transport_mode_air', 0.0),
                row.get('route_risk_score', 0.0)
            ]
            features.append(feat)
        
        data['route'].x = torch.tensor(features, dtype=torch.float)
        data['route'].num_nodes = len(features)
        
        logger.info("Added route nodes", count=len(features))
        return data
    
    def _add_climate_nodes(self, data: HeteroData) -> HeteroData:
        """Add climate zone nodes."""
        if self.climate_data is None:
            return data
        
        features = []
        
        for idx, row in self.climate_data.iterrows():
            climate_id = row.get('climate_id', f'climate_{idx}')
            self.climate_id_to_idx[climate_id] = len(self.climate_id_to_idx)
            
            feat = [
                row.get('avg_temperature', 0.0),
                row.get('avg_humidity', 0.0),
                row.get('precipitation', 0.0),
                row.get('extreme_weather_freq', 0.0)
            ]
            features.append(feat)
        
        data['climate_zone'].x = torch.tensor(features, dtype=torch.float)
        data['climate_zone'].num_nodes = len(features)
        
        logger.info("Added climate nodes", count=len(features))
        return data
    
    def _add_product_packaging_edges(self, data: HeteroData) -> HeteroData:
        """Add edges between products and packaging with usage frequency."""
        edge_index = []
        edge_attr = []
        
        # Create edges based on compatibility and historical usage
        for product_id, prod_idx in self.product_id_to_idx.items():
            for packaging_id, pack_idx in self.packaging_id_to_idx.items():
                # Add edge with usage frequency weight
                # In real scenario, this would come from historical data
                usage_freq = np.random.random()  # Placeholder
                
                edge_index.append([prod_idx, pack_idx])
                edge_attr.append([usage_freq])
        
        if len(edge_index) > 0:
            data['product', 'uses', 'packaging'].edge_index = torch.tensor(
                edge_index, dtype=torch.long
            ).t().contiguous()
            data['product', 'uses', 'packaging'].edge_attr = torch.tensor(
                edge_attr, dtype=torch.float
            )
        
        logger.info("Added product-packaging edges", count=len(edge_index))
        return data
    
    def _add_packaging_damage_edges(self, data: HeteroData) -> HeteroData:
        """Add edges between packaging and damage events."""
        edge_index = []
        edge_attr = []
        
        # Connect packaging to damage events based on historical data
        for idx, row in self.damage_history.iterrows():
            packaging_id = row.get('packaging_id')
            if packaging_id in self.packaging_id_to_idx:
                pack_idx = self.packaging_id_to_idx[packaging_id]
                damage_idx = min(idx, data['damage_event'].num_nodes - 1)
                
                damage_prob = row.get('damage_probability', 0.0)
                
                edge_index.append([pack_idx, damage_idx])
                edge_attr.append([damage_prob])
        
        if len(edge_index) > 0:
            data['packaging', 'leads_to', 'damage_event'].edge_index = torch.tensor(
                edge_index, dtype=torch.long
            ).t().contiguous()
            data['packaging', 'leads_to', 'damage_event'].edge_attr = torch.tensor(
                edge_attr, dtype=torch.float
            )
        
        logger.info("Added packaging-damage edges", count=len(edge_index))
        return data
    
    def _add_packaging_co2_edges(self, data: HeteroData) -> HeteroData:
        """Add CO2 emission edges from packaging to materials."""
        edge_index = []
        edge_attr = []
        
        for pack_idx in range(data['packaging'].num_nodes):
            for mat_idx in range(data['material'].num_nodes):
                # CO2 emission factor
                co2_factor = np.random.random() * 100  # Placeholder
                
                edge_index.append([pack_idx, mat_idx])
                edge_attr.append([co2_factor])
        
        if len(edge_index) > 0:
            data['packaging', 'emits', 'material'].edge_index = torch.tensor(
                edge_index, dtype=torch.long
            ).t().contiguous()
            data['packaging', 'emits', 'material'].edge_attr = torch.tensor(
                edge_attr, dtype=torch.float
            )
        
        logger.info("Added packaging-CO2 edges", count=len(edge_index))
        return data
    
    def _add_material_sustainability_edges(self, data: HeteroData) -> HeteroData:
        """Add sustainability score self-loops for materials."""
        edge_index = []
        edge_attr = []
        
        for mat_idx in range(data['material'].num_nodes):
            # Self-loop with sustainability score
            sustainability = self.material_data.iloc[mat_idx].get('sustainability_score', 0.5)
            
            edge_index.append([mat_idx, mat_idx])
            edge_attr.append([sustainability])
        
        if len(edge_index) > 0:
            data['material', 'sustainable', 'material'].edge_index = torch.tensor(
                edge_index, dtype=torch.long
            ).t().contiguous()
            data['material', 'sustainable', 'material'].edge_attr = torch.tensor(
                edge_attr, dtype=torch.float
            )
        
        logger.info("Added material sustainability edges", count=len(edge_index))
        return data
    
    def _add_product_route_edges(self, data: HeteroData) -> HeteroData:
        """Add edges between products and routes."""
        if self.route_data is None or 'route' not in data.node_types:
            return data
        
        edge_index = []
        edge_attr = []
        
        for prod_idx in range(data['product'].num_nodes):
            for route_idx in range(data['route'].num_nodes):
                # Shipment volume
                volume = np.random.random()  # Placeholder
                
                edge_index.append([prod_idx, route_idx])
                edge_attr.append([volume])
        
        if len(edge_index) > 0:
            data['product', 'ships_via', 'route'].edge_index = torch.tensor(
                edge_index, dtype=torch.long
            ).t().contiguous()
            data['product', 'ships_via', 'route'].edge_attr = torch.tensor(
                edge_attr, dtype=torch.float
            )
        
        logger.info("Added product-route edges", count=len(edge_index))
        return data
    
    def _add_product_climate_edges(self, data: HeteroData) -> HeteroData:
        """Add climate risk edges between products and climate zones."""
        if self.climate_data is None or 'climate_zone' not in data.node_types:
            return data
        
        edge_index = []
        edge_attr = []
        
        for prod_idx in range(data['product'].num_nodes):
            for climate_idx in range(data['climate_zone'].num_nodes):
                # Risk score based on product sensitivity
                risk = np.random.random()  # Placeholder
                
                edge_index.append([prod_idx, climate_idx])
                edge_attr.append([risk])
        
        if len(edge_index) > 0:
            data['product', 'climate_risk', 'climate_zone'].edge_index = torch.tensor(
                edge_index, dtype=torch.long
            ).t().contiguous()
            data['product', 'climate_risk', 'climate_zone'].edge_attr = torch.tensor(
                edge_attr, dtype=torch.float
            )
        
        logger.info("Added product-climate edges", count=len(edge_index))
        return data
    
    def _add_route_climate_edges(self, data: HeteroData) -> HeteroData:
        """Add edges between routes and climate zones."""
        if (self.route_data is None or self.climate_data is None or 
            'route' not in data.node_types or 'climate_zone' not in data.node_types):
            return data
        
        edge_index = []
        edge_attr = []
        
        for route_idx in range(data['route'].num_nodes):
            for climate_idx in range(data['climate_zone'].num_nodes):
                # Exposure to climate zone
                exposure = np.random.random()  # Placeholder
                
                edge_index.append([route_idx, climate_idx])
                edge_attr.append([exposure])
        
        if len(edge_index) > 0:
            data['route', 'exposed_to', 'climate_zone'].edge_index = torch.tensor(
                edge_index, dtype=torch.long
            ).t().contiguous()
            data['route', 'exposed_to', 'climate_zone'].edge_attr = torch.tensor(
                edge_attr, dtype=torch.float
            )
        
        logger.info("Added route-climate edges", count=len(edge_index))
        return data
