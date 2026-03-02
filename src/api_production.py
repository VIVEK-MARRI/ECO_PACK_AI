"""
Production-ready Flask API for ECO_PACK_AI
Phase 2 - Industrial backend with real models and proper error handling
"""

import os
import sys
import uuid
import time
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

# Setup path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from src.logger import setup_logger
from src.model_loader import get_model_registry
from src.predictor import get_predictor
from src.feature_pipeline import FeaturePipeline
import psycopg2
from psycopg2.extras import RealDictCursor

# Load environment
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, '.env'), override=True)

# Logger
logger = setup_logger('api_server')

# Flask app
app = Flask(__name__)
CORS(app)

# Configuration
API_KEY = os.getenv('API_KEY', 'your-secret-key-change-this')
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'ecopack'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'password')
}

# Initialize services
model_registry = get_model_registry()
predictor = get_predictor()

logger.info("=" * 80)
logger.info("ECO_PACK_AI BACKEND - PRODUCTION MODE")
logger.info("=" * 80)
logger.info(f"API Key configured: {bool(API_KEY)}")
logger.info(f"Database: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
logger.info(f"Models loaded: {model_registry.get_status()['models']}")

# ============================================================================
# DATABASE HELPERS
# ============================================================================

def get_db():
    """Get database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}", exc_info=True)
        return None

def init_db():
    """Initialize database schema"""
    conn = get_db()
    if not conn:
        logger.error("Cannot initialize database")
        return False
    
    try:
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
            request_id VARCHAR(100),
            product_id VARCHAR(100),
            material VARCHAR(50),
            eco_score FLOAT,
            co2_impact FLOAT,
            cost_per_unit FLOAT,
            suitability FLOAT,
            model_reliability VARCHAR(20),
            latency_ms FLOAT,
            created_at TIMESTAMP DEFAULT NOW()
        )
        """)
        
        conn.commit()
        logger.info("✓ Database schema initialized")
        return True
    
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}", exc_info=True)
        return False
    
    finally:
        cursor.close()
        conn.close()

# Initialize DB on startup
init_db()

# ============================================================================
# MIDDLEWARE
# ============================================================================

@app.before_request
def log_request():
    """Log incoming request"""
    request.request_id = str(uuid.uuid4())
    request.start_time = time.time()
    logger.info(f"[{request.request_id}] {request.method} {request.path}")

@app.after_request
def log_response(response):
    """Log outgoing response"""
    latency = (time.time() - request.start_time) * 1000
    logger.info(
        f"[{request.request_id}] {response.status_code} (latency: {latency:.2f}ms)"
    )
    return response

def require_api_key(f):
    """Decorator to require API key"""
    def decorated_function(*args, **kwargs):
        key = request.headers.get('X-API-Key')
        if key != API_KEY:
            logger.warning(f"[{request.request_id}] Invalid API key")
            return jsonify({'error': 'Invalid API key', 'request_id': request.request_id}), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# ============================================================================
# ENDPOINTS - HEALTH & DIAGNOSTICS
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health():
    """Comprehensive health check"""
    models = model_registry.get_status()
    
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'components': {
            'database': 'connected' if get_db() else 'disconnected',
            'models': {
                'loaded': models['models'],
                'count': len(models['models'])
            },
            'predictor': {
                'metrics': predictor.get_metrics()
            }
        },
        'version': '2.0.0-production'
    }
    
    return jsonify(health_status), 200

@app.route('/api/diagnostics', methods=['GET'])
@require_api_key
def diagnostics():
    """Detailed system diagnostics"""
    return jsonify({
        'timestamp': datetime.utcnow().isoformat(),
        'models': model_registry.get_status(),
        'predictor_metrics': predictor.get_metrics(),
        'database_status': 'connected' if get_db() else 'disconnected'
    }), 200

# ============================================================================
# ENDPOINTS - PRODUCT MANAGEMENT
# ============================================================================

@app.route('/api/product/input', methods=['POST'])
@require_api_key
def product_input():
    """Store product in database"""
    try:
        data = request.get_json()
        
        # Validate input
        is_valid, msg = FeaturePipeline.validate_input(data)
        if not is_valid:
            logger.warning(f"[{request.request_id}] Validation failed: {msg}")
            return jsonify({'error': msg, 'request_id': request.request_id}), 400
        
        product_id = data.get('product_id', f"PROD-{request.request_id}")
        category = data.get('category', 'general')
        weight = float(data['weight'])
        strength = float(data['strength'])
        biodegradability = float(data['biodegradability']) / 100.0
        recyclability = float(data['recyclability'])
        
        conn = get_db()
        if not conn:
            return jsonify({
                'error': 'Database unavailable',
                'request_id': request.request_id
            }), 503
        
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
            
            logger.info(f"[{request.request_id}] Product stored: {product_id}")
            
            return jsonify({
                'status': 'success',
                'product_id': product_id,
                'request_id': request.request_id,
                'timestamp': datetime.utcnow().isoformat()
            }), 201
        
        finally:
            cursor.close()
            conn.close()
    
    except Exception as e:
        logger.error(f"[{request.request_id}] Product input failed: {str(e)}", exc_info=True)
        return jsonify({
            'error': str(e),
            'request_id': request.request_id
        }), 500

