"""
Industrial Multi-Objective Recommendation Engine for EcoPackAI
==============================================================

Implements true industrial-grade recommendations with:
- Multi-option candidate generation
- Real-world constraint filtering
- Pareto optimization (multi-objective)
- Dynamic user preference weighting
- Diversity enforcement
- Comprehensive explanation layer
- Validation and testing framework

Author: ECO_PACK_AI Team
Version: 2.0 - Industrial Grade
"""

import numpy as np
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import warnings
warnings.filterwarnings('ignore')

from src.predictor import ProductionPredictor
from src.preprocessing import calculate_material_suitability

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class OptimizationObjective(Enum):
    """Optimization objectives for multi-objective ranking"""
    MINIMIZE_COST = "cost"
    MINIMIZE_CO2 = "co2"
    MINIMIZE_RISK = "risk"
    MAXIMIZE_SUSTAINABILITY = "sustainability"


@dataclass
class PackagingCandidate:
    """Represents a single packaging option with all predictions"""
    material_id: str
    material_type: str
    
    # Material properties
    strength: float
    weight_capacity: float
    cost_per_unit: float
    biodegradability_score: float
    recyclability_percentage: float
    
    # Predictions
    predicted_cost: float
    predicted_co2: float
    damage_risk: float
    
    # Derived scores
    sustainability_score: float
    suitability_score: float
    
    # Multi-objective scores
    normalized_cost: float = 0.0
    normalized_co2: float = 0.0
    normalized_risk: float = 0.0
    
    # Pareto ranking
    pareto_rank: int = 0
    crowding_distance: float = 0.0
    
    # Weighted score (user preferences)
    weighted_score: float = 0.0
    
    # Explanation
    tradeoff_summary: str = ""
    why_selected: str = ""
    pros: List[str] = None
    cons: List[str] = None
    
    def __post_init__(self):
        if self.pros is None:
            self.pros = []
        if self.cons is None:
            self.cons = []


@dataclass
class UserPreferences:
    """User preference weights for multi-objective optimization"""
    cost_weight: float = 0.33
    co2_weight: float = 0.33
    risk_weight: float = 0.34
    
    # Constraints
    max_budget: Optional[float] = None
    max_damage_risk: float = 0.8  # 0-1 scale
    min_sustainability: float = 0.3  # 0-1 scale
    max_co2_emission: Optional[float] = None  # kg CO2
    min_recyclability: float = 0.0  # 0-100 scale
    
    def validate(self):
        """Ensure weights sum to 1.0"""
        total = self.cost_weight + self.co2_weight + self.risk_weight
        if not (0.99 <= total <= 1.01):
            # Normalize
            self.cost_weight /= total
            self.co2_weight /= total
            self.risk_weight /= total


