"""
Performance Optimization Module
Enables sub-150ms P95 inference latency
"""

import numpy as np
import time
from typing import Dict, Any, Callable, Optional
from abc import ABC, abstractmethod
import structlog
from functools import wraps
import threading
from collections import deque

logger = structlog.get_logger(__name__)


class LatencyMonitor:
    """
    Monitors inference latency and tracks percentiles
    """
    
    def __init__(self, window_size: int = 1000):
        """
        Initialize latency monitor
        
        Args:
            window_size: Moving window size for percentile calculation
        """
        self.latencies = deque(maxlen=window_size)
        self.window_size = window_size
        self.lock = threading.Lock()
        self.total_requests = 0
    
    def record(self, latency_ms: float) -> None:
        """Record latency in milliseconds"""
        with self.lock:
            self.latencies.append(latency_ms)
            self.total_requests += 1
    
    def get_percentiles(self) -> Dict[str, float]:
        """Get latency percentiles"""
        with self.lock:
            if not self.latencies:
                return {}
            
            sorted_latencies = sorted(self.latencies)
            
            return {
                'p50': float(np.percentile(sorted_latencies, 50)),
                'p75': float(np.percentile(sorted_latencies, 75)),
                'p90': float(np.percentile(sorted_latencies, 90)),
                'p95': float(np.percentile(sorted_latencies, 95)),
                'p99': float(np.percentile(sorted_latencies, 99)),
                'mean': float(np.mean(sorted_latencies)),
                'std': float(np.std(sorted_latencies)),
                'min': float(np.min(sorted_latencies)),
                'max': float(np.max(sorted_latencies)),
            }
    
    def log_summary(self) -> None:
        """Log latency summary"""
        percentiles = self.get_percentiles()
        if percentiles:
            logger.info(
                "Latency summary",
                p95=percentiles['p95'],
                p99=percentiles['p99'],
                mean=percentiles['mean'],
                total_requests=self.total_requests
            )


