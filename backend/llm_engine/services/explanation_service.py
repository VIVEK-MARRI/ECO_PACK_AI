import os
import time
import logging
from ..providers.gemini_provider import GeminiProvider
from ..services.cache_service import CacheService
from ..services.fallback_service import FallbackService
from ..models.llm_response_models import (
    SustainabilityExplanation,
    ExecutiveSummary,
    ComplianceAnalysis,
    AlternativeAnalysis
)

logger = logging.getLogger(__name__)

class ExplanationService:
    def __init__(self):
        # We can fallback to gemini-1.5-flash for speed or keep pro for quality
        self.provider = GeminiProvider(model_name="gemini-1.5-flash")
        self.cache = CacheService()
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
    def _read_prompt(self, filename: str) -> str:
        path = os.path.join(self.base_dir, "prompts", filename)
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def explain_sustainability(self, category, weight, fragility, recommended_material, current_material, suitability_score, eco_score) -> dict:
        prompt_template = self._read_prompt("sustainability_prompt.txt")
        prompt = prompt_template.format(
            category=category,
            weight=weight,
            fragility=fragility,
            recommended_material=recommended_material,
            current_material=current_material or "None",
            suitability_score=suitability_score,
            eco_score=eco_score
        )
        
        cached = self.cache.get(prompt, self.provider.model_name)
        if cached:
            return cached

        try:
            parsed = self.provider.generate_structured(prompt, SustainabilityExplanation)
            result = parsed.model_dump()
            self.cache.set(prompt, self.provider.model_name, result)
            return result
        except Exception as e:
            logger.error(f"Gemini API Error in explain_sustainability: {e}")
            return FallbackService.get_sustainability_fallback(recommended_material, category)

    def generate_executive_summary(self, category, recommended_material, current_material, co2_savings, cost_savings) -> dict:
        prompt_template = self._read_prompt("executive_summary_prompt.txt")
        prompt = prompt_template.format(
            category=category,
            recommended_material=recommended_material,
            current_material=current_material or "None",
            co2_savings=co2_savings,
            cost_savings=cost_savings
        )
        
        cached = self.cache.get(prompt, self.provider.model_name)
        if cached:
            return cached

        try:
            parsed = self.provider.generate_structured(prompt, ExecutiveSummary)
            result = parsed.model_dump()
            self.cache.set(prompt, self.provider.model_name, result)
            return result
        except Exception as e:
            logger.error(f"Gemini API Error in generate_executive_summary: {e}")
            return FallbackService.get_executive_summary_fallback(recommended_material, co2_savings)

    def analyze_compliance(self, category, recommended_material) -> dict:
        prompt_template = self._read_prompt("compliance_prompt.txt")
        prompt = prompt_template.format(
            category=category,
            recommended_material=recommended_material
        )
        
        cached = self.cache.get(prompt, self.provider.model_name)
        if cached:
            return cached

        try:
            parsed = self.provider.generate_structured(prompt, ComplianceAnalysis)
            result = parsed.model_dump()
            self.cache.set(prompt, self.provider.model_name, result)
            return result
        except Exception as e:
            logger.error(f"Gemini API Error in analyze_compliance: {e}")
            return FallbackService.get_compliance_fallback(recommended_material)

    def analyze_alternatives(self, category, weight, alternatives) -> dict:
        prompt_template = self._read_prompt("alternative_analysis_prompt.txt")
        prompt = prompt_template.format(
            category=category,
            weight=weight,
            alternatives=", ".join(alternatives)
        )
        
        cached = self.cache.get(prompt, self.provider.model_name)
        if cached:
            return cached

        try:
            parsed = self.provider.generate_structured(prompt, AlternativeAnalysis)
            result = parsed.model_dump()
            self.cache.set(prompt, self.provider.model_name, result)
            return result
        except Exception as e:
            logger.error(f"Gemini API Error in analyze_alternatives: {e}")
            return FallbackService.get_alternative_analysis_fallback(alternatives)
