from pydantic import BaseModel, Field
from typing import List, Optional

class SustainabilityExplanation(BaseModel):
    reasoning: str = Field(description="A deep explanation of why this material fits the product's fragility and category.")
    carbon_savings_explanation: str = Field(description="A brief analysis of how it impacts the carbon footprint compared to standard alternatives.")
    tradeoffs: str = Field(description="What are the trade-offs (e.g., cost vs. durability) of this material?")

class ExecutiveSummary(BaseModel):
    summary: str = Field(description="A 1-2 sentence executive summary of the packaging optimization.")

class ComplianceWarning(BaseModel):
    warning: str

class ComplianceRecommendation(BaseModel):
    recommendation: str

class ComplianceAnalysis(BaseModel):
    is_compliant: bool = Field(description="Whether the material generally complies with global sustainability standards.")
    compliance_badges: List[str] = Field(description="List of applicable badges or certifications. Maximum 3.")
    warnings: List[str] = Field(description="List of potential compliance warnings or end-of-life disposal issues.")
    recommendations: List[str] = Field(description="Actionable compliance recommendations.")

class AlternativeAnalysisItem(BaseModel):
    material_name: str
    sustainability_impact: str
    cost_tradeoff: str
    why_choose_this: str

class AlternativeAnalysis(BaseModel):
    alternatives: List[AlternativeAnalysisItem]
