"""
Pareto Frontier Analysis
Dominance checking and Pareto-optimal solution identification
"""

from typing import List, Tuple, Dict
import numpy as np
import pandas as pd
import structlog

logger = structlog.get_logger(__name__)


class DominanceChecker:
    """Check dominance relationships between solutions."""
    
    @staticmethod
    def dominates(
        obj1: np.ndarray,
        obj2: np.ndarray,
        minimize_all: bool = True
    ) -> bool:
        """
        Check if obj1 dominates obj2.
        
        Args:
            obj1: First objective vector
            obj2: Second objective vector
            minimize_all: If True, all objectives are minimized
        
        Returns:
            True if obj1 dominates obj2
        """
        if minimize_all:
            # For minimization: obj1 <= obj2 in all, and < in at least one
            all_less_equal = bool(np.all(obj1 <= obj2))
            at_least_one_less = bool(np.any(obj1 < obj2))
            return all_less_equal and at_least_one_less
        else:
            # Mixed objectives handled here if needed
            raise NotImplementedError("Mixed objectives not implemented")
    
    @staticmethod
    def is_pareto_optimal(
        solution_idx: int,
        objectives: np.ndarray
    ) -> bool:
        """
        Check if a solution is Pareto optimal.
        
        Args:
            solution_idx: Index of solution to check
            objectives: Matrix of all objectives [N, num_objectives]
        
        Returns:
            True if solution is Pareto optimal
        """
        solution = objectives[solution_idx]
        
        for i, other in enumerate(objectives):
            if i == solution_idx:
                continue
            
            if DominanceChecker.dominates(other, solution):
                return False
        
        return True


