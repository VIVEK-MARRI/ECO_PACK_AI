# EcoPackAI API Documentation

## Base URL
```
http://localhost:5000/api
```

## Authentication
All endpoints (except `/health`) require an API key in the request header:
```
X-API-Key: your-secret-key-change-this
```

---

## Endpoints

### 1. Health Check
**GET** `/health`

Check API server status and model availability.

**Headers:** None required

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-02-02T05:52:02.284646",
  "models": "loaded"
}
```

**Status Codes:**
- `200 OK`: Server is healthy

---

### 2. Submit Product Input
**POST** `/product/input`

Submit a product for analysis and store in database.

**Headers:**
```
X-API-Key: your-secret-key-change-this
Content-Type: application/json
```

**Request Body:**
```json
{
  "product_id": "PROD_001",          // Required: Unique identifier
  "category": "electronics",         // Required: Product category
  "weight": 5.0,                     // Required: Weight in kg (>0)
  "strength": 75,                    // Optional: 0-100, default 50
  "biodegradability": 60,            // Optional: 0-100, default 50
  "recyclability": 85                // Optional: 0-100, default 50
}
```

**Valid Categories:**
- electronics
- food
- beverages
- cosmetics
- pharmaceuticals
- home
- textiles
- general

**Response:**
```json
{
  "status": "success",
  "message": "Product stored",
  "product_id": "PROD_001"
}
```

**Status Codes:**
- `201 Created`: Product successfully stored
- `400 Bad Request`: Invalid input data
- `401 Unauthorized`: Missing or invalid API key
- `500 Internal Server Error`: Database connection failed

---

### 3. Get Material Recommendations
**POST** `/recommend/material`

Get ML-powered material recommendations for a product.

**Headers:**
```
X-API-Key: your-secret-key-change-this
Content-Type: application/json
```

**Request Body:**
```json
{
  "product_id": "PROD_001"           // Required: Product ID
}
```

**Response:**
```json
{
  "status": "success",
  "product_id": "PROD_001",
  "recommendations": [
    {
      "material": "jute",
      "material_id": "MAT_JUTE_b752a9",
      "eco_score": 95.23,            // Overall score (0-100)
      "co2_impact": 0.025,           // CO₂ impact (0-1, lower better)
      "cost_efficiency": 0.682,      // Cost efficiency (0-1, higher better)
      "suitability": 0.854,          // Material suitability (0-1)
      "biodegradability": 0.99,      // Biodegradability (0-1)
      "recyclability": 88,           // Recyclability % (0-100)
      "cost_per_unit": 0.28,         // Cost per unit ($)
      "strength": 44                 // Material strength (0-100)
    },
    {
      "material": "bamboo",
      "eco_score": 93.15,
      ...
    }
    // ... up to 6 materials
  ],
  "timestamp": "2026-02-02T05:52:06.470033"
}
```

**Score Calculation:**
```
eco_score = (1 - co2_impact) × 30%
          + biodegradability × 35%
          + recyclability × 25%
          + cost_efficiency × 10%
