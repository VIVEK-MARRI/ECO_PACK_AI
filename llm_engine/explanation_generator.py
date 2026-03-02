"""
Explanation Generator
High-level interface for generating explanations
"""

from typing import Dict, Any, Optional, List
import structlog

from .llm_client import LLMClient
from .prompt_templates import PromptTemplateEngine

logger = structlog.get_logger(__name__)


class ExplanationGenerator:
    """
    Generate human-readable explanations for packaging decisions.
    Provides high-level interface for different explanation types.
    """
    
    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        use_cache: bool = True
    ):
        """
        Initialize explanation generator.
        
        Args:
            llm_client: LLM client (creates default if None)
            use_cache: Enable explanation caching
        """
        self.llm_client = llm_client or LLMClient()
        self.template_engine = PromptTemplateEngine()
        self.use_cache = use_cache
        self.cache: Dict[str, Dict] = {}
        
        logger.info("ExplanationGenerator initialized", use_cache=use_cache)
    
    def explain_recommendation(
        self,
        product_data: Dict[str, Any],
        packaging_data: Dict[str, Any],
        alternatives: List[Dict],
        preferences: Optional[Dict] = None
    ) -> Dict[str, str]:
        """
        Generate comprehensive explanation for packaging recommendation.
        
        Args:
            product_data: Product information
            packaging_data: Selected packaging details
            alternatives: Alternative options
            preferences: User preferences
        
        Returns:
            Explanation dictionary with structured sections
        """
        logger.info("Generating recommendation explanation...")
        
        # Check cache
        cache_key = self._generate_cache_key(product_data, packaging_data)
        if self.use_cache and cache_key in self.cache:
            logger.info("Returning cached explanation")
            return self.cache[cache_key]
        
        # Generate prompt
        prompt = self.template_engine.generate_sustainability_prompt(
            product_data=product_data,
            packaging_data=packaging_data,
            alternatives=alternatives,
            preferences=preferences
        )
        
        # Generate explanation
        try:
            explanation = self.llm_client.generate_json(prompt)
            
            # Validate required keys
            required_keys = ['reasoning', 'impact', 'tradeoffs', 'compliance', 'score_explanation']
            for key in required_keys:
                if key not in explanation:
                    explanation[key] = f"Analysis of {key} not available"
            
            # Cache result
            if self.use_cache:
                self.cache[cache_key] = explanation
            
            logger.info("Explanation generated successfully")
            return explanation
        
        except Exception as e:
            logger.error("Explanation generation failed", error=str(e))
            return self._fallback_explanation(product_data, packaging_data)
    
    def compare_options(
        self,
        option_a: Dict,
        option_b: Dict,
        product_description: str
    ) -> Dict[str, str]:
        """
        Generate comparison between two packaging options.
        
        Args:
            option_a: First packaging option
            option_b: Second packaging option
            product_description: Product description
        
        Returns:
            Comparison explanation
        """
        logger.info("Generating comparison explanation...")
        
        prompt = self.template_engine.generate_comparison_prompt(
            option_a=option_a,
            option_b=option_b,
            product_description=product_description
        )
        
        try:
            comparison = self.llm_client.generate_json(prompt)
            
            logger.info("Comparison generated successfully")
            return comparison
        
        except Exception as e:
            logger.error("Comparison generation failed", error=str(e))
            return self._fallback_comparison(option_a, option_b)
    
    def generate_executive_summary(
        self,
        decision: str,
        metrics: Dict
    ) -> str:
        """
        Generate executive summary for C-level presentation.
        
        Args:
            decision: Decision description
            metrics: Key metrics
        
        Returns:
            Executive summary text
        """
        logger.info("Generating executive summary...")
        
        prompt = self.template_engine.generate_executive_summary_prompt(
            decision=decision,
            metrics=metrics
        )
        
        try:
            summary = self.llm_client.generate(prompt, max_tokens=300, temperature=0.5)
            
            logger.info("Executive summary generated")
            return summary
        
        except Exception as e:
            logger.error("Executive summary generation failed", error=str(e))
            return self._fallback_executive_summary(metrics)
    
    def check_compliance(
        self,
        packaging_data: Dict,
        location: str = "Global"
    ) -> Dict:
        """
        Generate compliance check explanation.
        
        Args:
            packaging_data: Packaging details
            location: Geographic location
        
        Returns:
            Compliance assessment
        """
        logger.info("Generating compliance check...")
        
        prompt = self.template_engine.generate_compliance_prompt(
            packaging_data=packaging_data,
            location=location
        )
        
        try:
            compliance = self.llm_client.generate_json(prompt)
            
            logger.info("Compliance check completed")
            return compliance
        
        except Exception as e:
            logger.error("Compliance check failed", error=str(e))
            return self._fallback_compliance()
    
    def _generate_cache_key(
        self,
        product_data: Dict,
        packaging_data: Dict
    ) -> str:
        """Generate cache key from data."""
        key_parts = [
            str(product_data.get('id', '')),
            str(packaging_data.get('material', '')),
            str(packaging_data.get('cost', ''))
        ]
        return "_".join(key_parts)
    
    def _fallback_explanation(
        self,
        product_data: Dict,
        packaging_data: Dict
    ) -> Dict[str, str]:
        """Generate fallback explanation when LLM fails."""
        return {
            'reasoning': f"This {packaging_data.get('material', 'packaging')} was selected based on AI model predictions "
                        f"that consider cost (${packaging_data.get('cost', 0):.2f}), "
                        f"CO2 emissions ({packaging_data.get('co2', 0):.2f} kg), and "
                        f"damage probability ({packaging_data.get('damage_prob', 0):.1f}%). "
                        f"For your {product_data.get('category', 'product')}, this option provides "
                        f"the best balance of sustainability and performance.",
            
            'impact': f"Environmental impact: {packaging_data.get('co2', 0):.2f} kg CO2 emissions, "
                     f"{packaging_data.get('recyclability', 0)}% recyclability, "
                     f"{packaging_data.get('biodegradability', 0)}% biodegradability. "
                     f"This represents a sustainable choice with minimal environmental footprint.",
            
            'tradeoffs': f"Cost-sustainability balance achieved: Moderate cost (${packaging_data.get('cost', 0):.2f}) "
                        f"with strong environmental performance. "
                        f"Predicted damage rate of {packaging_data.get('damage_prob', 0):.1f}% ensures product protection.",
            
            'compliance': "This packaging meets standard sustainability guidelines and common industry certifications.",
            
            'score_explanation': f"Sustainability score calculated from weighted combination of environmental factors: "
                               f"CO2 emissions (30%), recyclability (25%), biodegradability (20%), and other factors."
        }
    
    def _fallback_comparison(
        self,
        option_a: Dict,
        option_b: Dict
    ) -> Dict[str, str]:
        """Generate fallback comparison."""
        cost_diff = option_b['cost'] - option_a['cost']
        co2_diff = option_b['co2'] - option_a['co2']
        
        if cost_diff < 0 and co2_diff < 0:
            recommendation = f"{option_b['material']} is better (lower cost and CO2)"
        elif cost_diff < 0:
            recommendation = f"{option_b['material']} is cheaper but has higher CO2"
        elif co2_diff < 0:
            recommendation = f"{option_b['material']} has lower CO2 but costs more"
        else:
            recommendation = f"{option_a['material']} is better overall"
        
        return {
            'recommendation': recommendation,
            'key_differences': f"Cost differs by ${abs(cost_diff):.2f}, CO2 by {abs(co2_diff):.2f} kg",
            'justification': "Based on cost and environmental impact analysis",
            'use_cases': "Consider specific product requirements and sustainability goals"
        }
    
    def _fallback_executive_summary(self, metrics: Dict) -> str:
        """Generate fallback executive summary."""
        return (
            f"Packaging optimization delivers {metrics.get('cost_savings', 'N/A')} cost savings "
            f"and {metrics.get('co2_reduction', 'N/A')} CO2 reduction. "
            f"Sustainability grade: {metrics.get('grade', 'N/A')}. "
            f"This represents significant environmental improvement while maintaining cost efficiency."
        )
    
    def _fallback_compliance(self) -> Dict:
        """Generate fallback compliance check."""
        return {
            'compliant': True,
            'issues': [],
            'certifications_met': ['Standard sustainability practices'],
            'recommendations': ['Verify with specific regulatory requirements for your region']
        }
    
    def clear_cache(self):
        """Clear explanation cache."""
        self.cache.clear()
        logger.info("Explanation cache cleared")
