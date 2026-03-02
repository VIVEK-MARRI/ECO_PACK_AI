"""
Enterprise AI Integration Example
Complete end-to-end usage of all AI components
"""

import numpy as np
import pandas as pd
from typing import Dict, List
import structlog

# Import all AI modules
from graph_models.graph_builder import GraphBuilder
from graph_models.gnn_model import HeteroGNN, ProductPackagingScorer
from graph_models.graph_inference import GraphInference
from ensemble.base_models import GradientBoostingModels, DeepTabularModels
from ensemble.stacking_ensemble import StackingEnsemble
from optimization.optimization_engine import OptimizationEngine
from carbon_engine.carbon_engine import CarbonAccountingEngine
from llm_engine.explanation_generator import ExplanationGenerator

logger = structlog.get_logger(__name__)


class EnterprisePackagingAI:
    """
    Complete AI pipeline for packaging recommendations.
    Integrates all enterprise components into a unified interface.
    """
    
    def __init__(
        self,
        gnn_model_path: str,
        ensemble_model_path: str,
        device: str = 'cpu'
    ):
        """
        Initialize complete AI pipeline.
        
        Args:
            gnn_model_path: Path to trained GNN model
            ensemble_model_path: Path to trained ensemble
            device: torch device
        """
        logger.info("Initializing EnterprisePackagingAI...")
        
        # 1. Graph Neural Network
        self.graph_builder = GraphBuilder()
        self.gnn_inference = GraphInference(
            model_path=gnn_model_path,
            device=device
        )
        
        # 2. Ensemble Models
        self.ensemble = StackingEnsemble.load(ensemble_model_path)
        
        # 3. Optimization Engine
        self.optimizer = OptimizationEngine()
        
        # 4. Carbon Accounting
        self.carbon_engine = CarbonAccountingEngine()
        
        # 5. LLM Explanations
        self.explainer = ExplanationGenerator()
        
        logger.info("EnterprisePackagingAI initialized successfully")
    
    def recommend_packaging(
        self,
        product: Dict,
        packaging_options: List[Dict],
        preferences: Dict = None
    ) -> Dict:
        """
        Complete packaging recommendation pipeline.
        
        Args:
            product: Product data
            packaging_options: Available packaging options
            preferences: User preferences (cost_weight, co2_weight, etc.)
        
        Returns:
            Complete recommendation with explanations
        """
        logger.info("Starting recommendation pipeline", product_id=product.get('id'))
        
        # Default preferences
        if preferences is None:
            preferences = {
                'cost_weight': 0.4,
                'co2_weight': 0.4,
                'damage_weight': 0.2
            }
        
        # Step 1: Predict metrics for all options
        predictions = self._predict_all_options(product, packaging_options)
        
        # Step 2: Multi-objective optimization
        optimized = self._optimize_selection(predictions, preferences)
        
        # Step 3: Carbon accounting
        sustainability = self._assess_sustainability(optimized['best_option'])
        
        # Step 4: Generate explanations
        explanations = self._generate_explanations(
            product=product,
            selected=optimized['best_option'],
            alternatives=optimized['pareto_front'][:3],
            preferences=preferences,
            sustainability=sustainability
        )
        
        # Step 5: Compile final recommendation
        recommendation = {
            'product_id': product.get('id'),
            'recommended_packaging': {
                'material': optimized['best_option']['material'],
                'cost': float(optimized['best_option']['cost']),
                'co2': float(optimized['best_option']['co2']),
                'damage_prob': float(optimized['best_option']['damage_prob']),
                'specifications': optimized['best_option'].get('specs', {})
            },
            'sustainability': {
                'grade': sustainability['grade'].name,
                'score': float(sustainability['score']),
                'lifecycle_co2': float(sustainability['lifecycle_co2']),
                'offset_cost': float(sustainability['offset_cost']),
                'certifications': sustainability.get('certifications', [])
            },
            'alternatives': [
                {
                    'material': alt['material'],
                    'cost': float(alt['cost']),
                    'co2': float(alt['co2']),
                    'damage_prob': float(alt['damage_prob'])
                }
                for alt in optimized['pareto_front'][:3]
            ],
            'explanations': explanations,
            'tradeoff_analysis': optimized['tradeoff_analysis'],
            'confidence': float(optimized.get('confidence', 0.85))
        }
        
        logger.info("Recommendation completed", 
                   material=recommendation['recommended_packaging']['material'],
                   grade=recommendation['sustainability']['grade'])
        
        return recommendation
    
    def batch_recommend(
        self,
        products: List[Dict],
        packaging_options: List[Dict],
        preferences: Dict = None
    ) -> List[Dict]:
        """
        Batch recommendation for multiple products.
        
        Args:
            products: List of product data
            packaging_options: Available packaging options
            preferences: User preferences
        
        Returns:
            List of recommendations
        """
        logger.info("Starting batch recommendation", num_products=len(products))
        
        recommendations = []
        for product in products:
            try:
                rec = self.recommend_packaging(product, packaging_options, preferences)
                recommendations.append(rec)
            except Exception as e:
                logger.error("Batch recommendation failed for product",
                           product_id=product.get('id'),
                           error=str(e))
                recommendations.append({
                    'product_id': product.get('id'),
                    'error': str(e)
                })
        
        logger.info("Batch recommendation completed", 
                   success_count=len([r for r in recommendations if 'error' not in r]))
        
        return recommendations
    
    def compare_packaging(
        self,
        product: Dict,
        option_a: Dict,
        option_b: Dict
    ) -> Dict:
        """
        Compare two packaging options in detail.
        
        Args:
            product: Product data
            option_a: First packaging option
            option_b: Second packaging option
        
        Returns:
            Detailed comparison
        """
        logger.info("Comparing packaging options")
        
        # Predict metrics
        pred_a = self._predict_single(product, option_a)
        pred_b = self._predict_single(product, option_b)
        
        # Carbon analysis
        carbon_a = self.carbon_engine.analyze_packaging({**option_a, **pred_a})
        carbon_b = self.carbon_engine.analyze_packaging({**option_b, **pred_b})
        
        # LLM comparison
        comparison = self.explainer.compare_options(
            option_a={**option_a, **pred_a, 'grade': carbon_a['grade'].name},
            option_b={**option_b, **pred_b, 'grade': carbon_b['grade'].name},
            product_description=product.get('description', product.get('category', 'Product'))
        )
        
        return {
            'option_a': {**pred_a, 'sustainability': carbon_a},
            'option_b': {**pred_b, 'sustainability': carbon_b},
            'comparison': comparison,
            'winner': 'A' if pred_a['cost'] + pred_a['co2'] < pred_b['cost'] + pred_b['co2'] else 'B'
        }
    
    def explain_decision(
        self,
        product: Dict,
        selected_packaging: Dict
    ) -> Dict:
        """
        Generate detailed explanation for a packaging decision.
        
        Args:
            product: Product data
            selected_packaging: Selected packaging
        
        Returns:
            Comprehensive explanation
        """
        logger.info("Generating decision explanation")
        
        # Get alternatives
        packaging_options = self._get_similar_options(selected_packaging)
        
        # Generate predictions
        predictions = self._predict_all_options(product, packaging_options)
        
        # Carbon analysis
        sustainability = self._assess_sustainability(selected_packaging)
        
        # Generate explanation
        explanation = self.explainer.explain_recommendation(
            product_data=product,
            packaging_data={**selected_packaging, **sustainability},
            alternatives=predictions[:3],
            preferences=None
        )
        
        return explanation
    
    def _predict_all_options(
        self,
        product: Dict,
        packaging_options: List[Dict]
    ) -> List[Dict]:
        """Predict metrics for all packaging options."""
        predictions = []
        
        for option in packaging_options:
            try:
                pred = self._predict_single(product, option)
                predictions.append({
                    **option,
                    **pred
                })
            except Exception as e:
                logger.error("Prediction failed", error=str(e))
                continue
        
        return predictions
    
    def _predict_single(
        self,
        product: Dict,
        packaging: Dict
    ) -> Dict:
        """Predict metrics for a single product-packaging pair."""
        # Create feature vector
        features = self._create_feature_vector(product, packaging)
        
        # GNN prediction
        gnn_pred = self.gnn_inference.predict_batch(
            product_ids=[product.get('id', 0)],
            packaging_ids=[packaging.get('id', 0)]
        )[0]
        
        # Ensemble prediction
        X = pd.DataFrame([features])
        ensemble_pred = self.ensemble.predict(X)[0]
        
        # Combine predictions (weighted average)
        cost = 0.6 * ensemble_pred['cost'] + 0.4 * gnn_pred['cost']
        co2 = 0.6 * ensemble_pred['co2'] + 0.4 * gnn_pred['co2']
        damage = 0.7 * ensemble_pred['damage'] + 0.3 * gnn_pred['damage']
        
        return {
            'cost': cost,
            'co2': co2,
            'damage_prob': damage * 100
        }
    
    def _optimize_selection(
        self,
        predictions: List[Dict],
        preferences: Dict
    ) -> Dict:
        """Optimize packaging selection."""
        # Extract objectives
        objectives = np.array([
            [p['cost'], p['co2'], p['damage_prob']]
            for p in predictions
        ])
        
        # Multi-objective optimization
        pareto_results = self.optimizer.optimize_multi_objective(
            objectives=objectives,
            method='nsga2',
            population_size=20,
            generations=10
        )
        
        # Weighted scalarization with preferences
        weighted_results = self.optimizer.optimize_weighted(
            objectives=objectives,
            weights=[
                preferences['cost_weight'],
                preferences['co2_weight'],
                preferences['damage_weight']
            ]
        )
        
        # Select best option
        best_idx = weighted_results['best_index']
        best_option = predictions[best_idx]
        
        # Tradeoff analysis
        tradeoff = self.optimizer.pareto_optimizer.analyze_tradeoffs(
            pareto_results['pareto_front']
        )
        
        return {
            'best_option': best_option,
            'pareto_front': [predictions[i] for i in pareto_results['pareto_indices']],
            'tradeoff_analysis': tradeoff,
            'confidence': weighted_results.get('confidence', 0.85)
        }
    
    def _assess_sustainability(self, packaging: Dict) -> Dict:
        """Assess sustainability of packaging."""
        analysis = self.carbon_engine.analyze_packaging(packaging)
        
        return {
            'grade': analysis['grade'],
            'score': analysis['score'],
            'lifecycle_co2': analysis['lifecycle_analysis']['total_co2'],
            'offset_cost': analysis['offset_analysis']['total_cost'],
            'certifications': analysis.get('certifications', [])
        }
    
    def _generate_explanations(
        self,
        product: Dict,
        selected: Dict,
        alternatives: List[Dict],
        preferences: Dict,
        sustainability: Dict
    ) -> Dict:
        """Generate all explanations."""
        # Main explanation
        main_explanation = self.explainer.explain_recommendation(
            product_data=product,
            packaging_data={**selected, **sustainability},
            alternatives=alternatives,
            preferences=preferences
        )
        
        # Executive summary
        exec_summary = self.explainer.generate_executive_summary(
            decision=f"Recommended {selected['material']} for {product.get('category')}",
            metrics={
                'cost_savings': f"${selected.get('cost', 0):.2f}",
                'co2_reduction': f"{selected.get('co2', 0):.2f} kg",
                'grade': sustainability['grade'].name
            }
        )
        
        # Compliance check
        compliance = self.explainer.check_compliance(
            packaging_data={**selected, **sustainability}
        )
        
        return {
            **main_explanation,
            'executive_summary': exec_summary,
            'compliance': compliance
        }
    
    def _create_feature_vector(
        self,
        product: Dict,
        packaging: Dict
    ) -> Dict:
        """Create feature vector for ensemble model."""
        return {
            'weight': product.get('weight', 0),
            'length': product.get('length', 0),
            'width': product.get('width', 0),
            'height': product.get('height', 0),
            'fragility': product.get('fragility_score', 0.5),
            'material_density': packaging.get('density', 0),
            'recyclability': packaging.get('recyclability', 0),
            'biodegradability': packaging.get('biodegradability', 0)
        }
    
    def _get_similar_options(self, selected: Dict) -> List[Dict]:
        """Get similar packaging options for comparison."""
        # Placeholder: In production, query from database
        return [selected]


