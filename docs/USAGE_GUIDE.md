# Enterprise AI System - Complete Usage Guide

## Table of Contents
1. [System Overview](#system-overview)
2. [Installation](#installation)
3. [Component Architecture](#component-architecture)
4. [Quick Start](#quick-start)
5. [Detailed Usage](#detailed-usage)
6. [Training Models](#training-models)
7. [API Integration](#api-integration)
8. [Performance Optimization](#performance-optimization)
9. [Production Deployment](#production-deployment)
10. [Troubleshooting](#troubleshooting)

---

## System Overview

ECO_PACK_AI Enterprise Platform is a production-grade AI system for sustainable packaging recommendations. It combines:

- **Graph Neural Networks (GNN)**: Relational intelligence between products, materials, and routes
- **Meta-Ensemble System**: Stacked models (LightGBM, XGBoost, CatBoost, TabNet) with neural meta-learner
- **Multi-Objective Optimization**: NSGA-II and weighted scalarization for cost/CO2/damage tradeoffs
- **Carbon Accounting Engine**: Lifecycle analysis, sustainability grading (A+ to F), offset calculation
- **LLM Explanation Engine**: Human-readable explanations using GPT-4/Claude with fallback

**Performance Targets:**
- Inference: <200ms per prediction
- Batch: >1000 predictions/second
- Availability: 99.9% uptime

---

## Installation

### Prerequisites
```bash
# Python 3.10+
python --version

# CUDA 12.1+ (for GPU acceleration)
nvidia-smi
```

### Install Dependencies
```bash
# Clone repository
git clone https://github.com/your-org/eco-pack-ai.git
cd eco-pack-ai

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install enterprise dependencies
pip install -r requirements_enterprise.txt

# Verify installation
python -c "import torch; import torch_geometric; print('Success!')"
```

### Environment Variables
Create `.env` file:
```bash
# LLM Configuration
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key

# Database
DATABASE_URL=postgresql://user:pass@localhost/ecopackai
MONGODB_URL=mongodb://localhost:27017/ecopackai
REDIS_URL=redis://localhost:6379

# MLflow
MLFLOW_TRACKING_URI=http://localhost:5000

# Feature Store
FEAST_REPO_PATH=./feature_repo
```

---

## Component Architecture

### 1. Graph Neural Network (`/graph_models`)

**Purpose**: Capture relational patterns between products, packaging, materials, routes, and climate zones.

**Components:**
- `graph_builder.py`: Constructs heterogeneous graph with 6 node types and 6 edge types
- `gnn_model.py`: PackagingGAT (attention), PackagingGraphSAGE (inductive), HeteroGNN (heterogeneous)
- `graph_trainer.py`: Training loop with MLflow tracking
- `graph_inference.py`: Real-time inference with embedding caching

**Example:**
```python
from graph_models.graph_inference import GraphInference

# Load trained model
inference = GraphInference(
    model_path='models/gnn_model.pt',
    device='cuda'
)

# Predict
predictions = inference.predict_batch(
    product_ids=[101, 102, 103],
    packaging_ids=[5, 5, 7]
)
# Returns: [{'cost': 12.5, 'co2': 2.3, 'damage': 0.05}, ...]
```

### 2. Meta-Ensemble System (`/ensemble`)

**Purpose**: Combine multiple gradient boosting models and TabNet with neural meta-learner.

**Components:**
- `base_models.py`: LightGBM, XGBoost, CatBoost, TabNet with cross-validation
- `meta_learner.py`: Neural network with separate heads for cost/co2/damage
- `stacking_ensemble.py`: Complete stacking pipeline

**Example:**
```python
from ensemble.stacking_ensemble import StackingEnsemble
import pandas as pd

# Train ensemble
ensemble = StackingEnsemble(device='cuda', use_gpu=True)

X_train = pd.read_csv('data/processed/X_train.csv')
y_train_cost = pd.read_csv('data/processed/y_cost_train.csv')
y_train_co2 = pd.read_csv('data/processed/y_co2_train.csv')
y_train_damage = pd.read_csv('data/processed/y_damage_train.csv')

ensemble.fit(
    X_train=X_train,
    y_cost=y_train_cost.values.ravel(),
    y_co2=y_train_co2.values.ravel(),
    y_damage=y_train_damage.values.ravel()
)

# Save
ensemble.save('models/ensemble.pkl')

# Predict
predictions = ensemble.predict(X_test)
# Returns: [{'cost': 10.2, 'co2': 1.8, 'damage': 0.03}, ...]
```

### 3. Multi-Objective Optimization (`/optimization`)

**Purpose**: Find Pareto-optimal packaging solutions balancing cost, CO2, and damage.

**Components:**
- `nsga2.py`: NSGA-II genetic algorithm for Pareto frontier
- `pareto.py`: Pareto analysis, knee point detection, dominance checking
- `weighted_scalarization.py`: Weighted linear combination with sensitivity analysis
- `optimization_engine.py`: Unified interface for all methods

**Example:**
```python
from optimization.optimization_engine import OptimizationEngine
import numpy as np

optimizer = OptimizationEngine()

# Objectives: [cost, co2, damage] for each packaging option
objectives = np.array([
    [10.0, 2.5, 0.05],  # Option 1
    [12.0, 1.8, 0.03],  # Option 2
    [8.0, 3.0, 0.07],   # Option 3
    # ... more options
])

# Find Pareto frontier
pareto_results = optimizer.optimize_multi_objective(
    objectives=objectives,
    method='nsga2',
    population_size=50,
    generations=100
)

print("Pareto-optimal indices:", pareto_results['pareto_indices'])
print("Knee point:", pareto_results['knee_point'])

# Weighted optimization (e.g., 40% cost, 40% CO2, 20% damage)
weighted_results = optimizer.optimize_weighted(
    objectives=objectives,
    weights=[0.4, 0.4, 0.2]
)

print("Best option index:", weighted_results['best_index'])
print("Weighted score:", weighted_results['best_score'])
```

### 4. Carbon Accounting Engine (`/carbon_engine`)

**Purpose**: Calculate lifecycle CO2, assign sustainability grades, recommend carbon offsets.

**Components:**
- `lifecycle_calculator.py`: 5-stage CO2 calculation (extraction, manufacturing, transport, usage, end-of-life)
- `sustainability_grader.py`: A+ to F grading system with numerical scoring
- `carbon_offset.py`: Offset project database and portfolio recommendations
- `carbon_engine.py`: Unified carbon accounting interface

**Example:**
```python
from carbon_engine.carbon_engine import CarbonAccountingEngine

engine = CarbonAccountingEngine()

packaging_data = {
    'material': 'Recycled Cardboard',
    'weight_kg': 0.5,
    'recyclability_percent': 95,
    'biodegradability_percent': 85,
    'manufacturing_energy_kwh': 2.5,
    'transport_distance_km': 500,
    'transport_mode': 'truck'
}

analysis = engine.analyze_packaging(packaging_data)

print("Lifecycle CO2:", analysis['lifecycle_analysis']['total_co2'], "kg")
print("Grade:", analysis['grade'].name)  # e.g., SustainabilityGrade.A
print("Score:", analysis['score'], "/100")
print("Recommendations:", analysis['recommendations'])
print("Carbon offset cost:", analysis['offset_analysis']['total_cost'])
```

### 5. LLM Explanation Engine (`/llm_engine`)

**Purpose**: Generate human-readable sustainability explanations using LLMs.

**Components:**
- `llm_client.py`: OpenAI/Anthropic abstraction with automatic fallback
- `prompt_templates.py`: Structured prompts for different explanation types
- `explanation_generator.py`: High-level explanation generation interface

**Example:**
```python
from llm_engine.explanation_generator import ExplanationGenerator

explainer = ExplanationGenerator()

product_data = {
    'category': 'Electronics',
    'weight': 2.5,
    'fragility': 'High'
}

packaging_data = {
    'material': 'Biodegradable Foam',
    'cost': 15.50,
    'co2': 1.8,
    'recyclability': 70,
    'biodegradability': 100,
    'damage_prob': 2.5
}

alternatives = [
    {'material': 'Plastic', 'cost': 10.0, 'co2': 3.5, 'recyclability': 20},
    {'material': 'Cardboard', 'cost': 8.0, 'co2': 2.0, 'recyclability': 95}
]

explanation = explainer.explain_recommendation(
    product_data=product_data,
    packaging_data=packaging_data,
    alternatives=alternatives
)

print("Reasoning:", explanation['reasoning'])
print("Impact:", explanation['impact'])
print("Tradeoffs:", explanation['tradeoffs'])
print("Compliance:", explanation['compliance'])
```

---

## Quick Start

### End-to-End Recommendation

```python
from examples.complete_integration import EnterprisePackagingAI

# Initialize AI system
ai = EnterprisePackagingAI(
    gnn_model_path='models/gnn_model.pt',
    ensemble_model_path='models/ensemble.pkl',
    device='cuda'
)

# Define product
product = {
    'id': 'PROD_001',
    'category': 'Electronics',
    'weight': 2.5,  # kg
    'length': 30,   # cm
    'width': 20,
    'height': 10,
    'fragility_score': 0.8
}

# Available packaging options
packaging_options = [
    {
        'id': 'PKG_001',
        'material': 'Recycled Cardboard',
        'density': 0.3,
        'recyclability': 95,
        'biodegradability': 85
    },
    {
        'id': 'PKG_002',
        'material': 'Biodegradable Foam',
        'density': 0.05,
        'recyclability': 70,
        'biodegradability': 100
    }
]

# Get recommendation
recommendation = ai.recommend_packaging(
    product=product,
    packaging_options=packaging_options,
    preferences={
        'cost_weight': 0.3,
        'co2_weight': 0.5,
        'damage_weight': 0.2
    }
)

# Access results
print("Recommended:", recommendation['recommended_packaging']['material'])
print("Cost: $", recommendation['recommended_packaging']['cost'])
print("CO2:", recommendation['recommended_packaging']['co2'], "kg")
print("Grade:", recommendation['sustainability']['grade'])
print("\nExplanation:", recommendation['explanations']['reasoning'])
```

---

## Training Models

### 1. Train Graph Neural Network

```python
from graph_models.graph_trainer import GraphTrainer
from graph_models.graph_builder import GraphBuilder
import pandas as pd

# Load data
products_df = pd.read_csv('data/processed/products.csv')
packaging_df = pd.read_csv('data/processed/packaging.csv')
relationships_df = pd.read_csv('data/processed/relationships.csv')

# Build graph
builder = GraphBuilder()
graph_data = builder.build_full_graph(
    products_df=products_df,
    packaging_df=packaging_df,
    materials_df=materials_df,
    routes_df=routes_df,
    climate_df=climate_df
)

# Train
trainer = GraphTrainer(
    hidden_dim=128,
    num_layers=3,
    model_type='HeteroGNN',
    device='cuda'
)

trained_model = trainer.train(
    graph_data=graph_data,
    num_epochs=100,
    batch_size=64,
    learning_rate=0.001
)

# Save
trainer.save_model('models/gnn_model.pt')
```

### 2. Train Ensemble

```python
from ensemble.stacking_ensemble import StackingEnsemble

ensemble = StackingEnsemble(device='cuda', use_gpu=True)

# Load training data
X_train = pd.read_csv('data/processed/X_train.csv')
y_cost = pd.read_csv('data/processed/y_cost_train.csv').values.ravel()
y_co2 = pd.read_csv('data/processed/y_co2_train.csv').values.ravel()
y_damage = pd.read_csv('data/processed/y_damage_train.csv').values.ravel()

# Train (includes cross-validation)
ensemble.fit(
    X_train=X_train,
    y_cost=y_cost,
    y_co2=y_co2,
    y_damage=y_damage,
    cv_folds=5
)

# Evaluate
X_test = pd.read_csv('data/processed/X_test.csv')
y_test_cost = pd.read_csv('data/processed/y_cost_test.csv').values.ravel()

predictions = ensemble.predict(X_test)
from sklearn.metrics import mean_squared_error, r2_score

cost_rmse = mean_squared_error(y_test_cost, [p['cost'] for p in predictions], squared=False)
cost_r2 = r2_score(y_test_cost, [p['cost'] for p in predictions])

print(f"Cost RMSE: {cost_rmse:.4f}, R²: {cost_r2:.4f}")

# Save
ensemble.save('models/ensemble.pkl')
```

---

## API Integration

### FastAPI Backend (Coming Soon)

```python
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from examples.complete_integration import EnterprisePackagingAI

app = FastAPI(title="ECO_PACK_AI Enterprise API")

# Initialize AI
ai = EnterprisePackagingAI(
    gnn_model_path='models/gnn_model.pt',
    ensemble_model_path='models/ensemble.pkl'
)

class RecommendationRequest(BaseModel):
    product: dict
    packaging_options: list
    preferences: dict = None

@app.post("/api/v1/recommend")
async def recommend(request: RecommendationRequest):
    """Get packaging recommendation."""
    result = ai.recommend_packaging(
        product=request.product,
        packaging_options=request.packaging_options,
        preferences=request.preferences
    )
    return result

@app.post("/api/v1/batch_recommend")
async def batch_recommend(products: list, packaging_options: list):
    """Batch recommendations."""
    results = ai.batch_recommend(products, packaging_options)
    return {"recommendations": results}

@app.get("/health")
async def health():
    return {"status": "healthy"}
```

---

## Performance Optimization

### GPU Acceleration
```python
# Enable GPU for all components
ai = EnterprisePackagingAI(
    gnn_model_path='models/gnn_model.pt',
    ensemble_model_path='models/ensemble.pkl',
    device='cuda'  # Use GPU
)

# Batch processing for throughput
products = load_products_batch(1000)
results = ai.batch_recommend(products, packaging_options)
```

### Caching
```python
# Enable embedding cache for GNN
from graph_models.graph_inference import GraphInference

inference = GraphInference(
    model_path='models/gnn_model.pt',
    cache_embeddings=True,
    max_cache_size=10000
)

# Enable explanation cache
from llm_engine.explanation_generator import ExplanationGenerator

explainer = ExplanationGenerator(use_cache=True)
```

### Async Processing
```python
import asyncio

async def recommend_async(product, options):
    # Async wrapper for CPU-bound operations
    return await asyncio.to_thread(
        ai.recommend_packaging,
        product=product,
        packaging_options=options
    )

# Process multiple concurrently
results = await asyncio.gather(*[
    recommend_async(prod, options)
    for prod in products
])
```

---

## Production Deployment

### Docker
```bash
# Build image
docker build -t ecopackai:latest .

# Run container
docker run -d \
  -p 8000:8000 \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  --gpus all \
  ecopackai:latest
```

### Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ecopackai
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ecopackai
  template:
    metadata:
      labels:
        app: ecopackai
    spec:
      containers:
      - name: api
        image: ecopackai:latest
        resources:
          limits:
            nvidia.com/gpu: 1
```

---

## Troubleshooting

### Common Issues

**Issue: CUDA out of memory**
```python
# Solution: Reduce batch size or use CPU
ai = EnterprisePackagingAI(device='cpu')
```

**Issue: LLM timeout**
```python
# Solution: Increase timeout or use fallback
from llm_engine.llm_client import LLMClient

client = LLMClient(timeout=60)  # 60 seconds
```

**Issue: Slow predictions**
```python
# Solution: Enable caching and batch processing
inference.predict_batch(product_ids, packaging_ids)  # Better than individual
```

---

## Support

- **Documentation**: [GitHub Wiki](https://github.com/your-org/eco-pack-ai/wiki)
- **Issues**: [GitHub Issues](https://github.com/your-org/eco-pack-ai/issues)
- **Email**: support@ecopackai.com
