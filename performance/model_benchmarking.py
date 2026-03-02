"""
Model Benchmarking Framework
Compares different packaging strategies
"""

from typing import Dict, Any, List
from dataclasses import dataclass
import numpy as np
import structlog

logger = structlog.get_logger(__name__)


class StrategyType:
    """Strategy types for benchmarking"""
    RANDOM = "random"  # Random selection
    CHEAPEST = "cheapest"  # Always pick cheapest
    MOST_ECO = "most_eco"  # Always pick most sustainable
    AI_OPTIMIZED = "ai_optimized"  # AI recommendation


@dataclass
class StrategyBenchmark:
    """Benchmark for a single strategy"""
    strategy: str
    avg_cost: float
    avg_co2: float
    avg_damage: float
    cost_std: float
    co2_std: float
    damage_std: float
    
    # Dominance metrics
    pareto_rank: int = 0  # 0 = Pareto-optimal
    dominance_score: float = 0.0  # 0-1, higher is better
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'strategy': self.strategy,
            'avg_cost': float(self.avg_cost),
            'avg_co2': float(self.avg_co2),
            'avg_damage': float(self.avg_damage),
            'cost_std': float(self.cost_std),
            'co2_std': float(self.co2_std),
            'damage_std': float(self.damage_std),
            'pareto_rank': self.pareto_rank,
            'dominance_score': float(self.dominance_score)
        }


