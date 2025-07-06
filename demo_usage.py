#!/usr/bin/env python3
"""
Example script showing how to use the LoadGenie K6 Runner API
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:8001"

def check_service_health():
    """Check if the service is running and healthy"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Service is healthy")
            return True
        else:
            print(f"❌ Service health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to service. Make sure it's running on port 8001")
        return False

def check_k6_health():
    """Check if K6 runner is ready"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/test/health")
        if response.status_code == 200:
            print("✅ K6 runner is ready")
            return True
        else:
            print(f"❌ K6 runner not ready: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ K6 health check failed: {e}")
        return False

def run_simple_test():
    """Run a simple load test"""
    print("\n🚀 Running a simple load test...")
    
    # Define the K6 script
    script = """
    import http from 'k6/http';
    import { check, sleep } from 'k6';
    
    export default function() {
        const response = http.get('https://httpbin.org/get');
        
        check(response, {
            'status is 200': (r) => r.status === 200,
            'response time < 2000ms': (r) => r.timings.duration < 2000,
        });
        
        sleep(0.1); // Small delay between requests
    }
    """
    
    # Test configuration
    payload = {
        "script": script,
        "options": {
            "vus": 5,
            "duration": "15s"
        }
    }
    
    try:
        # Start the test
        print("⏳ Starting test execution...")
        response = requests.post(f"{BASE_URL}/api/v1/test/run", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            
            # Display results
            print(f"✅ Test completed!")
            print(f"   Test ID: {result['test_id']}")
            print(f"   Execution Time: {result['execution_time']:.2f}s")
            print(f"   Status: {result['status']}")
            
            # Show metrics
            metrics = result['metrics']
            print(f"\n📊 Performance Metrics:")
            print(f"   Virtual Users: {metrics['virtual_users']}")
            print(f"   Total Requests: {metrics['total_requests']}")
            print(f"   Avg Response Time: {metrics['response_time_avg']:.1f}ms")
            print(f"   P95 Response Time: {metrics['response_time_p95']:.1f}ms")
            print(f"   Error Rate: {metrics['error_rate']:.1f}%")
            print(f"   Throughput: {metrics['requests_per_second']:.1f} RPS")
            
            # Show anomaly analysis
            anomaly = result['anomaly_analysis']
            print(f"\n🔍 Anomaly Analysis:")
            print(f"   Anomalies Detected: {anomaly['anomalies_detected']}")
            print(f"   Severity: {anomaly['severity']}")
            print(f"   Confidence: {anomaly['confidence']:.1%}")
            
            if anomaly['issues']:
                print(f"   Issues:")
                for issue in anomaly['issues']:
                    print(f"     - {issue}")
            
            print(f"   Recommendations:")
            for rec in anomaly['recommendations']:
                print(f"     - {rec}")
                
            return result['test_id']
            
        else:
            print(f"❌ Test failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return None

def view_test_history():
    """View recent test history"""
    print("\n📈 Recent Test History:")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/test/history?limit=5")
        
        if response.status_code == 200:
            data = response.json()
            tests = data.get('tests', [])
            
            if not tests:
                print("   No tests found")
                return
            
            for i, test in enumerate(tests, 1):
                metrics = test['metrics']
                anomaly = test['anomaly_analysis']
                
                print(f"\n   {i}. Test {test['test_id'][:8]}...")
                print(f"      Time: {test['timestamp']}")
                print(f"      Duration: {test['execution_time']:.1f}s")
                print(f"      Avg Response: {metrics['response_time_avg']:.1f}ms")
                print(f"      Error Rate: {metrics['error_rate']:.1f}%")
                print(f"      Anomalies: {'Yes' if anomaly['anomalies_detected'] else 'No'}")
                
        else:
            print(f"   Failed to get history: {response.status_code}")
            
    except Exception as e:
        print(f"   Error getting history: {e}")

def get_test_statistics():
    """Get overall test statistics"""
    print("\n📊 Test Statistics:")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/test/statistics")
        
        if response.status_code == 200:
            stats = response.json()
            
            print(f"   Total Tests: {stats['total_tests']}")
            print(f"   Avg Response Time: {stats['avg_response_time']:.1f}ms")
            print(f"   Avg Error Rate: {stats['avg_error_rate']:.1f}%")
            print(f"   Avg Throughput: {stats['avg_throughput']:.1f} RPS")
            print(f"   Tests with Anomalies: {stats['tests_with_anomalies']}")
            
        else:
            print(f"   Failed to get statistics: {response.status_code}")
            
    except Exception as e:
        print(f"   Error getting statistics: {e}")

def main():
    """Main demonstration function"""
    print("🎯 LoadGenie K6 Runner Demo")
    print("=" * 40)
    
    # Check service health
    if not check_service_health():
        return
    
    if not check_k6_health():
        return
    
    # Run a test
    test_id = run_simple_test()
    
    if test_id:
        # Wait a moment then view history
        time.sleep(1)
        view_test_history()
        get_test_statistics()
    
    print(f"\n🌐 Web Interface: {BASE_URL}/docs")
    print("📚 API Documentation available at the URL above")
    print("\nTry running more tests with different configurations!")

if __name__ == "__main__":
    main()
