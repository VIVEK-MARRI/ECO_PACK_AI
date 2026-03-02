"""
Unified Optimization Engine
Combines NSGA-II, Pareto analysis, and weighted scalarization
"""

from typing import Dict, List, Optional, Callable
import numpy as np
import structlog

from .nsga2 import NSGA2Optimizer
from .pareto import ParetoFrontier, DominanceChecker
from .weighted_scalarization import WeightedScalarization

logger = structlog.get_logger(__name__)


class OptimizationEngine:
    """
    Complete multi-objective optimization engine.
    Provides unified interface for all optimization methods.
    """
    
    def __init__(
        self,
        default_weights: Optional[np.ndarray] = None,
        nsga2_config: Optional[Dict] = None
    ):
        """
        Initialize optimization engine.
        
        Args:
            default_weights: Default objective weights
            nsga2_config: Configuration for NSGA-II
        """
        self.default_weights = default_weights or np.array([0.4, 0.3, 0.3])
        
        self.nsga2_config = nsga2_config or {
            'population_size': 100,
            'num_generations': 50,
            'crossover_rate': 0.9,
            'mutation_rate': 0.1
        }
        
        self.scalarizer = WeightedScalarization(
            weights=self.default_weights,
            normalize=True
        )
        
        logger.info("OptimizationEngine initialized",
                   default_weights=self.default_weights.tolist())
    
    def optimize_with_nsga2(
        self,
        evaluate_fn: Callable,
        num_packaging_options: int,
        product_context: dict
    ) -> Dict:
        """
        Run NSGA-II optimization to find Pareto-optimal solutions.
        
        Args:
            evaluate_fn: Function to evaluate objectives (packaging_id, context) -> [cost, co2, damage]
            num_packaging_options: Number of packaging options
            product_context: Product information
        
        Returns:
            Optimization results with Pareto front
        """
        logger.info("Running NSGA-II optimization...")
        
        # Run NSGA-II
        optimizer = NSGA2Optimizer(**self.nsga2_config)
        pareto_front = optimizer.optimize(
            evaluate_fn=evaluate_fn,
            num_packaging_options=num_packaging_options,
            product_context=product_context
        )
        
        # Extract results
        results = {
            'pareto_front': optimizer.get_pareto_front_data(),
            'num_pareto_solutions': len(pareto_front),
            'convergence_generation': self.nsga2_config['num_generations']
        }
        
        logger.info("NSGA-II optimization complete",
                   num_pareto_solutions=len(pareto_front))
        
        return results
    
    def optimize_all_packaging(
        self,
        packaging_options: List[int],
        evaluate_fn: Callable,
        product_context: dict,
        weights: Optional[np.ndarray] = None
    ) -> Dict:
        """
        Evaluate all packaging options and find optimal solutions.
        
        Args:
            packaging_options: List of packaging IDs
            evaluate_fn: Evaluation function
            product_context: Product information
            weights: Optional custom weights
        
        Returns:
            Complete optimization results
        """
        logger.info("Optimizing all packaging options...",
                   num_options=len(packaging_options))
        
        # Evaluate all options
        objectives_list = []
        for pack_id in packaging_options:
            obj = evaluate_fn(pack_id, product_context)
            objectives_list.append(obj)
        
        objectives = np.array(objectives_list)
        
        # Fit scalarizer
        self.scalarizer.fit(objectives)
        
        # Pareto analysis
        pareto = ParetoFrontier(objectives, packaging_options)
        pareto.compute()
        
        # Find knee point
        knee_idx = pareto.find_knee_point()
        knee_solution_id = packaging_options[knee_idx]
        
        # Rank solutions
        use_weights = weights if weights is not None else self.default_weights
        ranked = self.scalarizer.rank_solutions(
            objectives,
            packaging_options,
            use_weights
        )
        
        # Tradeoff analysis
        tradeoff_df = pareto.get_tradeoff_analysis()
        
        results = {
            'pareto_front': pareto.get_pareto_solution_ids(),
            'knee_point': {
                'solution_id': knee_solution_id,
                'objectives': objectives[knee_idx].tolist()
            },
            'ranked_solutions': ranked[:10],  # Top 10
            'tradeoff_analysis': tradeoff_df.head(10).to_dict('records'),
            'summary_stats': pareto.get_summary_stats(),
            'visualization_data': pareto.visualize_2d_projection(0, 1)
        }
        
        logger.info("Optimization complete",
                   num_pareto=len(pareto.get_pareto_solution_ids()),
                   best_solution=ranked[0]['solution_id'])
        
        return results
    
    def interactive_optimization(
        self,
        packaging_options: List[int],
        evaluate_fn: Callable,
        product_context: dict,
        cost_weight: float = 0.4,
        co2_weight: float = 0.3,
        damage_weight: float = 0.3
    ) -> Dict:
        """
        Interactive optimization with user-specified weights.
        
        Args:
            packaging_options: List of packaging IDs
            evaluate_fn: Evaluation function
            product_context: Product information
            cost_weight: Weight for cost objective
            co2_weight: Weight for CO2 objective
            damage_weight: Weight for damage objective
        
        Returns:
            Optimization results with custom weights
        """
        # Normalize weights
        total = cost_weight + co2_weight + damage_weight
        weights = np.array([cost_weight, co2_weight, damage_weight]) / total
        
        logger.info("Running interactive optimization",
                   weights=weights.tolist())
        
        # Evaluate all options
        objectives_list = []
        for pack_id in packaging_options:
            obj = evaluate_fn(pack_id, product_context)
            objectives_list.append(obj)
        
        objectives = np.array(objectives_list)
        
        # Fit scalarizer
        self.scalarizer.fit(objectives)
        
        # Find best with custom weights
        best = self.scalarizer.find_best_solution(
            objectives,
            packaging_options,
            weights
        )
        
        # Get top 5 ranked
        ranked = self.scalarizer.rank_solutions(
            objectives,
            packaging_options,
            weights
        )[:5]
        
        # Sensitivity analysis
        sensitivity = self.scalarizer.sensitivity_analysis(
            objectives,
            packaging_options,
            weights,
            perturbation=0.1
        )
        
        results = {
            'best_solution': best,
            'top_5_ranked': ranked,
            'sensitivity_analysis': sensitivity,
            'weights_used': {
                'cost': float(weights[0]),
                'co2': float(weights[1]),
                'damage': float(weights[2])
            }
        }
        
        logger.info("Interactive optimization complete",
                   best_solution=best['solution_id'])
        
        return results
    
    def batch_optimize(
        self,
        products: List[dict],
        packaging_options: List[int],
        evaluate_fn: Callable
    ) -> List[Dict]:
        """
        Optimize packaging for multiple products in batch.
        
        Args:
            products: List of product contexts
            packaging_options: List of packaging IDs
            evaluate_fn: Evaluation function
        
        Returns:
            List of optimization results for each product
        """
        logger.info("Running batch optimization",
                   num_products=len(products))
        
        results = []
        
        for i, product in enumerate(products):
            logger.info("Optimizing product",
                       product_idx=i+1,
                       total=len(products))
            
            result = self.optimize_all_packaging(
                packaging_options=packaging_options,
                evaluate_fn=evaluate_fn,
                product_context=product
            )
            
            result['product_id'] = product.get('id', i)
            results.append(result)
        
        logger.info("Batch optimization complete")
        
        return results
    
    def get_pareto_curve_data(
        self,
        packaging_options: List[int],
        evaluate_fn: Callable,
        product_context: dict
    ) -> Dict:
        """
        Get data for Pareto curve visualization.
        
        Args:
            packaging_options: List of packaging IDs
            evaluate_fn: Evaluation function
            product_context: Product information
        
        Returns:
            Visualization data for Pareto curve
        """
        # Evaluate all options
        objectives_list = []
        for pack_id in packaging_options:
            obj = evaluate_fn(pack_id, product_context)
            objectives_list.append(obj)
        
        objectives = np.array(objectives_list)
        
        # Pareto analysis
        pareto = ParetoFrontier(objectives, packaging_options)
        pareto.compute()
        
        # Get 2D projections
        cost_vs_co2 = pareto.visualize_2d_projection(0, 1)
        cost_vs_damage = pareto.visualize_2d_projection(0, 2)
        co2_vs_damage = pareto.visualize_2d_projection(1, 2)
        
        return {
            'cost_vs_co2': cost_vs_co2,
            'cost_vs_damage': cost_vs_damage,
            'co2_vs_damage': co2_vs_damage,
            'pareto_front_ids': pareto.get_pareto_solution_ids(),
            'summary': pareto.get_summary_stats()
        }