# Example usage
if __name__ == "__main__":
    # Initialize AI system
    ai = EnterprisePackagingAI(
        gnn_model_path='models/gnn_model.pt',
        ensemble_model_path='models/ensemble.pkl'
    )
    
    # Example product
    product = {
        'id': 'PROD_12345',
        'category': 'Electronics',
        'weight': 2.5,
        'length': 30,
        'width': 20,
        'height': 10,
        'fragility_score': 0.8,
        'description': 'Laptop computer'
    }
    
    # Example packaging options
    packaging_options = [
        {
            'id': 'PKG_001',
            'material': 'Recycled Cardboard',
            'density': 0.3,
            'recyclability': 95,
            'biodegradability': 85
        },
        {
            'id': 'PKG_002',
            'material': 'Biodegradable Foam',
            'density': 0.05,
            'recyclability': 70,
            'biodegradability': 100
        },
        {
            'id': 'PKG_003',
            'material': 'Standard Plastic',
            'density': 0.9,
            'recyclability': 30,
            'biodegradability': 5
        }
    ]
    
    # Get recommendation
    recommendation = ai.recommend_packaging(
        product=product,
        packaging_options=packaging_options,
        preferences={
            'cost_weight': 0.3,
            'co2_weight': 0.5,
            'damage_weight': 0.2
        }
    )
    
    print("Recommended Packaging:", recommendation['recommended_packaging']['material'])
    print("Sustainability Grade:", recommendation['sustainability']['grade'])
    print("\nExplanation:", recommendation['explanations']['reasoning'])
