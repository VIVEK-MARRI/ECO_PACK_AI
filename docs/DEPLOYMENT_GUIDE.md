# Production Deployment Guide

## Table of Contents
1. [Infrastructure Setup](#infrastructure-setup)
2. [Database Configuration](#database-configuration)
3. [Model Deployment](#model-deployment)
4. [API Deployment](#api-deployment)
5. [Monitoring & Logging](#monitoring--logging)
6. [CI/CD Pipeline](#cicd-pipeline)
7. [Scaling Strategy](#scaling-strategy)
8. [Security](#security)
9. [Disaster Recovery](#disaster-recovery)

---

## Infrastructure Setup

### System Requirements

**Minimum Production Setup:**
- **Compute**: 8 CPU cores, 32GB RAM
- **GPU**: NVIDIA T4 or better (16GB VRAM)
- **Storage**: 500GB SSD
- **Network**: 1Gbps connection

**Recommended High-Traffic Setup:**
- **Compute**: 16 CPU cores, 64GB RAM per node
- **GPU**: NVIDIA A100 (40GB VRAM) per node
- **Storage**: 2TB NVMe SSD
- **Network**: 10Gbps connection

### Cloud Provider Setup

#### AWS
```bash
# Create VPC
aws ec2 create-vpc --cidr-block 10.0.0.0/16

# Launch GPU instance (p3.2xlarge with V100)
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type p3.2xlarge \
  --key-name my-key \
  --security-group-ids sg-xxx \
  --subnet-id subnet-xxx

# Setup EKS cluster
eksctl create cluster \
  --name ecopackai-prod \
  --version 1.28 \
  --region us-east-1 \
  --nodegroup-name gpu-nodes \
  --node-type p3.2xlarge \
  --nodes 3 \
  --nodes-min 2 \
  --nodes-max 5
```

#### GCP
```bash
# Create GKE cluster with GPUs
gcloud container clusters create ecopackai-prod \
  --zone us-central1-a \
  --num-nodes 3 \
  --machine-type n1-standard-8 \
  --accelerator type=nvidia-tesla-t4,count=1 \
  --enable-autoscaling \
  --min-nodes 2 \
  --max-nodes 10
```

#### Azure
```bash
# Create AKS cluster
az aks create \
  --resource-group ecopackai-rg \
  --name ecopackai-prod \
  --node-count 3 \
  --node-vm-size Standard_NC6s_v3 \
  --enable-cluster-autoscaler \
  --min-count 2 \
  --max-count 10
```

---

## Database Configuration

### PostgreSQL (Transactional Data)

```sql
-- Create database
CREATE DATABASE ecopackai_prod;

-- Create tables
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    product_id VARCHAR(50) UNIQUE NOT NULL,
    category VARCHAR(100),
    weight DECIMAL(10,2),
    length DECIMAL(10,2),
    width DECIMAL(10,2),
    height DECIMAL(10,2),
    fragility_score DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_created_at ON products(created_at);

CREATE TABLE packaging_options (
    id SERIAL PRIMARY KEY,
    packaging_id VARCHAR(50) UNIQUE NOT NULL,
    material VARCHAR(100),
    density DECIMAL(10,4),
    recyclability INTEGER,
    biodegradability INTEGER,
    manufacturing_energy_kwh DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_packaging_material ON packaging_options(material);

CREATE TABLE recommendations (
    id SERIAL PRIMARY KEY,
    request_id UUID UNIQUE NOT NULL,
    product_id VARCHAR(50) REFERENCES products(product_id),
    recommended_packaging_id VARCHAR(50) REFERENCES packaging_options(packaging_id),
    predicted_cost DECIMAL(10,2),
    predicted_co2 DECIMAL(10,2),
    predicted_damage DECIMAL(5,2),
    sustainability_grade VARCHAR(5),
    sustainability_score INTEGER,
    preferences JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_recommendations_product ON recommendations(product_id);
CREATE INDEX idx_recommendations_created_at ON recommendations(created_at);
```

**Connection Pooling:**
```python
# config/database.py
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    "postgresql://user:pass@db-host:5432/ecopackai_prod",
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_timeout=30,
    pool_recycle=3600
)
```

### MongoDB (Feature Store & Logs)

```javascript
// Create collections
db.createCollection("product_features", {
    validator: {
        $jsonSchema: {
            bsonType: "object",
            required: ["product_id", "features", "timestamp"],
            properties: {
                product_id: { bsonType: "string" },
                features: { bsonType: "object" },
                timestamp: { bsonType: "date" }
            }
        }
    }
});

// Create indexes
db.product_features.createIndex({ product_id: 1 });
db.product_features.createIndex({ timestamp: -1 });

db.createCollection("inference_logs");
db.inference_logs.createIndex({ timestamp: -1 });
db.inference_logs.createIndex({ request_id: 1 });
```

### Redis (Caching)

```python
# config/cache.py
import redis
from redis.sentinel import Sentinel

# Setup Redis Sentinel for HA
sentinel = Sentinel([
    ('sentinel-1', 26379),
    ('sentinel-2', 26379),
    ('sentinel-3', 26379)
], socket_timeout=0.1)

# Master for writes
master = sentinel.master_for('mymaster', socket_timeout=0.1)

# Slave for reads
slave = sentinel.slave_for('mymaster', socket_timeout=0.1)

# Cache configuration
CACHE_CONFIG = {
    'embedding_ttl': 3600,  # 1 hour
    'prediction_ttl': 300,   # 5 minutes
    'explanation_ttl': 1800  # 30 minutes
}
```

---

## Model Deployment

### Model Registry (MLflow)

```python
# deploy/register_models.py
import mlflow

mlflow.set_tracking_uri("http://mlflow:5000")

# Register GNN model
with mlflow.start_run(run_name="gnn_production_v1"):
    mlflow.pytorch.log_model(
        gnn_model,
        artifact_path="model",
        registered_model_name="PackagingGNN"
    )
    mlflow.log_metrics({
        "test_rmse": 0.45,
        "test_r2": 0.92
    })

# Register ensemble
with mlflow.start_run(run_name="ensemble_production_v1"):
    mlflow.sklearn.log_model(
        ensemble_model,
        artifact_path="model",
        registered_model_name="PackagingEnsemble"
    )

# Promote to production
client = mlflow.tracking.MlflowClient()
client.transition_model_version_stage(
    name="PackagingGNN",
    version=1,
    stage="Production"
)
```

### Model Serving with TorchServe

```bash
# Package model
torch-model-archiver \
  --model-name gnn_packaging \
  --version 1.0 \
  --serialized-file models/gnn_model.pt \
  --handler handlers/gnn_handler.py

# Deploy
torchserve \
  --start \
  --model-store model_store \
  --models gnn=gnn_packaging.mar \
  --ncs \
  --ts-config config.properties

# config.properties
inference_address=http://0.0.0.0:8080
management_address=http://0.0.0.0:8081
metrics_address=http://0.0.0.0:8082
number_of_gpu=1
gpu_id=0
```

### Kubernetes Deployment

```yaml
# k8s/gnn-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gnn-inference
  namespace: ecopackai
spec:
  replicas: 3
  selector:
    matchLabels:
      app: gnn-inference
  template:
    metadata:
      labels:
        app: gnn-inference
    spec:
      containers:
      - name: gnn
        image: ecopackai/gnn:v1.0
        ports:
        - containerPort: 8080
        resources:
          requests:
            memory: "16Gi"
            cpu: "4"
            nvidia.com/gpu: 1
          limits:
            memory: "32Gi"
            cpu: "8"
            nvidia.com/gpu: 1
        env:
        - name: MODEL_PATH
          value: "/models/gnn_model.pt"
        - name: DEVICE
          value: "cuda"
        volumeMounts:
        - name: model-storage
          mountPath: /models
      volumes:
      - name: model-storage
        persistentVolumeClaim:
          claimName: model-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: gnn-service
  namespace: ecopackai
spec:
  selector:
    app: gnn-inference
  ports:
  - port: 8080
    targetPort: 8080
  type: LoadBalancer
```

---

## API Deployment

### FastAPI Application

```python
# api/main.py
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, generate_latest
import structlog

app = FastAPI(title="ECO_PACK_AI Enterprise API", version="1.0.0")

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Metrics
request_count = Counter('api_requests_total', 'Total API requests', ['method', 'endpoint'])
request_duration = Histogram('api_request_duration_seconds', 'Request duration')

# Initialize AI
from examples.complete_integration import EnterprisePackagingAI

ai = EnterprisePackagingAI(
    gnn_model_path='/models/gnn_model.pt',
    ensemble_model_path='/models/ensemble.pkl',
    device='cuda'
)

@app.post("/api/v1/recommend")
async def recommend(request: dict):
    request_count.labels(method='POST', endpoint='/recommend').inc()
    
    with request_duration.time():
        result = ai.recommend_packaging(
            product=request['product'],
            packaging_options=request['packaging_options'],
            preferences=request.get('preferences')
        )
    
    return result

@app.get("/metrics")
async def metrics():
    return generate_latest()

@app.get("/health")
async def health():
    return {"status": "healthy"}
```

### Docker Configuration

```dockerfile
# Dockerfile
FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

# Install Python
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements
COPY requirements_enterprise.txt .
RUN pip install --no-cache-dir -r requirements_enterprise.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DATABASE_URL=postgresql://postgres:password@db:5432/ecopackai
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=ecopackai
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  
  mlflow:
    image: ghcr.io/mlflow/mlflow:v2.10.0
    ports:
      - "5000:5000"
    command: mlflow server --host 0.0.0.0 --backend-store-uri postgresql://postgres:password@db:5432/mlflow

volumes:
  postgres_data:
```

---

## Monitoring & Logging

### Prometheus Configuration

```yaml
# prometheus/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'ecopackai-api'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'
  
  - job_name: 'nvidia-gpu'
    static_configs:
      - targets: ['dcgm-exporter:9400']
```

### Grafana Dashboards

```json
{
  "dashboard": {
    "title": "ECO_PACK_AI Production Metrics",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [
          {
            "expr": "rate(api_requests_total[5m])"
          }
        ]
      },
      {
        "title": "Request Duration (p95)",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, api_request_duration_seconds_bucket)"
          }
        ]
      },
      {
        "title": "GPU Utilization",
        "targets": [
          {
            "expr": "DCGM_FI_DEV_GPU_UTIL"
          }
        ]
      },
      {
        "title": "Model Inference Latency",
        "targets": [
          {
            "expr": "rate(model_inference_duration_sum[5m]) / rate(model_inference_duration_count[5m])"
          }
        ]
      }
    ]
  }
}
```

### Structured Logging

```python
# config/logging.py
import structlog

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()
```

---

## CI/CD Pipeline

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          pip install -r requirements_enterprise.txt
          pip install pytest pytest-cov
      
      - name: Run tests
        run: |
          pytest tests/ --cov=src --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build Docker image
        run: |
          docker build -t ecopackai:${{ github.sha }} .
      
      - name: Push to registry
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker push ecopackai:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to Kubernetes
        run: |
          kubectl set image deployment/api api=ecopackai:${{ github.sha }} -n ecopackai
          kubectl rollout status deployment/api -n ecopackai
```

---

## Scaling Strategy

### Horizontal Pod Autoscaler

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
  namespace: ecopackai
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "1000"
```

### Load Balancing

```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api-ingress
  namespace: ecopackai
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - api.ecopackai.com
    secretName: api-tls
  rules:
  - host: api.ecopackai.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: api-service
            port:
              number: 8000
```

---

## Security

### API Authentication

```python
# api/auth.py
from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

security = HTTPBearer()

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=["HS256"]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### Secrets Management

```yaml
# k8s/secrets.yaml
apiVersion: v1
kind: Secret
metadata:
  name: api-secrets
  namespace: ecopackai
type: Opaque
data:
  database-url: <base64-encoded>
  openai-api-key: <base64-encoded>
  jwt-secret: <base64-encoded>
```

---

## Disaster Recovery

### Backup Strategy

```bash
# Backup PostgreSQL
pg_dump -h db-host -U postgres ecopackai_prod > backup_$(date +%Y%m%d).sql

# Backup models
aws s3 sync models/ s3://ecopackai-models-backup/

# Automated daily backups
# crontab
0 2 * * * /scripts/backup.sh
```

### Restore Procedure

```bash
# Restore database
psql -h db-host -U postgres ecopackai_prod < backup_20240101.sql

# Restore models
aws s3 sync s3://ecopackai-models-backup/ models/
```

---

## Performance Benchmarks

**Target Metrics:**
- Single prediction: <200ms (p99)
- Batch 100 predictions: <2s
- Throughput: >1000 req/s
- Availability: 99.9%

**Load Testing:**
```bash
# Using locust
locust -f tests/load_test.py --host=https://api.ecopackai.com
```

---

## Support Contacts

- **DevOps**: devops@ecopackai.com
- **On-call**: +1-XXX-XXX-XXXX
- **Pagerduty**: https://ecopackai.pagerduty.com