class IndustrialRecommendationEngine:
    """
    Industrial-grade recommendation engine with multi-objective optimization
    
    Features:
    - Generates all feasible packaging candidates
    - Applies real-world constraints
    - Performs Pareto optimization
    - Supports dynamic user preferences
    - Enforces diversity in recommendations
    - Provides comprehensive explanations
    """
    
    def __init__(self, db_config: Dict):
        self.db_config = db_config
        self.predictor = None
        self.load_models()
        
        # Material diversity tracking
        self.material_families = {
            'paper': ['paper', 'cardboard'],
            'plant': ['bamboo', 'bagasse', 'jute'],
            'synthetic': ['plastic', 'polymer'],
            'metal': ['metal', 'aluminum', 'steel'],
            'glass': ['glass']
        }
    
    def load_models(self):
        """Load industrial LightGBM models"""
        try:
            self.predictor = ProductionPredictor()
            print("[IndustrialEngine] Production predictor loaded")
        except Exception as e:
            print(f"[IndustrialEngine] Predictor loading error: {e}")
            self.predictor = None
    
    def get_db_connection(self):
        """Get database connection"""
        return psycopg2.connect(**self.db_config)
    
    def get_all_materials(self) -> List[Dict]:
        """Fetch all materials from database"""
        conn = self.get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cursor.execute("""
                SELECT 
                    material_id,
                    material_type,
                    strength,
                    weight_capacity,
                    cost_per_unit,
                    biodegradability_score,
                    recyclability_percentage
                FROM materials
            """)
            materials = cursor.fetchall()
            return [dict(m) for m in materials]
        finally:
            cursor.close()
            conn.close()
    
    # =====================================================
    # PHASE 1: MULTI-OPTION GENERATION
    # =====================================================
    
    def generate_all_candidates(
        self, 
        product_data: Dict,
        materials: Optional[List[Dict]] = None
    ) -> List[PackagingCandidate]:
        """
        Generate all feasible packaging candidates with predictions
        
        Args:
            product_data: Product specifications
            materials: Optional pre-fetched materials list
        
        Returns:
            List of PackagingCandidate objects with all predictions
        """
        if materials is None:
            materials = self.get_all_materials()
        
        candidates = []
        
        for material in materials:
            try:
                # Prepare input for ML predictor
                input_data = {
                    'strength': material.get('strength', 50.0),
                    'weight_capacity': product_data.get('weight', 10.0),
                    'biodegradability_score': material.get('biodegradability_score', 0.5),
                    'recyclability_percentage': material.get('recyclability_percentage', 50.0),
                    'fragility_level': product_data.get('fragility_level', 2),
                    'material_name': material.get('material_type', 'paper').lower(),
                    'shipping_mode': product_data.get('shipping_mode', 'Ground')
                }
                
                # Predict cost and CO2
                if self.predictor:
                    result = self.predictor.predict(input_data)
                    predicted_cost = result['cost_prediction']
                    predicted_co2 = result['co2_prediction']
                else:
                    # Fallback
                    predicted_cost = material['cost_per_unit'] * product_data.get('weight', 10.0)
                    predicted_co2 = predicted_cost * 2.0
                
                # Calculate damage risk
                damage_risk = self._calculate_damage_risk(product_data, material)
                
                # Sustainability score
                sustainability_score = (
                    material['biodegradability_score'] * 0.5 +
                    material['recyclability_percentage'] / 100.0 * 0.5
                )
                
                # Suitability score
                suitability_score = calculate_material_suitability(product_data, material)
                
                # Create candidate
                candidate = PackagingCandidate(
                    material_id=material['material_id'],
                    material_type=material['material_type'],
                    strength=material['strength'],
                    weight_capacity=material['weight_capacity'],
                    cost_per_unit=material['cost_per_unit'],
                    biodegradability_score=material['biodegradability_score'],
                    recyclability_percentage=material['recyclability_percentage'],
                    predicted_cost=predicted_cost,
                    predicted_co2=predicted_co2,
                    damage_risk=damage_risk,
                    sustainability_score=sustainability_score,
                    suitability_score=suitability_score
                )
                
                candidates.append(candidate)
                
            except Exception as e:
                print(f"Error processing material {material.get('material_type')}: {e}")
                continue
        
        return candidates
    
    def _calculate_damage_risk(self, product_data: Dict, material: Dict) -> float:
        """
        Calculate damage risk score (0-1, higher = more risk)
        
        Considers:
        - Product fragility
        - Material strength
        - Shipping mode
        """
        fragility = product_data.get('fragility_level', 2) / 3.0  # Normalize to 0-1
        strength_factor = 1.0 - min(material.get('strength', 50.0) / 100.0, 1.0)
        shipping_mode = product_data.get('shipping_mode', 'Ground')
        shipping_risk = 0.3 if shipping_mode == 'Air' else 0.1
        
        # Combined risk
        damage_risk = (
            fragility * 0.5 +
            strength_factor * 0.3 +
            shipping_risk * 0.2
        )
        
        return min(max(damage_risk, 0.0), 1.0)
    
    # =====================================================
    # PHASE 2: CONSTRAINT FILTERING
    # =====================================================
    
    def apply_constraints(
        self,
        candidates: List[PackagingCandidate],
        preferences: UserPreferences
    ) -> List[PackagingCandidate]:
        """
        Filter candidates based on real-world constraints
        
        Constraints:
        - Budget limits
        - Damage risk thresholds
        - Sustainability minimums
        - CO2 emission caps
        - Recyclability requirements
        """
        filtered = []
        
        for candidate in candidates:
            # Budget constraint
            if preferences.max_budget is not None:
                if candidate.predicted_cost > preferences.max_budget:
                    continue
            
            # Damage risk constraint
            if candidate.damage_risk > preferences.max_damage_risk:
                continue
            
            # Sustainability constraint
            if candidate.sustainability_score < preferences.min_sustainability:
                continue
            
            # CO2 emission constraint
            if preferences.max_co2_emission is not None:
                if candidate.predicted_co2 > preferences.max_co2_emission:
                    continue
            
            # Recyclability constraint
            if candidate.recyclability_percentage < preferences.min_recyclability:
                continue
            
            filtered.append(candidate)
        
        return filtered
    
    # =====================================================
    # PHASE 3: MULTI-OBJECTIVE OPTIMIZATION
    # =====================================================
    
    def normalize_objectives(self, candidates: List[PackagingCandidate]):
        """Normalize objectives to 0-1 scale for fair comparison"""
        if not candidates:
            return
        
        # Extract objective values
        costs = [c.predicted_cost for c in candidates]
        co2s = [c.predicted_co2 for c in candidates]
        risks = [c.damage_risk for c in candidates]
        
        # Normalize (min-max scaling)
        cost_min, cost_max = min(costs), max(costs)
        co2_min, co2_max = min(co2s), max(co2s)
        risk_min, risk_max = min(risks), max(risks)
        
        for candidate in candidates:
            # Normalize to 0-1 (0 = best, 1 = worst)
            if cost_max > cost_min:
                candidate.normalized_cost = (candidate.predicted_cost - cost_min) / (cost_max - cost_min)
            else:
                candidate.normalized_cost = 0.0
            
            if co2_max > co2_min:
                candidate.normalized_co2 = (candidate.predicted_co2 - co2_min) / (co2_max - co2_min)
            else:
                candidate.normalized_co2 = 0.0
            
            if risk_max > risk_min:
                candidate.normalized_risk = (candidate.damage_risk - risk_min) / (risk_max - risk_min)
            else:
                candidate.normalized_risk = 0.0
    
    def compute_pareto_ranking(self, candidates: List[PackagingCandidate]) -> List[PackagingCandidate]:
        """
        Compute Pareto ranking using non-dominated sorting
        
        Returns candidates sorted by Pareto rank and crowding distance
        """
        if not candidates:
            return []
        
        # Normalize objectives first
        self.normalize_objectives(candidates)
        
        # Non-dominated sorting
        fronts = self._non_dominated_sort(candidates)
        
        # Assign Pareto ranks
        for rank, front in enumerate(fronts):
            for candidate in front:
                candidate.pareto_rank = rank
        
        # Calculate crowding distance for each front
        for front in fronts:
            self._calculate_crowding_distance(front)
        
        # Sort: first by Pareto rank, then by crowding distance (descending)
        sorted_candidates = sorted(
            candidates,
            key=lambda c: (c.pareto_rank, -c.crowding_distance)
        )
        
        return sorted_candidates
    
    def _non_dominated_sort(self, candidates: List[PackagingCandidate]) -> List[List[PackagingCandidate]]:
        """
        Non-dominated sorting (NSGA-II algorithm)
        
        Returns list of Pareto fronts
        """
        fronts = [[]]
        domination_count = {id(c): 0 for c in candidates}
        dominated_solutions = {id(c): [] for c in candidates}
        
        # Compare all pairs
        for i, p in enumerate(candidates):
            for q in candidates[i+1:]:
                if self._dominates(p, q):
                    dominated_solutions[id(p)].append(q)
                    domination_count[id(q)] += 1
                elif self._dominates(q, p):
                    dominated_solutions[id(q)].append(p)
                    domination_count[id(p)] += 1
            
            # If not dominated by anyone, add to first front
            if domination_count[id(p)] == 0:
                fronts[0].append(p)
        
        # Build subsequent fronts
        i = 0
        while fronts[i]:
            next_front = []
            for p in fronts[i]:
                for q in dominated_solutions[id(p)]:
                    domination_count[id(q)] -= 1
                    if domination_count[id(q)] == 0:
                        next_front.append(q)
            i += 1
            if next_front:
                fronts.append(next_front)
        
        return fronts[:-1] if not fronts[-1] else fronts
    
    def _dominates(self, p: PackagingCandidate, q: PackagingCandidate) -> bool:
        """
        Check if solution p dominates solution q
        
        p dominates q if:
        - p is no worse than q in all objectives
        - p is strictly better than q in at least one objective
        """
        better_in_one = False
        
        # Compare all three objectives (all minimize)
        objectives_p = [p.normalized_cost, p.normalized_co2, p.normalized_risk]
        objectives_q = [q.normalized_cost, q.normalized_co2, q.normalized_risk]
        
        for obj_p, obj_q in zip(objectives_p, objectives_q):
            if obj_p > obj_q:  # p is worse in this objective
                return False
            elif obj_p < obj_q:  # p is better in this objective
                better_in_one = True
        
        return better_in_one
    
    def _calculate_crowding_distance(self, front: List[PackagingCandidate]):
        """
        Calculate crowding distance for solutions in a front
        
        Crowding distance promotes diversity by favoring solutions
        in less crowded regions of the objective space
        """
        if len(front) <= 2:
            for candidate in front:
                candidate.crowding_distance = float('inf')
            return
        
        # Initialize
        for candidate in front:
            candidate.crowding_distance = 0.0
        
        # Calculate for each objective
        objectives = ['normalized_cost', 'normalized_co2', 'normalized_risk']
        
        for obj in objectives:
            # Sort by this objective
            front.sort(key=lambda c: getattr(c, obj))
            
            # Boundary solutions get infinite distance
            front[0].crowding_distance = float('inf')
            front[-1].crowding_distance = float('inf')
            
            # Calculate distance for intermediate solutions
            obj_min = getattr(front[0], obj)
            obj_max = getattr(front[-1], obj)
            obj_range = obj_max - obj_min
            
            if obj_range > 0:
                for i in range(1, len(front) - 1):
                    distance = (getattr(front[i+1], obj) - getattr(front[i-1], obj)) / obj_range
                    front[i].crowding_distance += distance
    
    # =====================================================
    # PHASE 4: USER PREFERENCE WEIGHTING
    # =====================================================
    
    def apply_user_preferences(
        self,
        candidates: List[PackagingCandidate],
        preferences: UserPreferences
    ) -> List[PackagingCandidate]:
        """
        Apply user preference weights to compute weighted scores
        
        Lower weighted_score = better (minimization)
        """
        preferences.validate()
        
        for candidate in candidates:
            # Weighted sum of normalized objectives
            weighted_score = (
                preferences.cost_weight * candidate.normalized_cost +
                preferences.co2_weight * candidate.normalized_co2 +
                preferences.risk_weight * candidate.normalized_risk
            )
            
            candidate.weighted_score = weighted_score
        
        # Sort by weighted score (ascending - lower is better)
        return sorted(candidates, key=lambda c: c.weighted_score)
    
    # =====================================================
    # PHASE 5: DIVERSITY ENFORCEMENT
    # =====================================================
    
    def enforce_diversity(
        self,
        candidates: List[PackagingCandidate],
        top_n: int = 5
    ) -> List[PackagingCandidate]:
        """
        Ensure recommendations are diverse by penalizing duplicate material families
        
        Strategy:
        - Select top candidate
        - For each subsequent selection, penalize candidates from same material family
        - Add small tie-breaking randomness within close scores
        """
        if len(candidates) <= top_n:
            return candidates
        
        selected = []
        remaining = candidates.copy()
        selected_families = set()
        
        # Random tie-breaking factor (±2% of score)
        np.random.seed(42)  # Reproducible randomness
        
        while len(selected) < top_n and remaining:
            # Apply diversity penalty
            for candidate in remaining:
                family = self._get_material_family(candidate.material_type)
                
                # Penalty if family already selected
                if family in selected_families:
                    penalty = 0.15  # 15% penalty
                else:
                    penalty = 0.0
                
                # Add small random tie-breaker (±2%)
                tie_breaker = np.random.uniform(-0.02, 0.02)
                
                # Adjusted score
                candidate.diversity_adjusted_score = candidate.weighted_score + penalty + tie_breaker
            
            # Select best remaining candidate (with diversity penalty)
            best = min(remaining, key=lambda c: c.diversity_adjusted_score)
            selected.append(best)
            remaining.remove(best)
            
            # Track selected family
            family = self._get_material_family(best.material_type)
            selected_families.add(family)
        
        return selected
    
    def _get_material_family(self, material_type: str) -> str:
        """Get material family for diversity tracking"""
        material_lower = material_type.lower()
        
        for family, members in self.material_families.items():
            if any(member in material_lower for member in members):
                return family
        
        return 'other'
    
    # =====================================================
    # PHASE 6: EXPLANATION LAYER
    # =====================================================
    
    def generate_explanations(self, candidates: List[PackagingCandidate], product_data: Dict):
        """Generate human-readable explanations for each recommendation"""
        for rank, candidate in enumerate(candidates, 1):
            # Tradeoff summary
            candidate.tradeoff_summary = self._generate_tradeoff_summary(candidate)
            
            # Why selected
            candidate.why_selected = self._generate_why_selected(candidate, rank)
            
            # Pros and cons
            candidate.pros, candidate.cons = self._generate_pros_cons(candidate)
    
    def _generate_tradeoff_summary(self, candidate: PackagingCandidate) -> str:
        """Generate tradeoff summary"""
        cost_level = "Low" if candidate.normalized_cost < 0.33 else "Medium" if candidate.normalized_cost < 0.67 else "High"
        co2_level = "Low" if candidate.normalized_co2 < 0.33 else "Medium" if candidate.normalized_co2 < 0.67 else "High"
        risk_level = "Low" if candidate.normalized_risk < 0.33 else "Medium" if candidate.normalized_risk < 0.67 else "High"
        
        return f"{cost_level} cost, {co2_level} CO₂, {risk_level} risk"
    
    def _generate_why_selected(self, candidate: PackagingCandidate, rank: int) -> str:
        """Generate explanation for why this option was selected"""
        if rank == 1:
            strongest = self._get_strongest_attribute(candidate)
            return f"Best overall balance across all objectives. {strongest}"
        elif candidate.pareto_rank == 0:
            return "Pareto-optimal solution with strong multi-objective performance."
        else:
            strongest = self._get_strongest_attribute(candidate)
            return f"Strong alternative option. {strongest}"
    
    def _get_strongest_attribute(self, candidate: PackagingCandidate) -> str:
        """Identify strongest attribute of candidate"""
        attrs = {
            'cost': candidate.normalized_cost,
            'CO₂': candidate.normalized_co2,
            'risk': candidate.normalized_risk
        }
        
        best_attr = min(attrs.items(), key=lambda x: x[1])
        
        if best_attr[1] < 0.2:
            return f"Excellent {best_attr[0]} performance."
        elif best_attr[1] < 0.4:
            return f"Strong {best_attr[0]} efficiency."
        else:
            return "Balanced performance across objectives."
    
    def _generate_pros_cons(self, candidate: PackagingCandidate) -> Tuple[List[str], List[str]]:
        """Generate pros and cons lists"""
        pros = []
        cons = []
        
        # Cost
        if candidate.normalized_cost < 0.3:
            pros.append("Highly cost-effective")
        elif candidate.normalized_cost > 0.7:
            cons.append("Higher cost")
        
        # CO2
        if candidate.normalized_co2 < 0.3:
            pros.append("Low carbon footprint")
        elif candidate.normalized_co2 > 0.7:
            cons.append("High CO₂ emissions")
        
        # Risk
        if candidate.normalized_risk < 0.3:
            pros.append("Low damage risk")
        elif candidate.normalized_risk > 0.7:
            cons.append("Higher damage risk")
        
        # Sustainability
        if candidate.sustainability_score > 0.7:
            pros.append("Excellent sustainability")
        elif candidate.sustainability_score < 0.3:
            cons.append("Limited eco-friendliness")
        
        # Biodegradability
        if candidate.biodegradability_score > 0.8:
            pros.append("Highly biodegradable")
        elif candidate.biodegradability_score < 0.2:
            cons.append("Poor biodegradability")
        
        # Recyclability
        if candidate.recyclability_percentage > 85:
            pros.append("Excellent recyclability")
        elif candidate.recyclability_percentage < 40:
            cons.append("Limited recycling options")
        
        # Strength
        if candidate.strength > 70:
            pros.append("Strong and durable")
        elif candidate.strength < 40:
            cons.append("Lower structural strength")
        
        # Ensure at least one pro and one con
        if not pros:
            pros.append("Moderate overall performance")
        if not cons:
            cons.append("Trade-offs with specific attributes")
        
        return pros, cons
    
    # =====================================================
    # MAIN RECOMMENDATION API
    # =====================================================
    
    def get_recommendations(
        self,
        product_data: Dict,
        preferences: Optional[UserPreferences] = None,
        top_n: int = 5
    ) -> List[Dict]:
        """
        Get industrial-grade multi-objective recommendations
        
        Args:
            product_data: Product specifications
            preferences: User preference weights and constraints
            top_n: Number of recommendations to return
        
        Returns:
            List of recommendation dicts with comprehensive information
        """
        # Default preferences if not provided
        if preferences is None:
            preferences = UserPreferences()
        
        # PHASE 1: Generate all candidates
        candidates = self.generate_all_candidates(product_data)
        
        if not candidates:
            return []
        
        # PHASE 2: Apply constraints
        candidates = self.apply_constraints(candidates, preferences)
        
        if not candidates:
            print("⚠ No candidates passed constraint filtering")
            return []
        
        # PHASE 3: Multi-objective optimization (Pareto ranking)
        candidates = self.compute_pareto_ranking(candidates)
        
        # PHASE 4: Apply user preferences
        candidates = self.apply_user_preferences(candidates, preferences)
        
        # PHASE 5: Enforce diversity
        candidates = self.enforce_diversity(candidates, top_n)
        
        # PHASE 6: Generate explanations
        self.generate_explanations(candidates, product_data)
        
        # Convert to output format
        recommendations = []
        for rank, candidate in enumerate(candidates[:top_n], 1):
            recommendations.append({
                'rank': rank,
                'material': candidate.material_type,
                'material_id': candidate.material_id,
                
                # Predictions
                'cost': round(candidate.predicted_cost, 3),
                'co2': round(candidate.predicted_co2, 3),
                'damage_risk': round(candidate.damage_risk, 3),
                'sustainability_score': round(candidate.sustainability_score, 3),
                
                # Normalized objectives
                'normalized_cost': round(candidate.normalized_cost, 3),
                'normalized_co2': round(candidate.normalized_co2, 3),
                'normalized_risk': round(candidate.normalized_risk, 3),
                
                # Multi-objective metrics
                'pareto_rank': candidate.pareto_rank,
                'crowding_distance': round(candidate.crowding_distance, 3) if candidate.crowding_distance != float('inf') else 'inf',
                'weighted_score': round(candidate.weighted_score, 3),
                
                # Material properties
                'strength': candidate.strength,
                'biodegradability': candidate.biodegradability_score,
                'recyclability': candidate.recyclability_percentage,
                'cost_per_unit': candidate.cost_per_unit,
                
                # Explanations
                'tradeoff_summary': candidate.tradeoff_summary,
                'why_selected': candidate.why_selected,
                'pros': candidate.pros,
                'cons': candidate.cons
            })
        
        return recommendations
    
    # =====================================================
    # CONVENIENCE METHOD (backward compatibility)
    # =====================================================
    
    def get_simple_recommendations(
        self,
        product_data: Dict,
        cost_weight: float = 0.33,
        co2_weight: float = 0.33,
        risk_weight: float = 0.34,
        top_n: int = 6
    ) -> List[Dict]:
        """
        Simplified API for backward compatibility
        
        Args:
            product_data: Product specifications
            cost_weight: Weight for cost objective (0-1)
            co2_weight: Weight for CO2 objective (0-1)
            risk_weight: Weight for risk objective (0-1)
            top_n: Number of recommendations
        
        Returns:
            List of recommendation dicts
        """
        preferences = UserPreferences(
            cost_weight=cost_weight,
            co2_weight=co2_weight,
            risk_weight=risk_weight
        )
        
        return self.get_recommendations(product_data, preferences, top_n)
