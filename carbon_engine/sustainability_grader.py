"""
Sustainability Grader
Grades packaging sustainability (A-F) based on multiple factors
"""

from typing import Dict, Optional
from dataclasses import dataclass
from enum import Enum
import numpy as np
import structlog

logger = structlog.get_logger(__name__)


class SustainabilityGrade(str, Enum):
    """Sustainability grade levels."""
    A_PLUS = "A+"
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    F = "F"


@dataclass
class SustainabilityFactors:
    """Factors for sustainability grading."""
    co2_emissions_kg: float
    recyclability: float  # 0-1
    biodegradability: float  # 0-1
    renewable_source: bool
    toxicity_score: float  # 0-1, 0=non-toxic
    water_usage_liters: float
    energy_usage_kwh: float
    packaging_weight_kg: float
    reusability: float  # 0-1


class SustainabilityGrader:
    """
    Grade packaging sustainability based on comprehensive factors.
    Produces letter grades (A+-F) and numerical scores.
    """
    
    # Thresholds for grading
    GRADE_THRESHOLDS = {
        'co2': {
            'A+': 5,
            'A': 10,
            'B': 25,
            'C': 50,
            'D': 100,
            'F': float('inf')
        },
        'recyclability': {
            'A+': 0.95,
            'A': 0.90,
            'B': 0.75,
            'C': 0.60,
            'D': 0.40,
            'F': 0.0
        },
        'biodegradability': {
            'A+': 0.90,
            'A': 0.80,
            'B': 0.60,
            'C': 0.40,
            'D': 0.20,
            'F': 0.0
        }
    }
    
    # Weights for overall score
    FACTOR_WEIGHTS = {
        'co2': 0.30,
        'recyclability': 0.20,
        'biodegradability': 0.15,
        'renewable_source': 0.10,
        'toxicity': 0.10,
        'resource_efficiency': 0.10,
        'reusability': 0.05
    }
    
    def __init__(self):
        """Initialize sustainability grader."""
        logger.info("SustainabilityGrader initialized")
    
    def grade_factor(
        self,
        factor_name: str,
        value: float,
        higher_is_better: bool = True
    ) -> SustainabilityGrade:
        """
        Grade a single factor.
        
        Args:
            factor_name: Name of factor ('co2', 'recyclability', etc.)
            value: Factor value
            higher_is_better: If True, higher values get better grades
        
        Returns:
            Sustainability grade
        """
        if factor_name not in self.GRADE_THRESHOLDS:
            return SustainabilityGrade.C
        
        thresholds = self.GRADE_THRESHOLDS[factor_name]
        
        if higher_is_better:
            # For factors like recyclability (higher is better)
            if value >= thresholds['A+']:
                return SustainabilityGrade.A_PLUS
            elif value >= thresholds['A']:
                return SustainabilityGrade.A
            elif value >= thresholds['B']:
                return SustainabilityGrade.B
            elif value >= thresholds['C']:
                return SustainabilityGrade.C
            elif value >= thresholds['D']:
                return SustainabilityGrade.D
            else:
                return SustainabilityGrade.F
        else:
            # For factors like CO2 (lower is better)
            if value <= thresholds['A+']:
                return SustainabilityGrade.A_PLUS
            elif value <= thresholds['A']:
                return SustainabilityGrade.A
            elif value <= thresholds['B']:
                return SustainabilityGrade.B
            elif value <= thresholds['C']:
                return SustainabilityGrade.C
            elif value <= thresholds['D']:
                return SustainabilityGrade.D
            else:
                return SustainabilityGrade.F
    
    def calculate_numerical_score(
        self,
        factors: SustainabilityFactors
    ) -> float:
        """
        Calculate numerical sustainability score (0-100).
        
        Args:
            factors: Sustainability factors
        
        Returns:
            Score from 0 (worst) to 100 (best)
        """
        # CO2 score (normalized, inverted)
        co2_score = max(0, min(100, 100 - factors.co2_emissions_kg))
        
        # Recyclability score (0-100)
        recyclability_score = factors.recyclability * 100
        
        # Biodegradability score (0-100)
        biodegradability_score = factors.biodegradability * 100
        
        # Renewable source score (0 or 100)
        renewable_score = 100 if factors.renewable_source else 0
        
        # Toxicity score (inverted)
        toxicity_score = (1 - factors.toxicity_score) * 100
        
        # Resource efficiency (based on weight, water, energy)
        # Normalize to reasonable ranges
        weight_score = max(0, 100 - factors.packaging_weight_kg * 10)
        water_score = max(0, 100 - factors.water_usage_liters / 10)
        energy_score = max(0, 100 - factors.energy_usage_kwh * 5)
        resource_efficiency_score = (weight_score + water_score + energy_score) / 3
        
        # Reusability score
        reusability_score = factors.reusability * 100
        
        # Weighted average
        total_score = (
            self.FACTOR_WEIGHTS['co2'] * co2_score +
            self.FACTOR_WEIGHTS['recyclability'] * recyclability_score +
            self.FACTOR_WEIGHTS['biodegradability'] * biodegradability_score +
            self.FACTOR_WEIGHTS['renewable_source'] * renewable_score +
            self.FACTOR_WEIGHTS['toxicity'] * toxicity_score +
            self.FACTOR_WEIGHTS['resource_efficiency'] * resource_efficiency_score +
            self.FACTOR_WEIGHTS['reusability'] * reusability_score
        )
        
        return float(np.clip(total_score, 0, 100))
    
    def grade_overall(
        self,
        numerical_score: float
    ) -> SustainabilityGrade:
        """
        Convert numerical score to letter grade.
        
        Args:
            numerical_score: Score from 0-100
        
        Returns:
            Overall sustainability grade
        """
        if numerical_score >= 95:
            return SustainabilityGrade.A_PLUS
        elif numerical_score >= 85:
            return SustainabilityGrade.A
        elif numerical_score >= 70:
            return SustainabilityGrade.B
        elif numerical_score >= 55:
            return SustainabilityGrade.C
        elif numerical_score >= 40:
            return SustainabilityGrade.D
        else:
            return SustainabilityGrade.F
    
    def generate_report(
        self,
        factors: SustainabilityFactors,
        include_recommendations: bool = True
    ) -> Dict:
        """
        Generate comprehensive sustainability report.
        
        Args:
            factors: Sustainability factors
            include_recommendations: Include improvement recommendations
        
        Returns:
            Complete sustainability report
        """
        # Calculate numerical score
        numerical_score = self.calculate_numerical_score(factors)
        
        # Overall grade
        overall_grade = self.grade_overall(numerical_score)
        
        # Individual factor grades
        co2_grade = self.grade_factor('co2', factors.co2_emissions_kg, higher_is_better=False)
        recyclability_grade = self.grade_factor('recyclability', factors.recyclability)
        biodegradability_grade = self.grade_factor('biodegradability', factors.biodegradability)
        
        # Build report
        report = {
            'overall_grade': overall_grade.value,
            'numerical_score': round(numerical_score, 2),
            'factor_grades': {
                'co2_emissions': {
                    'value': factors.co2_emissions_kg,
                    'grade': co2_grade.value,
                    'unit': 'kg CO2'
                },
                'recyclability': {
                    'value': factors.recyclability * 100,
                    'grade': recyclability_grade.value,
                    'unit': '%'
                },
                'biodegradability': {
                    'value': factors.biodegradability * 100,
                    'grade': biodegradability_grade.value,
                    'unit': '%'
                },
                'renewable_source': {
                    'value': factors.renewable_source,
                    'grade': 'A+' if factors.renewable_source else 'F'
                },
                'toxicity': {
                    'value': factors.toxicity_score,
                    'grade': self._toxicity_grade(factors.toxicity_score).value
                },
                'reusability': {
                    'value': factors.reusability * 100,
                    'grade': self._reusability_grade(factors.reusability).value,
                    'unit': '%'
                }
            },
            'resource_usage': {
                'water_liters': factors.water_usage_liters,
                'energy_kwh': factors.energy_usage_kwh,
                'packaging_weight_kg': factors.packaging_weight_kg
            }
        }
        
        # Add recommendations
        if include_recommendations:
            report['recommendations'] = self._generate_recommendations(factors, numerical_score)
        
        logger.info("Sustainability report generated",
                   overall_grade=overall_grade.value,
                   score=numerical_score)
        
        return report
    
    def _toxicity_grade(self, toxicity_score: float) -> SustainabilityGrade:
        """Grade toxicity (lower is better)."""
        if toxicity_score <= 0.05:
            return SustainabilityGrade.A_PLUS
        elif toxicity_score <= 0.15:
            return SustainabilityGrade.A
        elif toxicity_score <= 0.30:
            return SustainabilityGrade.B
        elif toxicity_score <= 0.50:
            return SustainabilityGrade.C
        elif toxicity_score <= 0.70:
            return SustainabilityGrade.D
        else:
            return SustainabilityGrade.F
    
    def _reusability_grade(self, reusability: float) -> SustainabilityGrade:
        """Grade reusability (higher is better)."""
        if reusability >= 0.90:
            return SustainabilityGrade.A_PLUS
        elif reusability >= 0.75:
            return SustainabilityGrade.A
        elif reusability >= 0.60:
            return SustainabilityGrade.B
        elif reusability >= 0.40:
            return SustainabilityGrade.C
        elif reusability >= 0.20:
            return SustainabilityGrade.D
        else:
            return SustainabilityGrade.F
    
    def _generate_recommendations(
        self,
        factors: SustainabilityFactors,
        current_score: float
    ) -> list[str]:
        """Generate improvement recommendations."""
        recommendations = []
        
        # CO2 recommendations
        if factors.co2_emissions_kg > 25:
            recommendations.append(
                "Consider materials with lower carbon footprint in manufacturing"
            )
        
        # Recyclability recommendations
        if factors.recyclability < 0.75:
            recommendations.append(
                "Choose materials with higher recyclability (>75%)"
            )
        
        # Biodegradability recommendations
        if factors.biodegradability < 0.60:
            recommendations.append(
                "Consider biodegradable or compostable materials"
            )
        
        # Renewable source
        if not factors.renewable_source:
            recommendations.append(
                "Switch to renewable or bio-based materials"
            )
        
        # Toxicity
        if factors.toxicity_score > 0.30:
            recommendations.append(
                "Reduce use of toxic substances in materials"
            )
        
        # Resource efficiency
        if factors.packaging_weight_kg > 5:
            recommendations.append(
                "Optimize packaging design to reduce material weight"
            )
        
        if factors.water_usage_liters > 100:
            recommendations.append(
                "Reduce water consumption in manufacturing process"
            )
        
        # Reusability
        if factors.reusability < 0.50:
            recommendations.append(
                "Design packaging for reusability or multiple use cycles"
            )
        
        # Overall
        if current_score < 70:
            recommendations.insert(0,
                "Overall sustainability needs significant improvement"
            )
        
        return recommendations
    
    def compare_packaging_options(
        self,
        options: Dict[str, SustainabilityFactors]
    ) -> Dict:
        """
        Compare multiple packaging options.
        
        Args:
            options: Dictionary of {option_name: factors}
        
        Returns:
            Comparison report with rankings
        """
        results = {}
        
        for name, factors in options.items():
            score = self.calculate_numerical_score(factors)
            grade = self.grade_overall(score)
            
            results[name] = {
                'score': score,
                'grade': grade.value,
                'factors': factors
            }
        
        # Rank by score
        ranked = sorted(
            results.items(),
            key=lambda x: x[1]['score'],
            reverse=True
        )
        
        comparison = {
            'rankings': [
                {
                    'rank': i + 1,
                    'name': name,
                    'score': data['score'],
                    'grade': data['grade']
                }
                for i, (name, data) in enumerate(ranked)
            ],
            'best': ranked[0][0],
            'worst': ranked[-1][0],
            'score_range': ranked[0][1]['score'] - ranked[-1][1]['score']
        }
        
        logger.info("Packaging comparison complete",
                   best=comparison['best'],
                   num_options=len(options))
        
        return comparison
