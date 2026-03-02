"""
Carbon Offset Calculator
Calculate carbon credits and offset recommendations
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class CarbonOffset:
    """Carbon offset project."""
    project_name: str
    project_type: str  # reforestation, renewable_energy, etc.
    cost_per_ton_co2: float
    location: str
    certification: str  # Gold Standard, VCS, etc.
    co_benefits: List[str]  # biodiversity, jobs, etc.


class CarbonOffsetCalculator:
    """
    Calculate carbon offsets required for neutrality.
    Recommend offset programs and calculate costs.
    """
    
    # Example offset projects (in reality, these would come from API/database)
    OFFSET_PROJECTS = [
        CarbonOffset(
            project_name="Amazon Reforestation",
            project_type="reforestation",
            cost_per_ton_co2=12.0,
            location="Brazil",
            certification="Gold Standard",
            co_benefits=["biodiversity", "indigenous communities", "water cycle"]
        ),
        CarbonOffset(
            project_name="Wind Farm India",
            project_type="renewable_energy",
            cost_per_ton_co2=8.0,
            location="India",
            certification="VCS",
            co_benefits=["clean energy", "jobs", "air quality"]
        ),
        CarbonOffset(
            project_name="Biogas Kenya",
            project_type="waste_to_energy",
            cost_per_ton_co2=10.0,
            location="Kenya",
            certification="Gold Standard",
            co_benefits=["clean cooking", "health", "deforestation_prevention"]
        ),
        CarbonOffset(
            project_name="Ocean Plastic Cleanup",
            project_type="ocean_conservation",
            cost_per_ton_co2=15.0,
            location="Global",
            certification="Blue Carbon",
            co_benefits=["marine_life", "circular_economy", "coastal_communities"]
        )
    ]
    
    def __init__(self):
        """Initialize carbon offset calculator."""
        logger.info("CarbonOffsetCalculator initialized")
    
    def calculate_offset_required(
        self,
        co2_emissions_kg: float,
        target_neutrality: float = 1.0
    ) -> float:
        """
        Calculate carbon offset required for neutrality.
        
        Args:
            co2_emissions_kg: CO2 emissions in kg
            target_neutrality: Target neutrality ratio (1.0 = 100% neutral)
        
        Returns:
            Required offset in tons CO2
        """
        offset_tons = (co2_emissions_kg / 1000.0) * target_neutrality
        
        logger.info("Offset calculated",
                   emissions_kg=co2_emissions_kg,
                   offset_tons=offset_tons)
        
        return offset_tons
    
    def calculate_offset_cost(
        self,
        offset_tons: float,
        project: Optional[CarbonOffset] = None
    ) -> Dict:
        """
        Calculate cost of carbon offset.
        
        Args:
            offset_tons: Tons of CO2 to offset
            project: Specific offset project (or use average if None)
        
        Returns:
            Cost calculation details
        """
        if project is None:
            # Use average cost across projects
            avg_cost = sum(p.cost_per_ton_co2 for p in self.OFFSET_PROJECTS) / len(self.OFFSET_PROJECTS)
            cost = offset_tons * avg_cost
            
            return {
                'offset_tons': offset_tons,
                'cost_per_ton': avg_cost,
                'total_cost': cost,
                'currency': 'USD',
                'project': 'Mixed portfolio'
            }
        else:
            cost = offset_tons * project.cost_per_ton_co2
            
            return {
                'offset_tons': offset_tons,
                'cost_per_ton': project.cost_per_ton_co2,
                'total_cost': cost,
                'currency': 'USD',
                'project': project.project_name,
                'project_type': project.project_type,
                'location': project.location,
                'certification': project.certification,
                'co_benefits': project.co_benefits
            }
    
    def recommend_offset_projects(
        self,
        offset_tons: float,
        budget: Optional[float] = None,
        preferred_types: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Recommend offset projects based on criteria.
        
        Args:
            offset_tons: Tons of CO2 to offset
            budget: Optional budget constraint
            preferred_types: Optional list of preferred project types
        
        Returns:
            List of recommended projects with costs
        """
        recommendations = []
        
        for project in self.OFFSET_PROJECTS:
            # Filter by type if specified
            if preferred_types and project.project_type not in preferred_types:
                continue
            
            cost_calc = self.calculate_offset_cost(offset_tons, project)
            
            # Filter by budget if specified
            if budget and cost_calc['total_cost'] > budget:
                continue
            
            recommendations.append(cost_calc)
        
        # Sort by cost (lowest first)
        recommendations.sort(key=lambda x: x['total_cost'])
        
        logger.info("Offset recommendations generated",
                   num_recommendations=len(recommendations))
        
        return recommendations
    
    def calculate_cumulative_savings(
        self,
        baseline_co2_kg: float,
        optimized_co2_kg: float,
        num_shipments: int
    ) -> Dict:
        """
        Calculate cumulative carbon savings from optimization.
        
        Args:
            baseline_co2_kg: Baseline CO2 per shipment
            optimized_co2_kg: Optimized CO2 per shipment
            num_shipments: Number of shipments
        
        Returns:
            Savings calculation
        """
        savings_per_shipment = baseline_co2_kg - optimized_co2_kg
        total_savings_kg = savings_per_shipment * num_shipments
        total_savings_tons = total_savings_kg / 1000.0
        
        # Calculate equivalent trees planted
        # 1 tree absorbs ~21 kg CO2 per year
        equivalent_trees = total_savings_kg / 21.0
        
        # Calculate monetary value of savings
        avg_offset_cost = sum(p.cost_per_ton_co2 for p in self.OFFSET_PROJECTS) / len(self.OFFSET_PROJECTS)
        monetary_value = total_savings_tons * avg_offset_cost
        
        return {
            'baseline_co2_kg': baseline_co2_kg,
            'optimized_co2_kg': optimized_co2_kg,
            'savings_per_shipment_kg': savings_per_shipment,
            'total_savings_kg': total_savings_kg,
            'total_savings_tons': total_savings_tons,
            'num_shipments': num_shipments,
            'reduction_percentage': (savings_per_shipment / baseline_co2_kg * 100) if baseline_co2_kg > 0 else 0,
            'equivalent_trees_year': int(equivalent_trees),
            'monetary_value_usd': monetary_value
        }
    
    def generate_carbon_neutral_plan(
        self,
        co2_emissions_kg: float,
        budget: Optional[float] = None
    ) -> Dict:
        """
        Generate complete carbon neutral plan.
        
        Args:
            co2_emissions_kg: CO2 emissions to neutralize
            budget: Optional budget constraint
        
        Returns:
            Complete neutralization plan
        """
        offset_required = self.calculate_offset_required(co2_emissions_kg)
        
        # Get recommended projects
        recommendations = self.recommend_offset_projects(
            offset_required,
            budget=budget
        )
        
        if not recommendations:
            logger.warning("No offset projects fit constraints", budget=budget)
            return {
                'feasible': False,
                'message': 'No offset projects available within budget'
            }
        
        # Use cheapest option by default
        selected_project = recommendations[0]
        
        # Alternative: diversified portfolio
        portfolio = self._create_diversified_portfolio(offset_required, budget)
        
        plan = {
            'feasible': True,
            'emissions_to_offset_kg': co2_emissions_kg,
            'offset_required_tons': offset_required,
            'recommended_project': selected_project,
            'alternative_projects': recommendations[1:3],  # Top 3
            'diversified_portfolio': portfolio,
            'timeline': 'Immediate offset available',
            'verification': 'Annual third-party verification included'
        }
        
        logger.info("Carbon neutral plan generated",
                   offset_tons=offset_required)
        
        return plan
    
    def _create_diversified_portfolio(
        self,
        offset_tons: float,
        budget: Optional[float] = None
    ) -> List[Dict]:
        """Create diversified portfolio of offset projects."""
        portfolio = []
        
        # Allocate across project types
        allocations = {
            'reforestation': 0.40,
            'renewable_energy': 0.30,
            'waste_to_energy': 0.20,
            'ocean_conservation': 0.10
        }
        
        total_cost = 0
        
        for project in self.OFFSET_PROJECTS:
            if project.project_type in allocations:
                allocation = allocations[project.project_type]
                allocated_tons = offset_tons * allocation
                cost = allocated_tons * project.cost_per_ton_co2
                
                if budget and total_cost + cost > budget:
                    break
                
                portfolio.append({
                    'project': project.project_name,
                    'type': project.project_type,
                    'tons': allocated_tons,
                    'cost': cost,
                    'allocation_percentage': allocation * 100
                })
                
                total_cost += cost
        
        return portfolio
