"""
Model Registry & Versioning
Central management for all models
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import structlog

logger = structlog.get_logger(__name__)


class ModelStatus(Enum):
    """Model status"""
    ACTIVE = "active"
    STANDBY = "standby"
    DEPRECATED = "deprecated"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


@dataclass
class ModelMetadata:
    """Model metadata and health information"""
    model_id: str
    version: str
    status: ModelStatus
    created_at: datetime
    deployed_at: Optional[datetime] = None
    rolled_back_at: Optional[datetime] = None
    
    # Performance metrics
    accuracy: float = 0.0
    latency_p95_ms: float = 0.0
    latency_p99_ms: float = 0.0
    error_rate: float = 0.0
    
    # Health metrics
    requests_processed: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    health_score: float = 1.0  # 0-1, 1.0 = fully healthy
    
    # Drift and retraining
    data_drift_detected: bool = False
    concept_drift_detected: bool = False
    last_retrained_at: Optional[datetime] = None
    retraining_epoch: int = 0
    
    metadata: Dict[str, Any] = field(default_factory=dict)


class ModelRegistry:
    """
    Central registry for model versioning and management
    """
    
    def __init__(self):
        """Initialize model registry"""
        self.models: Dict[str, List[ModelMetadata]] = {}  # model_name -> [versions]
        self.active_models: Dict[str, ModelMetadata] = {}  # model_name -> active version
        self.standby_models: Dict[str, ModelMetadata] = {}  # model_name -> standby version
        
        logger.info("ModelRegistry initialized")
    
    def register_model(
        self,
        model_id: str,
        version: str,
        status: ModelStatus = ModelStatus.ACTIVE,
        **metadata
    ) -> ModelMetadata:
        """
        Register a new model version
        
        Args:
            model_id: Model identifier
            version: Version string (e.g., "v1.0.0")
            status: Initial status
            **metadata: Additional metadata
        
        Returns:
            ModelMetadata
        """
        meta = ModelMetadata(
            model_id=model_id,
            version=version,
            status=status,
            created_at=datetime.utcnow(),
            metadata=metadata
        )
        
        if model_id not in self.models:
            self.models[model_id] = []
        
        self.models[model_id].append(meta)
        
        if status == ModelStatus.ACTIVE:
            self.active_models[model_id] = meta
        elif status == ModelStatus.STANDBY:
            self.standby_models[model_id] = meta
        
        logger.info(
            "Model registered",
            model_id=model_id,
            version=version,
            status=status.value
        )
        
        return meta
    
    def deploy_model(
        self,
        model_id: str,
        version: str
    ) -> ModelMetadata:
        """
        Deploy a model version (mark as active)
        
        Args:
            model_id: Model identifier
            version: Version to deploy
        
        Returns:
            Deployed model metadata
        """
        # Find the version
        if model_id not in self.models:
            raise ValueError(f"Model {model_id} not found")
        
        model = None
        for m in self.models[model_id]:
            if m.version == version:
                model = m
                break
        
        if model is None:
            raise ValueError(f"Version {version} not found for model {model_id}")
        
        # Mark previous active as standby
        if model_id in self.active_models:
            old_active = self.active_models[model_id]
            old_active.status = ModelStatus.STANDBY
            self.standby_models[model_id] = old_active
        
        # Set new as active
        model.status = ModelStatus.ACTIVE
        model.deployed_at = datetime.utcnow()
        self.active_models[model_id] = model
        
        logger.info(
            "Model deployed",
            model_id=model_id,
            version=version
        )
        
        return model
    
    def get_active_model(self, model_id: str) -> Optional[ModelMetadata]:
        """Get active model"""
        return self.active_models.get(model_id)
    
    def get_standby_model(self, model_id: str) -> Optional[ModelMetadata]:
        """Get standby model"""
        return self.standby_models.get(model_id)
    
    def get_model_version(
        self,
        model_id: str,
        version: str
    ) -> Optional[ModelMetadata]:
        """Get specific model version"""
        if model_id not in self.models:
            return None
        
        for m in self.models[model_id]:
            if m.version == version:
                return m
        
        return None
    
    def get_all_versions(self, model_id: str) -> List[ModelMetadata]:
        """Get all versions of a model"""
        return self.models.get(model_id, [])
    
    def update_model_metrics(
        self,
        model_id: str,
        version: str,
        accuracy: float = None,
        latency_p95_ms: float = None,
        latency_p99_ms: float = None,
        error_rate: float = None,
        health_score: float = None
    ) -> ModelMetadata:
        """Update model performance metrics"""
        model = self.get_model_version(model_id, version)
        
        if model is None:
            raise ValueError(f"Model {model_id}:{version} not found")
        
        if accuracy is not None:
            model.accuracy = accuracy
        if latency_p95_ms is not None:
            model.latency_p95_ms = latency_p95_ms
        if latency_p99_ms is not None:
            model.latency_p99_ms = latency_p99_ms
        if error_rate is not None:
            model.error_rate = error_rate
        if health_score is not None:
            model.health_score = health_score
        
        logger.info(
            "Model metrics updated",
            model_id=model_id,
            version=version,
            accuracy=accuracy,
            health_score=health_score
        )
        
        return model
    
    def record_request(
        self,
        model_id: str,
        version: str,
        success: bool
    ) -> None:
        """Record a request to a model"""
        model = self.get_model_version(model_id, version)
        
        if model is None:
            return
        
        model.requests_processed += 1
        
        if success:
            model.successful_requests += 1
        else:
            model.failed_requests += 1
        
        # Update error rate
        if model.requests_processed > 0:
            model.error_rate = model.failed_requests / model.requests_processed
    
    def mark_drift_detected(
        self,
        model_id: str,
        version: str,
        drift_type: str = "data"
    ) -> None:
        """Mark that drift was detected"""
        model = self.get_model_version(model_id, version)
        
        if model is None:
            return
        
        if drift_type == "data":
            model.data_drift_detected = True
        elif drift_type == "concept":
            model.concept_drift_detected = True
        
        logger.warning(
            "Drift detected for model",
            model_id=model_id,
            version=version,
            drift_type=drift_type
        )
    
    def rollback_model(
        self,
        model_id: str,
        target_version: Optional[str] = None
    ) -> ModelMetadata:
        """
        Rollback to previous model version
        
        Args:
            model_id: Model to rollback
            target_version: Specific version to rollback to (default: standby)
        
        Returns:
            Rolled-back model metadata
        """
        if target_version is None:
            # Rollback to standby
            standby = self.standby_models.get(model_id)
            if standby is None:
                raise ValueError(f"No standby model for {model_id}")
            target_version = standby.version
        
        # Get target version
        target_model = self.get_model_version(model_id, target_version)
        if target_model is None:
            raise ValueError(f"Version {target_version} not found")
        
        # Mark current active as rolled back
        active = self.active_models.get(model_id)
        if active:
            active.status = ModelStatus.ROLLED_BACK
            active.rolled_back_at = datetime.utcnow()
        
        # Deploy target version
        self.deploy_model(model_id, target_version)
        
        logger.warning(
            "Model rolled back",
            model_id=model_id,
            rolled_back_version=active.version if active else None,
            target_version=target_version
        )
        
        return target_model
    
    def deprecate_model(self, model_id: str, version: str) -> None:
        """Mark model as deprecated"""
        model = self.get_model_version(model_id, version)
        
        if model:
            model.status = ModelStatus.DEPRECATED
            logger.info(
                "Model deprecated",
                model_id=model_id,
                version=version
            )


__all__ = ['ModelRegistry', 'ModelMetadata', 'ModelStatus']
