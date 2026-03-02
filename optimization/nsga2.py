"""
NSGA-II Multi-Objective Optimization
Non-dominated Sorting Genetic Algorithm II
"""

from typing import List, Tuple, Callable, Optional
import numpy as np
from dataclasses import dataclass
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class Individual:
    """Represents a solution in the population."""
    genes: np.ndarray  # Solution encoding
    objectives: np.ndarray  # Objective values [cost, co2, damage]
    rank: int = 0  # Pareto rank
    crowding_distance: float = 0.0  # Crowding distance
    
    def __repr__(self):
        return f"Individual(obj={self.objectives}, rank={self.rank}, cd={self.crowding_distance:.3f})"


class NSGA2Optimizer:
    """
    NSGA-II optimizer for multi-objective packaging optimization.
    
    Objectives:
        1. Minimize cost
        2. Minimize CO2 footprint
        3. Minimize damage probability
    """
    
    def __init__(
        self,
        population_size: int = 100,
        num_generations: int = 50,
        crossover_rate: float = 0.9,
        mutation_rate: float = 0.1,
        num_objectives: int = 3,
        random_state: Optional[int] = None
    ):
        """
        Initialize NSGA-II optimizer.
        
        Args:
            population_size: Population size (must be even)
            num_generations: Number of generations
            crossover_rate: Probability of crossover
            mutation_rate: Probability of mutation
            num_objectives: Number of objectives to optimize
            random_state: Random seed
        """
        self.population_size = population_size if population_size % 2 == 0 else population_size + 1
        self.num_generations = num_generations
        self.crossover_rate = crossover_rate
        self.mutation_rate = mutation_rate
        self.num_objectives = num_objectives
        
        if random_state is not None:
            np.random.seed(random_state)
        
        self.population: List[Individual] = []
        self.pareto_front: List[Individual] = []
        
        logger.info("NSGA2Optimizer initialized",
                   population_size=population_size,
                   num_generations=num_generations)
    
    def optimize(
        self,
        evaluate_fn: Callable,
        num_packaging_options: int,
        product_context: dict
    ) -> List[Individual]:
        """
        Run NSGA-II optimization.
        
        Args:
            evaluate_fn: Function to evaluate objectives for a packaging choice
                         Returns [cost, co2, damage_prob]
            num_packaging_options: Number of packaging options
            product_context: Product information for evaluation
        
        Returns:
            Pareto-optimal solutions
        """
        logger.info("Starting NSGA-II optimization...")
        
        # Initialize population
        self.population = self._initialize_population(
            num_packaging_options,
            evaluate_fn,
            product_context
        )
        
        # Evolution loop
        for generation in range(self.num_generations):
            # Create offspring
            offspring = self._create_offspring(
                evaluate_fn,
                num_packaging_options,
                product_context
            )
            
            # Combine parent and offspring
            combined = self.population + offspring
            
            # Non-dominated sorting
            fronts = self._fast_non_dominated_sort(combined)
            
            # Select next generation
            self.population = self._select_next_generation(fronts)
            
            # Log progress
            if (generation + 1) % 10 == 0:
                logger.info("Generation complete",
                           generation=generation+1,
                           pareto_front_size=len(fronts[0]))
        
        # Extract final Pareto front
        fronts = self._fast_non_dominated_sort(self.population)
        self.pareto_front = fronts[0]
        
        logger.info("NSGA-II optimization complete",
                   pareto_front_size=len(self.pareto_front))
        
        return self.pareto_front
    
    def _initialize_population(
        self,
        num_options: int,
        evaluate_fn: Callable,
        context: dict
    ) -> List[Individual]:
        """Initialize random population."""
        population = []
        
        for _ in range(self.population_size):
            # Random packaging selection
            genes = np.random.randint(0, num_options, size=1)
            
            # Evaluate objectives
            objectives = evaluate_fn(int(genes[0]), context)
            
            individual = Individual(
                genes=genes,
                objectives=np.array(objectives)
            )
            population.append(individual)
        
        return population
    
    def _fast_non_dominated_sort(
        self,
        population: List[Individual]
    ) -> List[List[Individual]]:
        """
        Fast non-dominated sorting algorithm.
        
        Returns:
            List of fronts, where front[0] is the Pareto front
        """
        n = len(population)
        
        # Initialize
        for p in population:
            p.rank = 0
        
        # Domination counts
        S = [[] for _ in range(n)]  # Solutions dominated by i
        n_dominated = [0] * n  # Number of solutions dominating i
        
        fronts = [[]]
        
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                
                if self._dominates(population[i], population[j]):
                    S[i].append(j)
                elif self._dominates(population[j], population[i]):
                    n_dominated[i] += 1
            
            if n_dominated[i] == 0:
                population[i].rank = 0
                fronts[0].append(population[i])
        
        # Build subsequent fronts
        front_idx = 0
        while fronts[front_idx]:
            next_front = []
            
            for individual in fronts[front_idx]:
                i = population.index(individual)
                
                for j in S[i]:
                    n_dominated[j] -= 1
                    if n_dominated[j] == 0:
                        population[j].rank = front_idx + 1
                        next_front.append(population[j])
            
            front_idx += 1
            if next_front:
                fronts.append(next_front)
        
        return fronts
    
    def _dominates(self, ind1: Individual, ind2: Individual) -> bool:
        """
        Check if ind1 dominates ind2.
        For minimization: ind1 dominates ind2 if all objectives are <=
        and at least one is strictly <
        """
        all_less_equal = np.all(ind1.objectives <= ind2.objectives)
        at_least_one_less = np.any(ind1.objectives < ind2.objectives)
        
        return all_less_equal and at_least_one_less
    
    def _calculate_crowding_distance(self, front: List[Individual]):
        """Calculate crowding distance for individuals in a front."""
        n = len(front)
        
        if n == 0:
            return
        
        # Initialize
        for ind in front:
            ind.crowding_distance = 0.0
        
        # For each objective
        for obj_idx in range(self.num_objectives):
            # Sort by objective
            front.sort(key=lambda x: x.objectives[obj_idx])
            
            # Boundary points get infinite distance
            front[0].crowding_distance = float('inf')
            front[-1].crowding_distance = float('inf')
            
            # Calculate range
            obj_min = front[0].objectives[obj_idx]
            obj_max = front[-1].objectives[obj_idx]
            obj_range = obj_max - obj_min
            
            if obj_range == 0:
                continue
            
            # Calculate crowding distance for interior points
            for i in range(1, n - 1):
                distance = (
                    front[i + 1].objectives[obj_idx] -
                    front[i - 1].objectives[obj_idx]
                ) / obj_range
                
                front[i].crowding_distance += distance
    
    def _select_next_generation(
        self,
        fronts: List[List[Individual]]
    ) -> List[Individual]:
        """Select next generation using crowding distance."""
        next_gen = []
        
        for front in fronts:
            if len(next_gen) + len(front) <= self.population_size:
                # Calculate crowding distance
                self._calculate_crowding_distance(front)
                next_gen.extend(front)
            else:
                # Calculate crowding distance and select best
                self._calculate_crowding_distance(front)
                front.sort(key=lambda x: x.crowding_distance, reverse=True)
                
                remaining = self.population_size - len(next_gen)
                next_gen.extend(front[:remaining])
                break
        
        return next_gen
    
    def _create_offspring(
        self,
        evaluate_fn: Callable,
        num_options: int,
        context: dict
    ) -> List[Individual]:
        """Create offspring through selection, crossover, and mutation."""
        offspring = []
        
        while len(offspring) < self.population_size:
            # Tournament selection
            parent1 = self._tournament_selection()
            parent2 = self._tournament_selection()
            
            # Crossover
            if np.random.random() < self.crossover_rate:
                child1_genes, child2_genes = self._crossover(
                    parent1.genes, parent2.genes
                )
            else:
                child1_genes = parent1.genes.copy()
                child2_genes = parent2.genes.copy()
            
            # Mutation
            if np.random.random() < self.mutation_rate:
                child1_genes = self._mutate(child1_genes, num_options)
            if np.random.random() < self.mutation_rate:
                child2_genes = self._mutate(child2_genes, num_options)
            
            # Evaluate offspring
            child1_obj = evaluate_fn(int(child1_genes[0]), context)
            child2_obj = evaluate_fn(int(child2_genes[0]), context)
            
            offspring.append(Individual(
                genes=child1_genes,
                objectives=np.array(child1_obj)
            ))
            offspring.append(Individual(
                genes=child2_genes,
                objectives=np.array(child2_obj)
            ))
        
        return offspring[:self.population_size]
    
    def _tournament_selection(self, tournament_size: int = 2) -> Individual:
        """Select individual using tournament selection."""
        tournament = np.random.choice(
            self.population,
            size=tournament_size,
            replace=False
        )
        
        # Select best by rank, then crowding distance
        tournament = sorted(
            tournament,
            key=lambda x: (x.rank, -x.crowding_distance)
        )
        
        return tournament[0]
    
    def _crossover(
        self,
        genes1: np.ndarray,
        genes2: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Single-point crossover for packaging selection."""
        # For single gene, swap with 50% probability
        if np.random.random() < 0.5:
            return genes2.copy(), genes1.copy()
        else:
            return genes1.copy(), genes2.copy()
    
    def _mutate(
        self,
        genes: np.ndarray,
        num_options: int
    ) -> np.ndarray:
        """Random mutation."""
        mutated = genes.copy()
        mutated[0] = np.random.randint(0, num_options)
        return mutated
    
    def get_pareto_front_data(self) -> List[dict]:
        """Get Pareto front as list of dictionaries."""
        return [
            {
                'packaging_id': int(ind.genes[0]),
                'cost': float(ind.objectives[0]),
                'co2': float(ind.objectives[1]),
                'damage_prob': float(ind.objectives[2]),
                'rank': ind.rank,
                'crowding_distance': float(ind.crowding_distance)
            }
            for ind in self.pareto_front
        ]