def timed_inference(monitor: Optional[LatencyMonitor] = None):
    """
    Decorator to measure and record inference latency
    
    Args:
        monitor: LatencyMonitor instance
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            elapsed_ms = (time.time() - start_time) * 1000
            
            if monitor:
                monitor.record(elapsed_ms)
            
            return result
        
        return wrapper
    
    return decorator


class ModelCache:
    """
    Caches model predictions to avoid redundant inference
    Thread-safe LRU cache
    """
    
    def __init__(self, max_size: int = 10000, ttl_seconds: int = 300):
        """
        Initialize model cache
        
        Args:
            max_size: Maximum cache size
            ttl_seconds: Time-to-live for cache entries
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, tuple] = {}  # {key: (value, timestamp)}
        self.lock = threading.Lock()
        self.hits = 0
        self.misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached value"""
        with self.lock:
            if key in self.cache:
                value, timestamp = self.cache[key]
                
                # Check TTL
                if time.time() - timestamp < self.ttl_seconds:
                    self.hits += 1
                    return value
                else:
                    del self.cache[key]  # Expired
                    self.misses += 1
                    return None
            
            self.misses += 1
            return None
    
    def set(self, key: str, value: Any) -> None:
        """Set cache value"""
        with self.lock:
            # Evict oldest if at capacity
            if len(self.cache) >= self.max_size:
                # Remove oldest (simplistic FIFO, not true LRU)
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
            
            self.cache[key] = (value, time.time())
    
    def clear(self) -> None:
        """Clear cache"""
        with self.lock:
            self.cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self.lock:
            total = self.hits + self.misses
            hit_rate = (self.hits / total * 100) if total > 0 else 0.0
            
            return {
                'size': len(self.cache),
                'max_size': self.max_size,
                'hits': self.hits,
                'misses': self.misses,
                'hit_rate_pct': hit_rate
            }


class BatchProcessor:
    """
    Batches requests for efficient GPU utilization
    """
    
    def __init__(
        self,
        batch_size: int = 32,
        timeout_ms: float = 100,
        inference_fn: Optional[Callable] = None
    ):
        """
        Initialize batch processor
        
        Args:
            batch_size: Batch size
            timeout_ms: Max time to wait for batch
            inference_fn: Inference function
        """
        self.batch_size = batch_size
        self.timeout_ms = timeout_ms
        self.inference_fn = inference_fn
        
        self.pending_batch = []
        self.batch_lock = threading.Lock()
        self.batch_event = threading.Event()
        self.results = {}
    
    def add_request(self, request_id: str, request_data: Any) -> Any:
        """
        Add request to batch
        
        Args:
            request_id: Unique request ID
            request_data: Request data
        
        Returns:
            Inference result
        """
        with self.batch_lock:
            self.pending_batch.append((request_id, request_data))
            
            # Check if batch is full
            if len(self.pending_batch) >= self.batch_size:
                self._process_batch()
        
        # Wait for result (with timeout)
        start = time.time()
        while request_id not in self.results:
            if (time.time() - start) * 1000 > self.timeout_ms:
                # Force process batch if timeout exceeded
                with self.batch_lock:
                    if self.pending_batch:
                        self._process_batch()
            
            time.sleep(0.001)  # Sleep 1ms to avoid busy-wait
        
        result = self.results.pop(request_id)
        return result
    
    def _process_batch(self) -> None:
        """Process pending batch"""
        if not self.pending_batch or not self.inference_fn:
            return
        
        request_ids, request_data = zip(*self.pending_batch)
        self.pending_batch = []
        
        # Batch inference
        batch_results = self.inference_fn(list(request_data))
        
        # Store results
        for req_id, result in zip(request_ids, batch_results):
            self.results[req_id] = result
        
        logger.debug(f"Batch processed: {len(request_ids)} requests")


class PerformanceOptimizer:
    """
    Coordinates performance optimization techniques
    """
    
    def __init__(
        self,
        target_p95_ms: float = 150.0,
        target_p99_ms: float = 200.0
    ):
        """
        Initialize performance optimizer
        
        Args:
            target_p95_ms: Target P95 latency
            target_p99_ms: Target P99 latency
        """
        self.target_p95_ms = target_p95_ms
        self.target_p99_ms = target_p99_ms
        
        self.latency_monitor = LatencyMonitor()
        self.prediction_cache = ModelCache()
        self.batch_processor = None
        
        logger.info(
            "PerformanceOptimizer initialized",
            target_p95=target_p95_ms,
            target_p99=target_p99_ms
        )
    
    def check_latency_targets(self) -> Dict[str, Any]:
        """Check if latency targets are met"""
        percentiles = self.latency_monitor.get_percentiles()
        
        p95_met = percentiles.get('p95', float('inf')) <= self.target_p95_ms
        p99_met = percentiles.get('p99', float('inf')) <= self.target_p99_ms
        
        return {
            'p95_target_met': p95_met,
            'p99_target_met': p99_met,
            'p95_actual': percentiles.get('p95'),
            'p99_actual': percentiles.get('p99'),
            'target_p95': self.target_p95_ms,
            'target_p99': self.target_p99_ms
        }
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """Generate performance optimization report"""
        cache_stats = self.prediction_cache.get_stats()
        latency_stats = self.latency_monitor.get_percentiles()
        target_check = self.check_latency_targets()
        
        recommendations = []
        
        # Check cache effectiveness
        if cache_stats['hit_rate_pct'] < 20:
            recommendations.append("Low cache hit rate - consider caching config adjustment")
        
        # Check P95 latency
        if not target_check['p95_target_met']:
            recommendations.append(f"P95 latency ({latency_stats['p95']:.1f}ms) exceeds target ({self.target_p95_ms}ms)")
        
        # Check P99 latency
        if not target_check['p99_target_met']:
            recommendations.append(f"P99 latency ({latency_stats['p99']:.1f}ms) exceeds target ({self.target_p99_ms}ms)")
        
        # Check variance
        if latency_stats['std'] > latency_stats['mean']:
            recommendations.append("High latency variance - consider batch size adjustment")
        
        return {
            'cache': cache_stats,
            'latency': latency_stats,
            'targets': target_check,
            'recommendations': recommendations,
            'optimization_possible': len(recommendations) > 0
        }


__all__ = [
    'LatencyMonitor',
    'ModelCache',
    'BatchProcessor',
    'PerformanceOptimizer',
    'timed_inference'
]
