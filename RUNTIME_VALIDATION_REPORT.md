# ECO_PACK_AI Runtime Validation Report

Generated: 2026-03-01T19:19:05.360340
Python Version: 3.13.5

## Executive Summary

System Health Score: **0.0/100**

- Total Checks: 39
- Passed: 34
- Failed: 5
- Warnings: 1
- Errors: 5

## Detailed Results

### Python Version
Status: [PASS]
Message: Python 3.13.5 ✓

### Project Directories
Status: [PASS]
Message: All 12 directories present

### Dependency: PyTorch (ML Backend)
Status: [PASS]
Message: torch==2.10.0+cpu

### Dependency: PyTorch Geometric (GNN)
Status: [FAIL]
Message: Import failed: No module named 'torch-geometric'

### Dependency: FastAPI (API Framework)
Status: [PASS]
Message: fastapi==0.119.0

### Dependency: Uvicorn (ASGI Server)
Status: [PASS]
Message: uvicorn==0.37.0

### Dependency: Pandas (Data Processing)
Status: [PASS]
Message: pandas==2.2.3

### Dependency: NumPy (Numerical Ops)
Status: [PASS]
Message: numpy==2.1.1

### Dependency: Scikit-Learn (ML)
Status: [PASS]
Message: sklearn==1.6.1

### Dependency: XGBoost (Gradient Boosting)
Status: [PASS]
Message: xgboost==3.2.0

### Dependency: PyMOO (Multi-Objective Optimization)
Status: [PASS]
Message: pymoo==0.6.1.6

### Dependency: StructLog (Logging)
Status: [PASS]
Message: structlog==25.5.0

### Dependency: SciPy (Scientific Computing)
Status: [PASS]
Message: scipy==1.16.2

### Dependency: NetworkX (Graph Algorithms)
Status: [PASS]
Message: networkx==3.4.2

### Import: GNN Model
Status: [FAIL]
Message: Import failed: cannot import name 'NeighborLoader' from '<unknown module name>' (unknown location)

### Import: Graph Builder
Status: [PASS]
Message: Successfully imported graph_models.graph_builder

### Import: Optimization Engine
Status: [PASS]
Message: Successfully imported optimization.optimization_engine

### Import: Carbon Calculator
Status: [PASS]
Message: Successfully imported carbon_engine.carbon_calculator

### Import: LLM Client
Status: [PASS]
Message: Successfully imported llm_engine.llm_client

### Import: Feedback Collector
Status: [PASS]
Message: Successfully imported online_learning.feedback_collector

### Import: Drift Detector
Status: [PASS]
Message: Successfully imported monitoring.drift_detector

### Import: Uncertainty Estimator
Status: [PASS]
Message: Successfully imported uncertainty.uncertainty_estimator

### Import: Financial Impact Engine
Status: [PASS]
Message: Successfully imported roi_engine.financial_impact

### Import: FastAPI Application
Status: [PASS]
Message: Successfully imported src.api

### GNN: Module Import
Status: [PASS]
Message: HeteroGNN module imported successfully

### Ensemble: Instantiation
Status: [PASS]
Message: StackingEnsemble created

### Ensemble: Module Loaded
Status: [PASS]
Message: Stacking Ensemble module available

### Optimization: Setup
Status: [FAIL]
Message: The truth value of an array with more than one element is ambiguous. Use a.any() or a.all()

### Carbon Engine: Instantiation
Status: [PASS]
Message: CarbonAccountingEngine created

### Carbon Engine: Analysis
Status: [FAIL]
Message: Analysis complete, Grade: N/A

### Drift Detector: Instantiation
Status: [PASS]
Message: DriftDetector created

### Drift Detector: Detection
Status: [PASS]
Message: Drift detection result: DriftType.NONE

### Uncertainty: Instantiation
Status: [PASS]
Message: UncertaintyEstimator created

### Uncertainty: Estimation
Status: [PASS]
Message: Generated uncertainty estimate with confidence

### ROI Engine: Instantiation
Status: [PASS]
Message: FinancialROIEngine created

### ROI Engine: Calculation
Status: [FAIL]
Message: ROI: -4445.5%, Payback: inf months

### API: Flask App
Status: [PASS]
Message: Flask application loaded successfully

### API: Server Ready
Status: [PASS]
Message: API framework loaded - Flask

### E2E: Module Imports
Status: [PASS]
Message: All major modules imported successfully

## Warnings

- [WARN] Module graph_models.gnn_model failed import: Traceback (most recent call last):
  File "C:\vivek\Infosys_Internship\ECO_PACK_AI\ECO_PACK_AI\validate_runtime.py", line 240, in validate_imports
    mod = importlib.import_module(module_path)
  File "C:\Users\vivek\AppData\Local\Programs\Python\Python313\Lib\importlib\__init__.py", line 88, in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<frozen importlib._bootstrap>", line 1387, in _gcd_import
  File "<frozen importlib._bootstrap>", line 1360, in _find_and_load
  File "<frozen importlib._bootstrap>", line 1310, in _find_and_load_unlocked
  File "<frozen importlib._bootstrap>", line 488, in _call_with_frames_removed
  File "<frozen importlib._bootstrap>", line 1387, in _gcd_import
  File "<frozen importlib._bootstrap>", line 1360, in _find_and_load
  File "<frozen importlib._bootstrap>", line 1331, in _find_and_load_unlocked
  File "<frozen importlib._bootstrap>", line 935, in _load_unlocked
  File "<frozen importlib._bootstrap_external>", line 1026, in exec_module
  File "<frozen importlib._bootstrap>", line 488, in _call_with_frames_removed
  File "C:\vivek\Infosys_Internship\ECO_PACK_AI\ECO_PACK_AI\graph_models\__init__.py", line 8, in <module>
    from .graph_trainer import GraphTrainer
  File "C:\vivek\Infosys_Internship\ECO_PACK_AI\ECO_PACK_AI\graph_models\graph_trainer.py", line 14, in <module>
    from torch_geometric.loader import NeighborLoader
ImportError: cannot import name 'NeighborLoader' from '<unknown module name>' (unknown location)


## Errors Found

- [ERROR] Dependency: PyTorch Geometric (GNN): Import failed: No module named 'torch-geometric'
- [ERROR] Import: GNN Model: Import failed: cannot import name 'NeighborLoader' from '<unknown module name>' (unknown location)
- [ERROR] Optimization: Setup: The truth value of an array with more than one element is ambiguous. Use a.any() or a.all()
- [ERROR] Carbon Engine: Analysis: Analysis complete, Grade: N/A
- [ERROR] ROI Engine: Calculation: ROI: -4445.5%, Payback: inf months

