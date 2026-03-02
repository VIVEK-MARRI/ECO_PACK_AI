"""
Flask REST API for ECO_PACK_AI
Simple practical implementation with PostgreSQL
"""

import sys
import os

# Configure UTF-8 encoding for Windows console
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach())

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import joblib
from datetime import datetime
from functools import wraps
from dotenv import load_dotenv
from src.recommendation import RecommendationEngine
from src.preprocessing import validate_product_input

# Import industrial recommendation engine (new)
try:
    from src.recommendation_engine_industrial import (
        IndustrialRecommendationEngine,
        UserPreferences
    )
    print("✓ Industrial recommendation engine available")
    INDUSTRIAL_ENGINE_AVAILABLE = True
except ImportError as e:
    print(f"⚠ Industrial recommendation engine not available: {e}")
    IndustrialRecommendationEngine = None
    UserPreferences = None
    INDUSTRIAL_ENGINE_AVAILABLE = False

# Base directory (project root)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(BASE_DIR, '.env')

# Load environment variables from .env file (override=True forces override of existing vars)
load_dotenv(env_path, override=True)

# ============================================================================
# CONFIGURATION
# ============================================================================

app = Flask(__name__)
CORS(app)

# API Key for security
API_KEY = os.getenv('API_KEY', 'your-secret-key-change-this')

# PostgreSQL Config
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'ecopack'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'password')
}

# Initialize ML Recommendation Engine (Legacy)
try:
    recommendation_engine = RecommendationEngine(DB_CONFIG)
    print("✓ ML Recommendation Engine initialized (legacy)")
except Exception as e:
    print(f"⚠ Recommendation Engine initialization error: {e}")
    recommendation_engine = None

# Initialize Industrial Recommendation Engine (New)
industrial_engine = None
if INDUSTRIAL_ENGINE_AVAILABLE:
    try:
        industrial_engine = IndustrialRecommendationEngine(DB_CONFIG)
        print("✓ Industrial Recommendation Engine initialized")
    except Exception as e:
        print(f"⚠ Industrial Engine initialization error: {e}")
        industrial_engine = None

# ============================================================================
# DATABASE HELPERS
# ============================================================================

def get_db():
    """Get database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"DB Error: {e}")
        return None

def init_db():
    """Create tables if they don't exist"""
    conn = get_db()
    if not conn:
        print("Cannot initialize DB")
        return
    
    cursor = conn.cursor()
    
    # Products table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id SERIAL PRIMARY KEY,
        product_id VARCHAR(100) UNIQUE,
        category VARCHAR(50),
        weight FLOAT,
        strength FLOAT,
        biodegradability FLOAT,
        recyclability FLOAT,
        created_at TIMESTAMP DEFAULT NOW()
    )
    """)
    
    # Recommendations table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recommendations (
        id SERIAL PRIMARY KEY,
        product_id VARCHAR(100),
        material VARCHAR(50),
        cost_score FLOAT,
        co2_score FLOAT,
        eco_score FLOAT,
        created_at TIMESTAMP DEFAULT NOW(),
        FOREIGN KEY (product_id) REFERENCES products(product_id)
    )
    """)
    
    conn.commit()
    cursor.close()
    conn.close()
    print("✓ Database initialized")

# ============================================================================
# DECORATORS
# ============================================================================

def require_api_key(f):
    """Check API key"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        key = request.headers.get('X-API-Key')
        if key != API_KEY:
            return jsonify({'error': 'Invalid API key'}), 401
        return f(*args, **kwargs)
    return decorated_function

def json_response(f):
    """Wrap response in standard format"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            result = f(*args, **kwargs)
            return result
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    return decorated_function

# ============================================================================
# ENDPOINTS
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health():
    """Health check"""
    models_loaded = 'loaded' if recommendation_engine else 'not loaded'
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'models': models_loaded
    }), 200

