"""
Carbon Calculator - Alias module for CarbonAccountingEngine
Provides backward compatibility with validation scripts
"""

from .carbon_engine import CarbonAccountingEngine

# Export for use
CarbonCalculator = CarbonAccountingEngine

__all__ = ['CarbonCalculator']
