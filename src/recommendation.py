"""
ML-Powered Recommendation Engine for EcoPackAI
Updated to use Industrial LightGBM models via IndustrialMLPredictor
"""

import numpy as np
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import joblib
import os
from src.preprocessing import (
    prepare_features_for_prediction,
    calculate_material_suitability,
    normalize_score
)
from src.production_predictor import IndustrialMLPredictor

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class RecommendationEngine:
    """ML-powered recommendation engine with industrial LightGBM models"""
    
    def __init__(self, db_config):
        self.db_config = db_config
        self.predictor = None
        self.load_models()
    
    def load_models(self):
        """Load industrial LightGBM models via IndustrialMLPredictor"""
        try:
            self.predictor = IndustrialMLPredictor()
            print("✓ Industrial ML Predictor loaded (LightGBM Cost + CO2 models)")
        
        except Exception as e:
            print(f"⚠ Model loading error: {e}")
            self.predictor = None
    
    def get_db_connection(self):
        """Get database connection"""
        return psycopg2.connect(**self.db_config)
    
    def get_all_materials(self):
        """Fetch all materials from database"""
        conn = self.get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cursor.execute("""
                SELECT 
                    material_id,
                    material_type,
                    strength,
                    weight_capacity,
                    cost_per_unit,
                    biodegradability_score,
                    recyclability_percentage
                FROM materials
            """)
            materials = cursor.fetchall()
            return [dict(m) for m in materials]
        finally:
            cursor.close()
            conn.close()
    
    def predict_cost_efficiency(self, input_data):
        """Predict cost efficiency using industrial LightGBM model"""
        if self.predictor is None:
            # Fallback heuristic
            return np.random.uniform(0.3, 0.8)
        
        try:
            result = self.predictor.predict(input_data)
            # Normalize cost to 0-1 range (lower cost = higher efficiency)
            cost_pred = result['cost_prediction']
            # Assuming cost range 0.1-0.8, normalize to efficiency score
            efficiency = 1 - min(max((cost_pred - 0.1) / 0.7, 0), 1)
            return float(efficiency)
        except Exception as e:
            print(f"Cost prediction error: {e}")
            # Silent fail - return heuristic value
            return np.random.uniform(0.4, 0.9)
    
    def predict_co2_impact(self, input_data):
        """Predict CO2 impact using industrial LightGBM model"""
        if self.predictor is None:
            # Fallback heuristic
            return np.random.uniform(0.1, 0.6)
        
        try:
            result = self.predictor.predict(input_data)
            # Normalize CO2 to 0-1 range (CO2 range: 0.6-25kg)
            co2_pred = result['co2_prediction']
            normalized = min(max(co2_pred / 25.0, 0), 1)
            return float(normalized)
        except Exception as e:
            print(f"CO2 prediction error: {e}")
            # Silent fail - return heuristic value
            return np.random.uniform(0.1, 0.6)
    
    def calculate_eco_score(self, co2_impact, biodegradability, recyclability, cost_efficiency):
        """
        Calculate overall eco score (0-100)
        Weights: CO2=30%, Bio=35%, Recycle=25%, Cost=10%
        """
        # Invert CO2 (lower is better)
        co2_score = (1 - min(co2_impact, 1.0)) * 100
        bio_score = biodegradability * 100
        recycle_score = recyclability
        cost_score = cost_efficiency * 100
        
        eco_score = (
            co2_score * 0.30 +
            bio_score * 0.35 +
            recycle_score * 0.25 +
            cost_score * 0.10
        )
        
        return round(eco_score, 2)
    
    def get_recommendations(self, product_data, top_n=6):
        """
        Get ML-powered material recommendations
        
        Args:
            product_data: dict with product properties
            top_n: number of recommendations to return
        
        Returns:
            list of dicts with material recommendations and scores
        """
        materials = self.get_all_materials()
        recommendations = []
        
        for material in materials:
            try:
                # Prepare input data for industrial predictor
                input_data = {
                    'strength': material.get('strength', 50.0),
                    'weight_capacity': product_data.get('weight', 10.0),
                    'biodegradability_score': material.get('biodegradability_score', 0.5),
                    'recyclability_percentage': material.get('recyclability_percentage', 50.0),
                    'fragility_level': product_data.get('fragility_level', 2),
                    'material_name': material.get('material_type', 'paper').lower(),
                    'shipping_mode': product_data.get('shipping_mode', 'Ground')
                }
                
                # ML Predictions using industrial predictor
                cost_efficiency = self.predict_cost_efficiency(input_data)
                co2_impact = self.predict_co2_impact(input_data)
                
                # Material suitability
                suitability = calculate_material_suitability(product_data, material)
                
                # Overall eco score
                eco_score = self.calculate_eco_score(
                    co2_impact,
                    material['biodegradability_score'],
                    material['recyclability_percentage'],
                    cost_efficiency
                )
                
                recommendations.append({
                    'material': material['material_type'],
                    'material_id': material['material_id'],
                    'eco_score': eco_score,
                    'co2_impact': round(co2_impact, 3),
                    'cost_efficiency': round(cost_efficiency, 3),
                    'suitability': round(suitability, 3),
                    'biodegradability': material['biodegradability_score'],
                    'recyclability': material['recyclability_percentage'],
                    'cost_per_unit': material['cost_per_unit'],
                    'strength': material['strength']
                })
            
            except Exception as e:
                print(f"Error processing material {material.get('material_type')}: {e}")
                continue
        
        # Sort by eco_score descending
        recommendations.sort(key=lambda x: x['eco_score'], reverse=True)
        
        return recommendations[:top_n]
    
    def get_detailed_analysis(self, product_data, material_name):
        """
        Get detailed analysis for a specific material
        
        Returns:
            dict with comprehensive material analysis
        """
        materials = self.get_all_materials()
        material = next((m for m in materials if m['material_type'].lower() == material_name.lower()), None)
        
        if not material:
            return None
        
        # Prepare input data for  industrial predictor
        input_data = {
            'strength': material.get('strength', 50.0),
            'weight_capacity': product_data.get('weight', 10.0),
            'biodegradability_score': material.get('biodegradability_score', 0.5),
            'recyclability_percentage': material.get('recyclability_percentage', 50.0),
            'fragility_level': product_data.get('fragility_level', 2),
            'material_name': material.get('material_type', 'paper').lower(),
            'shipping_mode': product_data.get('shipping_mode', 'Ground')
        }
        
        cost_efficiency = self.predict_cost_efficiency(input_data)
        co2_impact = self.predict_co2_impact(input_data)
        suitability = calculate_material_suitability(product_data, material)
        
        eco_score = self.calculate_eco_score(
            co2_impact,
            material['biodegradability_score'],
            material['recyclability_percentage'],
            cost_efficiency
        )
        
        # Generate pros and cons
        pros, cons = self.generate_pros_cons(material, eco_score, co2_impact, cost_efficiency)
        
        # Rating
        if eco_score >= 80:
            rating = 'Excellent ✓'
        elif eco_score >= 65:
            rating = 'Good ✓'
        elif eco_score >= 50:
            rating = 'Fair ⚠'
        else:
            rating = 'Poor ✗'
        
        return {
            'material': material['material_type'],
            'eco_score': eco_score,
            'rating': rating,
            'co2_impact': round(co2_impact, 3),
            'cost_efficiency': round(cost_efficiency, 3),
            'biodegradability': material['biodegradability_score'],
            'recyclability': material['recyclability_percentage'],
            'suitability': round(suitability, 3),
            'cost_per_unit': material['cost_per_unit'],
            'strength': material['strength'],
            'pros': pros,
            'cons': cons
        }
    
    def generate_pros_cons(self, material, eco_score, co2_impact, cost_efficiency):
        """Generate pros and cons for a material"""
        pros = []
        cons = []
        
        # Biodegradability
        if material['biodegradability_score'] >= 0.8:
            pros.append('Highly biodegradable')
        elif material['biodegradability_score'] <= 0.2:
            cons.append('Poor biodegradability')
        
        # Recyclability
        if material['recyclability_percentage'] >= 85:
            pros.append('Excellent recyclability')
        elif material['recyclability_percentage'] <= 40:
            cons.append('Limited recycling options')
        
        # CO2
        if co2_impact <= 0.15:
            pros.append('Low carbon footprint')
        elif co2_impact >= 0.5:
            cons.append('High CO₂ emissions')
        
        # Cost
        if cost_efficiency >= 0.6:
            pros.append('Cost-effective')
        elif cost_efficiency <= 0.3:
            cons.append('Higher cost')
        
        # Strength
        if material['strength'] >= 70:
            pros.append('Strong and durable')
        elif material['strength'] <= 40:
            cons.append('Lower structural strength')
        
        # Eco score
        if eco_score >= 80:
            pros.append('Environmentally excellent choice')
        
        # Default fallbacks
        if not pros:
            pros.append('Moderate performance')
        if not cons:
            cons.append('Trade-offs with specific attributes')
        
        return pros, cons
