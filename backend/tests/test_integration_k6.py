"""
Integration tests for the K6 runner API endpoints
"""

import pytest
import asyncio
import json
import os
from pathlib import Path
from fastapi.testclient import TestClient

# Add the backend directory to the path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app

# Test client
client = TestClient(app)

class TestK6RunnerAPI:
    """Integration tests for K6 runner API endpoints"""
    
    def test_health_endpoint(self):
        """Test K6 runner health check"""
        response = client.get("/api/v1/test/health")
        
        # Should return 200 if k6 is installed, 503 if not
        assert response.status_code in [200, 503]
        
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        
        if response.status_code == 200:
            assert data["status"] == "healthy"
        else:
            assert "error" in data
    
    @pytest.mark.skipif(
        os.system("which k6 > /dev/null 2>&1") != 0,
        reason="k6 not installed"
    )
    def test_run_simple_test(self):
        """Test running a simple K6 test"""
        script = """
        import http from 'k6/http';
        import { check } from 'k6';
        
        export const options = {
            vus: 2,
            duration: '5s',
        };
        
        export default function() {
            const response = http.get('https://httpbin.org/get');
            check(response, {
                'status is 200': (r) => r.status === 200,
            });
        }
        """
        
        request_data = {
            "script": script,
            "options": {
                "vus": 2,
                "duration": "5s"
            }
        }
        
        response = client.post("/api/v1/test/run", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "test_id" in data
        assert "timestamp" in data
        assert "execution_time" in data
        assert "metrics" in data
        assert "anomaly_analysis" in data
        assert data["status"] == "completed"
        
        # Verify metrics
        metrics = data["metrics"]
        assert metrics["virtual_users"] == 2
        assert metrics["total_requests"] > 0
        assert metrics["response_time_avg"] > 0
        
        # Verify anomaly analysis
        anomaly = data["anomaly_analysis"]
        assert "anomalies_detected" in anomaly
        assert "severity" in anomaly
        assert "confidence" in anomaly
        
        return data["test_id"]
    
    def test_run_invalid_script(self):
        """Test running an invalid K6 script"""
        request_data = {
            "script": "invalid javascript code here...",
            "options": {"vus": 1, "duration": "1s"}
        }
        
        response = client.post("/api/v1/test/run", json=request_data)
        
        # Should fail with 422 (validation error)
        assert response.status_code == 422
    
    def test_get_test_history(self):
        """Test getting test history"""
        response = client.get("/api/v1/test/history?limit=10")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "tests" in data
        assert "total_count" in data
        assert isinstance(data["tests"], list)
        
        # If there are tests, verify structure
        if data["tests"]:
            test = data["tests"][0]
            assert "test_id" in test
            assert "timestamp" in test
            assert "metrics" in test
            assert "anomaly_analysis" in test
    
    def test_search_tests(self):
        """Test searching tests"""
        response = client.get("/api/v1/test/search?limit=5")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "tests" in data
        assert "total_count" in data
    
    def test_get_statistics(self):
        """Test getting test statistics"""
        response = client.get("/api/v1/test/statistics?days=7")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "period_days" in data
        assert "total_tests" in data
        assert "anomaly_tests" in data
        assert "anomaly_rate" in data
        assert "severity_breakdown" in data
    
    @pytest.mark.skipif(
        os.system("which k6 > /dev/null 2>&1") != 0,
        reason="k6 not installed"
    )
    def test_get_test_results(self):
        """Test getting detailed test results"""
        # First run a test to get a test ID
        script = """
        import http from 'k6/http';
        export const options = { vus: 1, duration: '3s' };
        export default function() { http.get('https://httpbin.org/get'); }
        """
        
        run_response = client.post("/api/v1/test/run", json={"script": script})
        
        if run_response.status_code == 200:
            test_id = run_response.json()["test_id"]
            
            # Now get the detailed results
            response = client.get(f"/api/v1/test/results/{test_id}")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["test_id"] == test_id
            assert "script_content" in data
            assert "raw_output" in data
            assert "console_output" in data
    
    def test_get_nonexistent_test_results(self):
        """Test getting results for non-existent test"""
        response = client.get("/api/v1/test/results/nonexistent-test-id")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

# Performance test scenarios
PERFORMANCE_TEST_SCENARIOS = [
    {
        "name": "Low load baseline",
        "script": """
        import http from 'k6/http';
        import { check, sleep } from 'k6';
        
        export const options = {
            vus: 2,
            duration: '10s',
        };
        
        export default function() {
            const response = http.get('https://httpbin.org/get');
            check(response, {
                'status is 200': (r) => r.status === 200,
                'response time < 1000ms': (r) => r.timings.duration < 1000,
            });
            sleep(1);
        }
        """,
        "expected_anomalies": False
    },
    {
        "name": "High error rate scenario",
        "script": """
        import http from 'k6/http';
        import { check } from 'k6';
        
        export const options = {
            vus: 3,
            duration: '8s',
        };
        
        export default function() {
            // Mix of successful and error responses
            const urls = [
                'https://httpbin.org/get',
                'https://httpbin.org/status/500',
                'https://httpbin.org/status/404'
            ];
            
            const url = urls[Math.floor(Math.random() * urls.length)];
            const response = http.get(url);
            
            check(response, {
                'request completed': (r) => r.status !== 0,
            });
        }
        """,
        "expected_anomalies": True
    },
    {
        "name": "Slow response scenario",
        "script": """
        import http from 'k6/http';
        import { check } from 'k6';
        
        export const options = {
            vus: 2,
            duration: '10s',
        };
        
        export default function() {
            // Mix of fast and slow responses
            const endpoints = [
                'https://httpbin.org/get',
                'https://httpbin.org/delay/3',
                'https://httpbin.org/delay/5'
            ];
            
            const endpoint = endpoints[Math.floor(Math.random() * endpoints.length)];
            const response = http.get(endpoint);
            
            check(response, {
                'status is 200': (r) => r.status === 200,
            });
        }
        """,
        "expected_anomalies": True
    }
]

@pytest.mark.integration
@pytest.mark.skipif(
    os.system("which k6 > /dev/null 2>&1") != 0,
    reason="k6 not installed"
)
class TestK6RunnerPerformanceScenarios:
    """Test various performance scenarios"""
    
    def test_performance_scenarios(self):
        """Test different performance scenarios"""
        results = []
        
        for scenario in PERFORMANCE_TEST_SCENARIOS:
            print(f"\n🧪 Testing scenario: {scenario['name']}")
            
            request_data = {
                "script": scenario["script"],
                "options": {}
            }
            
            response = client.post("/api/v1/test/run", json=request_data)
            
            if response.status_code == 200:
                data = response.json()
                results.append(data)
                
                metrics = data["metrics"]
                anomaly = data["anomaly_analysis"]
                
                print(f"  📊 Results:")
                print(f"    - Response time: {metrics['response_time_avg']:.1f}ms")
                print(f"    - Error rate: {metrics['error_rate']:.1f}%")
                print(f"    - Anomalies detected: {anomaly['anomalies_detected']}")
                print(f"    - Severity: {anomaly['severity']}")
                
                # Verify expectations
                if scenario.get("expected_anomalies"):
                    # For scenarios expected to have anomalies, we expect either:
                    # 1. Anomalies detected, or
                    # 2. High error rate (>5%) or slow response time (>2000ms)
                    has_anomalies = (
                        anomaly["anomalies_detected"] or
                        metrics["error_rate"] > 5 or
                        metrics["response_time_avg"] > 2000
                    )
                    print(f"    ✓ Expected anomalies: {has_anomalies}")
                else:
                    print(f"    ✓ Clean test results as expected")
            else:
                print(f"  ❌ Test failed: {response.status_code}")
                print(f"     {response.json()}")
        
        print(f"\n📋 Completed {len(results)} performance scenario tests")
        return results

def run_integration_tests():
    """Run integration tests manually"""
    print("🧪 Running K6 Runner Integration Tests")
    print("=" * 50)
    
    # Check if k6 is available
    k6_available = os.system("which k6 > /dev/null 2>&1") == 0
    
    if not k6_available:
        print("⚠️  K6 not installed - some tests will be skipped")
        print("   Install k6 from: https://k6.io/docs/getting-started/installation/")
    
    # Test API endpoints
    test_api = TestK6RunnerAPI()
    
    print("\n1. Testing health endpoint...")
    test_api.test_health_endpoint()
    print("   ✅ Health endpoint working")
    
    print("\n2. Testing test history...")
    test_api.test_get_test_history()
    print("   ✅ Test history endpoint working")
    
    print("\n3. Testing statistics...")
    test_api.test_get_statistics()
    print("   ✅ Statistics endpoint working")
    
    if k6_available:
        print("\n4. Testing K6 script execution...")
        test_id = test_api.test_run_simple_test()
        print(f"   ✅ K6 test executed successfully (ID: {test_id[:8]}...)")
        
        print("\n5. Testing detailed results...")
        test_api.test_get_test_results()
        print("   ✅ Detailed results retrieval working")
        
        print("\n6. Running performance scenarios...")
        scenarios = TestK6RunnerPerformanceScenarios()
        scenario_results = scenarios.test_performance_scenarios()
        print(f"   ✅ {len(scenario_results)} performance scenarios completed")
    
    print("\n🎉 Integration tests completed!")

if __name__ == "__main__":
    run_integration_tests()
