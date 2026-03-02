"""
Lifecycle Carbon Footprint Calculator
Calculates CO2 emissions across material lifecycle stages
"""

from typing import Dict, Optional
from dataclasses import dataclass
import numpy as np
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class MaterialProperties:
    """Material properties for carbon calculations."""
    material_id: str
    material_type: str
    weight_kg: float
    extraction_co2_per_kg: float  # kg CO2 per kg material
    manufacturing_co2_per_kg: float
    recyclability: float  # 0-1
    biodegradability: float  # 0-1
    renewable_source: bool


@dataclass
class TransportProperties:
    """Transport properties for carbon calculations."""
    distance_km: float
    transport_mode: str  # truck, rail, ship, air
    weight_kg: float


@dataclass
class UsageProperties:
    """Usage/storage properties."""
    storage_days: int
    warehouse_energy_kwh_per_day: float = 0.1


class LifecycleCalculator:
    """
    Calculate carbon footprint across material lifecycle.
    
    Stages:
        1. Material extraction
        2. Manufacturing
        3. Transportation
        4. Usage (storage)
        5. End-of-life
    """
    
    # CO2 emission factors (kg CO2 per ton-km)
    TRANSPORT_EMISSION_FACTORS = {
        'truck': 0.12,
        'rail': 0.03,
        'ship': 0.01,
        'air': 1.2,
        'default': 0.15
    }
    
    # Energy grid CO2 factor (kg CO2 per kWh)
    GRID_CO2_FACTOR = 0.5  # Average global
    
    # End-of-life factors
    LANDFILL_CO2_FACTOR = 0.8  # kg CO2 per kg waste
    INCINERATION_CO2_FACTOR = 0.3  # kg CO2 per kg waste
    RECYCLING_CREDIT_FACTOR = -0.4  # Negative = carbon credit
    
    def __init__(self):
        """Initialize lifecycle calculator."""
        logger.info("LifecycleCalculator initialized")
    
    def calculate_extraction_emissions(
        self,
        material: MaterialProperties
    ) -> float:
        """
        Calculate emissions from material extraction.
        
        Args:
            material: Material properties
        
        Returns:
            CO2 emissions in kg
        """
        emissions = material.weight_kg * material.extraction_co2_per_kg
        
        # Credit for renewable sources
        if material.renewable_source:
            emissions *= 0.7  # 30% reduction
        
        return emissions
    
    def calculate_manufacturing_emissions(
        self,
        material: MaterialProperties
    ) -> float:
        """
        Calculate emissions from manufacturing.
        
        Args:
            material: Material properties
        
        Returns:
            CO2 emissions in kg
        """
        emissions = material.weight_kg * material.manufacturing_co2_per_kg
        
        return emissions
    
    def calculate_transport_emissions(
        self,
        transport: TransportProperties
    ) -> float:
        """
        Calculate emissions from transportation.
        
        Args:
            transport: Transport properties
        
        Returns:
            CO2 emissions in kg
        """
        # Get emission factor for transport mode
        factor = self.TRANSPORT_EMISSION_FACTORS.get(
            transport.transport_mode.lower(),
            self.TRANSPORT_EMISSION_FACTORS['default']
        )
        
        # Convert weight to tons and calculate
        weight_tons = transport.weight_kg / 1000.0
        emissions = transport.distance_km * weight_tons * factor
        
        return emissions
    
    def calculate_usage_emissions(
        self,
        usage: UsageProperties
    ) -> float:
        """
        Calculate emissions from warehouse storage.
        
        Args:
            usage: Usage properties
        
        Returns:
            CO2 emissions in kg
        """
        # Energy consumption
        energy_kwh = usage.storage_days * usage.warehouse_energy_kwh_per_day
        emissions = energy_kwh * self.GRID_CO2_FACTOR
        
        return emissions
    
    def calculate_end_of_life_emissions(
        self,
        material: MaterialProperties,
        recycling_rate: Optional[float] = None
    ) -> float:
        """
        Calculate end-of-life emissions (or credits).
        
        Args:
            material: Material properties
            recycling_rate: Actual recycling rate (0-1)
        
        Returns:
            CO2 emissions in kg (negative = credit)
        """
        if recycling_rate is None:
            recycling_rate = material.recyclability
        
        weight = material.weight_kg
        
        # Recycled portion gets credit
        recycled_weight = weight * recycling_rate
        recycling_credit = recycled_weight * self.RECYCLING_CREDIT_FACTOR
        
        # Biodegradable portion
        biodegradable_weight = weight * (1 - recycling_rate) * material.biodegradability
        biodegradable_emissions = biodegradable_weight * 0.1  # Low emissions for composting
        
        # Remaining goes to landfill or incineration
        remaining_weight = weight * (1 - recycling_rate) * (1 - material.biodegradability)
        
        # Assume 70% landfill, 30% incineration
        landfill_emissions = remaining_weight * 0.7 * self.LANDFILL_CO2_FACTOR
        incineration_emissions = remaining_weight * 0.3 * self.INCINERATION_CO2_FACTOR
        
        total_emissions = (
            recycling_credit +
            biodegradable_emissions +
            landfill_emissions +
            incineration_emissions
        )
        
        return total_emissions
    
    def calculate_total_lifecycle_emissions(
        self,
        material: MaterialProperties,
        transport: Optional[TransportProperties] = None,
        usage: Optional[UsageProperties] = None,
        recycling_rate: Optional[float] = None
    ) -> Dict[str, float]:
        """
        Calculate total lifecycle CO2 emissions.
        
        Args:
            material: Material properties
            transport: Optional transport properties
            usage: Optional usage properties
            recycling_rate: Optional actual recycling rate
        
        Returns:
            Dictionary with emissions by stage and total
        """
        # Calculate each stage
        extraction = self.calculate_extraction_emissions(material)
        manufacturing = self.calculate_manufacturing_emissions(material)
        
        if transport:
            transportation = self.calculate_transport_emissions(transport)
        else:
            transportation = 0.0
        
        if usage:
            usage_emissions = self.calculate_usage_emissions(usage)
        else:
            usage_emissions = 0.0
        
        end_of_life = self.calculate_end_of_life_emissions(material, recycling_rate)
        
        total = extraction + manufacturing + transportation + usage_emissions + end_of_life
        
        results = {
            'extraction': float(extraction),
            'manufacturing': float(manufacturing),
            'transportation': float(transportation),
            'usage': float(usage_emissions),
            'end_of_life': float(end_of_life),
            'total': float(total)
        }
        
        logger.info("Lifecycle emissions calculated",
                   material=material.material_type,
                   total_co2=total)
        
        return results
    
    def compare_materials(
        self,
        materials: list[tuple[MaterialProperties, Optional[TransportProperties], Optional[UsageProperties]]],
        material_names: list[str]
    ) -> Dict:
        """
        Compare lifecycle emissions of multiple materials.
        
        Args:
            materials: List of (material, transport, usage) tuples
            material_names: Names for each material
        
        Returns:
            Comparison results
        """
        results = {}
        
        for name, (material, transport, usage) in zip(material_names, materials):
            lifecycle = self.calculate_total_lifecycle_emissions(
                material, transport, usage
            )
            results[name] = lifecycle
        
        # Find best and worst
        totals = {name: data['total'] for name, data in results.items()}
        best_material = min(totals, key=totals.get)
        worst_material = max(totals, key=totals.get)
        
        comparison = {
            'materials': results,
            'best_material': best_material,
            'worst_material': worst_material,
            'best_emissions': totals[best_material],
            'worst_emissions': totals[worst_material],
            'savings_potential': totals[worst_material] - totals[best_material]
        }
        
        logger.info("Material comparison complete",
                   best=best_material,
                   savings_kg_co2=comparison['savings_potential'])
        
        return comparison