```

**Status Codes:**
- `200 OK`: Recommendations generated
- `400 Bad Request`: Missing product_id
- `404 Not Found`: Product not found in database
- `401 Unauthorized`: Missing or invalid API key
- `500 Internal Server Error`: Database or ML error

---

### 4. Get Environmental Score
**POST** `/score/environmental`

Get detailed environmental analysis for a specific material-product combination.

**Headers:**
```
X-API-Key: your-secret-key-change-this
Content-Type: application/json
```

**Request Body:**
```json
{
  "product_id": "PROD_001",          // Required
  "material": "bamboo"               // Required: Material name (lowercase)
}
```

**Response:**
```json
{
  "status": "success",
  "product_id": "PROD_001",
  "material": "bamboo",
  "overall_score": 86.9,             // Overall eco score (0-100)
  "rating": "Excellent ✓",           // Rating category
  "co2_intensity": 0.2,              // CO₂ impact (0-1)
  "biodegradability": 0.98,          // Biodegradability (0-1)
  "recyclability": 85.0,             // Recyclability % (0-100)
  "cost_efficiency": 0.685,          // ML-predicted cost efficiency
  "timestamp": "2026-02-02T05:52:08.573751"
}
```

**Rating Categories:**
- `Excellent ✓`: score ≥ 80
- `Good ✓`: 65 ≤ score < 80
- `Fair ⚠`: 50 ≤ score < 65
- `Poor ✗`: score < 50

**Status Codes:**
- `200 OK`: Analysis completed
- `400 Bad Request`: Missing required fields
- `404 Not Found`: Product or material not found
- `401 Unauthorized`: Missing or invalid API key
- `500 Internal Server Error`: Database or ML error

---

### 5. Get History
**GET** `/history/<product_id>`

Retrieve analysis history for a product.

**Headers:**
```
X-API-Key: your-secret-key-change-this
```

**URL Parameters:**
- `product_id`: Product identifier (string)

**Response:**
```json
{
  "status": "success",
  "product_id": "PROD_001",
  "count": 3,
  "history": [
    {
      "id": 15,
      "product_id": "PROD_001",
      "material": "bamboo",
      "cost_score": 0.685,
      "co2_score": 0.2,
      "eco_score": 86.9,
      "created_at": "Mon, 02 Feb 2026 11:22:08 GMT"
    },
    {
      "id": 14,
      "product_id": "PROD_001",
      "material": "paper",
      ...
    }
    // ... up to 10 most recent entries
  ]
}
```

**Status Codes:**
- `200 OK`: History retrieved (may be empty array)
- `401 Unauthorized`: Missing or invalid API key
- `500 Internal Server Error`: Database error

---

## Error Response Format

All error responses follow this format:
```json
{
  "error": "Descriptive error message"
}
```

Or for complex errors:
```json
{
  "status": "error",
  "message": "Detailed error description"
}
```

---

## Rate Limiting

Currently no rate limiting is implemented. For production:
- Recommended: 100 requests/minute per API key
- Implement using Flask-Limiter or similar

---

## CORS

CORS is enabled for all origins in development. For production:
- Restrict to specific domains
- Configure in `src/api.py`:
```python
CORS(app, resources={r"/api/*": {"origins": "https://yourdomain.com"}})
```

---

## Machine Learning Details

### Models Used
1. **Random Forest** (Cost Efficiency)
   - Input: 8 engineered features
   - Output: Cost efficiency score (0-1)
   - Training R² score: ~0.85

2. **XGBoost** (CO₂ Impact)
   - Input: 8 engineered features
   - Output: CO₂ impact index (0-1)
   - Training R² score: ~0.90

### Feature Engineering
Input features are automatically engineered from product and material properties:
- Strength matching
- Weight capacity estimation
- Biodegradability alignment
- Recyclability preference
- Fragility mapping
- Shipping type encoding

---

## Code Examples

### Python (requests)
```python
import requests

API_URL = "http://localhost:5000/api"
headers = {
    "X-API-Key": "your-secret-key-change-this",
    "Content-Type": "application/json"
}

# Submit product
response = requests.post(
    f"{API_URL}/product/input",
    headers=headers,
    json={
        "product_id": "PROD_123",
        "category": "electronics",
        "weight": 2.5,
        "strength": 70,
        "biodegradability": 65,
        "recyclability": 80
    }
)

# Get recommendations
response = requests.post(
    f"{API_URL}/recommend/material",
    headers=headers,
    json={"product_id": "PROD_123"}
)

recommendations = response.json()
```

### JavaScript (Axios)
```javascript
import axios from 'axios'

const API_URL = 'http://localhost:5000/api'
const headers = {
  'X-API-Key': 'your-secret-key-change-this',
  'Content-Type': 'application/json'
}

// Submit product
const response = await axios.post(
  `${API_URL}/product/input`,
  {
    product_id: 'PROD_123',
    category: 'electronics',
    weight: 2.5,
    strength: 70,
    biodegradability: 65,
    recyclability: 80
  },
  { headers }
)

// Get recommendations
const recommendations = await axios.post(
  `${API_URL}/recommend/material`,
  { product_id: 'PROD_123' },
  { headers }
)
```

### cURL
```bash
# Submit product
curl -X POST http://localhost:5000/api/product/input \
  -H "X-API-Key: your-secret-key-change-this" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "PROD_123",
    "category": "electronics",
    "weight": 2.5,
    "strength": 70,
    "biodegradability": 65,
    "recyclability": 80
  }'

# Get recommendations
curl -X POST http://localhost:5000/api/recommend/material \
  -H "X-API-Key: your-secret-key-change-this" \
  -H "Content-Type: application/json" \
  -d '{"product_id": "PROD_123"}'
```

---

## Changelog

### v1.0.0 (2026-02-02)
- Initial ML-powered API release
- Random Forest + XGBoost integration
- Real-time predictions
- Input validation
- History tracking

---

## Support

For issues or questions:
1. Check [QUICKSTART.md](QUICKSTART.md) for setup help
2. Review [END_TO_END_TEST.md](END_TO_END_TEST.md) for integration details
3. Open an issue on GitHub
