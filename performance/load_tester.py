"""
Load Testing & Benchmarking Suite
Stress tests the system and generates performance reports
"""

import time
import json
import statistics
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class LoadTestRequest:
    """Single load test request"""
    request_id: str
    product_data: Dict[str, Any]
    packaging_options: List[Dict[str, Any]]
    start_time: float
    response_time_ms: float
    success: bool
    error: str = None


@dataclass
class LoadTestResult:
    """Complete load test results"""
    test_name: str
    num_requests: int
    num_workers: int
    duration_seconds: float
    
    # Throughput
    throughput_rps: float
    requests_per_second: List[float]
    
    # Latency
    latencies: List[float]
    latency_p50: float
    latency_p75: float
    latency_p90: float
    latency_p95: float
    latency_p99: float
    latency_mean: float
    latency_std: float
    latency_min: float
    latency_max: float
    
    # Success/Failure
    success_count: int
    failure_count: int
    success_rate_pct: float
    
    # Resource usage
    peak_memory_mb: float = None
    cpu_percent: float = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


class LoadTester:
    """
    Load testing framework for ECO_PACK_AI
    """
    
    def __init__(self, inference_fn=None):
        """
        Initialize load tester
        
        Args:
            inference_fn: Function to test (recommend_packaging)
        """
        self.inference_fn = inference_fn
        self.test_results: List[LoadTestResult] = []
        
        logger.info("LoadTester initialized")
    
    def run_load_test(
        self,
        test_name: str,
        num_requests: int = 1000,
        num_workers: int = 10,
        request_data: List[Dict[str, Any]] = None,
        timeout_seconds: float = 300.0
    ) -> LoadTestResult:
        """
        Run load test
        
        Args:
            test_name: Name of test
            num_requests: Number of requests to send
            num_workers: Number of concurrent workers
            request_data: List of request data
            timeout_seconds: Test timeout
        
        Returns:
            Load test results
        """
        logger.info(
            "Starting load test",
            test_name=test_name,
            num_requests=num_requests,
            workers=num_workers
        )
        
        if request_data is None:
            request_data = self._generate_test_data(num_requests)
        
        results = []
        latencies = []
        success_count = 0
        failure_count = 0
        
        start_time = time.time()
        
        # Run load test with thread pool
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = []
            
            for i, req_data in enumerate(request_data[:num_requests]):
                future = executor.submit(self._execute_request, i, req_data)
                futures.append(future)
            
            # Collect results
            for future in as_completed(futures, timeout=timeout_seconds):
                try:
                    latency_ms = future.result()
                    latencies.append(latency_ms)
                    success_count += 1
                except Exception as e:
                    failure_count += 1
                    logger.error("Request failed", error=str(e))
        
        duration = time.time() - start_time
        
        # Calculate statistics
        if not latencies:
            logger.error("No successful requests in load test")
            return None
        
        sorted_latencies = sorted(latencies)
        
        result = LoadTestResult(
            test_name=test_name,
            num_requests=num_requests,
            num_workers=num_workers,
            duration_seconds=duration,
            throughput_rps=num_requests / duration,
            requests_per_second=self._calculate_rps(latencies, duration),
            latencies=latencies,
            latency_p50=statistics.median(sorted_latencies),
            latency_p75=self._percentile(sorted_latencies, 75),
            latency_p90=self._percentile(sorted_latencies, 90),
            latency_p95=self._percentile(sorted_latencies, 95),
            latency_p99=self._percentile(sorted_latencies, 99),
            latency_mean=statistics.mean(latencies),
            latency_std=statistics.stdev(latencies) if len(latencies) > 1 else 0,
            latency_min=min(latencies),
            latency_max=max(latencies),
            success_count=success_count,
            failure_count=failure_count,
            success_rate_pct=(success_count / (success_count + failure_count) * 100)
                             if (success_count + failure_count) > 0 else 0
        )
        
        self.test_results.append(result)
        
        logger.info(
            "Load test completed",
            test_name=test_name,
            throughput=result.throughput_rps,
            p95=result.latency_p95,
            success_rate=result.success_rate_pct
        )
        
        return result
    
    def _execute_request(self, request_id: int, request_data: Dict) -> float:
        """
        Execute single request and return latency
        
        Args:
            request_id: Request ID
            request_data: Request data
        
        Returns:
            Latency in milliseconds
        """
        if not self.inference_fn:
            # Simulate inference
            time.sleep(0.05 + (request_id % 3) * 0.01)
            return (50 + (request_id % 3) * 10)  # ms
        
        start = time.time()
        
        try:
            result = self.inference_fn(
                product=request_data.get('product'),
                packaging_options=request_data.get('packaging_options'),
                preferences=request_data.get('preferences')
            )
            latency_ms = (time.time() - start) * 1000
            return latency_ms
        
        except Exception as e:
            logger.error(f"Request {request_id} failed", error=str(e))
            raise
    
    def generate_report(self, result: LoadTestResult) -> str:
        """
        Generate markdown report from load test
        
        Args:
            result: LoadTestResult
        
        Returns:
            Markdown report
        """
        report = f"""# Load Test Report: {result.test_name}

**Generated**: {datetime.utcnow().isoformat()}

## Test Configuration

| Parameter | Value |
|-----------|-------|
| Total Requests | {result.num_requests} |
| Concurrent Workers | {result.num_workers} |
| Test Duration | {result.duration_seconds:.2f}s |
| Timeout | 300s |

## Performance Results

### Throughput
- **Requests/sec**: {result.throughput_rps:.2f}
- **Total Requests**: {result.success_count} successful, {result.failure_count} failed
- **Success Rate**: {result.success_rate_pct:.2f}%

### Latency (milliseconds)

| Percentile | Latency (ms) |
|-----------|---------|
| Min | {result.latency_min:.2f} |
| P50 | {result.latency_p50:.2f} |
| P75 | {result.latency_p75:.2f} |
| P90 | {result.latency_p90:.2f} |
| **P95** | **{result.latency_p95:.2f}** |
| **P99** | **{result.latency_p99:.2f}** |
| Mean | {result.latency_mean:.2f} |
| Std Dev | {result.latency_std:.2f} |
| Max | {result.latency_max:.2f} |

## Target Achievement

| Target | Value | Status |
|--------|-------|--------|
| P95 ≤ 150ms | {result.latency_p95:.2f}ms | {'✅ PASS' if result.latency_p95 <= 150 else '❌ FAIL'} |
| P99 ≤ 200ms | {result.latency_p99:.2f}ms | {'✅ PASS' if result.latency_p99 <= 200 else '❌ FAIL'} |
| Throughput ≥ 100 req/s | {result.throughput_rps:.2f} req/s | {'✅ PASS' if result.throughput_rps >= 100 else '❌ FAIL'} |
| Success Rate ≥ 99% | {result.success_rate_pct:.2f}% | {'✅ PASS' if result.success_rate_pct >= 99 else '❌ FAIL'} |

## Recommendations

"""
        # Add recommendations based on results
        if result.latency_p95 > 150:
            report += "- ⚠️  P95 latency exceeds target - consider model optimization or caching\n"
        
        if result.latency_p99 > 200:
            report += "- ⚠️  P99 latency exceeds target - check for outliers and bottlenecks\n"
        
        if result.throughput_rps < 100:
            report += "- ⚠️  Throughput below target - increase worker concurrency or batch size\n"
        
        if result.success_rate_pct < 99:
            report += "- ⚠️  Success rate below 99% - investigate failure modes\n"
        
        if result.latency_std > result.latency_mean:
            report += "- ⚠️  High latency variance - consider request prioritization\n"
        
        if not any([
            result.latency_p95 > 150,
            result.latency_p99 > 200,
            result.throughput_rps < 100,
            result.success_rate_pct < 99
        ]):
            report += "- ✅ All targets met! System is production-ready.\n"
        
        report += f"""

## Benchmarks

- **Inference Framework**: ECO_PACK_AI v2.0
- **Test Date**: {datetime.utcnow().isoformat()}
- **Environment**: Production Load Test

---

*Generated by ECO_PACK_AI Load Testing Suite*
"""
        return report
    
    def run_stress_test(
        self,
        max_workers: int = 100,
        step_size: int = 10,
        step_duration_seconds: int = 30
    ) -> List[LoadTestResult]:
        """
        Run stress test with gradually increasing load
        
        Args:
            max_workers: Maximum concurrent workers
            step_size: Increase workers by this amount each step
            step_duration_seconds: Duration of each step
        
        Returns:
            List of results for each load level
        """
        logger.info(
            "Starting stress test",
            max_workers=max_workers,
            step_size=step_size
        )
        
        results = []
        
        for num_workers in range(step_size, max_workers + 1, step_size):
            result = self.run_load_test(
                test_name=f"stress_test_workers_{num_workers}",
                num_requests=100,  # Small batch per step
                num_workers=num_workers,
                timeout_seconds=step_duration_seconds
            )
            
            results.append(result)
            
            # Check if system is saturated
            if num_workers > step_size and results[-1].success_rate_pct < 90:
                logger.warning(
                    "System approaching saturation",
                    workers=num_workers,
                    success_rate=results[-1].success_rate_pct
                )
                break
        
        return results
    
    def _generate_test_data(self, num_requests: int) -> List[Dict]:
        """Generate synthetic test data"""
        test_data = []
        
        for i in range(num_requests):
            product = {
                'id': f'PROD_{i % 100}',
                'category': ['Electronics', 'Fragile', 'Food'][i % 3],
                'weight': 0.5 + (i % 10) * 0.1,
                'fragility_score': 0.3 + (i % 7) * 0.1
            }
            
            packaging_options = [
                {
                    'id': 'PKG_001',
                    'material': 'Cardboard',
                    'recyclability': 95,
                    'biodegradability': 85
                },
                {
                    'id': 'PKG_002',
                    'material': 'Foam',
                    'recyclability': 30,
                    'biodegradability': 100
                },
                {
                    'id': 'PKG_003',
                    'material': 'Plastic',
                    'recyclability': 20,
                    'biodegradability': 0
                }
            ]
            
            test_data.append({
                'product': product,
                'packaging_options': packaging_options,
                'preferences': {
                    'cost_weight': 0.3,
                    'co2_weight': 0.5,
                    'damage_weight': 0.2
                }
            })
        
        return test_data
    
    def _percentile(self, data: List[float], p: float) -> float:
        """Calculate percentile"""
        k = (len(data) - 1) * p / 100
        f = int(k)
        c = k - f
        
        if f + 1 < len(data):
            return data[f] * (1 - c) + data[f + 1] * c
        
        return data[f]
    
    def _calculate_rps(self, latencies: List[float], duration: float) -> List[float]:
        """Calculate requests per second over time"""
        rps_list = []
        window_size = max(1, len(latencies) // 10)  # 10 windows
        
        for i in range(0, len(latencies), window_size):
            window = latencies[i:i + window_size]
            window_duration = sum(window) / 1000  # Convert to seconds
            
            if window_duration > 0:
                rps = len(window) / window_duration
                rps_list.append(rps)
        
        return rps_list


__all__ = ['LoadTester', 'LoadTestResult', 'LoadTestRequest']
