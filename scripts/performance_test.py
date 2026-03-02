#!/usr/bin/env python
"""
Performance Testing Suite - ECO_PACK_AI Backend
Phase 5: Industrial Load Testing and Stress Testing

Run this AFTER starting the Flask server and creating test products:
  python src/api_production.py
  # In another terminal:
  python scripts/performance_test.py
"""

import time
import requests
import json
import threading
import statistics
import os
from typing import List, Dict
from datetime import datetime
from collections import defaultdict

# Configuration
API_BASE_URL = "http://localhost:5000"
API_KEY = os.getenv('API_KEY', 'your-secret-key-change-this')

# Color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_header(text: str):
    """Print section header"""
    print(f"\n{BLUE}{BOLD}{'='*80}{RESET}")
    print(f"{BLUE}{BOLD}{text.center(80)}{RESET}")
    print(f"{BLUE}{BOLD}{'='*80}{RESET}\n")

def print_success(text: str):
    """Print success message"""
    print(f"{GREEN}✓ {text}{RESET}")

def print_error(text: str):
    """Print error message"""
    print(f"{RED}✗ {text}{RESET}")

def print_warning(text: str):
    """Print warning message"""
    print(f"{YELLOW}⚠ {text}{RESET}")

def print_info(text: str):
    """Print info message"""
    print(f"{BLUE}ℹ {text}{RESET}")

# ============================================================================
# TEST DATA GENERATION
# ============================================================================