class ParetoFrontier:
    """
    Pareto frontier computation and analysis.
    """
    
    def __init__(self, objectives: np.ndarray, solution_ids: List[int]):
        """
        Initialize Pareto frontier.
        
        Args:
            objectives: Objective values [N, num_objectives]
            solution_ids: Solution identifiers
        """
        self.objectives = objectives
        self.solution_ids = solution_ids
        self.pareto_indices: List[int] = []
        self.dominated_by: Dict[int, List[int]] = {}
        
        logger.info("ParetoFrontier initialized",
                   num_solutions=len(objectives))
    
    def compute(self) -> List[int]:
        """
        Compute Pareto-optimal solutions.
        
        Returns:
            Indices of Pareto-optimal solutions
        """
        logger.info("Computing Pareto frontier...")
        
        n = len(self.objectives)
        is_pareto = np.ones(n, dtype=bool)
        
        for i in range(n):
            if not is_pareto[i]:
                continue
            
            # Check if any other solution dominates this one
            for j in range(n):
                if i == j or not is_pareto[j]:
                    continue
                
                if DominanceChecker.dominates(self.objectives[j], self.objectives[i]):
                    is_pareto[i] = False
                    
                    if i not in self.dominated_by:
                        self.dominated_by[i] = []
                    self.dominated_by[i].append(j)
                    break
        
        self.pareto_indices = np.where(is_pareto)[0].tolist()
        
        logger.info("Pareto frontier computed",
                   num_pareto_optimal=len(self.pareto_indices))
        
        return self.pareto_indices
    
    def get_pareto_front(self) -> np.ndarray:
        """Get objective values of Pareto-optimal solutions."""
        if not self.pareto_indices:
            self.compute()
        
        return self.objectives[self.pareto_indices]
    
    def get_pareto_solution_ids(self) -> List[int]:
        """Get IDs of Pareto-optimal solutions."""
        if not self.pareto_indices:
            self.compute()
        
        return [self.solution_ids[i] for i in self.pareto_indices]
    
    def get_dominated_solutions(self) -> Dict[int, List[int]]:
        """Get mapping of dominated solutions to their dominators."""
        return self.dominated_by
    
    def find_knee_point(self) -> int:
        """
        Find knee point (best compromise) in Pareto front.
        Uses maximum distance from ideal and nadir points.
        
        Returns:
            Index of knee point solution
        """
        if not self.pareto_indices:
            self.compute()
        
        pareto_front = self.get_pareto_front()
        
        if len(pareto_front) == 0:
            raise ValueError("No Pareto-optimal solutions found")
        
        # Normalize objectives
        ideal = pareto_front.min(axis=0)
        nadir = pareto_front.max(axis=0)
        
        # Avoid division by zero
        ranges = nadir - ideal
        ranges[ranges == 0] = 1.0
        
        normalized = (pareto_front - ideal) / ranges
        
        # Find solution farthest from ideal point in normalized space
        distances = np.linalg.norm(normalized, axis=1)
        knee_idx = np.argmin(distances)
        
        logger.info("Knee point found",
                   knee_solution_id=self.solution_ids[self.pareto_indices[knee_idx]])
        
        return self.pareto_indices[knee_idx]
    
    def rank_solutions(
        self,
        weights: np.ndarray = None
    ) -> List[Tuple[int, float]]:
        """
        Rank all solutions by weighted scalarization.
        
        Args:
            weights: Objective weights [num_objectives]
                     Default: equal weights
        
        Returns:
            List of (solution_id, score) tuples, sorted by score
        """
        if weights is None:
            weights = np.ones(self.objectives.shape[1]) / self.objectives.shape[1]
        
        # Normalize objectives
        ideal = self.objectives.min(axis=0)
        nadir = self.objectives.max(axis=0)
        ranges = nadir - ideal
        ranges[ranges == 0] = 1.0
        
        normalized = (self.objectives - ideal) / ranges
        
        # Compute weighted scores
        scores = np.dot(normalized, weights)
        
        # Sort by score (lower is better)
        ranked = sorted(
            zip(self.solution_ids, scores),
            key=lambda x: x[1]
        )
        
        return ranked
    
    def get_tradeoff_analysis(self) -> pd.DataFrame:
        """
        Analyze tradeoffs in Pareto front.
        
        Returns:
            DataFrame with Pareto-optimal solutions and metrics
        """
        if not self.pareto_indices:
            self.compute()
        
        pareto_front = self.get_pareto_front()
        pareto_ids = self.get_pareto_solution_ids()
        
        df = pd.DataFrame(
            pareto_front,
            columns=['cost', 'co2', 'damage_prob']
        )
        df['solution_id'] = pareto_ids
        
        # Add normalized scores
        ideal = pareto_front.min(axis=0)
        nadir = pareto_front.max(axis=0)
        ranges = nadir - ideal
        ranges[ranges == 0] = 1.0
        
        normalized = (pareto_front - ideal) / ranges
        
        df['normalized_cost'] = normalized[:, 0]
        df['normalized_co2'] = normalized[:, 1]
        df['normalized_damage'] = normalized[:, 2]
        
        # Composite score (equal weights)
        df['composite_score'] = normalized.mean(axis=1)
        
        # Distance from ideal
        df['distance_from_ideal'] = np.linalg.norm(normalized, axis=1)
        
        # Sort by composite score
        df = df.sort_values('composite_score')
        
        return df
    
    def visualize_2d_projection(
        self,
        obj1_idx: int = 0,
        obj2_idx: int = 1
    ) -> Dict:
        """
        Get data for 2D projection visualization.
        
        Args:
            obj1_idx: First objective index
            obj2_idx: Second objective index
        
        Returns:
            Dictionary with plot data
        """
        if not self.pareto_indices:
            self.compute()
        
        all_obj1 = self.objectives[:, obj1_idx]
        all_obj2 = self.objectives[:, obj2_idx]
        
        pareto_obj1 = all_obj1[self.pareto_indices]
        pareto_obj2 = all_obj2[self.pareto_indices]
        
        return {
            'all_solutions': {
                'x': all_obj1.tolist(),
                'y': all_obj2.tolist(),
                'ids': self.solution_ids
            },
            'pareto_front': {
                'x': pareto_obj1.tolist(),
                'y': pareto_obj2.tolist(),
                'ids': self.get_pareto_solution_ids()
            },
            'labels': {
                'x': ['cost', 'co2', 'damage_prob'][obj1_idx],
                'y': ['cost', 'co2', 'damage_prob'][obj2_idx]
            }
        }
    
    def get_summary_stats(self) -> Dict:
        """Get summary statistics of Pareto front."""
        if not self.pareto_indices:
            self.compute()
        
        pareto_front = self.get_pareto_front()
        
        return {
            'num_total_solutions': len(self.objectives),
            'num_pareto_optimal': len(self.pareto_indices),
            'pareto_ratio': len(self.pareto_indices) / len(self.objectives),
            'objective_ranges': {
                'cost': {
                    'min': float(pareto_front[:, 0].min()),
                    'max': float(pareto_front[:, 0].max()),
                    'mean': float(pareto_front[:, 0].mean())
                },
                'co2': {
                    'min': float(pareto_front[:, 1].min()),
                    'max': float(pareto_front[:, 1].max()),
                    'mean': float(pareto_front[:, 1].mean())
                },
                'damage_prob': {
                    'min': float(pareto_front[:, 2].min()),
                    'max': float(pareto_front[:, 2].max()),
                    'mean': float(pareto_front[:, 2].mean())
                }
            }
        }
