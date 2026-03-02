"""
Drift Detection & Auto-Retraining Pipeline
Monitors data distribution and model performance drift
"""

from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import numpy as np
import structlog
from scipy import stats

logger = structlog.get_logger(__name__)


class DriftType(Enum):
    """Types of drift detected"""
    COVARIATE = "covariate"  # Input distribution changed
    LABEL = "label"  # Output distribution changed
    CONCEPT = "concept"  # Relationship between input/output changed
    TEMPORAL = "temporal"  # Time-dependent drift
    NONE = "none"  # No drift detected


@dataclass
class DriftMetrics:
    """Drift metrics and thresholds"""
    kl_divergence: float  # Kullback-Leibler divergence
    ks_statistic: float  # Kolmogorov-Smirnov statistic
    ks_pvalue: float  # KS test p-value
    wasserstein_distance: float  # Earth Mover's distance
    distribution_shift: float  # Custom shift metric
    feature_importance_change: Dict[str, float]  # Per-feature changes
    
    drift_detected: bool
    drift_type: DriftType
    severity: float  # 0-1, 0 = no drift, 1 = severe drift


class DriftDetectionMethod(Enum):
    """Drift detection methods"""
    KL_DIVERGENCE = "kl_divergence"
    KOLMOGOROV_SMIRNOV = "kolmogorov_smirnov"
    WASSERSTEIN = "wasserstein"
    FEATURE_IMPORTANCE = "feature_importance"
    ENSEMBLE = "ensemble"  # Multiple methods


