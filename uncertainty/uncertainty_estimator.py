"""
Uncertainty Estimation Module
Provides confidence ranges for predictions
"""

import numpy as np
from typing import Dict, Any, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import structlog

logger = structlog.get_logger(__name__)


class RiskLevel(Enum):
    """Risk levels for predictions"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class PredictionWithUncertainty:
    """Prediction with confidence and uncertainty estimates"""
    value: float
    confidence_score: float  # 0-1
    uncertainty_interval: Tuple[float, float]  # (lower, upper)
    risk_level: RiskLevel
    std_dev: float  # Standard deviation
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'value': float(self.value),
            'confidence_score': float(self.confidence_score),
            'uncertainty_interval': [float(self.uncertainty_interval[0]), float(self.uncertainty_interval[1])],
            'risk_level': self.risk_level.value,
            'std_dev': float(self.std_dev)
        }


class UncertaintyEstimator:
    """
    Estimates prediction uncertainty and confidence.
    Combines multiple uncertainty estimation techniques.
    """
    
    def __init__(
        self,
        confidence_threshold_low: float = 0.85,
        confidence_threshold_high: float = 0.95,
        uncertainty_percentile: float = 0.95
    ):
        """
        Initialize uncertainty estimator
        
        Args:
            confidence_threshold_low: Below this = medium risk
            confidence_threshold_high: Below this = high risk
            uncertainty_percentile: Percentile for confidence interval
        """
        self.confidence_threshold_low = confidence_threshold_low
        self.confidence_threshold_high = confidence_threshold_high
        self.uncertainty_percentile = uncertainty_percentile
        
        logger.info(
            "UncertaintyEstimator initialized",
            low_threshold=confidence_threshold_low,
            high_threshold=confidence_threshold_high
        )
    
    def estimate_from_ensemble(
        self,
        ensemble_predictions: np.ndarray,
        metric_name: str = "ensemble"
    ) -> PredictionWithUncertainty:
        """
        Estimate uncertainty from ensemble predictions
        
        Uses variance across ensemble members.
        
        Args:
            ensemble_predictions: Array of shape (n_models,) with predictions
            metric_name: Name of metric being predicted
        
        Returns:
            Prediction with uncertainty
        """
        mean = np.mean(ensemble_predictions)
        std_dev = np.std(ensemble_predictions)
        
        # Confidence based on ensemble agreement
        # If all models agree (low std), confidence is high
        confidence_score = 1.0 / (1.0 + std_dev)  # Sigmoid-like scaling
        confidence_score = np.clip(confidence_score, 0, 1)
        
        # Confidence interval (95%)
        z_score = 1.96  # 95% confidence
        margin_of_error = z_score * std_dev / np.sqrt(len(ensemble_predictions))
        lower = mean - margin_of_error
        upper = mean + margin_of_error
        
        # Risk level
        risk_level = self._assess_risk_level(confidence_score)
        
        logger.debug(
            "Ensemble uncertainty estimated",
            metric=metric_name,
            confidence=confidence_score,
            std_dev=std_dev
        )
        
        return PredictionWithUncertainty(
            value=mean,
            confidence_score=confidence_score,
            uncertainty_interval=(max(0, lower), upper),
            risk_level=risk_level,
            std_dev=float(std_dev)
        )
    
    def estimate_from_bootstrap(
        self,
        bootstrap_predictions: np.ndarray,
        percentile: Optional[float] = None
    ) -> PredictionWithUncertainty:
        """
        Estimate uncertainty from bootstrap ensemble
        
        Args:
            bootstrap_predictions: Array of shape (n_bootstrap,) with predictions
            percentile: Percentile for percentile-based CI
        
        Returns:
            Prediction with uncertainty
        """
        if percentile is None:
            percentile = self.uncertainty_percentile
        
        mean = np.mean(bootstrap_predictions)
        std_dev = np.std(bootstrap_predictions)
        
        # Confidence score based on ensemble variance
        confidence_score = 1.0 / (1.0 + std_dev) if std_dev > 0 else 1.0
        confidence_score = np.clip(confidence_score, 0, 1)
        
        # Percentile-based confidence interval
        lower_percentile = (100 - percentile) / 2
        upper_percentile = 100 - lower_percentile
        
        lower = np.percentile(bootstrap_predictions, lower_percentile)
        upper = np.percentile(bootstrap_predictions, upper_percentile)
        
        risk_level = self._assess_risk_level(confidence_score)
        
        return PredictionWithUncertainty(
            value=mean,
            confidence_score=confidence_score,
            uncertainty_interval=(lower, upper),
            risk_level=risk_level,
            std_dev=float(std_dev)
        )
    
    def estimate_from_dropout(
        self,
        dropout_predictions: np.ndarray,
        num_samples: int = 100
    ) -> PredictionWithUncertainty:
        """
        Estimate uncertainty using Monte Carlo Dropout
        
        Args:
            dropout_predictions: Array of shape (num_samples,) from dropout predictions
            num_samples: Number of dropout samples (for scaling)
        
        Returns:
            Prediction with uncertainty
        """
        mean = np.mean(dropout_predictions)
        std_dev = np.std(dropout_predictions)
        
        # Confidence inversely proportional to variance
        confidence_score = np.exp(-std_dev / mean) if mean > 0 else 0.5
        confidence_score = np.clip(confidence_score, 0, 1)
        
        # Standard error
        standard_error = std_dev / np.sqrt(num_samples)
        z_score = 1.96  # 95% CI
        
        lower = mean - z_score * standard_error
        upper = mean + z_score * standard_error
        
        risk_level = self._assess_risk_level(confidence_score)
        
        return PredictionWithUncertainty(
            value=mean,
            confidence_score=confidence_score,
            uncertainty_interval=(max(0, lower), upper),
            risk_level=risk_level,
            std_dev=float(std_dev)
        )
    
    def estimate_from_prediction_range(
        self,
        points: np.ndarray,
        weights: Optional[np.ndarray] = None,
        use_mad: bool = True
    ) -> PredictionWithUncertainty:
        """
        Estimate uncertainty from range of predictions
        
        Args:
            points: Array of predictions
            weights: Optional weights for predictions
            use_mad: Use Median Absolute Deviation (more robust)
        
        Returns:
            Prediction with uncertainty
        """
        if weights is not None:
            mean = np.average(points, weights=weights)
        else:
            mean = np.mean(points)
        
        if use_mad:
            # Median Absolute Deviation (robust to outliers)
            median = np.median(points)
            mad = np.median(np.abs(points - median))
            std_dev = 1.4826 * mad  # Constant to convert MAD to std dev
        else:
            std_dev = np.std(points)
        
        # Confidence from range compression
        range_width = np.max(points) - np.min(points)
        confidence_score = 1.0 / (1.0 + range_width / mean) if mean > 0 else 0.5
        confidence_score = np.clip(confidence_score, 0, 1)
        
        # Confidence interval
        z_score = 1.96
        margin = z_score * std_dev
        
        lower = mean - margin
        upper = mean + margin
        
        risk_level = self._assess_risk_level(confidence_score)
        
        return PredictionWithUncertainty(
            value=mean,
            confidence_score=confidence_score,
            uncertainty_interval=(max(0, lower), upper),
            risk_level=risk_level,
            std_dev=float(std_dev)
        )
    
    def combine_multiple_estimates(
        self,
        estimates: list[PredictionWithUncertainty],
        weights: Optional[np.ndarray] = None
    ) -> PredictionWithUncertainty:
        """
        Combine multiple uncertainty estimates
        
        Args:
            estimates: List of uncertainty estimates
            weights: Optional weights for each estimate
        
        Returns:
            Combined prediction with uncertainty
        """
        values = np.array([e.value for e in estimates])
        std_devs = np.array([e.std_dev for e in estimates])
        confidences = np.array([e.confidence_score for e in estimates])
        
        if weights is not None:
            combined_value = np.average(values, weights=weights)
            combined_std = np.average(std_devs, weights=weights)
            combined_confidence = np.average(confidences, weights=weights)
        else:
            combined_value = np.mean(values)
            combined_std = np.mean(std_devs)
            combined_confidence = np.mean(confidences)
        
        # Confidence interval from combined std dev
        z_score = 1.96
        margin = z_score * combined_std
        
        lower = combined_value - margin
        upper = combined_value + margin
        
        risk_level = self._assess_risk_level(combined_confidence)
        
        return PredictionWithUncertainty(
            value=combined_value,
            confidence_score=float(combined_confidence),
            uncertainty_interval=(max(0, lower), upper),
            risk_level=risk_level,
            std_dev=float(combined_std)
        )
    
    def _assess_risk_level(self, confidence_score: float) -> RiskLevel:
        """Assess risk level from confidence score"""
        if confidence_score >= self.confidence_threshold_high:
            return RiskLevel.LOW
        elif confidence_score >= self.confidence_threshold_low:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.HIGH
    
    def get_prediction_with_uncertainty(
        self,
        value: float,
        std_dev: float,
        confidence: float,
        risk_level: RiskLevel = None
    ) -> Dict[str, Any]:
        """
        Format prediction with uncertainty for output
        
        Args:
            value: Predicted value
            std_dev: Standard deviation
            confidence: Confidence score
            risk_level: Risk level (auto-calculated if None)
        
        Returns:
            Dictionary suitable for API output
        """
        if risk_level is None:
            risk_level = self._assess_risk_level(confidence)
        
        z_score = 1.96
        margin = z_score * std_dev
        
        return {
            'value': float(value),
            'confidence_score': float(confidence),
            'uncertainty_interval': [
                float(max(0, value - margin)),
                float(value + margin)
            ],
            'risk_level': risk_level.value,
            'std_dev': float(std_dev)
        }


# Module initialization
__all__ = [
    'UncertaintyEstimator',
    'PredictionWithUncertainty',
    'RiskLevel'
]
