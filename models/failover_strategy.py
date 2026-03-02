"""
Failover & Model Rollback Strategy
Ensures high availability with automatic fallback
"""

from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import structlog

from models.model_registry import ModelRegistry, ModelMetadata, ModelStatus
from monitoring.drift_detector import DriftDetector, DriftMetrics

logger = structlog.get_logger(__name__)


class FailoverTrigger(Enum):
    """Reasons to trigger failover"""
    PERFORMANCE_DEGRADATION = "performance_degradation"
    HIGH_ERROR_RATE = "high_error_rate"
    DRIFT_DETECTED = "drift_detected"
    LATENCY_SLA_BREACH = "latency_sla_breach"
    HEALTH_CHECK_FAILED = "health_check_failed"
    MANUAL = "manual"


@dataclass
class FailoverConfig:
    """Configuration for failover behavior"""
    # Failover triggers
    enable_automatic_failover: bool = True
    error_rate_threshold: float = 0.05  # 5% error rate
    latency_p95_threshold_ms: float = 200.0  # P95 exceeds 200ms
    latency_p99_threshold_ms: float = 300.0  # P99 exceeds 300ms
    health_check_interval_seconds: float = 60.0
    health_check_failure_threshold: int = 3  # Consecutive failures before failover
    
    # Drift triggers
    enable_drift_based_failover: bool = True
    drift_severity_threshold: float = 0.7  # 0-1, severity to trigger failover
    
    # Performance degradation
    enable_performance_failover: bool = True
    performance_degradation_threshold: float = 0.1  # 10% degradation
    
    # Timing
    failover_cooldown_seconds: float = 300.0  # Wait 5 minutes before failover again
    max_failovers_per_hour: int = 5  # Prevent thrashing


@dataclass
class FailoverEvent:
    """Record of a failover event"""
    timestamp: datetime
    trigger: FailoverTrigger
    from_model: ModelMetadata
    to_model: ModelMetadata
    reason: str
    success: bool


