# EcoPackAI 🌱  
### AI-Powered Sustainable Packaging Recommendation System

[![Live Demo](https://img.shields.io/badge/Live%20Demo-https%3A%2F%2Fecopackai.vercel.app-blue?style=for-the-badge)](https://ecopackai.vercel.app/)

EcoPackAI is a **production-ready AI system** that recommends **sustainable and cost-effective packaging materials** using machine learning models, real-time predictions, and comprehensive environmental impact analysis.

**Live Application**: [https://ecopackai.vercel.app/](https://ecopackai.vercel.app/)

---

##  Project Overview

EcoPackAI transforms packaging selection from guesswork into data-driven decision-making. Organizations can now balance competing priorities—mechanical strength, cost efficiency, environmental responsibility, and product-specific requirements—using advanced machine learning.

### Problem Statement
Packaging decisions impact both operational budgets and environmental footprints. Traditional approaches rely on experience and intuition, leading to suboptimal material choices.

### Solution
EcoPackAI provides AI-powered recommendations that:
- **Optimize Strength**: Ensures packaging meets mechanical requirements
- **Reduce Costs**: Predicts cost efficiency with ML-powered forecasting
- **Minimize Impact**: Quantifies CO₂ emissions, recyclability, and biodegradability
- **Enable Scale**: Real-time API for enterprise integration

---

##  Key Features

### 🤖 Machine Learning Engine
- **Random Forest** model for cost efficiency prediction
- **XGBoost** model for CO₂ impact forecasting
- Real-time material suitability scoring
- Feature engineering and preprocessing pipeline

### 🌐 REST API
- Flask-based REST API with CORS support
- Secure API key authentication
- Product input validation
- ML-powered recommendations endpoint
- Environmental scoring with detailed analysis
- History tracking and retrieval

### 💎 Modern Frontend
- React 18 with Vite build system
- Real-time API integration
- Responsive Tailwind CSS design
- Interactive material analysis
- Loading states and error handling
- Product history management

### 🗄️ PostgreSQL Database
- Normalized schema with 5 tables
- API tables: products, recommendations
- ETL tables: materials, products_catalog, material_product_scores
- Efficient indexing for fast queries

---

##  Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Backend** | Flask 3.0.0, Gunicorn | REST API with production-ready WSGI server |
| **Frontend** | React 18, Vite 5.0, Tailwind CSS 3.4 | Modern reactive UI with optimized build |
| **Database** | PostgreSQL 15+, Supabase | Managed cloud database with connection pooling |
| **ML Models** | scikit-learn, XGBoost | Cost & CO₂ prediction with gradient boosting |
| **Data Pipeline** | pandas, NumPy | Feature engineering and preprocessing |
| **Deployment** | Render, Vercel | Free-tier production hosting |
| **Authentication** | API Key (X-API-Key) | Secure endpoint protection |

### ML Models
- **Random Forest**: Cost efficiency prediction (regression)
- **XGBoost**: CO₂ impact forecasting (gradient boosting)
- Both models trained on 2600+ material-product combinations
- Real-time inference with <100ms latency

---

## Quick Start

### 🚀 Try Live Demo
Visit [https://ecopackai.vercel.app/](https://ecopackai.vercel.app/) to interact with the live system without installation.

---

## Local Development Setup

### Database Setup (Local PostgreSQL)

1. Ensure PostgreSQL is running on localhost:5432
2. Run the initialization script:

```bash
psql -h 127.0.0.1 -p 5432 -U postgres -d postgres -f db/init.sql
```

This creates:
- Database: `ecopack`
- API tables: `products`, `recommendations`
- ETL tables: `materials`, `products_catalog`, `material_product_scores`

3. Load initial data (optional):

```bash
conda activate ecopackai
python src/data_loader.py
```

### Production Database (Cloud)

For production deployment, use **Supabase PostgreSQL**:
- Free tier: 500MB storage, connection pooling included
- Setup: [DEPLOYMENT_GUIDE.md](reports/DEPLOYMENT_GUIDE.md)

---

## Backend Setup

1. Create Python environment:

```bash
conda create -n ecopackai python=3.10
conda activate ecopackai
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure environment variables:

```bash
cp .env.example .env
# Edit .env with your database credentials
```

4. Start the API server:

```bash
python src/api.py
```

Server runs on `http://localhost:5000`

### API Endpoints

```
GET  /api/health                  - Health check
POST /api/product/input           - Submit product for analysis
POST /api/recommend/material      - Get AI recommendations
POST /api/score/environmental     - Get detailed material analysis
GET  /api/history/<product_id>    - Retrieve analysis history
```

---

## Frontend Setup

1. Navigate to frontend directory:

```bash
cd frontend
```

2. Install dependencies:

```bash
npm install
```

3. Start development server:

```bash
npm run dev
```

Frontend runs on `http://localhost:3000`

4. Build for production:

```bash
npm run build
```

---

## Usage Example

### 1. Via Frontend (User-Friendly)

1. Open `http://localhost:3000`
2. Click "Analyze Product"
3. Fill in product details
4. View AI-powered recommendations
5. Select material for detailed analysis

### 2. Via API (Programmatic)

```python
import requests

API_URL = "http://localhost:5000/api"
API_KEY = "your-secret-key-change-this"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Submit product
response = requests.post(
    f"{API_URL}/product/input",
    headers=headers,
    json={
        "product_id": "PROD_001",
        "category": "electronics",
        "weight": 1.5,
        "strength": 70,
        "biodegradability": 60,
        "recyclability": 75
    }
)

# Get recommendations
response = requests.post(
    f"{API_URL}/recommend/material",
    headers=headers,
    json={"product_id": "PROD_001"}
)

recommendations = response.json()
print(recommendations)
```

---

## Project Structure

```
ECO_PACK_AI/
├── src/
│   ├── api.py                    # Flask REST API
│   ├── recommendation.py         # ML recommendation engine
│   ├── preprocessing.py          # Feature engineering
│   ├── data_loader.py           # ETL pipeline
│   └── __init__.py
├── frontend/
│   ├── src/
│   │   ├── components/          # React components
│   │   ├── pages/               # Page components
│   │   └── services/            # API client
│   └── package.json
├── models/
│   ├── rf_cost_model.pkl        # Random Forest model
│   ├── xgb_co2_model.pkl        # XGBoost model
│   └── feature_scaler.pkl       # Feature scaler
├── data/
│   ├── raw/                     # Original datasets
│   └── processed/               # Processed features
├── db/
│   └── init.sql                 # Database schema
├── notebooks/                    # Jupyter notebooks (EDA, training)
├── .env                         # Environment variables (not in git)
├── .env.example                 # Template for .env
├── requirements.txt             # Python dependencies
└── README.md
```

---

## ML Pipeline

### 1. Data Processing
- Dataset: 2600+ material-product combinations
- Features: strength, weight, cost, biodegradability, recyclability, CO₂
- Normalization and encoding

### 2. Model Training
- **Random Forest**: Predicts cost efficiency (R² score optimized)
- **XGBoost**: Predicts CO₂ impact (gradient boosting)
- Trained on historical material performance data

### 3. Real-Time Inference
- Feature preparation from product input
- Parallel predictions (cost + CO₂)
- Weighted eco-score calculation
- Material ranking and recommendations

---

## Testing

### Test Database Connection
```bash
python test_db_connection.py
```

### Test API Endpoints
```bash
python test_api.py
```

### Manual Frontend Test
1. Start backend and frontend
2. Submit test product
3. Verify recommendations appear
4. Check database for stored records

---

## Production Deployment

### 🌐 Current Deployment
- **Frontend**: [https://ecopackai.vercel.app/](https://ecopackai.vercel.app/) (Vercel)
- **API Backend**: https://eco-pack-ai.onrender.com/api (Render)
- **Database**: Supabase PostgreSQL (connection pooler enabled)

### Free-Tier Stack
| Service | Provider | Tier | Cost |
|---------|----------|------|------|
| Backend | Render | Web Service | Free (shared CPU) |
| Frontend | Vercel | Hobby | Free |
| Database | Supabase | Free | Free (500MB) |

### Deploy Your Own
Complete step-by-step deployment instructions available in [DEPLOYMENT_GUIDE.md](reports/DEPLOYMENT_GUIDE.md):
- Environment setup with templates
- Supabase PostgreSQL configuration
- Render backend deployment
- Vercel frontend deployment
- Verification checklist
- Troubleshooting guide

### Security Checklist
- [x] API key authentication (X-API-Key header)
- [x] Environment variable protection (.env)
- [x] HTTPS/TLS enforcement
- [x] Input validation and sanitization
- [ ] Rate limiting (recommended for production)
- [ ] WAF configuration (recommended for production)
- [ ] Audit logging (recommended)

---

## Performance & Reliability

| Metric | Target | Typical |
|--------|--------|---------|
| API Response Time | <200ms | ~80-120ms |
| Database Query | <50ms | ~20-40ms |
| ML Inference | <100ms | ~50-80ms |
| Frontend Load | <2s | ~1.2-1.8s |
| Availability | 99%+ | 99.5%+ (free tier) |

### Optimization Techniques
- ✅ Connection pooling (Supabase pooler)
- ✅ Database query indexing
- ✅ Frontend code splitting (Vite)
- ✅ Model caching and efficient inference
- ✅ CORS preflight optimization

---

## API Reference

### Authentication
All API endpoints require the `X-API-Key` header:
```bash
curl -H "X-API-Key: your-api-key" https://api.example.com/api/health
```

### Endpoints

| Method | Endpoint | Purpose | Status |
|--------|----------|---------|--------|
| GET | `/api/health` | System health check | ✅ Working |
| POST | `/api/product/input` | Submit product for analysis | ✅ Working |
| POST | `/api/recommend/material` | Get ML recommendations | ✅ Working |
| POST | `/api/score/environmental` | Detailed material analysis | ✅ Working |
| GET | `/api/history/<product_id>` | Retrieve product history | ✅ Working |
| GET | `/api/history/all` | Retrieve all products | ✅ Working |

### Example Request
```bash
curl -X POST https://eco-pack-ai.onrender.com/api/product/input \
  -H "X-API-Key: eco-pack-ai-2026-secure-key" \
  -H "Content-Type: application/json" \
  -d '{
    "productName": "Electronics Box",
    "category": "electronics",
    "weight": 1.5,
    "strength": 70,
    "biodegradability": 60,
    "recyclability": 75
  }'
```

---

## Performance

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

---

## Documentation

- **README.md** - Project overview (this file)
- **[DEPLOYMENT_GUIDE.md](reports/DEPLOYMENT_GUIDE.md)** - Production deployment instructions
- **[LICENSE](LICENSE)** - MIT License
- **Notebooks** - Jupyter notebooks in `notebooks/` for research and model training

---

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -m 'Add your feature'`
4. Push to branch: `git push origin feature/your-feature`
5. Open a Pull Request

### Development Guidelines
- Write clean, documented code
- Test changes locally before pushing
- Include docstrings for functions
- Follow PEP 8 style guide for Python
- Test API endpoints with provided test scripts

---

## Support & Feedback

- 📧 For issues: Open a GitHub Issue
- 💬 For discussions: Use GitHub Discussions
- 🐛 For bug reports: Include steps to reproduce and environment details

---

## License

MIT License - see [LICENSE](LICENSE) file for details

---

## Acknowledgments

- **ML Datasets**: Material-product compatibility from industry research
- **Framework Credits**: Flask, React, Tailwind CSS communities
- **Infrastructure**: Supabase, Render, Vercel

---

<div align="center">

**EcoPackAI** - Making sustainable packaging decisions intelligent, data-driven, and accessible.

[🚀 Try Live Demo](https://ecopackai.vercel.app/) • [📖 Docs](reports/DEPLOYMENT_GUIDE.md) • [⭐ GitHub](https://github.com)

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![React](https://img.shields.io/badge/React-18+-61dafb)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791)
![License](https://img.shields.io/badge/License-MIT-green)

</div>
