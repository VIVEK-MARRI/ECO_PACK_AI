"""
Retraining Scheduler
Orchestrates incremental model retraining based on feedback
"""

import structlog
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import json

logger = structlog.get_logger(__name__)


class RetrainingTriggerType(Enum):
    """Trigger types for retraining"""
    SCHEDULED = "scheduled"  # Weekly/monthly schedule
    DATA_THRESHOLD = "data_threshold"  # N new samples
    DRIFT_DETECTED = "drift_detected"  # Statistical drift
    PERFORMANCE_DEGRADATION = "performance_degradation"  # Metrics degraded
    MANUAL = "manual"  # User-initiated


@dataclass
class RetrainingConfig:
    """Configuration for retraining"""
    # Scheduling
    schedule_interval_days: int = 7  # Retrain weekly
    
    # Data triggers
    min_samples_for_retrain: int = 1000  # Need 1000 new outcomes
    
    # Drift triggers
    drift_threshold: float = 0.3  # KL divergence threshold
    feature_drift_threshold: float = 0.2  # Kolmogorov-Smirnov test p-value
    
    # Performance triggers
    metric_degradation_pct: float = 5.0  # Allow 5% metric degradation
    
    # Retraining
    epochs: int = 10  # Mini-batch epochs
    learning_rate: float = 0.0001  # Lower for fine-tuning
    batch_size: int = 256
    validation_split: float = 0.2
    
    # Versioning
    keep_model_versions: int = 5
    auto_rollback_on_degradation: bool = True


