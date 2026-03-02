"""
Financial ROI Engine
Calculates business impact and ROI of AI recommendations
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
import structlog
from enum import Enum

logger = structlog.get_logger(__name__)


class ImpactCategory(Enum):
    """Categories of financial impact"""
    COST_SAVINGS = "cost_savings"
    DAMAGE_REDUCTION = "damage_reduction"
    CO2_REDUCTION = "co2_reduction"
    LABOR_EFFICIENCY = "labor_efficiency"


@dataclass
class FinancialInput:
    """Financial input parameters"""
    # Historical baselines
    baseline_monthly_packaging_cost: float  # $/month
    baseline_damage_rate: float  # % of shipments
    baseline_co2_emissions: float  # tons/month
    
    # Volume
    monthly_shipments: int
    avg_order_value: float  # $
    
    # Costs
    damage_replacement_cost_per_unit: float  # $
    water_impact_cost_per_unit: float  # $ per packaging unit
    carbon_tax_per_ton: float  # $/ton (for ESG)
    
    # Predictions from AI
    ai_recommended_packaging_cost: float  # $
    ai_predicted_damage_rate: float  # %
    ai_predicted_co2_emissions: float  # tons/month
    
    # Implementation costs
    implementation_cost: float = 0  # One-time setup
    ai_subscription_monthly: float = 0  # Monthly SaaS cost


@dataclass
class FinancialMetrics:
    """Financial metrics output"""
    monthly_cost_savings: float
    monthly_damage_reduction_savings: float
    monthly_co2_savings: float
    monthly_water_savings: float
    
    total_monthly_savings: float
    annual_savings: float
    
    roi_percentage: float
    payback_period_months: float
    
    # Break down by category
    breakdown: Dict[str, float]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'monthly_cost_savings': float(self.monthly_cost_savings),
            'monthly_damage_reduction': float(self.monthly_damage_reduction_savings),
            'monthly_co2_reduction': float(self.monthly_co2_savings),
            'monthly_water_savings': float(self.monthly_water_savings),
            'total_monthly_savings': float(self.total_monthly_savings),
            'annual_savings': float(self.annual_savings),
            'roi_percentage': float(self.roi_percentage),
            'payback_period_months': float(self.payback_period_months),
            'breakdown': {k: float(v) for k, v in self.breakdown.items()}
        }


class FinancialROIEngine:
    """
    Calculates financial ROI of AI packaging recommendations
    """
    
    def __init__(self):
        """Initialize ROI engine"""
        logger.info("FinancialROIEngine initialized")
    
    def calculate_roi(self, inputs: FinancialInput) -> FinancialMetrics:
        """
        Calculate complete ROI
        
        Args:
            inputs: Financial input parameters
        
        Returns:
            Financial metrics
        """
        logger.info(
            "Calculating financial ROI",
            monthly_shipments=inputs.monthly_shipments,
            baseline_cost=inputs.baseline_monthly_packaging_cost
        )
        
        # 1. Direct packaging cost savings
        packaging_cost_per_unit_baseline = (
            inputs.baseline_monthly_packaging_cost / inputs.monthly_shipments
        )
        packaging_cost_per_unit_ai = inputs.ai_recommended_packaging_cost
        
        monthly_cost_savings = (
            (packaging_cost_per_unit_baseline - packaging_cost_per_unit_ai) *
            inputs.monthly_shipments
        )
        
        # 2. Damage reduction savings
        baseline_damage_units = (
            inputs.monthly_shipments * inputs.baseline_damage_rate / 100
        )
        ai_damage_units = (
            inputs.monthly_shipments * inputs.ai_predicted_damage_rate / 100
        )
        
        damage_reduction_units = baseline_damage_units - ai_damage_units
        monthly_damage_savings = (
            damage_reduction_units * inputs.damage_replacement_cost_per_unit
        )
        
        # 3. CO2/Carbon tax savings
        co2_reduction_tons = (
            inputs.baseline_co2_emissions - inputs.ai_predicted_co2_emissions
        )
        monthly_co2_savings = co2_reduction_tons * inputs.carbon_tax_per_ton
        
        # 4. Water/Environmental impact savings
        monthly_water_savings = (
            inputs.monthly_shipments * inputs.water_impact_cost_per_unit
        )
        
        # Total monthly savings
        total_monthly_savings = (
            monthly_cost_savings +
            monthly_damage_savings +
            monthly_co2_savings +
            monthly_water_savings
        )
        
        # Annual metrics
        annual_savings = total_monthly_savings * 12
        
        # ROI calculation
        total_investment = (
            inputs.implementation_cost +
            (inputs.ai_subscription_monthly * 12)
        )
        
        if total_investment > 0:
            roi_percentage = (annual_savings / total_investment) * 100
            payback_period_months = (
                total_investment / total_monthly_savings
                if total_monthly_savings > 0 else float('inf')
            )
        else:
            roi_percentage = 0.0
            payback_period_months = 0.0
        
        # Breakdown
        breakdown = {
            'packaging_cost': monthly_cost_savings,
            'damage_reduction': monthly_damage_savings,
            'carbon_tax': monthly_co2_savings,
            'water_savings': monthly_water_savings
        }
        
        metrics = FinancialMetrics(
            monthly_cost_savings=monthly_cost_savings,
            monthly_damage_reduction_savings=monthly_damage_savings,
            monthly_co2_savings=monthly_co2_savings,
            monthly_water_savings=monthly_water_savings,
            total_monthly_savings=total_monthly_savings,
            annual_savings=annual_savings,
            roi_percentage=roi_percentage,
            payback_period_months=payback_period_months,
            breakdown=breakdown
        )
        
        logger.info(
            "ROI calculated",
            annual_savings=annual_savings,
            payback_months=payback_period_months,
            roi_pct=roi_percentage
        )
        
        return metrics
    
    def generate_executive_summary(
        self,
        inputs: FinancialInput,
        metrics: FinancialMetrics
    ) -> str:
        """
        Generate executive summary of financial impact
        
        Args:
            inputs: Financial inputs
            metrics: Calculated metrics
        
        Returns:
            Executive summary text
        """
        summary = f"""