@app.route('/api/product/input', methods=['POST'])
@require_api_key
@json_response
def product_input():
    """Handle product input and store in DB with validation"""
    data = request.get_json()
    
    # Validate input
    is_valid, error_msg = validate_product_input(data)
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    product_id = data['product_id']
    category = data.get('category', 'general')
    weight = float(data.get('weight', 0))
    strength = float(data.get('strength', 50))
    biodegradability = float(data.get('biodegradability', 50)) / 100  # Normalize to 0-1
    recyclability = float(data.get('recyclability', 50))
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO products 
            (product_id, category, weight, strength, biodegradability, recyclability)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (product_id) DO UPDATE SET
            category=%s, weight=%s, strength=%s, biodegradability=%s, recyclability=%s
        """, (product_id, category, weight, strength, biodegradability, recyclability,
              category, weight, strength, biodegradability, recyclability))
        
        conn.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Product stored',
            'product_id': product_id
        }), 201
    
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 400
    
    finally:
        cursor.close()
        conn.close()

@app.route('/api/recommend/material', methods=['POST'])
@require_api_key
@json_response
def recommend_material():
    """ML-powered material recommendation"""
    data = request.get_json()
    
    if not data.get('product_id'):
        return jsonify({'error': 'product_id required'}), 400
    
    product_id = data['product_id']

    fallback_recommendations = [
        {
            'material': 'bamboo',
            'eco_score': 93,
            'co2_impact': 0.20,
            'cost_efficiency': 0.85,
            'recyclability': 85,
            'biodegradability': 0.98,
            'cost_per_unit': 0.30,
            'strength': 78,
            'suitability': 0.86
        },
        {
            'material': 'paper',
            'eco_score': 90,
            'co2_impact': 0.30,
            'cost_efficiency': 0.72,
            'recyclability': 90,
            'biodegradability': 0.95,
            'cost_per_unit': 0.22,
            'strength': 50,
            'suitability': 0.78
        },
        {
            'material': 'jute',
            'eco_score': 92,
            'co2_impact': 0.25,
            'cost_efficiency': 0.68,
            'recyclability': 88,
            'biodegradability': 0.99,
            'cost_per_unit': 0.40,
            'strength': 80,
            'suitability': 0.84
        },
        {
            'material': 'glass',
            'eco_score': 80,
            'co2_impact': 0.50,
            'cost_efficiency': 0.45,
            'recyclability': 90,
            'biodegradability': 0.0,
            'cost_per_unit': 1.10,
            'strength': 85,
            'suitability': 0.60
        },
        {
            'material': 'metal',
            'eco_score': 78,
            'co2_impact': 0.60,
            'cost_efficiency': 0.40,
            'recyclability': 95,
            'biodegradability': 0.0,
            'cost_per_unit': 1.40,
            'strength': 90,
            'suitability': 0.58
        },
        {
            'material': 'plastic',
            'eco_score': 45,
            'co2_impact': 0.70,
            'cost_efficiency': 0.55,
            'recyclability': 40,
            'biodegradability': 0.10,
            'cost_per_unit': 0.35,
            'strength': 60,
            'suitability': 0.42
        }
    ]
    
    # Get product from DB
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cursor.execute("SELECT * FROM products WHERE product_id = %s", (product_id,))
        product = cursor.fetchone()
        
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        # Convert product to dict
        product_data = dict(product)
        
        # Get ML-powered recommendations
        if recommendation_engine:
            recommendations = recommendation_engine.get_recommendations(product_data, top_n=6)
            if not recommendations:
                recommendations = fallback_recommendations
        else:
            # Fallback to simple heuristic
            recommendations = fallback_recommendations
        
        return jsonify({
            'status': 'success',
            'product_id': product_id,
            'recommendations': recommendations,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    
    finally:
        cursor.close()
        conn.close()


@app.route('/api/recommend/industrial', methods=['POST'])
@require_api_key
@json_response
def recommend_material_industrial():
    """
    Industrial-grade multi-objective material recommendation
    
    Request body:
    {
        "product_id": "PRODUCT_001",
        "preferences": {
            "cost_weight": 0.33,
            "co2_weight": 0.33,
            "risk_weight": 0.34,
            "max_budget": null,
            "max_damage_risk": 0.8,
            "min_sustainability": 0.3,
            "max_co2_emission": null,
            "min_recyclability": 0.0
        },
        "top_n": 5
    }
    
    Returns:
    {
        "status": "success",
        "product_id": "PRODUCT_001",
        "recommendations": [
            {
                "rank": 1,
                "material": "bamboo",
                "cost": 1.23,
                "co2": 2.45,
                "damage_risk": 0.15,
                "sustainability_score": 0.85,
                "pareto_rank": 0,
                "weighted_score": 0.234,
                "tradeoff_summary": "Low cost, Low CO₂, Low risk",
                "why_selected": "Best overall balance...",
                "pros": ["Highly cost-effective", "Low carbon footprint"],
                "cons": ["Trade-offs with specific attributes"]
            },
            ...
        ],
        "engine": "industrial",
        "preferences_applied": {...},
        "timestamp": "2024-03-02T..."
    }
    """
    data = request.get_json()
    
    if not data.get('product_id'):
        return jsonify({'error': 'product_id required'}), 400
    
    product_id = data['product_id']
    
    # Check if industrial engine is available
    if not industrial_engine:
        return jsonify({
            'error': 'Industrial recommendation engine not available',
            'fallback': 'Use /api/recommend/material for legacy recommendations'
        }), 503
    
    # Get product from DB
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cursor.execute("SELECT * FROM products WHERE product_id = %s", (product_id,))
        product = cursor.fetchone()
        
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        # Convert product to dict
        product_data = dict(product)
        
        # Parse user preferences
        preferences_data = data.get('preferences', {})
        preferences = UserPreferences(
            cost_weight=preferences_data.get('cost_weight', 0.33),
            co2_weight=preferences_data.get('co2_weight', 0.33),
            risk_weight=preferences_data.get('risk_weight', 0.34),
            max_budget=preferences_data.get('max_budget', None),
            max_damage_risk=preferences_data.get('max_damage_risk', 0.8),
            min_sustainability=preferences_data.get('min_sustainability', 0.3),
            max_co2_emission=preferences_data.get('max_co2_emission', None),
            min_recyclability=preferences_data.get('min_recyclability', 0.0)
        )
        
        # Get number of results
        top_n = data.get('top_n', 5)
        
        # Get industrial recommendations
        recommendations = industrial_engine.get_recommendations(
            product_data,
            preferences,
            top_n
        )
        
        if not recommendations:
            return jsonify({
                'error': 'No feasible recommendations found',
                'message': 'Try relaxing constraints (max_budget, max_damage_risk, etc.)'
            }), 404
        
        return jsonify({
            'status': 'success',
            'product_id': product_id,
            'recommendations': recommendations,
            'engine': 'industrial',
            'preferences_applied': {
                'cost_weight': preferences.cost_weight,
                'co2_weight': preferences.co2_weight,
                'risk_weight': preferences.risk_weight,
                'max_budget': preferences.max_budget,
                'max_damage_risk': preferences.max_damage_risk,
                'min_sustainability': preferences.min_sustainability,
                'max_co2_emission': preferences.max_co2_emission,
                'min_recyclability': preferences.min_recyclability
            },
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    
    except Exception as e:
        print(f"Industrial recommendation error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500
    
    finally:
        cursor.close()
        conn.close()

@app.route('/api/score/environmental', methods=['POST'])
@require_api_key
@json_response
def environmental_score():
    """ML-powered environmental score calculation"""
    data = request.get_json()
    
    if not data.get('product_id') or not data.get('material'):
        return jsonify({'error': 'product_id and material required'}), 400
    
    product_id = data['product_id']
    material = data['material'].lower()
    
    # Get product from DB
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cursor.execute("SELECT * FROM products WHERE product_id = %s", (product_id,))
        product = cursor.fetchone()
        
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        product_data = dict(product)
        
        # Get ML-powered analysis
        if recommendation_engine:
            analysis = recommendation_engine.get_detailed_analysis(product_data, material)
            if not analysis:
                return jsonify({'error': f'Material {material} not found'}), 404
            
            overall = analysis['eco_score']
            rating = analysis['rating']
            co2 = analysis['co2_impact']
            bio = analysis['biodegradability']
            recycle = analysis['recyclability']
            cost_eff = analysis['cost_efficiency']
            
        else:
            # Fallback heuristic
            eco_data = {
                'bamboo': {'co2': 0.2, 'bio': 0.98, 'recycle': 85},
                'paper': {'co2': 0.3, 'bio': 0.95, 'recycle': 90},
                'jute': {'co2': 0.25, 'bio': 0.99, 'recycle': 88},
                'glass': {'co2': 0.5, 'bio': 0.0, 'recycle': 90},
                'metal': {'co2': 0.6, 'bio': 0.0, 'recycle': 95},
                'plastic': {'co2': 0.7, 'bio': 0.1, 'recycle': 40}
            }
            
            mat_eco = eco_data.get(material, eco_data['paper'])
            overall = (1 - mat_eco['co2']) * 40 + mat_eco['bio'] * 30 + mat_eco['recycle'] * 0.3
            rating = 'Excellent ✓' if overall >= 75 else 'Good ✓' if overall >= 60 else 'Fair ⚠'
            co2 = mat_eco['co2']
            bio = mat_eco['bio']
            recycle = mat_eco['recycle']
            cost_eff = 0.5
        
        # Store recommendation
        cursor.execute("""
            INSERT INTO recommendations (product_id, material, eco_score, co2_score, cost_score)
            VALUES (%s, %s, %s, %s, %s)
        """, (product_id, material, overall, co2, cost_eff))
        conn.commit()
        
        return jsonify({
            'status': 'success',
            'product_id': product_id,
            'material': material,
            'overall_score': round(overall, 2),
            'rating': rating,
            'co2_intensity': round(co2, 3),
            'biodegradability': round(bio, 3) if isinstance(bio, float) else bio,
            'recyclability': round(recycle, 2),
            'cost_efficiency': round(cost_eff, 3),
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    
    finally:
        cursor.close()
        conn.close()

@app.route('/api/history/<product_id>', methods=['GET'])
@require_api_key
@json_response
def get_history(product_id):
    """Get recommendation history for a product"""
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cursor.execute("""
            SELECT * FROM recommendations 
            WHERE product_id = %s 
            ORDER BY created_at DESC 
            LIMIT 10
        """, (product_id,))
        
        history = cursor.fetchall()
        
        return jsonify({
            'status': 'success',
            'product_id': product_id,
            'history': history if history else [],
            'count': len(history) if history else 0
        }), 200
    
    finally:
        cursor.close()
        conn.close()

@app.route('/api/history/all', methods=['GET'])
@require_api_key
@json_response
def get_all_history():
    """Get all products and their recommendations"""
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Get all products
        cursor.execute("SELECT * FROM products ORDER BY created_at DESC")
        products = cursor.fetchall()
        
        # Convert to frontend-compatible format
        history = []
        for product in products:
            history.append({
                'id': product['id'],
                'productName': product['product_id'],
                'category': product['category'],
                'weight': product['weight'],
                'strength': product['strength'],
                'recyclability': product['recyclability'],
                'createdAt': product['created_at'].isoformat() if product['created_at'] else None
            })
        
        return jsonify({
            'status': 'success',
            'history': history,
            'count': len(history)
        }), 200
    
    finally:
        cursor.close()
        conn.close()

# Error handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({'error': 'Method not allowed'}), 405

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*50)
    print("ECO_PACK_AI Flask API")
    print("="*50)
    
    # Initialize DB
    init_db()
    
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'False') == 'True'
    
    print(f"\nEndpoints:")
    print(f"  GET  /api/health")
    print(f"  POST /api/product/input")
    print(f"  POST /api/recommend/material")
    print(f"  POST /api/score/environmental")
    print(f"  GET  /api/history/<product_id>")
    print(f"  GET  /api/history/all")
    print(f"\nRunning on http://localhost:{port}")
    print("="*50 + "\n")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