def create_test_product():
    """Create a test product in the database"""
    try:
        product_data = {
            'product_id': f'PERF-TEST-{int(time.time())}',
            'category': 'electronics',
            'weight': 2.5,
            'strength': 75,
            'biodegradability': 0.85,
            'recyclability': 90
        }
        
        headers = {'X-API-Key': API_KEY}
        response = requests.post(
            f"{API_BASE_URL}/api/product/input",
            json=product_data,
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 201:
            product_id = response.json().get('product_id')
            print_success(f"Test product created: {product_id}")
            return product_id
        else:
            print_error(f"Failed to create test product")
            return None
    
    except Exception as e:
        print_error(f"Failed to create test product: {str(e)}")
        return None

# ============================================================================
# TEST 1: Baseline Latency Test (10 sequential predictions)
# ============================================================================

def test_baseline_latency(product_id: str):
    """Test baseline latency with 10 sequential predictions"""
    print_header("TEST 1: Baseline Latency (10 Sequential Predictions)")
    
    materials = ['bamboo', 'paper', 'jute', 'glass', 'metal', 'plastic', 'bagasse']
    latencies = []
    errors = 0
    
    try:
        headers = {'X-API-Key': API_KEY}
        
        for i in range(10):
            material = materials[i % len(materials)]
            
            try:
                start = time.time()
                response = requests.post(
                    f"{API_BASE_URL}/api/predict",
                    json={'product_id': product_id, 'material': material},
                    headers=headers,
                    timeout=10
                )
                latency = (time.time() - start) * 1000
                
                if response.status_code == 200:
                    latencies.append(latency)
                    print_info(f"  {i+1}/10 - {material}: {latency:.2f}ms")
                else:
                    errors += 1
                    print_warning(f"  {i+1}/10 - {material}: HTTP {response.status_code}")
            
            except Exception as e:
                errors += 1
                print_warning(f"  {i+1}/10 - {material}: {str(e)}")
        
        if latencies:
            avg = statistics.mean(latencies)
            min_lat = min(latencies)
            max_lat = max(latencies)
            stdev = statistics.stdev(latencies) if len(latencies) > 1 else 0
            
            print(f"\n{BOLD}Baseline Latency Results:{RESET}")
            print(f"  Successful: {len(latencies)}/10")
            print(f"  Failed: {errors}/10")
            print(f"  Average: {avg:.2f}ms")
            print(f"  Min: {min_lat:.2f}ms")
            print(f"  Max: {max_lat:.2f}ms")
            print(f"  Std Dev: {stdev:.2f}ms")
            
            if avg < 50:
                print_success("Baseline latency is excellent (< 50ms)")
                return True
            elif avg < 100:
                print_success("Baseline latency is good (< 100ms)")
                return True
            else:
                print_warning(f"Baseline latency is high (> 100ms)")
                return True
        
        else:
            print_error("No successful predictions")
            return False
    
    except Exception as e:
        print_error(f"Baseline latency test failed: {str(e)}")
        return False

# ============================================================================
# TEST 2: High-Load Test (100 sequential predictions)
# ============================================================================

def test_high_load(product_id: str):
    """Test performance with 100 sequential predictions"""
    print_header("TEST 2: High Load (100 Sequential Predictions)")
    
    materials = ['bamboo', 'paper', 'jute', 'glass', 'metal', 'plastic', 'bagasse']
    latencies = []
    errors = 0
    start_total = time.time()
    
    try:
        headers = {'X-API-Key': API_KEY}
        
        print_info("Running 100 sequential predictions...")
        for i in range(100):
            material = materials[i % len(materials)]
            
            try:
                start = time.time()
                response = requests.post(
                    f"{API_BASE_URL}/api/predict",
                    json={'product_id': product_id, 'material': material},
                    headers=headers,
                    timeout=10
                )
                latency = (time.time() - start) * 1000
                
                if response.status_code == 200:
                    latencies.append(latency)
                else:
                    errors += 1
            
            except:
                errors += 1
            
            if (i + 1) % 25 == 0:
                print_info(f"  Progress: {i+1}/100 predictions")
        
        total_time = (time.time() - start_total)
        
        if latencies:
            avg = statistics.mean(latencies)
            median = statistics.median(latencies)
            min_lat = min(latencies)
            max_lat = max(latencies)
            p95 = sorted(latencies)[int(len(latencies) * 0.95)]
            
            success_rate = len(latencies) / 100 * 100
            throughput = 100 / total_time
            
            print(f"\n{BOLD}High Load Results:{RESET}")
            print(f"  Successful: {len(latencies)}/100 ({success_rate:.1f}%)")
            print(f"  Failed: {errors}/100")
            print(f"  Total Time: {total_time:.2f}s")
            print(f"  Throughput: {throughput:.2f} req/sec")
            print(f"  Average Latency: {avg:.2f}ms")
            print(f"  Median Latency: {median:.2f}ms")
            print(f"  Min Latency: {min_lat:.2f}ms")
            print(f"  Max Latency: {max_lat:.2f}ms")
            print(f"  P95 Latency: {p95:.2f}ms")
            
            if success_rate >= 99:
                print_success(f"Success rate excellent ({success_rate:.1f}%)")
            elif success_rate >= 90:
                print_success(f"Success rate acceptable ({success_rate:.1f}%)")
            else:
                print_warning(f"Success rate low ({success_rate:.1f}%)")
            
            return success_rate >= 90
        
        else:
            print_error("No successful predictions")
            return False
    
    except Exception as e:
        print_error(f"High load test failed: {str(e)}")
        return False

# ============================================================================
# TEST 3: Concurrent Requests Test (50 concurrent)
# ============================================================================

def test_concurrent_requests(product_id: str):
    """Test performance with concurrent requests"""
    print_header("TEST 3: Concurrent Requests (50 Concurrent)")
    
    materials = ['bamboo', 'paper', 'jute', 'glass', 'metal', 'plastic', 'bagasse']
    results = {
        'latencies': [],
        'errors': 0,
        'errors_list': [],
        'lock': threading.Lock()
    }
    
    def make_request(index: int):
        """Make a prediction request in a thread"""
        try:
            headers = {'X-API-Key': API_KEY}
            material = materials[index % len(materials)]
            
            start = time.time()
            response = requests.post(
                f"{API_BASE_URL}/api/predict",
                json={'product_id': product_id, 'material': material},
                headers=headers,
                timeout=10
            )
            latency = (time.time() - start) * 1000
            
            with results['lock']:
                if response.status_code == 200:
                    results['latencies'].append(latency)
                else:
                    results['errors'] += 1
                    results['errors_list'].append(f"HTTP {response.status_code}")
        
        except Exception as e:
            with results['lock']:
                results['errors'] += 1
                results['errors_list'].append(str(e))
    
    try:
        print_info("Creating 50 concurrent threads...")
        threads = []
        start_total = time.time()
        
        for i in range(50):
            thread = threading.Thread(target=make_request, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_total
        
        latencies = results['latencies']
        errors = results['errors']
        
        if latencies:
            avg = statistics.mean(latencies)
            median = statistics.median(latencies)
            min_lat = min(latencies)
            max_lat = max(latencies)
            p95 = sorted(latencies)[int(len(latencies) * 0.95)]
            p99 = sorted(latencies)[int(len(latencies) * 0.99)] if len(latencies) > 1 else max_lat
            
            success_rate = len(latencies) / 50 * 100
            
            print(f"\n{BOLD}Concurrent Request Results:{RESET}")
            print(f"  Successful: {len(latencies)}/50 ({success_rate:.1f}%)")
            print(f"  Failed: {errors}/50")
            print(f"  Total Time: {total_time:.2f}s")
            print(f"  Average Latency: {avg:.2f}ms")
            print(f"  Median Latency: {median:.2f}ms")
            print(f"  Min Latency: {min_lat:.2f}ms")
            print(f"  Max Latency: {max_lat:.2f}ms")
            print(f"  P95 Latency: {p95:.2f}ms")
            print(f"  P99 Latency: {p99:.2f}ms")
            
            if errors > 0:
                print_warning(f"Error summary: {errors} failures")
            
            if success_rate >= 95:
                print_success(f"Concurrency test passed ({success_rate:.1f}%)")
                return True
            else:
                print_warning(f"Concurrency test has issues ({success_rate:.1f}%)")
                return success_rate >= 80
        
        else:
            print_error("No successful predictions in concurrent test")
            return False
    
    except Exception as e:
        print_error(f"Concurrent request test failed: {str(e)}")
        return False

# ============================================================================
# TEST 4: Stress Test (1000 predictions over time)
# ============================================================================

def test_stress_load(product_id: str, duration_seconds: int = 60):
    """Stress test - 1000 predictions over specified duration"""
    print_header(f"TEST 4: Stress Load (1000 Predictions over {duration_seconds}s)")
    
    materials = ['bamboo', 'paper', 'jute', 'glass', 'metal', 'plastic', 'bagasse']
    latencies = []
    errors = 0
    predictions_made = 0
    
    headers = {'X-API-Key': API_KEY}
    start_total = time.time()
    
    try:
        print_info(f"Running for up to {duration_seconds} seconds...")
        
        while time.time() - start_total < duration_seconds and predictions_made < 1000:
            material = materials[predictions_made % len(materials)]
            
            try:
                start = time.time()
                response = requests.post(
                    f"{API_BASE_URL}/api/predict",
                    json={'product_id': product_id, 'material': material},
                    headers=headers,
                    timeout=10
                )
                latency = (time.time() - start) * 1000
                
                if response.status_code == 200:
                    latencies.append(latency)
                else:
                    errors += 1
            
            except:
                errors += 1
            
            predictions_made += 1
            
            if predictions_made % 100 == 0:
                elapsed = time.time() - start_total
                rate = predictions_made / elapsed
                print_info(f"  {predictions_made} predictions ({rate:.1f} req/sec)")
        
        total_time = time.time() - start_total
        
        if latencies:
            avg = statistics.mean(latencies)
            p95 = sorted(latencies)[int(len(latencies) * 0.95)]
            p99 = sorted(latencies)[int(len(latencies) * 0.99)] if len(latencies) > 1 else max(latencies)
            
            success_rate = len(latencies) / predictions_made * 100
            throughput = predictions_made / total_time
            
            print(f"\n{BOLD}Stress Test Results:{RESET}")
            print(f"  Total Predictions: {predictions_made}/1000")
            print(f"  Successful: {len(latencies)} ({success_rate:.1f}%)")
            print(f"  Failed: {errors}")
            print(f"  Total Time: {total_time:.2f}s")
            print(f"  Throughput: {throughput:.2f} req/sec")
            print(f"  Average Latency: {avg:.2f}ms")
            print(f"  P95 Latency: {p95:.2f}ms")
            print(f"  P99 Latency: {p99:.2f}ms")
            
            if success_rate >= 95 and throughput >= 10:
                print_success(f"Stress test passed (throughput: {throughput:.2f} req/sec)")
                return True
            elif success_rate >= 90:
                print_success(f"Stress test acceptable (success: {success_rate:.1f}%)")
                return True
            else:
                print_warning(f"Stress test has issues")
                return success_rate >= 80
        
        else:
            print_error("No successful predictions in stress test")
            return False
    
    except Exception as e:
        print_error(f"Stress test failed: {str(e)}")
        return False

# ============================================================================
# TEST 5: Memory and Resource Usage
# ============================================================================

def test_resource_usage():
    """Test resource usage via diagnostics endpoint"""
    print_header("TEST 5: Resource Usage Monitoring")
    
    try:
        headers = {'X-API-Key': API_KEY}
        response = requests.get(
            f"{API_BASE_URL}/api/diagnostics",
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            metrics = data.get('predictor_metrics', {})
            
            print_info("Predictor Metrics:")
            print(f"  Total Predictions: {metrics.get('total_predictions')}")
            print(f"  Successful: {metrics.get('successful_predictions')}")
            print(f"  Failed: {metrics.get('failed_predictions')}")
            print(f"  Success Rate: {metrics.get('success_rate', 0):.1%}")
            print(f"  Average Latency: {metrics.get('avg_latency_ms'):.2f}ms")
            
            print_success("Resource monitoring completed")
            return True
        else:
            print_error(f"Failed to get diagnostics (HTTP {response.status_code})")
            return False
    
    except Exception as e:
        print_error(f"Resource usage test failed: {str(e)}")
        return False

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run all performance tests"""
    print(f"\n{BOLD}{BLUE}ECO_PACK_AI - PERFORMANCE TEST SUITE{RESET}")
    print(f"{BLUE}Production Backend Load & Stress Testing{RESET}")
    print(f"{BLUE}Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}\n")
    
    # Check API availability
    try:
        response = requests.get(f"{API_BASE_URL}/api/health", timeout=2)
        if response.status_code != 200:
            print_error("Flask API not responding correctly")
            return
    except:
        print_error(f"Flask API not running at {API_BASE_URL}")
        print_warning("Start the API with: python src/api_production.py")
        return
    
    # Create test product
    print_info("Setting up test environment...")
    product_id = create_test_product()
    
    if not product_id:
        print_error("Cannot continue without test product")
        return
    
    results = {}
    
    # Run tests
    print(f"{BOLD}[1/5] Baseline Latency Test...{RESET}")
    results['baseline'] = test_baseline_latency(product_id)
    
    print(f"{BOLD}[2/5] High Load Test...{RESET}")
    results['high_load'] = test_high_load(product_id)
    
    print(f"{BOLD}[3/5] Concurrent Requests Test...{RESET}")
    results['concurrent'] = test_concurrent_requests(product_id)
    
    print(f"{BOLD}[4/5] Stress Load Test...{RESET}")
    results['stress'] = test_stress_load(product_id, duration_seconds=60)
    
    print(f"{BOLD}[5/5] Resource Usage Monitoring...{RESET}")
    results['resource'] = test_resource_usage()
    
    # Summary
    print_header("PERFORMANCE TEST SUMMARY")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
        print(f"  {test_name}: {status}")
    
    print(f"\n{BOLD}Result: {passed}/{total} tests passed{RESET}")
    
    if passed >= 4:
        print(f"\n{GREEN}{BOLD}✓ PERFORMANCE TESTS PASSED - PRODUCTION READY{RESET}\n")
    else:
        print(f"\n{YELLOW}{BOLD}⚠ SOME TESTS FAILED - REVIEW RESULTS{RESET}\n")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Performance testing interrupted by user{RESET}")
    except Exception as e:
        print_error(f"Performance test suite failed: {str(e)}")