# Financial Impact Summary

## Baseline vs. AI Recommended

### Costs
- **Baseline Annual Cost**: ${inputs.baseline_monthly_packaging_cost * 12:,.2f}
- **AI Recommended Annual Cost**: ${inputs.ai_recommended_packaging_cost * inputs.monthly_shipments * 12:,.2f}
- **Annual Packaging Savings**: ${metrics.monthly_cost_savings * 12:,.2f}

### Damage Reduction
- **Baseline Damage Rate**: {inputs.baseline_damage_rate:.1f}%
- **AI Predicted Damage Rate**: {inputs.ai_predicted_damage_rate:.1f}%
- **Damage Reduction Savings**: ${metrics.monthly_damage_reduction_savings * 12:,.2f}/year

### Environmental Impact
- **Baseline CO2**: {inputs.baseline_co2_emissions:.1f} tons/month
- **AI Predicted CO2**: {inputs.ai_predicted_co2_emissions:.1f} tons/month
- **CO2 Savings**: {inputs.baseline_co2_emissions - inputs.ai_predicted_co2_emissions:.1f} tons/month
- **Carbon Tax Savings**: ${metrics.monthly_co2_savings * 12:,.2f}/year

## Financial Metrics

### Total Financial Impact
- **Monthly Savings**: ${metrics.total_monthly_savings:,.2f}
- **Annual Savings**: ${metrics.annual_savings:,.2f}
- **ROI**: {metrics.roi_percentage:.1f}%
- **Payback Period**: {metrics.payback_period_months:.1f} months

### Monthly Breakdown
- Packaging Cost Savings: ${metrics.breakdown['packaging_cost']:,.2f}
- Damage Reduction: ${metrics.breakdown['damage_reduction']:,.2f}
- Carbon Tax Savings: ${metrics.breakdown['carbon_tax']:,.2f}
- Water Savings: ${metrics.breakdown['water_savings']:,.2f}

## Key Findings

1. **Cost Efficiency**: AI optimization reduces packaging costs by an average of {(metrics.breakdown['packaging_cost'] / inputs.baseline_monthly_packaging_cost * 100):.1f}%

2. **Risk Reduction**: Damage rate improves from {inputs.baseline_damage_rate:.1f}% to {inputs.ai_predicted_damage_rate:.1f}%

3. **Environmental**: CO2 emissions reduced by {((inputs.baseline_co2_emissions - inputs.ai_predicted_co2_emissions) / inputs.baseline_co2_emissions * 100):.1f}%

4. **Investment**: Pays back in {metrics.payback_period_months:.1f} months with {metrics.roi_percentage:.0f}% ROI

---

*Generated by ECO_PACK_AI Financial ROI Engine*
"""
        return summary
    
    def compare_strategies(
        self,
        baseline_metrics: FinancialInput,
        ai_metrics: FinancialInput,
        cheapest_metrics: FinancialInput,
        eco_metrics: FinancialInput
    ) -> Dict[str, Any]:
        """
        Compare multiple packaging strategies
        
        Args:
            baseline_metrics: Baseline approach
            ai_metrics: AI-optimized approach
            cheapest_metrics: Cheapest option
            eco_metrics: Most eco-friendly option
        
        Returns:
            Comparison results
        """
        results = {
            'baseline': self.calculate_roi(baseline_metrics),
            'ai_optimized': self.calculate_roi(ai_metrics),
            'cheapest': self.calculate_roi(cheapest_metrics),
            'eco_friendly': self.calculate_roi(eco_metrics)
        }
        
        # Calculate relative performance
        baseline_savings = results['baseline'].total_monthly_savings
        ai_savings = results['ai_optimized'].total_monthly_savings
        cheapest_savings = results['cheapest'].total_monthly_savings
        eco_savings = results['eco_friendly'].total_monthly_savings
        
        comparison = {
            'results': {k: v.to_dict() for k, v in results.items()},
            'relative_improvement': {
                'ai_vs_baseline': ((ai_savings - baseline_savings) / baseline_savings * 100) if baseline_savings > 0 else 0,
                'ai_vs_cheapest': ((ai_savings - cheapest_savings) / cheapest_savings * 100) if cheapest_savings > 0 else 0,
                'ai_vs_eco': ((ai_savings - eco_savings) / eco_savings * 100) if eco_savings > 0 else 0,
            },
            'ranking': sorted(
                [('baseline', ai_savings),
                 ('ai_optimized', ai_savings),
                 ('cheapest', cheapest_savings),
                 ('eco_friendly', eco_savings)],
                key=lambda x: x[1],
                reverse=True
            )
        }
        
        return comparison


__all__ = [
    'FinancialROIEngine',
    'FinancialInput',
    'FinancialMetrics',
    'ImpactCategory'
]