class FailoverStrategy:
    """
    Implements active-standby failover with automatic rollback
    """
    
    def __init__(
        self,
        model_registry: ModelRegistry,
        drift_detector: DriftDetector = None,
        config: FailoverConfig = None
    ):
        """
        Initialize failover strategy
        
        Args:
            model_registry: Model registry instance
            drift_detector: Drift detector instance
            config: Failover configuration
        """
        self.registry = model_registry
        self.drift_detector = drift_detector
        self.config = config or FailoverConfig()
        
        self.failover_events: List[FailoverEvent] = []
        self.last_failover_time: Dict[str, datetime] = {}
        self.consecutive_health_failures: Dict[str, int] = {}
        
        logger.info("FailoverStrategy initialized", config=self.config.__dict__)
    
    def check_failover_needed(
        self,
        model_id: str,
        current_metrics: Dict[str, Any]
    ) -> bool:
        """
        Check if failover is needed
        
        Args:
            model_id: Model to check
            current_metrics: Current performance metrics
        
        Returns:
            True if failover should be triggered
        """
        if not self.config.enable_automatic_failover:
            return False
        
        active_model = self.registry.get_active_model(model_id)
        standby_model = self.registry.get_standby_model(model_id)
        
        if not standby_model:
            logger.debug("No standby model available")
            return False
        
        # Check cooldown
        if self._is_in_cooldown(model_id):
            return False
        
        # Check error rate
        if self._check_error_rate(current_metrics):
            logger.warning("Error rate threshold exceeded")
            return True
        
        # Check latency
        if self._check_latency(current_metrics):
            logger.warning("Latency SLA breach detected")
            return True
        
        # Check health
        if self._check_health(model_id):
            logger.warning("Health check failed")
            return True
        
        # Check drift
        if self._check_drift(model_id, current_metrics):
            logger.warning("Drift-induced failover triggered")
            return True
        
        return False
    
    def execute_failover(
        self,
        model_id: str,
        trigger: FailoverTrigger,
        reason: str
    ) -> bool:
        """
        Execute failover to standby model
        
        Args:
            model_id: Model to failover
            trigger: Failover trigger type
            reason: Detailed reason
        
        Returns:
            True if failover succeeded
        """
        active_model = self.registry.get_active_model(model_id)
        standby_model = self.registry.get_standby_model(model_id)
        
        if not standby_model:
            logger.error("No standby model available for failover")
            return False
        
        try:
            logger.warning(
                "Executing failover",
                model_id=model_id,
                from_version=active_model.version if active_model else None,
                to_version=standby_model.version,
                trigger=trigger.value,
                reason=reason
            )
            
            # Deploy standby as active
            self.registry.deploy_model(model_id, standby_model.version)
            
            # Record event
            event = FailoverEvent(
                timestamp=datetime.utcnow(),
                trigger=trigger,
                from_model=active_model,
                to_model=standby_model,
                reason=reason,
                success=True
            )
            
            self.failover_events.append(event)
            self.last_failover_time[model_id] = datetime.utcnow()
            self.consecutive_health_failures[model_id] = 0
            
            logger.info(
                "Failover completed successfully",
                model_id=model_id,
                to_version=standby_model.version
            )
            
            return True
        
        except Exception as e:
            logger.error("Failover failed", error=str(e), model_id=model_id)
            
            event = FailoverEvent(
                timestamp=datetime.utcnow(),
                trigger=trigger,
                from_model=active_model,
                to_model=standby_model,
                reason=reason,
                success=False
            )
            
            self.failover_events.append(event)
            return False
    
    def health_check(
        self,
        model_id: str,
        health_check_fn: Callable[[], bool]
    ) -> bool:
        """
        Perform health check on active model
        
        Args:
            model_id: Model to check
            health_check_fn: Function that returns True if healthy
        
        Returns:
            True if model is healthy
        """
        try:
            is_healthy = health_check_fn()
            
            if is_healthy:
                self.consecutive_health_failures[model_id] = 0
                logger.debug("Health check passed", model_id=model_id)
                return True
            
            else:
                self.consecutive_health_failures[model_id] = \
                    self.consecutive_health_failures.get(model_id, 0) + 1
                
                logger.warning(
                    "Health check failed",
                    model_id=model_id,
                    consecutive_failures=self.consecutive_health_failures[model_id]
                )
                
                return False
        
        except Exception as e:
            self.consecutive_health_failures[model_id] = \
                self.consecutive_health_failures.get(model_id, 0) + 1
            
            logger.error("Health check exception", error=str(e), model_id=model_id)
            return False
    
    def _is_in_cooldown(self, model_id: str) -> bool:
        """Check if failover is in cooldown period"""
        last_failover = self.last_failover_time.get(model_id)
        
        if not last_failover:
            return False
        
        elapsed = (datetime.utcnow() - last_failover).total_seconds()
        in_cooldown = elapsed < self.config.failover_cooldown_seconds
        
        if in_cooldown:
            logger.debug(
                "Failover in cooldown",
                model_id=model_id,
                elapsed=elapsed,
                cooldown=self.config.failover_cooldown_seconds
            )
        
        return in_cooldown
    
    def _check_error_rate(self, metrics: Dict[str, Any]) -> bool:
        """Check if error rate exceeds threshold"""
        if not self.config.enable_automatic_failover:
            return False
        
        error_rate = metrics.get('error_rate', 0)
        return error_rate > self.config.error_rate_threshold
    
    def _check_latency(self, metrics: Dict[str, Any]) -> bool:
        """Check if latency exceeds thresholds"""
        if not self.config.enable_automatic_failover:
            return False
        
        p95 = metrics.get('latency_p95_ms', 0)
        p99 = metrics.get('latency_p99_ms', 0)
        
        return (p95 > self.config.latency_p95_threshold_ms or
                p99 > self.config.latency_p99_threshold_ms)
    
    def _check_health(self, model_id: str) -> bool:
        """Check if consecutive health checks have failed"""
        if not self.config.enable_automatic_failover:
            return False
        
        consecutive_failures = self.consecutive_health_failures.get(model_id, 0)
        return consecutive_failures >= self.config.health_check_failure_threshold
    
    def _check_drift(self, model_id: str, metrics: Dict[str, Any]) -> bool:
        """Check if drift is severe enough to trigger failover"""
        if not (self.config.enable_drift_based_failover and self.drift_detector):
            return False
        
        drift_severity = metrics.get('drift_severity', 0)
        return drift_severity > self.config.drift_severity_threshold
    
    def get_failover_history(self) -> List[FailoverEvent]:
        """Get failover event history"""
        return self.failover_events
    
    def get_failover_count_last_hour(self) -> int:
        """Get number of failovers in last hour"""
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        
        return sum(
            1 for event in self.failover_events
            if event.timestamp > one_hour_ago and event.success
        )


class CircuitBreaker:
    """
    Circuit breaker for model inference
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout_seconds: int = 60
    ):
        """
        Initialize circuit breaker
        
        Args:
            failure_threshold: Failures before opening circuit
            recovery_timeout_seconds: Time to wait before half-open
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout_seconds
        
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "closed"  # closed, open, half-open
    
    def record_success(self) -> None:
        """Record successful call"""
        self.failure_count = 0
        self.state = "closed"
    
    def record_failure(self) -> None:
        """Record failed call"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.warning(
                "Circuit breaker opened",
                failure_count=self.failure_count
            )
    
    def is_open(self) -> bool:
        """Check if circuit is open"""
        if self.state == "open":
            # Check if we should try half-open
            if self.last_failure_time:
                elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
                
                if elapsed > self.recovery_timeout:
                    self.state = "half-open"
                    logger.info("Circuit breaker entering half-open state")
                    return False
            
            return True
        
        return False


__all__ = ['FailoverStrategy', 'FailoverConfig', 'FailoverEvent', 'FailoverTrigger', 'CircuitBreaker']
