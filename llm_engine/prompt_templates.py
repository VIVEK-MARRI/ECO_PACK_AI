"""
Prompt Template Engine
Manages structured prompts for LLM generation
"""

from typing import Dict, Any, Optional
import json
import structlog

logger = structlog.get_logger(__name__)


class PromptTemplateEngine:
    """
    Template engine for generating LLM prompts.
    Provides structured templates for different explanation types.
    """
    
    SUSTAINABILITY_EXPLANATION_TEMPLATE = """
You are a sustainability and packaging expert. Analyze the following packaging decision and provide a comprehensive explanation.

Product Details:
- Category: {category}
- Weight: {weight} kg
- Dimensions: {dimensions}
- Fragility: {fragility}
- Special Requirements: {special_requirements}

Selected Packaging:
- Material: {material}
- Cost: ${cost:.2f}
- CO2 Emissions: {co2:.2f} kg
- Recyclability: {recyclability}%
- Biodegradability: {biodegradability}%
- Damage Probability: {damage_prob}%

Alternative Options Considered:
{alternatives}

Context:
- User Preferences: {preferences}
- Optimization Objective: {objective}

Provide a detailed explanation covering:
1. **Reasoning**: Why this packaging was recommended
2. **Environmental Impact**: Analysis of sustainability metrics
3. **Tradeoffs**: Cost vs environmental vs performance balance
4. **Compliance**: Relevant standards and certifications
5. **Score Explanation**: How the sustainability score was calculated

Respond in JSON format with these exact keys: reasoning, impact, tradeoffs, compliance, score_explanation
"""
    
    COMPARISON_TEMPLATE = """
You are comparing two packaging options. Provide a clear, data-driven comparison.

Option A:
- Material: {material_a}
- Cost: ${cost_a}
- CO2: {co2_a} kg
- Recyclability: {recyclability_a}%
- Damage Risk: {damage_a}%

Option B:
- Material: {material_b}
- Cost: ${cost_b}
- CO2: {co2_b} kg
- Recyclability: {recyclability_b}%
- Damage Risk: {damage_b}%

Product: {product_description}

Compare these options and recommend the better choice. Explain the key differences and justify your recommendation.

Respond in JSON format with keys: recommendation, key_differences, justification, use_cases
"""
    
    EXECUTIVE_SUMMARY_TEMPLATE = """
Generate a concise executive summary for the following packaging decision.

Decision: {decision}
Key Metrics:
- Cost Savings: {cost_savings}
- CO2 Reduction: {co2_reduction}
- Sustainability Grade: {grade}

Provide a 3-5 sentence executive summary suitable for C-level presentation.
Focus on business impact and sustainability improvements.
"""
    
    COMPLIANCE_CHECK_TEMPLATE = """
Review this packaging for compliance with sustainability standards.

Packaging Details:
- Material: {material}
- CO2 Emissions: {co2} kg
- Recyclability: {recyclability}%
- Toxic Substances: {toxicity_info}
- Manufacturing Location: {location}

Check compliance with:
- ISO 14001 (Environmental Management)
- FSC Certification (if applicable)
- FDA Food Contact (if applicable)
- EU Packaging Directive
- Local Regulations: {local_regulations}

Provide compliance assessment in JSON format with keys: compliant, issues, certifications_met, recommendations
"""
    
    def __init__(self):
        """Initialize prompt template engine."""
        logger.info("PromptTemplateEngine initialized")
    
    def generate_sustainability_prompt(
        self,
        product_data: Dict[str, Any],
        packaging_data: Dict[str, Any],
        alternatives: list[Dict],
        preferences: Optional[Dict] = None
    ) -> str:
        """
        Generate sustainability explanation prompt.
        
        Args:
            product_data: Product information
            packaging_data: Selected packaging details
            alternatives: Alternative options considered
            preferences: User preferences
        
        Returns:
            Formatted prompt
        """
        # Format alternatives
        alternatives_text = "\n".join([
            f"- {alt['material']}: Cost=${alt['cost']}, CO2={alt['co2']}kg, "
            f"Recyclability={alt['recyclability']}%"
            for alt in alternatives[:3]  # Top 3
        ])
        
        # Format dimensions
        dimensions = f"{product_data.get('length', 0)}x{product_data.get('width', 0)}x{product_data.get('height', 0)} cm"
        
        preferences_str = json.dumps(preferences) if preferences else "None specified"
        objective = preferences.get('optimization_objective', 'Balanced') if preferences else 'Balanced'
        
        prompt = self.SUSTAINABILITY_EXPLANATION_TEMPLATE.format(
            category=product_data.get('category', 'General'),
            weight=product_data.get('weight', 0),
            dimensions=dimensions,
            fragility=product_data.get('fragility', 'Medium'),
            special_requirements=product_data.get('special_requirements', 'None'),
            material=packaging_data.get('material', 'Unknown'),
            cost=packaging_data.get('cost', 0),
            co2=packaging_data.get('co2', 0),
            recyclability=packaging_data.get('recyclability', 0),
            biodegradability=packaging_data.get('biodegradability', 0),
            damage_prob=packaging_data.get('damage_prob', 0),
            alternatives=alternatives_text,
            preferences=preferences_str,
            objective=objective
        )
        
        return prompt
    
    def generate_comparison_prompt(
        self,
        option_a: Dict,
        option_b: Dict,
        product_description: str
    ) -> str:
        """Generate comparison prompt."""
        prompt = self.COMPARISON_TEMPLATE.format(
            material_a=option_a['material'],
            cost_a=option_a['cost'],
            co2_a=option_a['co2'],
            recyclability_a=option_a['recyclability'],
            damage_a=option_a['damage_prob'],
            material_b=option_b['material'],
            cost_b=option_b['cost'],
            co2_b=option_b['co2'],
            recyclability_b=option_b['recyclability'],
            damage_b=option_b['damage_prob'],
            product_description=product_description
        )
        
        return prompt
    
    def generate_executive_summary_prompt(
        self,
        decision: str,
        metrics: Dict
    ) -> str:
        """Generate executive summary prompt."""
        prompt = self.EXECUTIVE_SUMMARY_TEMPLATE.format(
            decision=decision,
            cost_savings=metrics.get('cost_savings', 'N/A'),
            co2_reduction=metrics.get('co2_reduction', 'N/A'),
            grade=metrics.get('grade', 'N/A')
        )
        
        return prompt
    
    def generate_compliance_prompt(
        self,
        packaging_data: Dict,
        location: str = "Global"
    ) -> str:
        """Generate compliance check prompt."""
        prompt = self.COMPLIANCE_CHECK_TEMPLATE.format(
            material=packaging_data.get('material', 'Unknown'),
            co2=packaging_data.get('co2', 0),
            recyclability=packaging_data.get('recyclability', 0),
            toxicity_info=packaging_data.get('toxicity_info', 'No data'),
            location=packaging_data.get('manufacturing_location', 'Unknown'),
            local_regulations=location
        )
        
        return prompt
