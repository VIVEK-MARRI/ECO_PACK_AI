"""
PRODUCTION DEPLOYMENT GUIDE - ECO_PACK_AI BACKEND
Phase 5: Industrial-Grade ML Backend Transformation

This guide walks through deploying the production backend and validating the system.

========================================================================================================
PREREQUISITES
========================================================================================================

1. PYTHON ENVIRONMENT
   ✓ Python 3.9+ installed
   ✓ Virtual environment activated (venv or conda)
   ✓ Dependencies installed: pip install -r requirements.txt

2. POSTGRESQL DATABASE
   ✓ PostgreSQL 12+ running
   ✓ Database created (ecopack)
   ✓ Credentials configured in .env file
   
   Test connection:
   psql -h localhost -U postgres -d ecopack -c "SELECT NOW();"

3. TRAINED MODELS
   ✓ rf_cost_model.pkl exists at models/rf_cost_model.pkl
   ✓ xgb_co2_model.pkl exists at models/xgb_co2_model.pkl
   ✓ feature_scaler.pkl exists at models/feature_scaler.pkl
   
   Models should be trained RF + XGBoost models pickled with joblib.
   See notebooks/05_rf_cost_model.ipynb and 06_xgb_co2_model.ipynb for training details.

4. CONFIGURATION FILE (.env)
   Create .env in project root with:
   ```
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=ecopack
   DB_USER=postgres
   DB_PASSWORD=your_password
   API_KEY=your-secret-api-key-change-this
   FLASK_HOST=localhost
   FLASK_PORT=5000
   FLASK_ENV=production
   ```

========================================================================================================
DEPLOYMENT STEPS
========================================================================================================

STEP 1: Verify Environment Setup
─────────────────────────────────────────────────────────────────────────────────────────────────────

$ python -c "import sys; print(f'Python: {sys.version}')"
Python: 3.x.x (venv)

$ python -c "import flask; print(f'Flask: {flask.__version__}')"
Flask: 2.3.x

$ python -c "import psycopg2; print('PostgreSQL driver: OK')"
PostgreSQL driver: OK

$ ls -la models/
-rw-r--r-- rf_cost_model.pkl
-rw-r--r-- xgb_co2_model.pkl
-rw-r--r-- feature_scaler.pkl

$ python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(f\"API_KEY set: {bool(os.getenv('API_KEY'))}\")"
API_KEY set: True

STEP 2: Test Database Connection
─────────────────────────────────────────────────────────────────────────────────────────────────────

$ python -c "
from src.api_production import get_db
conn = get_db()
if conn:
    print('✓ Database connection successful')
    cursor = conn.cursor()
    cursor.execute('SELECT version();')
    print(f'  {cursor.fetchone()[0]}')
    conn.close()
else:
    print('✗ Database connection failed')
"

STEP 3: Test Component Initialization (Offline)
─────────────────────────────────────────────────────────────────────────────────────────────────────

$ python -c "
from src.logger import setup_logger
from src.model_loader import get_model_registry
from src.predictor import get_predictor
from src.feature_pipeline import FeaturePipeline

logger = setup_logger('test')
logger.info('Testing components...')

registry = get_model_registry()
print(f'✓ Models loaded: {registry.get_status()[\"models\"]}')

predictor = get_predictor()
print(f'✓ Predictor initialized')

metrics = predictor.get_metrics()
print(f'✓ Metrics: {metrics[\"total_predictions\"]} total predictions')
"

STEP 4: Start Flask Development Server
─────────────────────────────────────────────────────────────────────────────────────────────────────

# Terminal 1: Start the API server
$ python src/api_production.py

Expected Output:
================================================================================
ECO_PACK_AI BACKEND - PRODUCTION MODE
================================================================================
API Key configured: True
Database: localhost:5432/ecopack
Models loaded: ['rf_cost_model', 'xgb_co2_model']
Starting ECO_PACK_AI backend server...
* Running on http://localhost:5000

STEP 5: Validate in Separate Terminal
─────────────────────────────────────────────────────────────────────────────────────────────────────

# Terminal 2: Run validation suite
$ python scripts/validate_production.py

This will:
1. Test component initialization (offline)
2. Test /api/health endpoint
3. Test /api/diagnostics endpoint
4. Create test product
5. Test /api/recommend/material endpoint
6. Test /api/predict endpoint
7. Run performance check (10 predictions)

Expected Output:
================================================================================
ECO_PACK_AI - PHASE 5 VALIDATION SUITE
Production Backend Verification
================================================================================
[1/7] Running component validation...
✓ Logger initialized correctly
✓ Model registry loaded: ['rf_cost_model', 'xgb_co2_model']
✓ Feature pipeline validation passed
✓ Predictor initialized correctly

[2/7] Testing /api/health endpoint...
✓ Health check passed (status=healthy)
✓ Database: connected
✓ Models loaded: ['rf_cost_model', 'xgb_co2_model']

[3/7] Testing /api/diagnostics endpoint...
✓ Diagnostics endpoint accessible
ℹ Predictor - Total: 0, Success: 0, Failed: 0
ℹ Average latency: 0.00ms

[4/7] Testing product input...
✓ Product created: TEST-PROD-1705316400

[5/7] Testing material recommendations...
✓ Retrieved 7 material recommendations
ℹ Top 3 Materials:
  1. BAMBOO
     Eco Score: 86.2/100
     CO2 Impact: 0.24 kg CO2e
     Suitability: 0.92
     Latency: 18.34ms
  2. PAPER
     Eco Score: 84.1/100
     CO2 Impact: 0.28 kg CO2e
     Suitability: 0.88
     Latency: 15.22ms
  3. BAGASSE
     Eco Score: 83.5/100
     CO2 Impact: 0.24 kg CO2e
     Suitability: 0.85
     Latency: 12.45ms

[6/7] Testing single material prediction...
✓ Prediction retrieved
ℹ Material: bamboo
ℹ Eco Score: 86.2/100
ℹ CO2 Impact: 0.24 kg CO2e
ℹ Cost: $0.35
ℹ Reliability: high
ℹ Latency: 11.23ms

[7/7] Running performance check...
ℹ Running 10 rapid predictions...
ℹ   5/10 predictions completed
ℹ   10/10 predictions completed
✓ All predictions completed
ℹ Average latency: 14.67ms
ℹ Min latency: 11.23ms
ℹ Max latency: 18.34ms
✓ Latency is acceptable (< 100ms)

================================================================================
VALIDATION SUMMARY
================================================================================
component_validation: PASS
health: PASS
diagnostics: PASS
product_input: PASS
recommendations: PASS
single_prediction: PASS
performance: PASS

Result: 7/7 tests passed

✓ ALL TESTS PASSED - PRODUCTION BACKEND READY

========================================================================================================
API ENDPOINT REFERENCE
========================================================================================================

1. GET /api/health
   Status: Unauthenticated
   Purpose: Health check for load balancers
   
   curl http://localhost:5000/api/health
   
   Response:
   {
     "status": "healthy",
     "timestamp": "2024-01-15T10:30:45.123456",
     "components": {
       "database": "connected",
       "models": {"loaded": ["rf_cost_model", "xgb_co2_model"], "count": 2},
       "predictor": {"metrics": {...}}
     },
     "version": "2.0.0-production"
   }

2. GET /api/diagnostics
   Status: API Key Required (X-API-Key header)
   Purpose: Detailed system monitoring
   
   curl -H "X-API-Key: your-secret-key" http://localhost:5000/api/diagnostics
   
   Response:
   {
     "timestamp": "2024-01-15T10:30:45.123456",
     "models": {...},
     "predictor_metrics": {
       "total_predictions": 12,
       "successful_predictions": 12,
       "failed_predictions": 0,
       "success_rate": 1.0,
       "avg_latency_ms": 14.67
     },
     "database_status": "connected"
   }

3. POST /api/product/input
   Status: API Key Required
   Purpose: Store product in database
   
   curl -X POST http://localhost:5000/api/product/input \
     -H "X-API-Key: your-secret-key" \
     -H "Content-Type: application/json" \
     -d '{
       "product_id": "PROD-001",
       "category": "electronics",
       "weight": 2.5,
       "strength": 75,
       "biodegradability": 80,
       "recyclability": 90
     }'
   
   Response:
   {
     "status": "success",
     "product_id": "PROD-001",
     "request_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
     "timestamp": "2024-01-15T10:30:45.123456"
   }

4. POST /api/recommend/material
   Status: API Key Required
   Purpose: Get all 7 material recommendations (ML-powered)
   
   curl -X POST http://localhost:5000/api/recommend/material \
     -H "X-API-Key: your-secret-key" \
     -H "Content-Type: application/json" \
     -d '{"product_id": "PROD-001"}'
   
   Response:
   {
     "status": "success",
     "product_id": "PROD-001",
     "recommendations": [
       {
         "material": "bamboo",
         "eco_score": 86.2,
         "co2_impact": 0.24,
         "cost_per_unit": 0.35,
         "strength": 8.2,
         "recyclability": 0.72,
         "biodegradability": 0.91,
         "suitability": 0.92,
         "model_reliability": "high",
         "latency_ms": 14.67
       },
       ...
     ],
     "count": 7,
     "request_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
     "timestamp": "2024-01-15T10:30:45.123456"
   }

5. POST /api/predict
   Status: API Key Required
   Purpose: Get single material prediction
   
   curl -X POST http://localhost:5000/api/predict \
     -H "X-API-Key: your-secret-key" \
     -H "Content-Type: application/json" \
     -d '{"product_id": "PROD-001", "material": "bamboo"}'
   
   Response:
   {
     "status": "success",
     "prediction": {...same format as recommendations},
     "request_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
   }

========================================================================================================
PRODUCTION DEPLOYMENT CHECKLIST
========================================================================================================

Pre-Deployment:
☐ Python 3.9+ installed
☐ Virtual environment created and activated
☐ Dependencies installed (pip install -r requirements.txt)
☐ PostgreSQL 12+ running and accessible
☐ Models exist at models/{rf_cost_model,xgb_co2_model,feature_scaler}.pkl
☐ .env file created with database credentials and API key
☐ Database connection tested successfully
☐ All components imported and initialized without errors

Deployment:
☐ Start Flask server: python src/api_production.py
☐ Verify server running on http://localhost:5000
☐ Run validation suite: python scripts/validate_production.py
☐ All 7 validation tests pass
☐ Latency acceptable (< 100ms average)
☐ No errors in logs

Post-Deployment:
☐ Load test: 100 sequential predictions
☐ Concurrency test: 50 concurrent requests
☐ Stress test: 1000 predictions over 10 minutes
☐ Memory profiling: No leaks detected
☐ Database audit: Products and recommendations stored correctly
☐ API Key rotation: Change API_KEY in .env for production
☐ Enable HTTPS: Use reverse proxy (nginx) for TLS
☐ Enable autoscaling: Configure container orchestration if needed

========================================================================================================
TROUBLESHOOTING
========================================================================================================

Problem: "ModuleNotFoundError: No module named 'psycopg2'"
Solution: pip install psycopg2-binary

Problem: "Database connection refused"
Solution: 
  1. Check PostgreSQL is running: systemctl status postgresql
  2. Verify credentials in .env
  3. Create database: createdb ecopack
  4. Test: psql -h localhost -U postgres -d ecopack

Problem: "Models not found"
Solution:
  1. Check models directory: ls -la models/
  2. Verify model files exist and are not corrupted
  3. Check file permissions: chmod 644 models/*.pkl

Problem: "API Key validation failed"
Solution:
  1. Check X-API-Key header is set: curl -H "X-API-Key: your-key" ...
  2. Verify API_KEY matches .env file
  3. Ensure no typos in API key

Problem: "High latency (> 100ms per prediction)"
Solution:
  1. Check CPU usage: top or Task Manager
  2. Check database query performance: EXPLAIN ANALYZE
  3. Check model size: du -sh models/
  4. Consider caching predictions for identical inputs

Problem: "Memory leaks during stress test"
Solution:
  1. Profile memory: python -m memory_profiler src/api_production.py
  2. Check for unclosed database connections
  3. Monitor thread creation: threading.enumerate()
  4. Review predictor metrics for accumulated state

Problem: "Flask app crashes during concurrent requests"
Solution:
  1. Increase worker processes: gunicorn -w 4 src.api_production:app
  2. Check thread limits: ulimit -n (file descriptors)
  3. Monitor for deadlocks in model_loader.py
  4. Add request timeout: requests.post(..., timeout=30)

========================================================================================================
PRODUCTION OPERATIONS
========================================================================================================

Monitoring:
  - Log files stored in logs/ directory (JSON format)
  - Monitor log files: tail -f logs/api_server.log
  - Parse logs: cat logs/api_server.log | jq '. | select(.level=="ERROR")'
  - Metrics: Check /api/diagnostics for success rate and latency

Maintenance:
  - Restart server: Kill Flask process and restart
  - Database backup: pg_dump ecopack > backup.sql
  - Model update: Replace .pkl files and restart Flask
  - API Key rotation: Update API_KEY in .env, restart Flask

Scaling:
  - Load balancer: Use nginx to distribute traffic
  - Horizontal scaling: Run multiple Flask instances on different ports
  - Database replication: Configure PostgreSQL streaming replication
  - Caching: Add Redis for prediction result caching

Security:
  - API Key: Change default API_KEY to strong random string
  - HTTPS: Use reverse proxy with TLS certificates
  - Database: Use SSL/TLS for database connections
  - CORS: Restrict allowed origins in Flask app
  - Rate limiting: Add rate limiter middleware (10 req/second per IP)

========================================================================================================
NEXT STEPS
========================================================================================================

1. Deploy to development environment ✓
2. Run validation tests ✓
3. Performance testing (100, 1000 predictions)
4. Load testing (50 concurrent, stress test)
5. Prepare industrial readiness report
6. Deploy to staging environment
7. Deploy to production with monitoring
8. Set up alerting (latency, errors, database)
9. Schedule maintenance windows
10. Plan model retraining pipeline

========================================================================================================
"""

if __name__ == '__main__':
    print(__doc__)
