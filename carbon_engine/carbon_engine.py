"""
Carbon Accounting Engine
Unified engine for lifecycle analysis, grading, and offset calculation
"""

from typing import Dict, Optional, List
import structlog

from .lifecycle_calculator import LifecycleCalculator, MaterialProperties, TransportProperties, UsageProperties
from .sustainability_grader import SustainabilityGrader, SustainabilityFactors
from .carbon_offset import CarbonOffsetCalculator

logger = structlog.get_logger(__name__)


class CarbonAccountingEngine:
    """
    Complete carbon accounting system.
    Integrates lifecycle analysis, sustainability grading, and offset calculation.
    """
    
    def __init__(self):
        """Initialize carbon accounting engine."""
        self.lifecycle_calc = LifecycleCalculator()
        self.sustainability_grader = SustainabilityGrader()
        self.offset_calc = CarbonOffsetCalculator()
        
        logger.info("CarbonAccountingEngine initialized")
    
    def analyze_packaging(
        self,
        material: MaterialProperties,
        transport: Optional[TransportProperties] = None,
        usage: Optional[UsageProperties] = None,
        include_offset: bool = True,
        include_recommendations: bool = True
    ) -> Dict:
        """
        Complete carbon analysis for packaging.
        
        Args:
            material: Material properties
            transport: Optional transport properties
            usage: Optional usage properties
            include_offset: Include offset calculations
            include_recommendations: Include improvement recommendations
        
        Returns:
            Complete carbon analysis report
        """
        logger.info("Analyzing packaging carbon footprint...",
                   material=material.material_type)
        
        # 1. Lifecycle emissions
        lifecycle_emissions = self.lifecycle_calc.calculate_total_lifecycle_emissions(
            material, transport, usage
        )
        
        # 2. Sustainability grading
        factors = SustainabilityFactors(
            co2_emissions_kg=lifecycle_emissions['total'],
            recyclability=material.recyclability,
            biodegradability=material.biodegradability,
            renewable_source=material.renewable_source,
            toxicity_score=0.1,  # Placeholder
            water_usage_liters=material.weight_kg * 10,  # Estimate
            energy_usage_kwh=material.weight_kg * 2,  # Estimate
            packaging_weight_kg=material.weight_kg,
            reusability=0.3  # Default
        )
        
        sustainability_report = self.sustainability_grader.generate_report(
            factors,
            include_recommendations=include_recommendations
        )
        
        # 3. Carbon offset calculation
        offset_plan = None
        if include_offset:
            offset_plan = self.offset_calc.generate_carbon_neutral_plan(
                lifecycle_emissions['total']
            )
        
        # Compile complete analysis
        analysis = {
            'material_info': {
                'material_type': material.material_type,
                'weight_kg': material.weight_kg,
                'renewable_source': material.renewable_source
            },
            'lifecycle_emissions': lifecycle_emissions,
            'sustainability_report': sustainability_report,
            'offset_plan': offset_plan,
            'summary': {
                'total_co2_kg': lifecycle_emissions['total'],
                'sustainability_grade': sustainability_report['overall_grade'],
                'sustainability_score': sustainability_report['numerical_score'],
                'offset_cost_usd': offset_plan['recommended_project']['total_cost'] if offset_plan and offset_plan['feasible'] else None
            }
        }
        
        logger.info("Carbon analysis complete",
                   total_co2=lifecycle_emissions['total'],
                   grade=sustainability_report['overall_grade'])
        
        return analysis
    
    def compare_packaging_options(
        self,
        packaging_options: List[tuple[MaterialProperties, Optional[TransportProperties], Optional[UsageProperties]]],
        option_names: List[str]
    ) -> Dict:
        """
        Compare carbon performance of multiple packaging options.
        
        Args:
            packaging_options: List of (material, transport, usage) tuples
            option_names: Names for each option
        
        Returns:
            Comparison report with rankings
        """
        logger.info("Comparing packaging options...",
                   num_options=len(packaging_options))
        
        # Analyze each option
        analyses = {}
        factors_dict = {}
        
        for name, (material, transport, usage) in zip(option_names, packaging_options):
            analysis = self.analyze_packaging(
                material, transport, usage,
                include_offset=False,
                include_recommendations=False
            )
            
            analyses[name] = analysis
            
            # Extract factors for comparison
            factors_dict[name] = SustainabilityFactors(
                co2_emissions_kg=analysis['lifecycle_emissions']['total'],
                recyclability=material.recyclability,
                biodegradability=material.biodegradability,
                renewable_source=material.renewable_source,
                toxicity_score=0.1,
                water_usage_liters=material.weight_kg * 10,
                energy_usage_kwh=material.weight_kg * 2,
                packaging_weight_kg=material.weight_kg,
                reusability=0.3
            )
        
        # Lifecycle comparison
        lifecycle_comparison = self.lifecycle_calc.compare_materials(
            packaging_options,
            option_names
        )
        
        # Sustainability comparison
        sustainability_comparison = self.sustainability_grader.compare_packaging_options(
            factors_dict
        )
        
        # Compile comparison
        comparison = {
            'options': analyses,
            'lifecycle_comparison': lifecycle_comparison,
            'sustainability_ranking': sustainability_comparison,
            'best_overall': sustainability_comparison['best'],
            'worst_overall': sustainability_comparison['worst'],
            'recommendation': self._generate_comparison_recommendation(
                lifecycle_comparison,
                sustainability_comparison
            )
        }
        
        logger.info("Comparison complete",
                   best=comparison['best_overall'])
        
        return comparison
    
    def calculate_savings_potential(
        self,
        current_material: MaterialProperties,
        alternative_material: MaterialProperties,
        annual_shipments: int,
        transport: Optional[TransportProperties] = None
    ) -> Dict:
        """
        Calculate potential carbon savings from switching materials.
        
        Args:
            current_material: Current packaging material
            alternative_material: Alternative material
            annual_shipments: Annual shipment volume
            transport: Transport properties (same for both)
        
        Returns:
            Savings analysis
        """
        logger.info("Calculating savings potential...",
                   annual_shipments=annual_shipments)
        
        # Calculate emissions for both
        current_emissions = self.lifecycle_calc.calculate_total_lifecycle_emissions(
            current_material, transport
        )
        
        alternative_emissions = self.lifecycle_calc.calculate_total_lifecycle_emissions(
            alternative_material, transport
        )
        
        # Calculate savings
        savings = self.offset_calc.calculate_cumulative_savings(
            baseline_co2_kg=current_emissions['total'],
            optimized_co2_kg=alternative_emissions['total'],
            num_shipments=annual_shipments
        )
        
        # Calculate ROI
        # (Saved offset costs - material cost difference) / material cost difference
        avg_offset_cost_per_ton = 10.0  # USD
        offset_savings_usd = savings['total_savings_tons'] * avg_offset_cost_per_ton
        
        analysis = {
            'current_packaging': {
                'material': current_material.material_type,
                'co2_per_unit_kg': current_emissions['total'],
                'annual_co2_tons': current_emissions['total'] * annual_shipments / 1000
            },
            'alternative_packaging': {
                'material': alternative_material.material_type,
                'co2_per_unit_kg': alternative_emissions['total'],
                'annual_co2_tons': alternative_emissions['total'] * annual_shipments / 1000
            },
            'savings': savings,
            'financial_impact': {
                'offset_cost_savings_usd': offset_savings_usd,
                'payback_period_months': 'Immediate if material costs comparable'
            },
            'recommendation': self._generate_savings_recommendation(savings)
        }
        
        logger.info("Savings analysis complete",
                   total_reduction_pct=savings['reduction_percentage'])
        
        return analysis
    
    def _generate_comparison_recommendation(
        self,
        lifecycle_comparison: Dict,
        sustainability_comparison: Dict
    ) -> str:
        """Generate recommendation from comparison."""
        best_material = lifecycle_comparison['best_material']
        savings = lifecycle_comparison['savings_potential']
        
        if savings > 10:  # kg CO2
            return f"Strongly recommend switching to {best_material}. " \
                   f"Potential savings: {savings:.1f} kg CO2 per unit " \
                   f"({savings/lifecycle_comparison['worst_emissions']*100:.1f}% reduction)."
        elif savings > 2:
            return f"Consider switching to {best_material} for moderate carbon reduction " \
                   f"({savings:.1f} kg CO2 per unit)."
        else:
            return f"Carbon footprints are similar across options. " \
                   f"Consider other factors like cost and performance."
    
    def _generate_savings_recommendation(self, savings: Dict) -> str:
        """Generate recommendation from savings analysis."""
        reduction_pct = savings['reduction_percentage']
        
        if reduction_pct > 30:
            return f"Excellent opportunity! {reduction_pct:.1f}% carbon reduction " \
                   f"equivalent to {savings['equivalent_trees_year']} trees annually."
        elif reduction_pct > 15:
            return f"Good savings potential: {reduction_pct:.1f}% reduction. " \
                   f"Worth implementing if costs are comparable."
        elif reduction_pct > 5:
            return f"Moderate improvement: {reduction_pct:.1f}% reduction. " \
                   f"Evaluate cost-benefit carefully."
        else:
            return f"Minimal carbon difference ({reduction_pct:.1f}%). " \
                   f"Focus on other sustainability factors."
    
    def generate_sustainability_scorecard(
        self,
        material: MaterialProperties,
        transport: Optional[TransportProperties] = None
    ) -> Dict:
        """
        Generate compact sustainability scorecard for dashboard.
        
        Args:
            material: Material properties
            transport: Optional transport properties
        
        Returns:
            Scorecard data
        """
        analysis = self.analyze_packaging(
            material, transport,
            include_offset=False,
            include_recommendations=False
        )
        
        scorecard = {
            'grade': analysis['sustainability_report']['overall_grade'],
            'score': analysis['sustainability_report']['numerical_score'],
            'co2_total_kg': analysis['lifecycle_emissions']['total'],
            'co2_breakdown': {
                'extraction': analysis['lifecycle_emissions']['extraction'],
                'manufacturing': analysis['lifecycle_emissions']['manufacturing'],
                'transport': analysis['lifecycle_emissions']['transportation'],
                'end_of_life': analysis['lifecycle_emissions']['end_of_life']
            },
            'recyclability_pct': material.recyclability * 100,
            'biodegradability_pct': material.biodegradability * 100,
            'renewable_source': material.renewable_source
        }
        
        return scorecard