class RetrainingScheduler:
    """
    Schedules and coordinates incremental retraining.
    Monitors multiple trigger conditions.
    """
    
    def __init__(self, config: RetrainingConfig = None):
        """
        Initialize retraining scheduler
        
        Args:
            config: Retraining configuration
        """
        self.config = config or RetrainingConfig()
        self.last_retraining_time = datetime.utcnow()
        self.retraining_history: List[Dict[str, Any]] = []
        self.pending_retraining: Dict[RetrainingTriggerType, bool] = {
            trigger: False for trigger in RetrainingTriggerType
        }
        
        logger.info(
            "RetrainingScheduler initialized",
            schedule_interval=self.config.schedule_interval_days,
            min_samples=self.config.min_samples_for_retrain
        )
    
    def check_scheduled_retrain(self) -> bool:
        """Check if scheduled retraining is due"""
        elapsed = datetime.utcnow() - self.last_retraining_time
        interval = timedelta(days=self.config.schedule_interval_days)
        
        is_due = elapsed >= interval
        
        if is_due:
            logger.info(
                "Scheduled retraining due",
                days_elapsed=elapsed.days,
                schedule_days=self.config.schedule_interval_days
            )
            self.pending_retraining[RetrainingTriggerType.SCHEDULED] = True
        
        return is_due
    
    def check_data_threshold(self, new_samples: int) -> bool:
        """Check if minimum new samples collected"""
        is_threshold_met = new_samples >= self.config.min_samples_for_retrain
        
        if is_threshold_met:
            logger.info(
                "Data threshold reached for retraining",
                new_samples=new_samples,
                threshold=self.config.min_samples_for_retrain
            )
            self.pending_retraining[RetrainingTriggerType.DATA_THRESHOLD] = True
        
        return is_threshold_met
    
    def check_drift(
        self,
        feature_drift_metric: float,
        label_drift_metric: float
    ) -> bool:
        """
        Check for statistical drift
        
        Args:
            feature_drift_metric: Feature space drift (KL divergence)
            label_drift_metric: Label space drift (KL divergence)
        
        Returns:
            True if drift detected
        """
        max_drift = max(feature_drift_metric, label_drift_metric)
        is_drift_detected = max_drift > self.config.drift_threshold
        
        if is_drift_detected:
            logger.warning(
                "Drift detected - retraining triggered",
                feature_drift=feature_drift_metric,
                label_drift=label_drift_metric,
                threshold=self.config.drift_threshold
            )
            self.pending_retraining[RetrainingTriggerType.DRIFT_DETECTED] = True
        
        return is_drift_detected
    
    def check_performance_degradation(
        self,
        current_metrics: Dict[str, float],
        baseline_metrics: Dict[str, float]
    ) -> bool:
        """
        Check if model performance degraded
        
        Args:
            current_metrics: Current performance metrics
            baseline_metrics: Baseline metrics to compare
        
        Returns:
            True if degradation detected
        """
        degradations = {}
        max_degradation = 0.0
        
        for metric_name, baseline_value in baseline_metrics.items():
            if metric_name not in current_metrics:
                continue
            
            current_value = current_metrics[metric_name]
            
            # For loss metrics (lower is better), degradation means increase
            if 'loss' in metric_name or 'error' in metric_name:
                degradation = ((current_value - baseline_value) / baseline_value * 100)
                is_degraded = degradation > self.config.metric_degradation_pct
            
            # For accuracy metrics (higher is better), degradation means decrease
            else:
                degradation = ((baseline_value - current_value) / baseline_value * 100)
                is_degraded = degradation > self.config.metric_degradation_pct
            
            if is_degraded:
                degradations[metric_name] = degradation
                max_degradation = max(max_degradation, abs(degradation))
        
        if degradations:
            logger.warning(
                "Performance degradation detected",
                degradations=degradations,
                threshold_pct=self.config.metric_degradation_pct
            )
            self.pending_retraining[RetrainingTriggerType.PERFORMANCE_DEGRADATION] = True
            return True
        
        return False
    
    def should_retrain(self) -> bool:
        """Check if any retraining trigger is pending"""
        return any(self.pending_retraining.values())
    
    def get_pending_triggers(self) -> List[RetrainingTriggerType]:
        """Get all pending retrain triggers"""
        return [
            trigger for trigger, is_pending in self.pending_retraining.items()
            if is_pending
        ]
    
    def trigger_manual_retrain(self) -> bool:
        """Trigger manual retraining"""
        logger.info("Manual retraining triggered")
        self.pending_retraining[RetrainingTriggerType.MANUAL] = True
        return True
    
    def record_retrain_result(
        self,
        triggers: List[RetrainingTriggerType],
        success: bool,
        old_model_version: str,
        new_model_version: str,
        metrics_before: Dict[str, float],
        metrics_after: Dict[str, float],
        samples_used: int,
        duration_seconds: float
    ) -> None:
        """
        Record retraining result
        
        Args:
            triggers: Triggers that caused retraining
            success: Whether retraining was successful
            old_model_version: Previous model version
            new_model_version: New model version
            metrics_before: Metrics before retraining
            metrics_after: Metrics after retraining
            samples_used: Number of samples used
            duration_seconds: Retraining duration
        """
        result = {
            'timestamp': datetime.utcnow().isoformat(),
            'triggers': [t.value for t in triggers],
            'success': success,
            'old_model_version': old_model_version,
            'new_model_version': new_model_version,
            'metrics_before': metrics_before,
            'metrics_after': metrics_after,
            'samples_used': samples_used,
            'duration_seconds': duration_seconds,
            'improvement_pct': {}
        }
        
        # Calculate improvements
        for metric, before_value in metrics_before.items():
            if metric in metrics_after:
                after_value = metrics_after[metric]
                if before_value != 0:
                    improvement = ((after_value - before_value) / before_value) * 100
                    result['improvement_pct'][metric] = improvement
        
        self.retraining_history.append(result)
        self.last_retraining_time = datetime.utcnow()
        
        # Reset triggers
        self.pending_retraining = {
            trigger: False for trigger in RetrainingTriggerType
        }
        
        log_level = 'info' if success else 'error'
        logger.log(
            log_level,
            "Retraining result recorded",
            success=success,
            new_version=new_model_version,
            samples=samples_used,
            duration_s=duration_seconds
        )
    
    def get_retraining_status(self) -> Dict[str, Any]:
        """Get current retraining status"""
        pending_triggers = self.get_pending_triggers()
        
        return {
            'should_retrain': self.should_retrain(),
            'pending_triggers': [t.value for t in pending_triggers],
            'last_retrain_time': self.last_retraining_time.isoformat(),
            'retrainings_count': len(self.retraining_history),
            'recent_retraining': self.retraining_history[-1] if self.retraining_history else None
        }
    
    def get_retraining_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get retraining history"""
        return self.retraining_history[-limit:]
