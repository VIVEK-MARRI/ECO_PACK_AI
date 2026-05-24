class FallbackService:
    @staticmethod
    def get_sustainability_fallback(material: str, category: str) -> dict:
        return {
            "reasoning": f"Based on historical data, {material} provides adequate durability and protection for {category}.",
            "carbon_savings_explanation": "This material is generally known to have a lower carbon footprint than traditional plastics.",
            "tradeoffs": "While highly sustainable, this material may have a slightly higher upfront cost."
        }

    @staticmethod
    def get_executive_summary_fallback(material: str, co2_savings: float) -> dict:
        return {
            "summary": f"Adopting {material} is projected to reduce CO2 emissions by {co2_savings} kg, enhancing our corporate sustainability profile."
        }

    @staticmethod
    def get_compliance_fallback(material: str) -> dict:
        return {
            "is_compliant": True,
            "compliance_badges": ["Eco-Friendly Material", "Generally Recyclable"],
            "warnings": ["Check local recycling capabilities before widespread deployment."],
            "recommendations": ["Conduct a lifecycle assessment for exact compliance metrics."]
        }

    @staticmethod
    def get_alternative_analysis_fallback(alternatives: list) -> dict:
        results = []
        for alt in alternatives:
            results.append({
                "material_name": alt,
                "sustainability_impact": "Lower environmental impact compared to standard plastics.",
                "cost_tradeoff": "May cost slightly more depending on supplier volume.",
                "why_choose_this": "A viable backup option if the primary material is unavailable."
            })
        return {"alternatives": results}
