"""
Weighted Scalarization
Convert multi-objective problem to single-objective using weights
"""

from typing import Dict, List, Optional
import numpy as np
import structlog

logger = structlog.get_logger(__name__)


class WeightedScalarization:
    """
    Weighted linear scalarization for multi-objective optimization.
    Converts multiple objectives into single objective: w1*f1 + w2*f2 + w3*f3
    """
    
    def __init__(
        self,
        weights: Optional[np.ndarray] = None,
        normalize: bool = True
    ):
        """
        Initialize weighted scalarization.
        
        Args:
            weights: Objective weights [num_objectives]
                     Default: equal weights [1/3, 1/3, 1/3]
            normalize: Whether to normalize objectives
        """
        if weights is None:
            weights = np.array([1/3, 1/3, 1/3])  # Equal weights
        
        # Ensure weights sum to 1
        self.weights = weights / weights.sum()
        self.normalize = normalize
        
        # Normalization parameters
        self.obj_min: Optional[np.ndarray] = None
        self.obj_max: Optional[np.ndarray] = None
        
        logger.info("WeightedScalarization initialized",
                   weights=self.weights.tolist(),
                   normalize=normalize)
    
    def fit(self, objectives: np.ndarray):
        """
        Fit normalization parameters from data.
        
        Args:
            objectives: Objective values [N, num_objectives]
        """
        if self.normalize:
            self.obj_min = objectives.min(axis=0)
            self.obj_max = objectives.max(axis=0)
            
            logger.info("Normalization fitted",
                       obj_min=self.obj_min.tolist(),
                       obj_max=self.obj_max.tolist())
    
    def scalarize(
        self,
        objectives: np.ndarray,
        custom_weights: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Convert multi-objective to single objective.
        
        Args:
            objectives: Objective values [N, num_objectives] or [num_objectives]
            custom_weights: Optional custom weights for this calculation
        
        Returns:
            Scalar scores [N] or scalar
        """
        weights = custom_weights if custom_weights is not None else self.weights
        
        # Ensure weights sum to 1
        weights = weights / weights.sum()
        
        # Normalize if configured
        if self.normalize and self.obj_min is not None and self.obj_max is not None:
            ranges = self.obj_max - self.obj_min
            ranges[ranges == 0] = 1.0  # Avoid division by zero
            normalized = (objectives - self.obj_min) / ranges
        else:
            normalized = objectives
        
        # Compute weighted sum
        if normalized.ndim == 1:
            # Single solution
            return np.dot(normalized, weights)
        else:
            # Multiple solutions
            return np.dot(normalized, weights)
    
    def find_best_solution(
        self,
        objectives: np.ndarray,
        solution_ids: List[int],
        custom_weights: Optional[np.ndarray] = None
    ) -> Dict:
        """
        Find best solution according to weighted scalarization.
        
        Args:
            objectives: Objective values [N, num_objectives]
            solution_ids: Solution identifiers
            custom_weights: Optional custom weights
        
        Returns:
            Dictionary with best solution info
        """
        scores = self.scalarize(objectives, custom_weights)
        best_idx = np.argmin(scores)
        
        return {
            'solution_id': solution_ids[best_idx],
            'index': int(best_idx),
            'score': float(scores[best_idx]),
            'objectives': {
                'cost': float(objectives[best_idx, 0]),
                'co2': float(objectives[best_idx, 1]),
                'damage_prob': float(objectives[best_idx, 2])
            },
            'weights_used': (custom_weights if custom_weights is not None else self.weights).tolist()
        }
    
    def rank_solutions(
        self,
        objectives: np.ndarray,
        solution_ids: List[int],
        custom_weights: Optional[np.ndarray] = None
    ) -> List[Dict]:
        """
        Rank all solutions by scalarized score.
        
        Args:
            objectives: Objective values [N, num_objectives]
            solution_ids: Solution identifiers
            custom_weights: Optional custom weights
        
        Returns:
            List of solution dictionaries, sorted by score (best first)
        """
        scores = self.scalarize(objectives, custom_weights)
        
        # Sort by score (ascending = better)
        sorted_indices = np.argsort(scores)
        
        ranked = []
        for rank, idx in enumerate(sorted_indices, 1):
            ranked.append({
                'rank': rank,
                'solution_id': solution_ids[idx],
                'index': int(idx),
                'score': float(scores[idx]),
                'objectives': {
                    'cost': float(objectives[idx, 0]),
                    'co2': float(objectives[idx, 1]),
                    'damage_prob': float(objectives[idx, 2])
                }
            })
        
        return ranked
    
    def interactive_weights_search(
        self,
        objectives: np.ndarray,
        solution_ids: List[int],
        num_weight_combinations: int = 20
    ) -> List[Dict]:
        """
        Generate multiple solutions by varying weights systematically.
        
        Args:
            objectives: Objective values [N, num_objectives]
            solution_ids: Solution identifiers
            num_weight_combinations: Number of weight combinations to try
        
        Returns:
            List of distinct best solutions for different weight combinations
        """
        logger.info("Running interactive weights search...",
                   num_combinations=num_weight_combinations)
        
        results = []
        seen_solutions = set()
        
        # Generate weight combinations
        for i in range(num_weight_combinations):
            # Random weights
            w = np.random.dirichlet([1, 1, 1])
            
            best = self.find_best_solution(objectives, solution_ids, w)
            
            solution_id = best['solution_id']
            if solution_id not in seen_solutions:
                best['weight_combination'] = i
                results.append(best)
                seen_solutions.add(solution_id)
        
        logger.info("Interactive search complete",
                   distinct_solutions=len(results))
        
        return results
    
    def sensitivity_analysis(
        self,
        objectives: np.ndarray,
        solution_ids: List[int],
        base_weights: Optional[np.ndarray] = None,
        perturbation: float = 0.1
    ) -> Dict:
        """
        Analyze sensitivity of solution ranking to weight changes.
        
        Args:
            objectives: Objective values [N, num_objectives]
            solution_ids: Solution identifiers
            base_weights: Base weights to perturb
            perturbation: Amount to perturb weights (+/-)
        
        Returns:
            Sensitivity analysis results
        """
        if base_weights is None:
            base_weights = self.weights
        
        base_best = self.find_best_solution(objectives, solution_ids, base_weights)
        
        # Perturb each weight
        sensitivity = {}
        
        for obj_idx in range(3):
            for direction in [-1, 1]:
                perturbed = base_weights.copy()
                perturbed[obj_idx] += direction * perturbation
                
                # Ensure non-negative and sum to 1
                perturbed = np.maximum(perturbed, 0)
                perturbed = perturbed / perturbed.sum()
                
                perturbed_best = self.find_best_solution(objectives, solution_ids, perturbed)
                
                obj_name = ['cost', 'co2', 'damage'][obj_idx]
                direction_str = 'increase' if direction > 0 else 'decrease'
                key = f'{obj_name}_{direction_str}'
                
                sensitivity[key] = {
                    'weights': perturbed.tolist(),
                    'best_solution_id': perturbed_best['solution_id'],
                    'changed': perturbed_best['solution_id'] != base_best['solution_id']
                }
        
        return {
            'base_solution': base_best,
            'sensitivity': sensitivity,
            'stability_score': sum(1 for s in sensitivity.values() if not s['changed']) / len(sensitivity)
        }
