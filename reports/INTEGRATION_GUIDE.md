# Frontend-Backend Integration Guide

## Component-Backend Mapping

### API Endpoints vs Frontend Components

#### 1. **ProductForm Component** ↔ `/api/product/input`
**Frontend:** Collects product data (name, category, weight, strength, biodegradability, recyclability)
**Backend:** Stores in `products` table
```javascript
POST /api/product/input
{
  product_id: string (auto-generated),
  category: string,
  weight: float,
  strength: float,
  biodegradability: float,
  recyclability: float
}
```

#### 2. **Recommendations Component** ↔ `/api/recommend/material`
**Frontend:** Displays 6 materials with eco scores
**Backend:** Calculates material recommendations
```javascript
POST /api/recommend/material
{
  product_id: string
}
Response:
{
  recommendations: [
    { material: "bamboo", score: 0.92 },
    ...
  ]
}
```

#### 3. **Recommendations Component** ↔ `/api/score/environmental`
**Frontend:** Shows detailed scores (CO₂, biodegradability, recyclability)
**Backend:** Calculates environmental impact
```javascript
POST /api/score/environmental
{
  product_id: string,
  material: string
}
Response:
{
  overall_score: 88,
  co2_intensity: 0.3,
  biodegradability: 0.95,
  recyclability: 0.90
}
```

#### 4. **History Component** ↔ `/api/history/<product_id>`
**Frontend:** Lists previous recommendations
**Backend:** Retrieves from `recommendations` table
```javascript
GET /api/history/{product_id}
Response:
{
  history: [
    { product_id, material, eco_score, created_at },
    ...
  ]
}
```

#### 5. **Navbar Component** ↔ `/api/health`
**Frontend:** Checks backend availability
**Backend:** Returns service status
```javascript
GET /api/health
Response:
{
  status: "healthy",
  models: "loaded"
}
```

---

## Data Flow

```
User Input (ProductForm)
    ↓
ProductForm → api.inputProduct()
    ↓
Backend: POST /api/product/input
    ↓
Save to products table
    ↓
Return product_id
    ↓
Navigate to Recommendations
    ↓
Recommendations → api.getMaterialRecommendations()
    ↓
Backend: POST /api/recommend/material
    ↓
ML Models calculate scores
    ↓
Return 6 materials with scores
    ↓
Display in UI
    ↓
User selects material
    ↓
api.getEnvironmentalScore()
    ↓
Backend: POST /api/score/environmental
    ↓
Save to recommendations table
    ↓
Show detailed scores
```

---

## Frontend Data Structures

### Product Object (Local Storage)
```javascript
{
  id: number (timestamp),
  productName: string,
  category: string,
  weight: float,
  strength: float,
  biodegradability: float,
  recyclability: float,
  description: string,
  createdAt: ISO string,
  backendId: string (optional, if connected)
}
```

### Material Object
```javascript
{
  name: string,
  icon: string,
  score: number (0-100),
  co2: float,
  cost: float,
  recyclability: number,
  biodegradability: number,
  pros: string[],
  cons: string[]
}
```

---

## Current Integration Status

✅ **Working (Local Storage)**
- Product form submission
- Material recommendations display
- History tracking
- Navigation between pages

⚠️ **Needs Backend**
- Real AI-powered material scores
- Database persistence
- Environmental impact calculations
- User authentication (future)

---

## Environment Setup

### Frontend (.env.local)
```
VITE_API_URL=http://localhost:5000/api
VITE_API_KEY=your-secret-key-change-this
```

### Backend (.env)
```
FLASK_ENV=development
DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=ecopackai_api
DB_USER=postgres
DB_PASSWORD=admin
API_KEY=your-secret-key-change-this
```

---

## Testing the Integration

1. **Start Backend:**
```bash
cd src
python api.py
# Should run on http://localhost:5000
```

2. **Start Frontend:**
```bash
cd frontend
npm run dev
# Should run on http://localhost:3000
```

3. **Test Health Check:**
- Open browser console
- Frontend will auto-check `/api/health` on load
- Check if backend status shows in console

4. **Test Product Submission:**
- Fill in product form
- Click "Get AI Recommendations"
- Check Network tab to see API requests
- Data should appear in backend database

5. **Verify Data:**
```bash
psql -U postgres -d ecopackai_api
SELECT * FROM products;
SELECT * FROM recommendations;
```

---

## API Error Handling

### Fallback Strategy
- If backend is unavailable → Use localStorage
- If API key is invalid → 401 Unauthorized
- If database connection fails → 500 Server Error
- Console warnings show what failed

### Frontend Error Handling
- Try-catch blocks in api.js
- Graceful degradation to local storage
- User-friendly error messages

---

## Next Steps

1. **Database Setup** - Create `ecopackai_api` database
2. **CORS Configuration** - Already enabled in Flask
3. **API Key Management** - Update in both .env files
4. **Error Monitoring** - Add logging/Sentry
5. **Authentication** - Add user login (future)

---

## Component Files

- `src/services/api.js` - API client
- `src/pages/ProductForm.jsx` - Form submission with API
- `src/pages/Recommendations.jsx` - Material scoring display
- `src/pages/History.jsx` - Historical data view
- `src/components/Navbar.jsx` - Health check on mount