# ============================================================================
# ENDPOINTS - PREDICTIONS
# ============================================================================

@app.route('/api/recommend/material', methods=['POST'])
@require_api_key
def recommend_material():
    """Get real ML-powered material recommendations"""
    try:
        data = request.get_json()
        
        if not data.get('product_id'):
            return jsonify({
                'error': 'product_id required',
                'request_id': request.request_id
            }), 400
        
        product_id = data['product_id']
        
        # Get product from DB
        conn = get_db()
        if not conn:
            return jsonify({
                'error': 'Database unavailable',
                'request_id': request.request_id
            }), 503
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cursor.execute("SELECT * FROM products WHERE product_id = %s", (product_id,))
            product = cursor.fetchone()
        
        finally:
            cursor.close()
            conn.close()
        
        if not product:
            return jsonify({
                'error': 'Product not found',
                'request_id': request.request_id
            }), 404
        
        product_data = dict(product)
        materials = ['bamboo', 'paper', 'jute', 'glass', 'metal', 'plastic', 'bagasse']
        
        # Get predictions for all materials
        recommendations = []
        
        for material in materials:
            try:
                score = predictor.predict_material_score(
                    product_data, material, request.request_id
                )
                recommendations.append(score)
            except Exception as e:
                logger.error(
                    f"[{request.request_id}] Failed to predict for {material}: {str(e)}",
                    exc_info=True
                )
                continue
        
        # Sort by eco_score descending
        recommendations.sort(key=lambda x: x['eco_score'], reverse=True)
        
        logger.info(f"[{request.request_id}] Generated {len(recommendations)} recommendations")
        
        return jsonify({
            'status': 'success',
            'product_id': product_id,
            'recommendations': recommendations,
            'count': len(recommendations),
            'request_id': request.request_id,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    
    except Exception as e:
        logger.error(f"[{request.request_id}] Recommendation failed: {str(e)}", exc_info=True)
        return jsonify({
            'error': str(e),
            'request_id': request.request_id
        }), 500

@app.route('/api/predict', methods=['POST'])
@require_api_key
def predict():
    """Get prediction for material-product combination"""
    try:
        data = request.get_json()
        
        required = ['product_id', 'material']
        if not all(k in data for k in required):
            return jsonify({
                'error': f'Required fields: {required}',
                'request_id': request.request_id
            }), 400
        
        product_id = data['product_id']
        material = data['material']
        
        # Get product from DB
        conn = get_db()
        if not conn:
            return jsonify({'error': 'Database unavailable'}, 503)
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        try:
            cursor.execute("SELECT * FROM products WHERE product_id = %s", (product_id,))
            product = cursor.fetchone()
        finally:
            cursor.close()
            conn.close()
        
        if not product:
            return jsonify({'error': 'Product not found'}, 404)
        
        product_data = dict(product)
        
        # Get prediction
        score = predictor.predict_material_score(
            product_data, material, request.request_id
        )
        
        return jsonify({
            'status': 'success',
            'prediction': score,
            'request_id': request.request_id
        }), 200
    
    except Exception as e:
        logger.error(f"[{request.request_id}] Prediction failed: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}, 500)

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(e):
    """404 handler"""
    return jsonify({
        'error': 'Endpoint not found',
        'request_id': getattr(request, 'request_id', 'unknown')
    }), 404

@app.errorhandler(500)
def server_error(e):
    """500 handler"""
    logger.error(f"Server error: {str(e)}", exc_info=True)
    return jsonify({
        'error': 'Internal server error',
        'request_id': getattr(request, 'request_id', 'unknown')
    }), 500

# ============================================================================
# STARTUP
# ============================================================================

if __name__ == '__main__':
    logger.info("Starting ECO_PACK_AI backend server...")
    logger.info(f"Models loaded: {model_registry.get_status()['models']}")
    
    app.run(
        host=os.getenv('FLASK_HOST', 'localhost'),
        port=int(os.getenv('FLASK_PORT', 5000)),
        debug=os.getenv('FLASK_ENV', 'production') != 'production'
    )