class DriftDetector:
    """
    Detects data drift and concept drift
    """
    
    def __init__(
        self,
        baseline_data: np.ndarray = None,
        kl_threshold: float = 0.3,
        ks_threshold: float = 0.05,
        wasserstein_threshold: float = 0.5,
        ensemble_threshold: float = 0.6
    ):
        """
        Initialize drift detector
        
        Args:
            baseline_data: Baseline data distribution
            kl_threshold: KL divergence threshold
            ks_threshold: KS test p-value threshold
            wasserstein_threshold: Wasserstein distance threshold
            ensemble_threshold: Ensemble voting threshold (0-1)
        """
        self.baseline_data = baseline_data
        self.kl_threshold = kl_threshold
        self.ks_threshold = ks_threshold
        self.wasserstein_threshold = wasserstein_threshold
        self.ensemble_threshold = ensemble_threshold
        
        self.baseline_stats = self._calculate_stats(baseline_data) if baseline_data is not None else None
        
        logger.info(
            "DriftDetector initialized",
            kl_threshold=kl_threshold,
            ks_threshold=ks_threshold
        )
    
    def detect_drift(
        self,
        current_data: np.ndarray,
        method: DriftDetectionMethod = DriftDetectionMethod.ENSEMBLE,
        verbose: bool = True
    ) -> DriftMetrics:
        """
        Detect drift in current data
        
        Args:
            current_data: Current data batch
            method: Detection method
            verbose: Log detailed results
        
        Returns:
            Drift metrics
        """
        if self.baseline_data is None:
            raise ValueError("Baseline data required for drift detection")
        
        logger.info(
            "Starting drift detection",
            samples=len(current_data),
            method=method.value
        )
        
        if method == DriftDetectionMethod.KL_DIVERGENCE:
            return self._detect_kl_divergence(current_data, verbose)
        elif method == DriftDetectionMethod.KOLMOGOROV_SMIRNOV:
            return self._detect_ks(current_data, verbose)
        elif method == DriftDetectionMethod.WASSERSTEIN:
            return self._detect_wasserstein(current_data, verbose)
        elif method == DriftDetectionMethod.ENSEMBLE:
            return self._detect_ensemble(current_data, verbose)
        
        raise ValueError(f"Unknown method: {method}")
    
    def _detect_kl_divergence(
        self,
        current_data: np.ndarray,
        verbose: bool = True
    ) -> DriftMetrics:
        """Detect drift using KL divergence"""
        # Flatten for distribution estimation
        baseline_flat = self.baseline_data.flatten()
        current_flat = current_data.flatten()
        
        # Create histograms
        min_val = min(baseline_flat.min(), current_flat.min())
        max_val = max(baseline_flat.max(), current_flat.max())
        
        bins = np.linspace(min_val, max_val, 50)
        
        p, _ = np.histogram(baseline_flat, bins=bins)
        q, _ = np.histogram(current_flat, bins=bins)
        
        # Normalize
        p = p / p.sum()
        q = q / q.sum()
        
        # Add small epsilon to avoid log(0)
        epsilon = 1e-10
        p = p + epsilon
        q = q + epsilon
        p = p / p.sum()
        q = q / q.sum()
        
        # Calculate KL divergence
        kl_div = np.sum(p * np.log(p / q))
        
        drift_detected = kl_div > self.kl_threshold
        severity = min(1.0, kl_div / (self.kl_threshold * 2))
        
        drift_type = DriftType.COVARIATE if drift_detected else DriftType.NONE
        
        if verbose:
            logger.info(
                "KL divergence detection",
                kl=kl_div,
                threshold=self.kl_threshold,
                drift_detected=drift_detected
            )
        
        return DriftMetrics(
            kl_divergence=float(kl_div),
            ks_statistic=0.0,
            ks_pvalue=1.0,
            wasserstein_distance=0.0,
            distribution_shift=float(kl_div),
            feature_importance_change={},
            drift_detected=drift_detected,
            drift_type=drift_type,
            severity=float(severity)
        )
    
    def _detect_ks(
        self,
        current_data: np.ndarray,
        verbose: bool = True
    ) -> DriftMetrics:
        """Detect drift using Kolmogorov-Smirnov test"""
        baseline_flat = self.baseline_data.flatten()
        current_flat = current_data.flatten()
        
        # Perform KS test
        ks_stat, ks_pval = stats.ks_2samp(baseline_flat, current_flat)
        
        # Drift if p-value < threshold (reject null hypothesis of same distribution)
        drift_detected = ks_pval < self.ks_threshold
        severity = min(1.0, 1 - ks_pval)  # Higher severity = lower p-value
        
        drift_type = DriftType.COVARIATE if drift_detected else DriftType.NONE
        
        if verbose:
            logger.info(
                "KS test detection",
                ks_stat=ks_stat,
                ks_pval=ks_pval,
                threshold=self.ks_threshold,
                drift_detected=drift_detected
            )
        
        return DriftMetrics(
            kl_divergence=0.0,
            ks_statistic=float(ks_stat),
            ks_pvalue=float(ks_pval),
            wasserstein_distance=0.0,
            distribution_shift=float(max(0, 1 - ks_pval)),
            feature_importance_change={},
            drift_detected=drift_detected,
            drift_type=drift_type,
            severity=float(severity)
        )
    
    def _detect_wasserstein(
        self,
        current_data: np.ndarray,
        verbose: bool = True
    ) -> DriftMetrics:
        """Detect drift using Wasserstein distance"""
        baseline_flat = self.baseline_data.flatten()
        current_flat = current_data.flatten()
        
        # Calculate Wasserstein distance (Earth Mover's Distance)
        wasserstein = stats.wasserstein_distance(baseline_flat, current_flat)
        
        drift_detected = wasserstein > self.wasserstein_threshold
        severity = min(1.0, wasserstein / (self.wasserstein_threshold * 2))
        
        drift_type = DriftType.COVARIATE if drift_detected else DriftType.NONE
        
        if verbose:
            logger.info(
                "Wasserstein detection",
                wasserstein=wasserstein,
                threshold=self.wasserstein_threshold,
                drift_detected=drift_detected
            )
        
        return DriftMetrics(
            kl_divergence=0.0,
            ks_statistic=0.0,
            ks_pvalue=1.0,
            wasserstein_distance=float(wasserstein),
            distribution_shift=float(wasserstein),
            feature_importance_change={},
            drift_detected=drift_detected,
            drift_type=drift_type,
            severity=float(severity)
        )
    
    def _detect_ensemble(
        self,
        current_data: np.ndarray,
        verbose: bool = True
    ) -> DriftMetrics:
        """Detect drift using ensemble of multiple methods"""
        # Run all methods
        kl_result = self._detect_kl_divergence(current_data, verbose=False)
        ks_result = self._detect_ks(current_data, verbose=False)
        ws_result = self._detect_wasserstein(current_data, verbose=False)
        
        # Ensemble voting
        votes = [
            kl_result.drift_detected,
            ks_result.drift_detected,
            ws_result.drift_detected
        ]
        
        vote_ratio = sum(votes) / len(votes)
        drift_detected = vote_ratio >= self.ensemble_threshold
        
        # Average severity
        avg_severity = (kl_result.severity + ks_result.severity + ws_result.severity) / 3
        
        drift_type = DriftType.COVARIATE if drift_detected else DriftType.NONE
        
        if verbose:
            logger.info(
                "Ensemble drift detection",
                vote_ratio=vote_ratio,
                threshold=self.ensemble_threshold,
                drift_detected=drift_detected,
                average_severity=avg_severity
            )
        
        return DriftMetrics(
            kl_divergence=kl_result.kl_divergence,
            ks_statistic=ks_result.ks_statistic,
            ks_pvalue=ks_result.ks_pvalue,
            wasserstein_distance=ws_result.wasserstein_distance,
            distribution_shift=avg_severity,
            feature_importance_change={},
            drift_detected=drift_detected,
            drift_type=drift_type,
            severity=float(avg_severity)
        )
    
    def detect_concept_drift(
        self,
        baseline_predictions: np.ndarray,
        baseline_actuals: np.ndarray,
        current_predictions: np.ndarray,
        current_actuals: np.ndarray,
        performance_degradation_threshold: float = 0.05
    ) -> DriftMetrics:
        """
        Detect concept drift (model performance degradation)
        
        Args:
            baseline_predictions: Baseline model predictions
            baseline_actuals: Baseline ground truth
            current_predictions: Current model predictions
            current_actuals: Current ground truth
            performance_degradation_threshold: Max allowed degradation (0-1)
        
        Returns:
            Drift metrics
        """
        # Calculate error rates
        baseline_error = np.mean(np.abs(baseline_predictions - baseline_actuals))
        current_error = np.mean(np.abs(current_predictions - current_actuals))
        
        # Degradation
        if baseline_error > 0:
            degradation = (current_error - baseline_error) / baseline_error
        else:
            degradation = 0
        
        drift_detected = degradation > performance_degradation_threshold
        severity = min(1.0, degradation / (performance_degradation_threshold * 2))
        
        drift_type = DriftType.CONCEPT if drift_detected else DriftType.NONE
        
        logger.info(
            "Concept drift detection",
            baseline_error=baseline_error,
            current_error=current_error,
            degradation=degradation,
            drift_detected=drift_detected
        )
        
        return DriftMetrics(
            kl_divergence=0.0,
            ks_statistic=baseline_error,
            ks_pvalue=current_error,
            wasserstein_distance=degradation,
            distribution_shift=float(degradation),
            feature_importance_change={},
            drift_detected=drift_detected,
            drift_type=drift_type,
            severity=float(severity)
        )
    
    def _calculate_stats(self, data: np.ndarray) -> Dict[str, Any]:
        """Calculate baseline statistics"""
        return {
            'mean': np.mean(data),
            'std': np.std(data),
            'min': np.min(data),
            'max': np.max(data),
            'median': np.median(data)
        }


__all__ = ['DriftDetector', 'DriftMetrics', 'DriftType', 'DriftDetectionMethod']
