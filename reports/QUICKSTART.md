# EcoPackAI - Quick Start Guide

## Prerequisites
- Python 3.10+
- Node.js 16+
- PostgreSQL 12+
- Conda (recommended) or virtualenv

---

## 🚀 Quick Setup (5 minutes)

### Step 1: Database Setup
```bash
# Create database
createdb -h 127.0.0.1 -p 5432 -U postgres ecopack

# Initialize schema
psql -h 127.0.0.1 -p 5432 -U postgres -d ecopack -f db/init.sql

# Load data (optional)
conda activate ecopackai
python src/data_loader.py
```

### Step 2: Backend Setup
```bash
# Create environment
conda create -n ecopackai python=3.10 -y
conda activate ecopackai

# Install dependencies
pip install -r requirements.txt

# Configure .env
cp .env.example .env
# Edit .env with your DB password

# Start API
python src/api.py
```

Backend now running on http://localhost:5000

### Step 3: Frontend Setup
```bash
# In new terminal
cd frontend
npm install
npm run dev
```

Frontend now running on http://localhost:3000

---

## ✅ Verify Installation

### Test 1: Database
```bash
python test_db_connection.py
```
Expected: ✓ SUCCESS: Connected to PostgreSQL!

### Test 2: API
```bash
# In new terminal (keep API running)
python test_api.py
```
Expected: All 5 tests pass with ✓

### Test 3: Frontend
1. Open http://localhost:3000
2. Click "Analyze Product"
3. Fill form and submit
4. See AI recommendations

---

## 🔧 Troubleshooting

### Database Connection Failed
```bash
# Check PostgreSQL is running
psql -V

# Test connection
psql -h 127.0.0.1 -p 5432 -U postgres -d ecopack -c "SELECT 1"

# Check password in .env matches your postgres password
```

### API Import Errors
```bash
# Ensure you're in project root
cd C:\vivek\Infosys_Internship\ECO_PACK_AI\ECO_PACK_AI

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Frontend Won't Start
```bash
# Clear node_modules and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### API Returns 401 Unauthorized
- Ensure API_KEY in `.env` matches `frontend/src/services/api.js`
- Default: `your-secret-key-change-this`

### ML Models Not Loading
- Ensure files exist in `models/` directory:
  - rf_cost_model.pkl
  - xgb_co2_model.pkl
  - feature_scaler.pkl
- If missing, retrain using notebooks in `notebooks/`

---

## 📡 API Usage

### Health Check
```bash
curl http://localhost:5000/api/health
```

### Submit Product
```bash
curl -X POST http://localhost:5000/api/product/input \
  -H "X-API-Key: your-secret-key-change-this" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "TEST_001",
    "category": "electronics",
    "weight": 2.5,
    "strength": 75,
    "biodegradability": 60,
    "recyclability": 80
  }'
```

### Get Recommendations
```bash
curl -X POST http://localhost:5000/api/recommend/material \
  -H "X-API-Key: your-secret-key-change-this" \
  -H "Content-Type: application/json" \
  -d '{"product_id": "TEST_001"}'
```

---

## 🎯 Next Steps

1. **Customize ML Models**: Retrain with your own data in `notebooks/`
2. **Add Materials**: Insert new materials in database `materials` table
3. **Change API Key**: Update `.env` and `frontend/src/services/api.js`
4. **Deploy**: See README.md for production deployment guide

---

## 📊 Expected Results

### Material Recommendations
You should see 6 materials ranked by eco-score:
- Jute: ~95 (Excellent)
- Bamboo: ~93 (Excellent)
- Paper: ~88 (Good)
- Glass: ~80 (Good)
- Metal: ~75 (Good)
- Plastic: ~45 (Fair)

Scores are ML-predicted based on:
- CO₂ impact (30% weight)
- Biodegradability (35% weight)
- Recyclability (25% weight)
- Cost efficiency (10% weight)

---

## 💡 Tips

- **Backend Logs**: Watch API terminal for request logs and predictions
- **Database Inspection**: Use `psql -d ecopack` to query tables
- **Frontend Debugging**: Open browser DevTools Network tab
- **API Testing**: Use Postman or Thunder Client for easier testing

---

## 🆘 Still Having Issues?

1. Check [END_TO_END_TEST.md](END_TO_END_TEST.md) for detailed integration info
2. Verify all prerequisites are installed
3. Ensure PostgreSQL user has CREATE DATABASE permission
4. Check firewall isn't blocking ports 5000 or 3000

---

**Happy Analyzing! 🌱**