class ModelBenchmarkingFramework:
    """
    Compares multiple packaging strategies
    """
    
    def __init__(self):
        """Initialize benchmarking framework"""
        logger.info("ModelBenchmarkingFramework initialized")
    
    def benchmark_strategies(
        self,
        ai_predictions: List[Dict],
        packaging_options: List[Dict],
        num_iterations: int = 100
    ) -> Dict[str, StrategyBenchmark]:
        """
        Benchmark multiple strategies
        
        Args:
            ai_predictions: AI predictions for each packaging
            packaging_options: Available packaging options
            num_iterations: Number of iterations for averaging
        
        Returns:
            Benchmarks for each strategy
        """
        logger.info(
            "Starting model benchmarking",
            packages=len(packaging_options),
            iterations=num_iterations
        )
        
        results = {}
        
        # 1. Random selection
        results['random'] = self._benchmark_random(
            ai_predictions,
            packaging_options,
            num_iterations
        )
        
        # 2. Always cheapest
        results['cheapest'] = self._benchmark_cheapest(ai_predictions)
        
        # 3. Always most eco
        results['most_eco'] = self._benchmark_most_eco(ai_predictions)
        
        # 4. AI optimized
        results['ai_optimized'] = self._benchmark_ai(ai_predictions)
        
        # Calculate Pareto dominance
        self._calculate_pareto_dominance(results)
        
        logger.info(
            "Benchmarking completed",
            strategies=len(results),
            best_strategy=min(results.items(),
                            key=lambda x: x[1].dominance_score)[0]
        )
        
        return results
    
    def _benchmark_random(
        self,
        ai_predictions: List[Dict],
        packaging_options: List[Dict],
        iterations: int
    ) -> StrategyBenchmark:
        """Benchmark random selection strategy"""
        costs = []
        co2s = []
        damages = []
        
        for _ in range(iterations):
            # Random selection
            idx = np.random.randint(0, len(ai_predictions))
            pred = ai_predictions[idx]
            
            costs.append(pred.get('cost', 0))
            co2s.append(pred.get('co2', 0))
            damages.append(pred.get('damage_prob', 0))
        
        return StrategyBenchmark(
            strategy='random',
            avg_cost=float(np.mean(costs)),
            avg_co2=float(np.mean(co2s)),
            avg_damage=float(np.mean(damages)),
            cost_std=float(np.std(costs)),
            co2_std=float(np.std(co2s)),
            damage_std=float(np.std(damages))
        )
    
    def _benchmark_cheapest(
        self,
        ai_predictions: List[Dict]
    ) -> StrategyBenchmark:
        """Benchmark always-cheapest strategy"""
        costs = [p.get('cost', 0) for p in ai_predictions]
        co2s = [p.get('co2', 0) for p in ai_predictions]
        damages = [p.get('damage_prob', 0) for p in ai_predictions]
        
        # Always pick cheapest (same outcome each time)
        cheapest_idx = np.argmin(costs)
        cheapest_cost = costs[cheapest_idx]
        cheapest_co2 = co2s[cheapest_idx]
        cheapest_damage = damages[cheapest_idx]
        
        return StrategyBenchmark(
            strategy='cheapest',
            avg_cost=cheapest_cost,
            avg_co2=cheapest_co2,
            avg_damage=cheapest_damage,
            cost_std=0.0,  # Deterministic
            co2_std=0.0,
            damage_std=0.0
        )
    
    def _benchmark_most_eco(
        self,
        ai_predictions: List[Dict]
    ) -> StrategyBenchmark:
        """Benchmark always-most-eco strategy"""
        # Eco score: minimize CO2 and maximize recyclability
        eco_scores = []
        
        for pred in ai_predictions:
            co2 = pred.get('co2', 0)
            recyclability = pred.get('recyclability', 0)
            
            # Lower CO2 is better, higher recyclability is better
            score = (1 / (1 + co2)) * (recyclability / 100)
            eco_scores.append(score)
        
        most_eco_idx = np.argmax(eco_scores)
        
        costs = [p.get('cost', 0) for p in ai_predictions]
        co2s = [p.get('co2', 0) for p in ai_predictions]
        damages = [p.get('damage_prob', 0) for p in ai_predictions]
        
        return StrategyBenchmark(
            strategy='most_eco',
            avg_cost=costs[most_eco_idx],
            avg_co2=co2s[most_eco_idx],
            avg_damage=damages[most_eco_idx],
            cost_std=0.0,
            co2_std=0.0,
            damage_std=0.0
        )
    
    def _benchmark_ai(
        self,
        ai_predictions: List[Dict]
    ) -> StrategyBenchmark:
        """Benchmark AI-optimized strategy"""
        # AI already ranked - pick top option
        if not ai_predictions:
            return StrategyBenchmark(
                strategy='ai_optimized',
                avg_cost=0,
                avg_co2=0,
                avg_damage=0,
                cost_std=0,
                co2_std=0,
                damage_std=0
            )
        
        best_idx = 0  # Assuming first is AI-ranked best
        
        costs = [p.get('cost', 0) for p in ai_predictions]
        co2s = [p.get('co2', 0) for p in ai_predictions]
        damages = [p.get('damage_prob', 0) for p in ai_predictions]
        
        return StrategyBenchmark(
            strategy='ai_optimized',
            avg_cost=costs[best_idx],
            avg_co2=co2s[best_idx],
            avg_damage=damages[best_idx],
            cost_std=0.0,
            co2_std=0.0,
            damage_std=0.0
        )
    
    def _calculate_pareto_dominance(
        self,
        results: Dict[str, StrategyBenchmark]
    ) -> None:
        """Calculate Pareto dominance for all strategies"""
        strategies = list(results.values())
        
        for i, strategy_i in enumerate(strategies):
            dominators = 0
            dominated = 0
            
            for j, strategy_j in enumerate(strategies):
                if i == j:
                    continue
                
                # Check if j dominates i
                # Lower cost, CO2, and damage is better
                j_better_cost = strategy_j.avg_cost < strategy_i.avg_cost
                j_better_co2 = strategy_j.avg_co2 < strategy_i.avg_co2
                j_better_damage = strategy_j.avg_damage < strategy_i.avg_damage
                
                # Dominance: j is better in all metrics, or similar but better in risk
                if (j_better_cost and j_better_co2) or \
                   (j_better_cost and j_better_damage) or \
                   (j_better_co2 and j_better_damage):
                    dominators += 1
                
                # Check if i dominates j
                i_better_cost = strategy_i.avg_cost < strategy_j.avg_cost
                i_better_co2 = strategy_i.avg_co2 < strategy_j.avg_co2
                i_better_damage = strategy_i.avg_damage < strategy_j.avg_damage
                
                if (i_better_cost and i_better_co2) or \
                   (i_better_cost and i_better_damage) or \
                   (i_better_co2 and i_better_damage):
                    dominated += 1
            
            # Pareto rank
            strategy_i.pareto_rank = 0 if dominators == 0 else 1
            
            # Dominance score (0-1, higher = more dominant)
            total_comparisons = len(strategies) - 1
            if total_comparisons > 0:
                strategy_i.dominance_score = dominated / total_comparisons
            else:
                strategy_i.dominance_score = 0.0
    
    def generate_report(
        self,
        benchmarks: Dict[str, StrategyBenchmark]
    ) -> str:
        """Generate benchmarking report"""
        report = "# Model Benchmarking Report\n\n"
        
        report += "## Strategy Comparison\n\n"
        report += "| Strategy | Avg Cost | Avg CO2 | Avg Damage | Pareto Rank | Dominance Score |\n"
        report += "|----------|----------|---------|------------|-------------|-----------|\n"
        
        for strat_name, bench in sorted(benchmarks.items(), 
                                       key=lambda x: -x[1].dominance_score):
            report += (
                f"| {strat_name} | "
                f"${bench.avg_cost:.2f} | "
                f"{bench.avg_co2:.2f}kg | "
                f"{bench.avg_damage:.2f}% | "
                f"{bench.pareto_rank} | "
                f"{bench.dominance_score:.3f} |\n"
            )
        
        # Find Pareto-optimal strategies
        pareto_strategies = [
            name for name, bench in benchmarks.items()
            if bench.pareto_rank == 0
        ]
        
        report += f"\n## Pareto-Optimal Strategies\n\n"
        report += f"The following strategies are Pareto-optimal:\n"
        for strategy in pareto_strategies:
            report += f"- {strategy}\n"
        
        # Ranking
        report += f"\n## Rankings\n\n"
        
        by_cost = sorted(benchmarks.items(),
                        key=lambda x: x[1].avg_cost)
        report += f"\n### Lowest Cost\n1. {by_cost[0][0]} - ${by_cost[0][1].avg_cost:.2f}\n"
        
        by_co2 = sorted(benchmarks.items(),
                       key=lambda x: x[1].avg_co2)
        report += f"\n### Lowest CO2\n1. {by_co2[0][0]} - {by_co2[0][1].avg_co2:.2f}kg\n"
        
        by_damage = sorted(benchmarks.items(),
                          key=lambda x: x[1].avg_damage)
        report += f"\n### Lowest Damage\n1. {by_damage[0][0]} - {by_damage[0][1].avg_damage:.2f}%\n"
        
        return report


__all__ = ['ModelBenchmarkingFramework', 'StrategyBenchmark', 'StrategyType']
