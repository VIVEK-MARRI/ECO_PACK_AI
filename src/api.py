"""
Flask REST API for ECO_PACK_AI
Simple practical implementation with PostgreSQL
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import joblib
import os
import json
from datetime import datetime
from functools import wraps
from dotenv import load_dotenv

# Base directory (project root)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(BASE_DIR, '.env')

# Load environment variables from .env file (override=True forces override of existing vars)
load_dotenv(env_path, override=True)

# Debug: Read .env file directly
print(f"DEBUG: Reading .env directly from {env_path}")
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        content = f.read()
    print(f"DEBUG: .env content preview:")
    for line in content.split('\n'):
        if 'DB_PASSWORD' in line:
            print(f"  {line}")

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
    'database': os.getenv('DB_NAME', 'ecopackai'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'password')
}

print(f"DEBUG: Loaded DB_PASSWORD = '{os.getenv('DB_PASSWORD')}'")
print(f"DEBUG: DB_CONFIG = {DB_CONFIG}")

# Models
try:
    rf_model = joblib.load(os.path.join(BASE_DIR, 'models', 'rf_cost_model.pkl'))
    xgb_model = joblib.load(os.path.join(BASE_DIR, 'models', 'xgb_co2_model.pkl'))
    print("✓ Models loaded")
except Exception as e:
    print(f"⚠ Models not loaded - predictions disabled: {e}")
    rf_model = xgb_model = None

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
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'models': 'loaded' if rf_model and xgb_model else 'not loaded'
    }), 200

@app.route('/api/product/input', methods=['POST'])
@require_api_key
@json_response
def product_input():
    """Handle product input and store in DB"""
    data = request.get_json()
    
    # Validate
    if not data.get('product_id'):
        return jsonify({'error': 'product_id required'}), 400
    
    product_id = data['product_id']
    category = data.get('category', 'general')
    weight = float(data.get('weight', 0))
    strength = float(data.get('strength', 50))
    biodegradability = float(data.get('biodegradability', 0.5))
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
    """AI material recommendation"""
    data = request.get_json()
    
    if not data.get('product_id'):
        return jsonify({'error': 'product_id required'}), 400
    
    product_id = data['product_id']
    
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
        
        # Material recommendations based on properties
        materials = {
            'bamboo': {'recyclability': 0.85, 'biodegradability': 0.98},
            'paper': {'recyclability': 0.90, 'biodegradability': 0.95},
            'metal': {'recyclability': 0.95, 'biodegradability': 0.0},
            'plastic': {'recyclability': 0.40, 'biodegradability': 0.1},
            'glass': {'recyclability': 0.90, 'biodegradability': 0.0},
            'jute': {'recyclability': 0.88, 'biodegradability': 0.99}
        }
        
        # Score materials (eco-focused)
        scores = {}
        for material, props in materials.items():
            score = (props['biodegradability'] * 0.6 + props['recyclability'] * 0.4)
            scores[material] = score
        
        # Sort and get top 3
        sorted_materials = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        recommendations = [
            {'material': m[0], 'score': round(m[1], 2)} 
            for m in sorted_materials[:3]
        ]
        
        return jsonify({
            'status': 'success',
            'product_id': product_id,
            'recommendations': recommendations,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    
    finally:
        cursor.close()
        conn.close()

@app.route('/api/score/environmental', methods=['POST'])
@require_api_key
@json_response
def environmental_score():
    """Calculate environmental score"""
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
        
        # Material eco-scores
        eco_data = {
            'bamboo': {'co2': 0.2, 'bio': 0.98, 'recycle': 0.85},
            'paper': {'co2': 0.3, 'bio': 0.95, 'recycle': 0.90},
            'jute': {'co2': 0.25, 'bio': 0.99, 'recycle': 0.88},
            'glass': {'co2': 0.5, 'bio': 0.0, 'recycle': 0.90},
            'metal': {'co2': 0.6, 'bio': 0.0, 'recycle': 0.95},
            'plastic': {'co2': 0.7, 'bio': 0.1, 'recycle': 0.4}
        }
        
        mat_eco = eco_data.get(material, eco_data['paper'])
        
        # Calculate overall score (0-100)
        overall = (
            (1 - mat_eco['co2']) * 40 +
            mat_eco['bio'] * 30 +
            mat_eco['recycle'] * 30
        )
        
        # Rating
        if overall >= 75:
            rating = 'Excellent ✓'
        elif overall >= 60:
            rating = 'Good ✓'
        elif overall >= 45:
            rating = 'Fair ⚠'
        else:
            rating = 'Poor ✗'
        
        # Store recommendation
        cursor.execute("""
            INSERT INTO recommendations (product_id, material, eco_score)
            VALUES (%s, %s, %s)
        """, (product_id, material, overall))
        conn.commit()
        
        return jsonify({
            'status': 'success',
            'product_id': product_id,
            'material': material,
            'overall_score': round(overall, 2),
            'rating': rating,
            'co2_intensity': mat_eco['co2'],
            'biodegradability': mat_eco['bio'],
            'recyclability': mat_eco['recycle'],
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
    print(f"\nRunning on http://localhost:{port}")
    print("="*50 + "\n")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
