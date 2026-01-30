# Flask REST API - Setup Guide

## Quick Start

### 1. Install PostgreSQL
Download from: https://www.postgresql.org/download/

After install, create database:
```bash
psql -U postgres
CREATE DATABASE ecopackai;
\q
```

### 2. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 3. Update .env file
Change these values:
```
API_KEY=your-secret-key-change-this
DB_PASSWORD=your-postgres-password
```

### 4. Run the API
```bash
python src/api.py
```

You should see:
```
=====================================
ECO_PACK_AI Flask API
=====================================

Endpoints:
  GET  /api/health
  POST /api/product/input
  POST /api/recommend/material
  POST /api/score/environmental
  GET  /api/history/<product_id>

Running on http://localhost:5000
```

### 5. Test the API
```bash
python test_api.py
```

---

## API Endpoints

### 1. Health Check
```bash
GET /api/health
```
No API key needed. Check if server is running.

### 2. Input Product
```bash
POST /api/product/input
Header: X-API-Key: your-secret-key-change-this
Body:
{
  "product_id": "PROD_001",
  "category": "electronics",
  "weight": 5.0,
  "strength": 75,
  "biodegradability": 0.8,
  "recyclability": 85
}
```

### 3. Get Material Recommendation
```bash
POST /api/recommend/material
Header: X-API-Key: your-secret-key-change-this
Body:
{
  "product_id": "PROD_001"
}
```

Returns top 3 materials ranked by eco-friendliness.

### 4. Environmental Score
```bash
POST /api/score/environmental
Header: X-API-Key: your-secret-key-change-this
Body:
{
  "product_id": "PROD_001",
  "material": "bamboo"
}
```

Returns eco-score (0-100) with rating.

### 5. Get History
```bash
GET /api/history/PROD_001
Header: X-API-Key: your-secret-key-change-this
```

Returns all recommendations for a product.

---

## Test with cURL

```bash
# Health check
curl http://localhost:5000/api/health

# Input product
curl -X POST http://localhost:5000/api/product/input \
  -H "X-API-Key: your-secret-key-change-this" \
  -H "Content-Type: application/json" \
  -d '{"product_id": "PROD_001", "category": "electronics"}'

# Get recommendation
curl -X POST http://localhost:5000/api/recommend/material \
  -H "X-API-Key: your-secret-key-change-this" \
  -H "Content-Type: application/json" \
  -d '{"product_id": "PROD_001"}'

# Get score
curl -X POST http://localhost:5000/api/score/environmental \
  -H "X-API-Key: your-secret-key-change-this" \
  -H "Content-Type: application/json" \
  -d '{"product_id": "PROD_001", "material": "bamboo"}'
```

---

## Database Schema

### Products Table
- id (auto)
- product_id (unique)
- category
- weight
- strength
- biodegradability
- recyclability
- created_at

### Recommendations Table
- id (auto)
- product_id (foreign key)
- material
- cost_score
- co2_score
- eco_score
- created_at

---

## Security Notes

- Change `API_KEY` in `.env` file before deployment
- Never commit `.env` file
- Always use HTTPS in production
- Store API key securely

---

## Troubleshooting

**Port 5000 already in use:**
```bash
python src/api.py --port 8000
# or set PORT=8000 in .env
```

**Database connection failed:**
- Check PostgreSQL is running
- Verify DB_PASSWORD in .env
- Verify DB_USER has permissions

**Models not loaded:**
- Check model files exist in `models/` folder
- Models are optional - API works without them
